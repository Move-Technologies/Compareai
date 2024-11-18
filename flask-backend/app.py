from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import openai
from dotenv import load_dotenv
import logging
import pymupdf
import json
import re
import pandas as pd
from datetime import datetime
from fuzzywuzzy import fuzz
from typing import Dict
import numpy as np

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Remove or comment out this function since we're not using OCR
# def setup_tesseract():
#     """Configure Tesseract OCR path"""
#     try:
#         if 'TESSDATA_PREFIX' not in os.environ:
#             unix_paths = [
#                 '/usr/share/tessdata',
#                 '/usr/local/share/tessdata',
#                 '/app/.apt/usr/share/tessdata',
#                 './tessdata'
#             ]
#             
#             for path in unix_paths:
#                 if os.path.exists(path):
#                     os.environ['TESSDATA_PREFIX'] = path
#                     break
#             
#             if 'TESSDATA_PREFIX' not in os.environ:
#                 logger.warning("No Tesseract data path found. OCR might be limited.")
#     except Exception as e:
#         logger.error(f"Error setting up Tesseract: {str(e)}")

# Remove this line since we're not using the setup function
# setup_tesseract()

UNIT_STANDARDIZATION = {
    'SF': 'square_feet',
    'LF': 'linear_feet',
    'EA': 'each',
    'HR': 'hours',
    'MO': 'months',
    'WK': 'weeks',
    'CF': 'cubic_feet',
    'DA': 'days',
    'SQ': 'square' 
}

CATEGORIES = ['ACCESSORIES - MOBILE HOME', 'FLOOR COVERING - CARPET', 'OFFICE SUPPLIES', 'ORNAMENTAL IRON', 'PERSONAL CARE & BEAUTY', 'PERISHABLE - NON-PERISHABLE', 'PET & ANIMAL SUPPLIES', 'INTERIOR LATH & PLASTER', 'PLUMBING', 'PANELING & WOOD WALL FINISHES', 'PAINTING', 'SWIMMING POOLS & SPAS', 'ROOFING', 'SCAFFOLDING', 'SIDING', 'SOFFIT, FASCIA, & GUTTER', 'SPECIALTY ITEMS', 'SPORTING GOODS & OUTDOORS', 'STEEL JOIST COMPONENTS', 'STEEL COMPONENTS', 'STAIRS', 'STUCCO & EXTERIOR PLASTER', 'TOILET & BATH ACCESSORIES', 'TRAUMA/CRIME SCENE REMEDIATION', 'TILE', 'TIMBER FRAMING', 'TEMPORARY REPAIRS', 'TOOLS', 'TOYS & GAMES', 'USER DEFINED ITEMS', 'VALUATION TOOL COST', 'WINDOWS - ALUMINUM', 'WINDOWS - SLIDING PATIO DOORS', 'WINDOW REGLAZING & REPAIR', 'WINDOWS - SKYLIGHTS', 'WINDOW TREATMENT', 'WINDOWS - VINYL', 'WINDOWS - WOOD', 'WALLPAPER', 'WATER EXTRACTION & REMEDIATION', 'EXTERIOR STRUCTURES', 'AUTOMOTIVE & MOTORCYCLE ACC.', 'ANTIQUES & VINTAGE GOODS', 'APPLIANCES - MAJOR W/O INSTALL', 'APPLIANCES', 'APPLIANCES - SMALL', 'ART RESTORATION, CONSERVATION', 'ARTWORK', 'AWNINGS & PATIO COVERS', 'BUSINESS GOODS & EQUIPMENT', 'BOOKS, MAGAZINES & PERIODICALS', 'CABINETRY', 'CONT: CLEAN APPLIANCES', 'CASH & SECURITIES', 'CAMERAS, CAMCORDERS & EQUIP.', 'CONT: GARMENT & SOFT GOODS CLN', 'CONT: CLEAN ELECTRIC ITEMS', 'CONT: CLEAN - GENERAL ITEMS', 'CONT: CLEAN - HARD FURNITURE', 'CLOTHING & ACCESSORIES', 'CONT: CLEAN - LAMPS OR VASES', 'CLEANING', 'COMPUTERS & RELATED GOODS', 'CONCRETE & ASPHALT', 'CONTENT MANIPULATION', 'CONT: PACKING,HANDLNG,STORAGE', 'CREDIT', 'CONT: CLEAN, UPHOLSTERY & SOFT', 'CONT: CEILING/WALL HANGINGS', 'GENERAL DEMOLITION', 'DOCUMENTS & VALUABLE PAPERS', 'DOORS', 'DRYWALL', 'ELECTRONICS', 'ELECTRICAL', 'ELECTRICAL - SPECIAL SYSTEMS', 'MISC. EQUIPMENT - AGRICULTURAL', 'MISC. EQUIPMENT - COMMERCIAL', 'HEAVY EQUIPMENT', 'EXCAVATION', 'FLOOR COVERING - RESILIENT', 'FLOOR COVERING - STONE', 'FLOOR COVERING - CERAMIC TILE', 'FLOOR COVERING - VINYL', 'FLOOR COVERING - WOOD', 'FEES - CONTENTS MISC.', 'PERMITS AND FEES', 'FENCING', 'FINISH CARPENTRY / TRIMWORK', 'FINISH HARDWARE', 'FIREPLACES', 'FIRE PROTECTION SYSTEMS', 'FRAMING & ROUGH CARPENTRY', 'FURNITURE - HOME & OFFICE', 'GLASS, GLAZING, & STOREFRONTS', 'FIREARMS & ACCESSORIES', 'HOUSEWARES - DINING & FLATWARE', 'HEALTH & MEDICAL SUPPLIES', 'HAZARDOUS MATERIAL REMEDIATION', 'HOBBIES & COLLECTIBLES', 'HOUSEWARES - HOME DECOR', 'HEAT, VENT & AIR CONDITIONING', 'INFANT & BABY RELATED GOODS', 'INSULATION - MECHANICAL', 'JEWELRY & WATCHES', 'KITCHENWARE', 'LABOR ONLY', 'LAWN, GARDEN & PATIO', 'LINENS & SOFTGOODS', 'LIGHT FIXTURES', 'LANDSCAPING', 'LUGGAGE, BAGS & ACCESSORIES', 'MARBLE - CULTURED OR NATURAL', 'MUSIC, MOVIES & MEDIA', 'MOISTURE PROTECTION', 'MIRRORS & SHOWER DOORS', 'MOBILE HOMES, SKIRTING & SETUP', 'METAL STRUCTURES & COMPONENTS', 'MUSICAL INSTRUMENTS & EQUIP.']

def create_category_patterns():
    """Create intuitive category patterns with comprehensive item associations"""
    return {
        'ACCESSORIES - MOBILE HOME': r'(?i)(skirting|tie|anchor|mobile home|trailer|stabilizer|leveling|step|underpinning)',
        'FLOOR COVERING': r'(?i)(floor|carpet|tile|vinyl|wood|laminate|grout|hardwood|ceramic|stone|padding|rug|linoleum|parquet|bamboo|cork|epoxy)',
        'OFFICE SUPPLIES': r'(?i)(pen|pencil|paper|stapler|clipboard|folder|file|ink|toner|notebook|desk|office|stamp|envelope|label|printer|copier|calculator)',
        'ORNAMENTAL IRON': r'(?i)(railing|gate|fence|iron|wrought|metal work|baluster|handrail|decorative metal|scroll|steel ornament)',
        'PLUMBING': r'(?i)(pipe|faucet|sink|toilet|drain|water|shower|tub|valve|plumb|sewer|pump|heater|basin|fitting|fixture)',
        'PAINTING': r'(?i)(paint|brush|roller|primer|coating|finish|wall|ceiling|tape|canvas|spray|stain|varnish|sealer|texture)',
        'ROOFING': r'(?i)(roof|shingle|gutter|fascia|soffit|flashing|vent|membrane|slate|tile|metal roof|tar|pitch|eave)',
        'SIDING': r'(?i)(siding|vinyl|aluminum|wood|panel|cladding|weatherboard|lap|shake|shingle|facade|exterior)',
        'SPECIALTY ITEMS': r'(?i)(custom|specialty|unique|special order|bespoke|custom-made|specialized|one-of-a-kind)',
        'STEEL COMPONENTS': r'(?i)(beam|joist|column|steel|metal|structural|brace|frame|support|girder|truss|stud|angle)',
        'STAIRS': r'(?i)(stair|step|riser|tread|handrail|baluster|newel|landing|banister|railing|spiral|ladder)',
        'TILE': r'(?i)(tile|ceramic|porcelain|mosaic|grout|marble|stone|slate|travertine|backsplash|subway)',
        'TOOLS': r'(?i)(tool|drill|saw|hammer|wrench|screwdriver|level|measure|ladder|equipment|power tool|hand tool)',
        'WINDOWS': r'(?i)(window|glass|pane|screen|frame|seal|glazing|sill|casement|double-hung|slider|thermal)',
        'APPLIANCES': r'(?i)(remove\s+refrigerator|install\s+refrigerator|refrigerator\s*-?\s*reset|side\s+by\s+side|cf\b|washer|dryer|stove|oven|dishwasher|microwave|appliance|freezer|range|cooktop)',
        'CABINETRY': r'(?i)(cabinet|drawer|counter|shelf|vanity|cupboard|pantry|storage|kitchen|bathroom)',
        'CLEANING': r'(?i)(clean|vacuum|mop|broom|sanitiz|deodoriz|wash|scrub|dust|bleach|soap|detergent|disinfect)',
        'CONCRETE & ASPHALT': r'(?i)(concrete|asphalt|cement|foundation|slab|driveway|sidewalk|patio|aggregate|paving)',
        'DOORS': r'(?i)(door|knob|hinge|lock|frame|threshold|entrance|exit|jamb|panel|sliding|pocket|barn)',
        'DRYWALL': r'(?i)(drywall|sheetrock|gypsum|wall|panel|mud|tape|joint|texture|patch|repair|plaster)',
        'ELECTRICAL': r'(?i)(wire|outlet|switch|circuit|panel|breaker|electric|light|plug|voltage|amp|conduit|junction)',
        'FENCING': r'(?i)(fence|gate|post|panel|picket|chain link|privacy|wood fence|metal fence|rail)',
        'FINISH CARPENTRY': r'(?i)(trim|molding|baseboard|crown|casing|chair rail|wainscot|millwork|finish|woodwork)',
        'FIREPLACES': r'(?i)(fireplace|chimney|hearth|mantel|flue|damper|insert|wood stove|gas log|stone)',
        'FRAMING & CARPENTRY': r'(?i)(frame|stud|joist|rafter|beam|lumber|wood|timber|post|header|truss|deck)',
        'HVAC': r'(?i)(heat|cool|air|vent|duct|furnace|ac|hvac|thermostat|filter|conditioning|boiler)',
        'INSULATION': r'(?i)(insulation|fiberglass|foam|batting|vapor barrier|thermal|soundproof|weatherization)',
        'LANDSCAPING': r'(?i)(landscape|plant|tree|shrub|grass|mulch|soil|garden|irrigation|lawn|outdoor)',
        'MASONRY': r'(?i)(brick|block|stone|mortar|concrete|mason|wall|chimney|paver|veneer|foundation)',
        'PLASTER': r'(?i)(plaster|stucco|render|texture|finish|wall|ceiling|patch|repair|skim coat)',
        'SAFETY & SECURITY': r'(?i)(safety|guard|rail|fence|protect|secure|lock|alarm|camera|security|monitor)',
        'WATER EXTRACTION': r'(?i)(water|flood|dry|extract|dehumidify|moisture|damage|restore|remediate|mold)',
        'OFFICE SUPPLIES': r'(?i)(pen|pencil|paper|stapler|clipboard|folder|file|ink|toner|notebook|desk|office|stamp|envelope|label)',
        'CLEANING': r'(?i)(clean|vacuum|mop|broom|sanitiz|deodoriz|wash|scrub|dust|bleach|soap|detergent|disinfect)',
        'PLUMBING': r'(?i)(pipe|faucet|sink|toilet|drain|water|shower|tub|valve|plumb)',
        'ELECTRICAL': r'(?i)(wire|outlet|switch|circuit|panel|breaker|electric|light|plug|voltage|amp)',
        'FLOORING': r'(?i)(floor|carpet|tile|wood|vinyl|laminate|grout|hardwood|ceramic|stone)',
        'PAINTING': r'(?i)(paint|brush|roller|primer|coating|finish|wall|ceiling|tape|canvas)',
        'TOOLS': r'(?i)(tool|drill|saw|hammer|wrench|screwdriver|level|measure|ladder|equipment)',
        'FURNITURE': r'(?i)(chair|table|desk|cabinet|shelf|sofa|bed|drawer|furniture|couch)',
        'APPLIANCES': r'(?i)(washer|dryer|refrigerator|stove|oven|dishwasher|microwave|appliance)',
        'HVAC': r'(?i)(heat|cool|air|vent|duct|furnace|ac|hvac|thermostat)',
        'WINDOWS': r'(?i)(window|glass|pane|screen|frame|seal|glazing|sill)',
        'DOORS': r'(?i)(door|knob|hinge|lock|frame|threshold|entrance|exit)',
        'ROOFING': r'(?i)(roof|shingle|gutter|fascia|soffit|flashing|vent)',
        'SAFETY': r'(?i)(safety|guard|rail|fence|protect|secure|lock|alarm|camera)',
        'DUMPSTER & DEBRIS': r'(?i)(dumpster|debris|haul|waste|trash|dump|load|removal|container|disposal|clean\s*out|clean\s*up|garbage)',
        'PERMITS & FEES': r'(?i)(permit|fee|license|inspection|certificate|application|filing|approval|compliance|code|building\s*permit)',
        'TEMPORARY ITEMS': r'(?i)(temporary|temp|provisional|interim|portable|rental|short\s*term|temporary\s*power|temp\s*fence|portable\s*toilet)',
        'SUPERVISION & MANAGEMENT': r'(?i)(supervision|project management|residential supervision|manager|supervisor|management)',
        'SCAFFOLDING': r'(?i)(scaffold|rolling scaffold|scaffold setup|scaffold take down)',
        'BULLNOSE': r'(?i)(bullnose|rounded corner|corner round)',
        'LIGHTING & ELECTRICAL': r'(?i)(chandelier|light fixture|lighting|lamp|sconce|ceiling light|pendant)',
        'GAS SUPPLY': r'(?i)(gas supply|gas line|gas connector|gas fitting|gas pipe)',
        'APPLIANCES': r'(?i)(range|stove|r&r range|freestanding|gas range|electric range|cooktop)',
        'BATHROOM ACCESSORIES': r'(?i)(towel bar|robe hook|toilet paper|bathroom hardware|bath accessory)',
        'BALUSTRADE': r'(?i)(balustrade|railing|handrail|banister|stair rail)',
        'CLOSET ORGANIZATION': r'(?i)(closet organizer|melamine|storage system|closet system|shelf|drawer)',
        'PLUMBING FIXTURES': r'(?i)(p-trap|trap|drain|assembly|abs|plastic|plumbing)',
        'DEMOLITION & LABOR': r'(?i)(demolition|general demolition|labor|general labor|tear out|removal)',
        'SAFETY EQUIPMENT': r'(?i)(ppe|personal protective|safety equipment|protective gear)',
        'SMOKE & SAFETY DEVICES': r'(?i)(smoke detector|carbon monoxide|detector|alarm|safety device)',
        'VENTILATION': r'(?i)(exhaust fan|ventilation|fan|vent|air circulation)',
    }

CATEGORY_PATTERNS = create_category_patterns()

# Create a list to track unknown units
unknown_units = set()

def normalize_line_items(items_list):
    """Extract and normalize line items from list of dictionaries"""
    try:
        aggregated_items = {}
        
        # Process each item in the list
        for item in items_list:
            if not isinstance(item, dict):
                logger.warning(f"Skipping invalid item (not a dictionary): {item}")
                continue
                
            try:
                description = item.get('description', '').strip()
                if not description:
                    continue
                    
                # Create normalized item
                normalized_item = {
                    'description': description,
                    'quantity': float(item.get('quantity', 0)),
                    'unit': item.get('unit', ''),
                    'unit_cost': float(item.get('unit_cost', 0)),
                    'tax': float(item.get('tax', 0)),
                    'op': float(item.get('op', 0)),
                    'rcv': float(item.get('rcv', 0)),
                    'total_cost': float(item.get('rcv', 0)),
                    'occurrences': [{
                        'line_number': item.get('line_number', 0),
                        'quantity': float(item.get('quantity', 0)),
                        'rcv': float(item.get('rcv', 0)),
                        'page_number': item.get('page_number', 1)
                    }],
                    'occurrence_summary': {
                        'total_quantity': float(item.get('quantity', 0)),
                        'total_rcv': float(item.get('rcv', 0)),
                        'occurrences_detail': [
                            f"Line {item.get('line_number', 0)} (Page {item.get('page_number', 1)}): "
                            f"Qty={item.get('quantity', 0)}, RCV=${float(item.get('rcv', 0)):.2f}"
                        ]
                    }
                }
                
                if description in aggregated_items:
                    # Update existing item
                    existing = aggregated_items[description]
                    existing['quantity'] += normalized_item['quantity']
                    existing['tax'] += normalized_item['tax']
                    existing['op'] += normalized_item['op']
                    existing['rcv'] += normalized_item['rcv']
                    existing['total_cost'] += normalized_item['total_cost']
                    existing['occurrences'].append(normalized_item['occurrences'][0])
                    existing['occurrence_summary']['total_quantity'] += normalized_item['quantity']
                    existing['occurrence_summary']['total_rcv'] += normalized_item['rcv']
                    existing['occurrence_summary']['occurrences_detail'].append(
                        normalized_item['occurrence_summary']['occurrences_detail'][0]
                    )
                else:
                    aggregated_items[description] = normalized_item
                    
            except (ValueError, TypeError) as e:
                logger.warning(f"Error processing item: {item}. Error: {str(e)}")
                continue
        
        return list(aggregated_items.values())
        
    except Exception as e:
        logger.error(f"Error normalizing line items: {str(e)}")
        logger.error("Full traceback:", exc_info=True)
        return []

def compare_line_items(items1, items2):
    """Compare line items between two documents with occurrence tracking"""
    try:
        comparison_results = {
            'all_items_comparison': [],
            'cost_discrepancies': [],
            'quantity_discrepancies': [],
            'unique_to_doc1': [],
            'unique_to_doc2': []
        }
        
        # Compare items
        for item1 in items1:
            matched_item, match_ratio = find_best_match(item1['description'], items2)
            
            try:
                # Convert numeric values to float with explicit error handling
                item1_quantity = float(item1['quantity'])
                item1_cost = float(item1['total_cost'])
            except (ValueError, TypeError) as e:
                logger.error(f"Error converting item1 values: {e}")
                logger.error(f"item1 quantity: {item1['quantity']}, cost: {item1['total_cost']}")
                continue
            
            if matched_item:
                try:
                    matched_quantity = float(matched_item['quantity'])
                    matched_cost = float(matched_item['total_cost'])
                    quantity_diff = item1_quantity - matched_quantity
                    cost_diff = item1_cost - matched_cost
                    percentage_diff = (cost_diff / item1_cost * 100) if item1_cost != 0 else 0
                except (ValueError, TypeError) as e:
                    logger.error(f"Error converting matched_item values: {e}")
                    logger.error(f"matched quantity: {matched_item['quantity']}, cost: {matched_item['total_cost']}")
                    continue
            else:
                matched_quantity = None
                matched_cost = None
                quantity_diff = None
                cost_diff = None
                percentage_diff = None
            
            comparison_entry = {
                'description': item1['description'],
                'doc1_quantity': item1_quantity,
                'doc1_cost': item1_cost,
                'unit': item1['unit'],
                'doc1_occurrences': item1['occurrence_summary'],
                'doc2_quantity': matched_quantity,
                'doc2_cost': matched_cost,
                'doc2_occurrences': matched_item['occurrence_summary'] if matched_item else None,
                'quantity_difference': quantity_diff,
                'cost_difference': cost_diff,
                'percentage_cost_difference': percentage_diff,
                'match_confidence': match_ratio
            }
            
            comparison_results['all_items_comparison'].append(comparison_entry)
            
            if matched_item and cost_diff is not None:
                if abs(cost_diff) > 0.01:
                    comparison_results['cost_discrepancies'].append({
                        'description': item1['description'],
                        'doc1_cost': item1_cost,
                        'doc2_cost': matched_cost,
                        'difference': cost_diff,
                        'match_confidence': match_ratio
                    })
                
                if abs(quantity_diff) > 0.01:
                    comparison_results['quantity_discrepancies'].append({
                        'description': item1['description'],
                        'doc1_quantity': item1_quantity,
                        'doc2_quantity': matched_quantity,
                        'difference': quantity_diff,
                        'match_confidence': match_ratio
                    })
            else:
                comparison_results['unique_to_doc1'].append(item1)
        
        return comparison_results
        
    except Exception as e:
        logger.error(f"Error comparing line items: {str(e)}")
        logger.error(f"Full traceback:", exc_info=True)
        raise

def parse_quantity(quantity_text):
    """Parse quantity value from text that may include unit"""
    try:
        match = re.match(r'^([\d,\.]+)', quantity_text.strip())
        if match:
            return float(match.group(1).replace(',', ''))
        return 0.0
    except (ValueError, AttributeError):
        return 0.0

def extract_unit(quantity_text):
    """Extract unit from quantity text"""
    try:
        match = re.match(r'^\d+\.?\d*\s*([A-Za-z]+)', quantity_text.strip())
        if match:
            return match.group(1)
        return ''
    except (ValueError, AttributeError):
        return ''

def clean_numeric(value):
    """Clean numeric values, handling currency and percentages"""
    if not value:
        return 0.0
    try:
        # Remove currency symbols, commas, spaces, and parentheses
        value = str(value).replace('$', '').replace(',', '').replace(' ', '').strip('()')
        # Remove percentage signs
        value = value.replace('%', '')
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def extract_text_from_pdf(pdf_file, doc_id):
    """Extract tabular text from PDF file with structured column parsing"""
    try:
        pdf_file = pdf_file.read()
        doc = pymupdf.open(stream=pdf_file, filetype="pdf")
        line_items = []
        
        # Define column headers and their approximate positions
        columns = {
            'quantity': (0, 70),    # QUANTITY column
            'unit': (70, 120),      # UNIT column
            'tax': (120, 170),      # TAX column
            'op': (170, 220),       # O&P column
            'rcv': (220, 270),      # RCV column
            'age_life': (270, 320), # AGE/LIFE column
            'cond': (320, 370),     # COND. column
            'dep': (370, 420),      # DEP% column
            'deprec': (420, 470),   # DEPREC. column
            'acv': (470, 520)       # ACV column
        }
        
        current_description = ""
        line_number = 0
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")["blocks"]
            
            # Group text by y-position (row)
            rows = {}
            for block in blocks:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        y = round(span["bbox"][1], 1)  # y-coordinate for row grouping
                        x = span["bbox"][0]            # x-coordinate for column determination
                        
                        if y not in rows:
                            rows[y] = []
                        rows[y].append({
                            'text': span['text'].strip(),
                            'x': x,
                            'width': span["bbox"][2] - x
                        })
            
            # Process rows in order
            sorted_rows = sorted(rows.items())
            for y, spans in sorted_rows:
                # Sort spans by x-coordinate
                spans.sort(key=lambda s: s['x'])
                row_text = ' '.join(s['text'] for s in spans)
                
                # Check if this is a quantity row (starts with a number)
                if re.match(r'^\d+\.?\d*\s*[A-Za-z]+', row_text):
                    line_number += 1
                    # Parse row into columns
                    row_data = {'line_number': line_number, 'page_number': page_num + 1}
                    
                    for span in spans:
                        # Determine which column this text belongs to
                        for col_name, (start_x, end_x) in columns.items():
                            if start_x <= span['x'] < end_x:
                                row_data[col_name] = span['text']
                                break
                    
                    # Create line item with current description
                    if current_description:
                        item = {
                            'description': current_description,
                            'quantity': parse_quantity(row_data.get('quantity', '')),
                            'unit': extract_unit(row_data.get('quantity', '')),
                            'tax': clean_numeric(row_data.get('tax', '0')),
                            'op': clean_numeric(row_data.get('op', '0')),
                            'rcv': clean_numeric(row_data.get('rcv', '0')),
                            'age_life': row_data.get('age_life', ''),
                            'condition': row_data.get('cond', ''),
                            'depreciation': clean_numeric(row_data.get('dep', '0').rstrip('%')),
                            'deprec_value': clean_numeric(row_data.get('deprec', '0')),
                            'acv': clean_numeric(row_data.get('acv', '0')),
                            'line_number': row_data['line_number'],
                            'page_number': row_data['page_number']
                        }
                        line_items.append(item)
                
                # If row doesn't start with a number and isn't a header row,
                # treat it as a potential description
                elif not any(header in row_text.upper() for header in ['QUANTITY', 'UNIT', 'TAX', 'O&P', 'RCV']):
                    current_description = row_text.strip()
        
        logger.info(f"Successfully extracted {len(line_items)} items from document {doc_id}")
        return line_items
        
    except Exception as e:
        logger.error(f"Error extracting text: {str(e)}")
        logger.error("Full traceback:", exc_info=True)
        raise

def create_analysis_ready_dataframe(comparison_results):
    """Convert comparison results into an analysis-friendly format"""
    try:
        df = pd.DataFrame(comparison_results['all_items_comparison'])
        
        # Convert numeric columns to float type
        numeric_columns = [
            'doc1_quantity', 'doc2_quantity',
            'doc1_cost', 'doc2_cost',
            'cost_difference', 'quantity_difference',
            'percentage_cost_difference'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Add derived columns
        df['category'] = df['description'].apply(categorize_item)
        df['standardized_unit'] = df['unit'].apply(lambda x: UNIT_STANDARDIZATION.get(x, x))
        df['is_temporary'] = df['description'].str.contains('Temporary', case=False)
        df['is_labor'] = df['description'].str.contains('labor|hour|technician|supervisor', case=False)
        
        # Calculate significant difference
        df['significant_difference'] = df['percentage_cost_difference'].apply(
            lambda x: abs(x) > 5 if pd.notnull(x) else False
        )
        
        # Remove file saving operation since we're on a read-only filesystem
        # timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # csv_filename = f'enriched_comparison_{timestamp}.csv'
        # df.to_csv(csv_filename, index=False)
        
        return df
    except Exception as e:
        logger.error(f"Error creating analysis-ready dataframe: {str(e)}")
        raise



def process_comparison_result(comparison_json):
    """Process and format the comparison result for better presentation"""
    try:
        # Add additional processing here if needed
        return comparison_json
    except Exception as e:
        logger.error(f"Error processing comparison result: {str(e)}")
        raise

def categorize_item(description):
    """Categorize items based on common terminology and associations"""
    matches = []
    for category, pattern in CATEGORY_PATTERNS.items():
        if re.search(pattern, description):
            matches.append(category)
    
    # Return the first match, or 'UNCATEGORIZED' if no matches
    return matches[0] if matches else 'UNCATEGORIZED'

def clean_numeric_values(value):
    """Preserve numeric values by converting numpy types to Python native types"""
    if isinstance(value, (np.int64, np.float64)):
        return float(value) if np.isfinite(value) else str(value)
    return value

def create_category_summary(items):
    """Create summary statistics for a category of items"""
    total_items = len(items)
    total_cost_diff = 0
    items_with_discrepancies = 0
    valid_items = 0  # Counter for items with valid cost differences

    # Calculate values only for items with valid cost differences
    for item in items:
        cost_diff = item.get('cost_difference')
        if cost_diff is not None and not pd.isna(cost_diff):  # Check for both None and nan
            cost_diff = float(cost_diff)
            total_cost_diff += cost_diff
            valid_items += 1
            if abs(cost_diff) > 0:
                items_with_discrepancies += 1

    # Calculate average only using valid items
    avg_cost_diff = total_cost_diff / valid_items if valid_items > 0 else 0

    return {
        'total_items': int(total_items),
        'total_cost_difference': float(round(total_cost_diff, 2)),
        'average_cost_difference': float(round(avg_cost_diff, 2)),
        'items_with_discrepancies': int(items_with_discrepancies)
    }

def prepare_categorized_items(analysis_df, comparison_results):
    categorized_items = {}
    
    for category, group in analysis_df.groupby('category'):
        items = []
        for _, row in group.iterrows():
            item_data = {
                'description': row['description'],
                'doc1_quantity': row['doc1_quantity'],
                'doc2_quantity': row['doc2_quantity'],
                'doc1_cost': row['doc1_cost'],
                'doc2_cost': row['doc2_cost'],
                'unit': row['unit'],
                'cost_difference': row['cost_difference'],
                'percentage_difference': row['percentage_cost_difference'],
                'is_labor': row['is_labor'],
                'is_temporary': row['is_temporary'],
                'doc1_occurrences': row.get('doc1_occurrences'),
                'doc2_occurrences': row.get('doc2_occurrences'),
                'match_confidence': row.get('match_confidence', 0),
            }
            
            # Add additional fields from all_items_data if it exists
            all_items_data = next(
                (item for item in comparison_results['all_items_comparison'] 
                 if item['description'] == row['description']),
                None
            )
            
            if all_items_data:
                item_data.update({
                    'quantity': all_items_data.get('quantity'),
                    'unit_cost': all_items_data.get('unit_cost'),
                    'tax': all_items_data.get('tax'),
                    'op': all_items_data.get('op'),
                    'rcv': all_items_data.get('rcv'),
                    'total_cost': all_items_data.get('total_cost'),
                    'occurrences': all_items_data.get('occurrences', []),
                    'occurrence_count': all_items_data.get('occurrence_count', 0),
                    'occurrence_summary': all_items_data.get('occurrence_summary', {
                        'total_quantity': 0,
                        'total_rcv': 0,
                        'occurrences_detail': []
                    })
                })
            
            items.append(item_data)
        
        categorized_items[category] = {
            'items': items,
            'summary': create_category_summary(items)
        }
    
    return categorized_items

def extract_specifications(description: str) -> dict:
    """
    Extract key specifications from item descriptions.
    """
    specs = {
        'measurements': [],
        'r_value': None,
        'type': None,
        'is_removal': False,  # New flag for removal items
        'action_type': None   # New field to track action type
    }
    
    # Check for removal action
    specs['is_removal'] = description.lower().strip().startswith('remove')
    
    # Determine action type
    if specs['is_removal']:
        specs['action_type'] = 'remove'
    elif description.lower().strip().startswith('install'):
        specs['action_type'] = 'install'
    elif description.lower().strip().startswith('replace'):
        specs['action_type'] = 'replace'
    elif description.lower().strip().startswith('repair'):
        specs['action_type'] = 'repair'
    
    # Extract measurements (e.g., 6", 10")
    measurements = re.findall(r'(\d+)(?:\s*(?:"|inch|inches))', description.lower())
    specs['measurements'] = [int(m) for m in measurements]
    
    # Extract R-value
    r_value_match = re.search(r'r-?(\d+)', description.lower())
    if r_value_match:
        specs['r_value'] = int(r_value_match.group(1))
    
    # Extract type (e.g., batt, faced, unfaced)
    type_keywords = ['batt', 'faced', 'unfaced']
    specs['type'] = [kw for kw in type_keywords if kw in description.lower()]
    
    return specs

def are_specs_compatible(specs1: dict, specs2: dict) -> bool:
    """
    Compare specifications to determine if items are truly the same.
    """
    # If one is a removal and the other isn't, they're different items
    if specs1['is_removal'] != specs2['is_removal']:
        return False
    
    # If action types are different (install vs remove vs replace vs repair), they're different items
    if specs1['action_type'] != specs2['action_type']:
        return False
    
    # If measurements are different, items are different
    if specs1['measurements'] and specs2['measurements']:
        if specs1['measurements'] != specs2['measurements']:
            return False
    
    # If R-values are different, items are different
    if specs1['r_value'] and specs2['r_value']:
        if specs1['r_value'] != specs2['r_value']:
            return False
    
    # If types conflict, items are different
    if specs1['type'] and specs2['type']:
        if any(t in specs1['type'] and t not in specs2['type'] for t in ['faced', 'unfaced']):
            return False
    
    return True

def find_best_match(description: str, items_list: list, threshold: float = 80) -> tuple:
    """
    Find the best matching item from a list based on description similarity.
    Returns tuple of (matched_item, match_ratio).
    """
    try:
        best_match = None
        best_ratio = 0
        
        # Extract key characteristics from the description
        desc_specs = extract_specifications(description)
        
        # Get base description without action words for better matching
        base_desc = re.sub(r'^(remove|install|replace|repair)\s+', '', description.lower().strip())
        
        for item in items_list:
            # Extract specifications from potential match
            item_specs = extract_specifications(item['description'])
            
            # If specifications are different, skip this match
            if not are_specs_compatible(desc_specs, item_specs):
                continue
            
            # Get base description for comparison item
            item_base_desc = re.sub(r'^(remove|install|replace|repair)\s+', '', item['description'].lower().strip())
            
            # Calculate similarity ratio using token sort ratio for better partial matching
            ratio = fuzz.token_sort_ratio(base_desc, item_base_desc)
            
            # Update best match if this ratio is higher
            if ratio > best_ratio and ratio >= threshold:
                best_ratio = ratio
                best_match = item
        
        return (best_match, best_ratio)
    
    except Exception as e:
        logger.error(f"Error in find_best_match: {str(e)}")
        return (None, 0)

def create_overall_summary(analysis_df):
    """Create summary statistics for the entire comparison"""
    return {
        'total_items': len(analysis_df),
        'total_discrepancies': len(analysis_df[analysis_df['cost_difference'].abs() > 0]),
        'total_cost_difference': analysis_df['cost_difference'].sum(),
        'average_difference_percentage': analysis_df['percentage_cost_difference'].mean(),
        'categories_affected': analysis_df['category'].nunique()
    }

def generate_ai_insights(analysis_df):
    """Generate professional insurance claims expert insights and recommendations"""
    
    # Calculate key metrics
    total_discrepancy = analysis_df['cost_difference'].sum()
    major_discrepancies = analysis_df[analysis_df['percentage_cost_difference'].abs() > 10]
    underpaid_items = analysis_df[analysis_df['cost_difference'] < 0]
    
    # Analyze patterns in discrepancies
    labor_discrepancies = analysis_df[
        (analysis_df['is_labor'] == True) & 
        (analysis_df['cost_difference'].abs() > 0)
    ]
    
    material_discrepancies = analysis_df[
        (analysis_df['is_labor'] == False) & 
        (analysis_df['cost_difference'].abs() > 0)
    ]

    insights = {
        'summary': {
            'total_underpaid_amount': abs(total_discrepancy) if total_discrepancy < 0 else 0,
            'number_of_underpaid_items': len(underpaid_items),
            'largest_discrepancies': major_discrepancies.nlargest(5, 'cost_difference').to_dict('records')
        },
        'key_findings': [
            f"Found {len(major_discrepancies)} items with significant pricing discrepancies (>10% difference)",
            "Primary areas of concern:",
            "1. Labor Costs: " + _analyze_labor_discrepancies(labor_discrepancies),
            "2. Material Costs: " + _analyze_material_discrepancies(material_discrepancies),
            "3. Missing Items: " + _analyze_missing_items(analysis_df)
        ],
        'recommendations': [
            {
                'priority': 'High',
                'action': 'Document Preparation',
                'details': [
                    'Compile detailed photos of all damaged items',
                    'Gather original receipts and invoices',
                    'Document any temporary repairs or mitigation efforts'
                ]
            },
            {
                'priority': 'High',
                'action': 'Discussion Points',
                'details': [
                    f'Focus on the top 5 discrepancies totaling ${abs(major_discrepancies["cost_difference"].sum()):.2f}',
                    'Request line-by-line review of labor rates',
                    'Address any missing items from the carrier\'s estimate'
                ]
            },
            {
                'priority': 'Medium',
                'action': 'Next Steps',
                'details': [
                    'Schedule a detailed review meeting with adjuster',
                    'Consider requesting a re-inspection',
                    'Document all communication in writing'
                ]
            }
        ],
        'negotiation_strategy': _generate_negotiation_strategy(analysis_df),
        'potential_recoverable_amount': _calculate_recoverable_amount(analysis_df)
    }
    
    return insights

def _analyze_labor_discrepancies(labor_df):
    """Analyze patterns in labor cost discrepancies"""
    if len(labor_df) == 0:
        return "No significant labor cost discrepancies found."
    
    total_labor_diff = labor_df['cost_difference'].sum()
    return (f"Found ${abs(total_labor_diff):.2f} in labor cost discrepancies. "
            "Key issues include rate differences and missing labor operations.")

def _analyze_material_discrepancies(material_df):
    """Analyze patterns in material cost discrepancies"""
    if len(material_df) == 0:
        return "No significant material cost discrepancies found."
    
    total_material_diff = material_df['cost_difference'].sum()
    return (f"Found ${abs(total_material_diff):.2f} in material cost discrepancies. "
            "Focus on quantity differences and unit price variations.")

def _analyze_missing_items(df):
    """Analyze items present in doc1 but missing in doc2"""
    missing_items = df[df['doc2_cost'].isna()]
    if len(missing_items) == 0:
        return "No missing items identified."
    
    total_missing = missing_items['doc1_cost'].sum()
    return (f"Identified {len(missing_items)} items totaling ${total_missing:.2f} "
            "that are missing from the carrier's estimate.")

def _generate_negotiation_strategy(df):
    """Generate specific negotiation strategies based on patterns"""
    return {
        'primary_focus': 'Start with largest discrepancies first',
        'documentation_needed': [
            'Photos of damaged items',
            'Local contractor quotes',
            'Material price documentation',
            'Industry standard labor rates'
        ],
        'talking_points': [
            'Current market conditions affecting prices',
            'Local labor rate documentation',
            'Specific code requirements',
            'Additional damage found during repairs'
        ],
        'common_carrier_positions': [
            'How to counter depreciation arguments',
            'Addressing scope of work differences',
            'Handling overhead and profit discussions'
        ]
    }

def _calculate_recoverable_amount(df):
    """Calculate potentially recoverable amount with confidence levels"""
    total_diff = df['cost_difference'].sum()
    if total_diff >= 0:
        return {
            'amount': 0,
            'confidence': 'N/A',
            'note': 'No underpayment identified'
        }
    
    high_confidence = df[
        (df['cost_difference'] < 0) & 
        (df['match_confidence'] > 80)
    ]['cost_difference'].sum()
    
    medium_confidence = df[
        (df['cost_difference'] < 0) & 
        (df['match_confidence'].between(50, 80))
    ]['cost_difference'].sum()
    
    return {
        'total_potential': abs(total_diff),
        'breakdown': {
            'highly_likely': abs(high_confidence),
            'moderately_likely': abs(medium_confidence),
            'requires_additional_documentation': abs(total_diff - high_confidence - medium_confidence)
        },
        'next_steps': [
            'Focus first on high-confidence items',
            'Gather additional documentation for medium-confidence items',
            'Consider cost-benefit of pursuing low-confidence items'
        ]
    }

@app.route('/api/compare', methods=['POST'])
def compare_pdfs():
    """API endpoint to compare two PDF documents"""
    try:
        if 'file1' not in request.files or 'file2' not in request.files:
            return jsonify({'error': 'Two PDF files are required'}), 400
            
        file1 = request.files['file1']
        file2 = request.files['file2']
        
        if not file1.filename.endswith('.pdf') or not file2.filename.endswith('.pdf'):
            return jsonify({'error': 'Both files must be PDFs'}), 400
            
        logger.info("Received comparison request")
        
        # Extract and compare documents
        comparison_results = compare_documents(file1, file2)  # No tuple unpacking
        
        return jsonify(comparison_results)
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({'error': str(e)}), 500

def compare_documents(doc1_file, doc2_file):
    """Compare two PDF documents"""
    try:
        # Extract items from both documents
        doc1_items = extract_text_from_pdf(doc1_file, 'doc1')
        doc2_items = extract_text_from_pdf(doc2_file, 'doc2')
        
        # Normalize items
        items1 = normalize_line_items(doc1_items)  # No tuple unpacking
        items2 = normalize_line_items(doc2_items)  # No tuple unpacking
        
        # Compare normalized items
        comparison_results = compare_line_items(items1, items2)
        
        # Create analysis dataframe
        analysis_df = create_analysis_ready_dataframe(comparison_results)
        
        return comparison_results
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise

if __name__ == '__main__':
    app.run(debug=True, port=5000)