from flask import Flask, request, jsonify
import pdfplumber
from pdfplumber.utils.text import extract_text
import pandas as pd
import re
from flask_cors import CORS
import logging
from fuzzywuzzy import fuzz
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
from dotenv import load_dotenv
import logging
import re
import pandas as pd
from fuzzywuzzy import fuzz
from datetime import datetime

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'pdf'}

client = openai.OpenAI(api_key="")


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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_pdf(pdf_file):
    pdf = pdfplumber.open(pdf_file)
    all_text = []

    for page in pdf.pages:
        chars = page.chars.copy()

        for table in page.find_tables(table_settings={
            "vertical_strategy": "text",
            "horizontal_strategy": "lines",
            "snap_tolerance": 3,
            "join_tolerance": 3,
            "edge_min_length": 3
        }):
            try:
                df = pd.DataFrame(table.extract())
                if len(df) > 0:
                    if df.iloc[0].isna().any():
                        df.columns = df.iloc[1]
                        df = df.drop([0, 1])
                    else:
                        df.columns = df.iloc[0]
                        df = df.drop(0)
                    
                    df = df.fillna('')
                    markdown = df.to_markdown(index=False)
                    
                    chars.append({
                        "text": "\n" + markdown + "\n",
                        "x0": table.bbox[0],
                        "top": table.bbox[1],
                        "x1": table.bbox[2],
                        "bottom": table.bbox[3],
                        "doctop": table.bbox[1],
                        "upright": True,
                        "size": 12,
                        "width": table.bbox[2] - table.bbox[0]
                    })

            except Exception as e:
                print(f"Error processing table: {e}")
                continue

        page_text = extract_text(chars, layout=True)
        all_text.append(page_text)

    pdf.close()
    return "\n".join(all_text)

def clean_item_number(item_number):
    """
    Extracts only the numerical part from an item number and adds a period.
    Examples: 
    'DD2WW59.' -> '259.'
    'CClloosseett ((11))286.' -> '286.'
    'BBeeddrroooomm 22 MM CClloosseett 516.' -> '516.'
    'Room 2 516.' -> '516.'  # Now handles room numbers correctly
    Rejects: 'LLaauunnddrryy RRoo 1oomm1 1. .4 43'
    """
    # Split at the period to get just the item number part
    item_parts = item_number.split('.')
    if not item_parts:
        return None
    
    item_number_part = item_parts[0]
    
    # Check if there are numbers with spaces at the end of the string
    if re.search(r'\d\s+\d+\s*$', item_number_part):
        return None
        
    # First remove any parentheses and their contents
    no_parentheses = re.sub(r'\([^)]*\)', '', item_number_part)
    # Remove any scattered spaces
    no_spaces = re.sub(r'\s+', '', no_parentheses)
    
    # Find all groups of consecutive digits
    digit_groups = re.findall(r'\d+', no_spaces)
    
    if not digit_groups:
        return None
        
    # Take the last group of digits (usually the line number)
    digits = digit_groups[-1]
    
    # Validation checks
    if len(digits) > 4:  # Assuming line numbers won't be more than 4 digits
        return None
        
    # Add period to the cleaned number
    return f"{digits}."

def parse_quantity(quantity_text):
    """
    Parse quantity value from text that may include unit.
    Examples:
    '1.00EA' -> 1.0
    '10.5SF' -> 10.5
    '100LF' -> 100.0
    """
    if quantity_text is None:
        return 0.0
        
    try:
        # Remove any units (EA, SF, LF, etc) and convert to float
        quantity_str = re.match(r'^([\d,\.]+)', str(quantity_text).strip())
        if quantity_str:
            return float(quantity_str.group(1).replace(',', ''))
        return 0.0
    except (ValueError, AttributeError):
        logger.warning(f"Could not parse quantity: {quantity_text}")
        return 0.0

def cleanup_line_item(item):
    """
    Post-process a line item to ensure properties are correctly populated and track occurrences
    """
    try:
        # Combine notes into a single string for easier processing
        notes_text = ' '.join(str(note) for note in item.get('notes', []))
        
        # Initialize default values for required fields
        item.setdefault('quantity', '0')
        item.setdefault('rcv', '0')
        item.setdefault('item_number', '0')
        item.setdefault('page_number', 1)
        item.setdefault('description', '')
        item.setdefault('notes', [])
        
        # Updated pattern to match the actual format in notes
        quantity_pattern = r'''
            (\d+\.?\d*(?:SF|EA|LF)?)\s+           # Quantity with optional unit
            ([-\d,\.]+)\s+                         # Unit cost
            ([-\d,\.]+)\s+                         # Tax
            ([-\d,\.]+)\s+                         # O&P
            ([-\d,\.]+)                           # RCV
            (?:\s+(\d+/\d+|\d+/[A-Z]+|0/NA)\s+)?  # Optional AGE/LIFE
            (?:yr\s+)?                            # Optional "yr"
            (?:Avg\.\s+)?                         # Optional "Avg."
            (?:(\d+)%)?                           # Optional Depreciation percentage
        '''
        
        # Check notes first, then description
        for text in [notes_text, item['description']]:
            quantity_match = re.search(quantity_pattern, text, re.VERBOSE)
            if quantity_match and not item.get('quantity'):  # Only update if properties are empty
                quantity = quantity_match.group(1)
                
                # Extract unit type from quantity
                unit_type = re.search(r'(SF|EA|LF)$', quantity)
                unit = unit_type.group(1) if unit_type else 'EA'
                # Remove unit from quantity if present
                quantity = re.sub(r'(SF|EA|LF)$', '', quantity)
                
                item.update({
                    'quantity': quantity.strip() or '0',
                    'unit': unit,
                    'unit_cost': quantity_match.group(2).replace(',', '') or '0',
                    'tax': quantity_match.group(3).replace(',', '') or '0',
                    'o&p': quantity_match.group(4).replace(',', '') or '0',
                    'rcv': quantity_match.group(5).replace(',', '') or '0',
                    'age_life': quantity_match.group(6) if quantity_match.group(6) else 'N/A',
                    'dep_percent': quantity_match.group(7) if quantity_match.group(7) else '0'
                })
                
                # Calculate depreciation and ACV if we have RCV and dep_percent
                try:
                    rcv = float(item['rcv'])
                    dep_percent = float(item['dep_percent'])
                    depreciation = rcv * (dep_percent / 100)
                    acv = rcv - depreciation
                    
                    item.update({
                        'depreciation': f"{depreciation:.2f}",
                        'acv': f"{acv:.2f}"
                    })
                except (ValueError, TypeError):
                    item.update({
                        'depreciation': '0.00',
                        'acv': '0.00'
                    })
        
        # Add occurrence tracking
        if not item.get('occurrences'):
            item['occurrences'] = []
        
        # Add current occurrence with proper quantity parsing and error handling
        try:
            occurrence = {
                'line_number': str(item.get('item_number', '0')),
                'quantity': parse_quantity(item.get('quantity', '0')),
                'rcv': float(str(item.get('rcv', '0')).replace(',', '') or '0'),
                'page_number': int(item.get('page_number', 1))
            }
        except (ValueError, TypeError):
            occurrence = {
                'line_number': '0',
                'quantity': 0.0,
                'rcv': 0.0,
                'page_number': 1
            }
        
        item['occurrences'].append(occurrence)
        
        # Calculate totals for all occurrences
        try:
            total_quantity = sum(occ['quantity'] for occ in item['occurrences'])
            total_rcv = sum(occ['rcv'] for occ in item['occurrences'])
        except (ValueError, TypeError):
            total_quantity = 0.0
            total_rcv = 0.0
        
        # Add occurrence summary
        item['occurrence_summary'] = {
            'total_quantity': total_quantity,
            'total_rcv': total_rcv,
            'occurrences_detail': [
                f"Line {occ['line_number']} (Page {occ['page_number']}): "
                f"Qty={occ['quantity']}, RCV=${float(occ['rcv']):.2f}"
                for occ in item['occurrences']
            ]
        }
        
        return item
        
    except Exception as e:
        logger.error(f"Error in cleanup_line_item: {str(e)}")
        # Return a safe default item
        return {
            'description': item.get('description', ''),
            'quantity': '0',
            'unit': 'EA',
            'rcv': '0',
            'occurrences': [],
            'occurrence_summary': {
                'total_quantity': 0.0,
                'total_rcv': 0.0,
                'occurrences_detail': []
            }
        }

def parse_line_items(text):
    """Parse line items with page number tracking"""
    line_items = []
    
    # Updated pattern to be more strict about line endings
    line_pattern = r'^\s*(?!.*(?:\.\s+\.\s+\d|\d\s+\.\s+\d))([A-Za-z0-9()\s]*?\d+[A-Za-z]*)\.\s+(.*?)(?:\s*\*)?$'
    
    # Updated quantity pattern to be more strict about number formats
    quantity_pattern = r'''^\s*
        (?!.*\b\d+\s+\d+\s+\d+\b)              # Negative lookahead to prevent matching scattered numbers
        (\d+\.?\d*(?:\s*[A-Z]{1,3})?)\s+      # Quantity with optional unit (allowing space)
        ([-\d,\.]+)\s+                         # Unit cost
        ([-\d,\.]+)\s+                         # Tax
        ([-\d,\.]+)\s+                         # O&P
        ([-\d,\.]+)\s+                         # RCV
        (?:(\d+/(?:NA|[A-Z]+))\s+)?           # Optional AGE/LIFE (now handles "NA")
        (?:Avg\.\s+)?                          # Optional "Avg."
        (\d+)%\s+                              # Depreciation percentage
        (?:\[[A-Z]\]\s+)?                      # Optional [M] or other bracketed letter
        \(([^)]+)\)\s+                         # Depreciation amount in parentheses
        ([-\d,\.]+)                           # ACV
    '''
    
    headers = {'QUANTITY', 'UNIT', 'TAX', 'O&P', 'RCV', 'AGE/LIFE', 'COND.', 'DEP %', 'DEPREC.', 'ACV'}
    
    lines = text.split('\n')
    i = 0
    current_item = None
    current_page = 1
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for page markers
        page_match = re.search(r'Page:\s*(\d+)', line)
        if page_match:
            current_page = int(page_match.group(1))
            i += 1
            continue
            
        # Skip empty lines and headers
        if not line or any(header in line for header in headers):
            i += 1
            continue
            
        # Check for page markers or totals
        if 'Page:' in line or line.startswith('Totals:'):
            i += 1
            continue
        
        # Try to match a new line item
        match = re.match(line_pattern, line)
        if match:
            raw_item_number = match.group(1)
            cleaned_item_number = clean_item_number(raw_item_number)
            
            # Skip this item if cleaning returned None
            if cleaned_item_number is None:
                i += 1
                continue
                
            # If we have a current item, append it before starting new one
            if current_item:
                line_items.append(current_item)
                
            description = match.group(2).strip()
            current_item = {
                'item_number': cleaned_item_number,
                'raw_item_number': raw_item_number, 
                'description': description,
                'quantity': None,
                'unit_cost': None,
                'tax': None,
                'o&p': None,
                'rcv': None,
                'age_life': None,
                'dep_percent': None,
                'depreciation': None,
                'acv': None,
                'notes': [],
                'page_number': current_page
            }
            i += 1
            continue
            
        # Try to match quantity line
        quantity_match = re.match(quantity_pattern, line, re.VERBOSE)
        if current_item and quantity_match:
            current_item.update({
                'quantity': quantity_match.group(1),
                'unit_cost': quantity_match.group(2).replace(',', ''),
                'tax': quantity_match.group(3).replace(',', ''),
                'o&p': quantity_match.group(4).replace(',', ''),
                'rcv': quantity_match.group(5).replace(',', ''),
                'age_life': quantity_match.group(6) if quantity_match.group(6) else 'N/A',
                'dep_percent': quantity_match.group(7),
                'depreciation': quantity_match.group(8).replace(',', ''),
                'acv': quantity_match.group(9).replace(',', '')
            })
            
            # Extract unit type from quantity if present
            unit_type = re.search(r'[A-Z]{2,}$', quantity_match.group(1))
            current_item['unit'] = unit_type.group(0) if unit_type else 'EA'
            
            i += 1
            continue
            
        # If line doesn't match quantity pattern and we have a current item,
        # treat it as a note
        if current_item and line:
            current_item['notes'].append(line)
        
        i += 1
    
    # Don't forget to append the last item
    if current_item:
        current_item = cleanup_line_item(current_item)
        line_items.append(current_item)
    
    # Clean up all items one final time
    line_items = [cleanup_line_item(item) for item in line_items]
    
    return line_items

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

def extract_numeric_value(value_str):
    """Extract numeric value from strings like '8.00MO' or '120.00LF'"""
    if not value_str or pd.isna(value_str):
        return 0.0
    try:
        # Extract numeric part using regex
        match = re.match(r'^([-+]?\d*\.?\d+)', str(value_str))
        if match:
            return float(match.group(1))
        return 0.0
    except (ValueError, TypeError):
        return 0.0

def extract_unit(value_str):
    """
    Extract unit from strings like '8.00MO', '120.00LF', or '12 LF'
    """
    if not value_str or pd.isna(value_str):
        return 'EA'  # Default unit
    try:
        # Extract unit part using regex, handling both cases:
        # - Units directly after number (8.00MO)
        # - Units with space after number (12 LF)
        match = re.search(r'\s*([A-Za-z]+)$', str(value_str))
        if match:
            return match.group(1).upper()
        return 'EA'  # Default unit
    except (ValueError, TypeError):
        return 'EA'  # Default unit

def compare_line_items(items1, items2):
    """Compare line items with occurrence tracking"""
    comparison_results = {
        'all_items_comparison': [],
        'cost_discrepancies': [],
        'quantity_discrepancies': [],
        'unique_to_doc1': [],
        'unique_to_doc2': []
    }
    
    # Track matched items from doc2 to avoid duplicates
    matched_items_doc2 = set()
    
    # Compare items
    for item1 in items1:
        matched_item, match_ratio = find_best_match(
            item1['description'], 
            [item for item in items2 if item['description'] not in matched_items_doc2]
        )
        
        try:
            # Extract numeric values and units
            item1_quantity = extract_numeric_value(item1.get('quantity', 0))
            item1_unit = extract_unit(item1.get('quantity', 'EA'))
            item1_cost = float(item1.get('rcv', 0))
            
            if matched_item:
                # Add to tracked items to prevent future matches
                matched_items_doc2.add(matched_item['description'])
                
                matched_quantity = extract_numeric_value(matched_item.get('quantity', 0))
                matched_unit = extract_unit(matched_item.get('quantity', 'EA'))
                matched_cost = float(matched_item.get('rcv', 0))
                
                quantity_diff = item1_quantity - matched_quantity if item1_unit == matched_unit else None
                cost_diff = item1_cost - matched_cost
                percentage_diff = (cost_diff / item1_cost * 100) if item1_cost != 0 else 0
                
                # Ensure we're getting the correct occurrence data
                doc2_occurrences = matched_item.get('occurrence_summary', {
                    'total_quantity': 0,
                    'total_rcv': 0,
                    'occurrences_detail': []
                })
            else:
                matched_quantity = None
                matched_unit = None
                matched_cost = None
                quantity_diff = None
                cost_diff = None
                percentage_diff = None
                doc2_occurrences = None
            
            comparison_entry = {
                'description': item1['description'],
                'doc1_quantity': item1_quantity,
                'doc2_quantity': matched_quantity,
                'unit': item1_unit,
                'doc1_cost': item1_cost,
                'doc2_cost': matched_cost,
                'doc1_occurrences': item1.get('occurrence_summary', {
                    'total_quantity': 0,
                    'total_rcv': 0,
                    'occurrences_detail': []
                }),
                'doc2_occurrences': doc2_occurrences,
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
                
                if quantity_diff is not None and abs(quantity_diff) > 0.01:
                    comparison_results['quantity_discrepancies'].append({
                        'description': item1['description'],
                        'doc1_quantity': item1_quantity,
                        'doc2_quantity': matched_quantity,
                        'unit': item1_unit,
                        'difference': quantity_diff,
                        'match_confidence': match_ratio
                    })
            else:
                comparison_results['unique_to_doc1'].append(item1)
                
        except Exception as e:
            logger.error(f"Error processing item: {str(e)}")
            logger.error(f"Item details: {item1}")
            continue
    
    # Find items unique to doc2
    matched_descriptions = {item['description'] for item in comparison_results['all_items_comparison']}
    comparison_results['unique_to_doc2'] = [
        item for item in items2 
        if item['description'] not in matched_descriptions
    ]
    
    return comparison_results

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
    """Prepare items categorized by type with summaries"""
    categorized_items = {}
    
    for category, group in analysis_df.groupby('category'):
        items = []
        for _, row in group.iterrows():
            item_data = {
                'description': row['description'],
                'doc1_quantity': float(row['doc1_quantity']) if pd.notnull(row['doc1_quantity']) else None,
                'doc2_quantity': float(row['doc2_quantity']) if pd.notnull(row['doc2_quantity']) else None,
                'doc1_cost': float(row['doc1_cost']) if pd.notnull(row['doc1_cost']) else None,
                'doc2_cost': float(row['doc2_cost']) if pd.notnull(row['doc2_cost']) else None,
                'unit': row['unit'],
                'cost_difference': float(row['cost_difference']) if pd.notnull(row['cost_difference']) else None,
                'percentage_difference': float(row['percentage_cost_difference']) if pd.notnull(row['percentage_cost_difference']) else None,
                'is_labor': bool(row['is_labor']),
                'is_temporary': bool(row['is_temporary']),
                'doc1_occurrences': row.get('doc1_occurrences'),
                'doc2_occurrences': row.get('doc2_occurrences'),
                'match_confidence': float(row.get('match_confidence', 0)),
            }
            
            # Add additional fields from all_items_data if it exists
            all_items_data = next(
                (item for item in comparison_results['all_items_comparison'] 
                 if item['description'] == row['description']),
                None
            )
            
            if all_items_data:
                additional_data = {
                    'quantity': float(all_items_data.get('quantity')) if all_items_data.get('quantity') is not None else None,
                    'unit_cost': float(all_items_data.get('unit_cost')) if all_items_data.get('unit_cost') is not None else None,
                    'tax': float(all_items_data.get('tax')) if all_items_data.get('tax') is not None else None,
                    'op': float(all_items_data.get('op')) if all_items_data.get('op') is not None else None,
                    'rcv': float(all_items_data.get('rcv')) if all_items_data.get('rcv') is not None else None,
                    'total_cost': float(all_items_data.get('total_cost')) if all_items_data.get('total_cost') is not None else None,
                    'occurrences': all_items_data.get('occurrences', []),
                    'occurrence_count': int(all_items_data.get('occurrence_count', 0)),
                    'occurrence_summary': all_items_data.get('occurrence_summary', {
                        'total_quantity': 0,
                        'total_rcv': 0,
                        'occurrences_detail': []
                    })
                }
                item_data.update(additional_data)
            
            items.append(item_data)
        
        categorized_items[category] = {
            'items': items,
            'summary': create_category_summary(items)
        }
    
    return categorized_items

def create_overall_summary(analysis_df):
    """Create summary statistics for the entire comparison"""
    return {
        'total_items': len(analysis_df),
        'total_discrepancies': len(analysis_df[analysis_df['cost_difference'].abs() > 0]),
        'total_cost_difference': float(analysis_df['cost_difference'].sum()),  # Convert numpy float to Python float
        'average_difference_percentage': float(analysis_df['percentage_cost_difference'].mean()),
        'categories_affected': int(analysis_df['category'].nunique())  # Convert numpy int to Python int
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
            'total_underpaid_amount': float(abs(total_discrepancy)) if total_discrepancy < 0 else 0,
            'number_of_underpaid_items': int(len(underpaid_items)),
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
                    f'Focus on the top 5 discrepancies totaling ${abs(float(major_discrepancies["cost_difference"].sum())):.2f}',
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
    
    total_labor_diff = float(labor_df['cost_difference'].sum())
    return (f"Found ${abs(total_labor_diff):.2f} in labor cost discrepancies. "
            "Key issues include rate differences and missing labor operations.")

def _analyze_material_discrepancies(material_df):
    """Analyze patterns in material cost discrepancies"""
    if len(material_df) == 0:
        return "No significant material cost discrepancies found."
    
    total_material_diff = float(material_df['cost_difference'].sum())
    return (f"Found ${abs(total_material_diff):.2f} in material cost discrepancies. "
            "Focus on quantity differences and unit price variations.")

def _analyze_missing_items(df):
    """Analyze items present in doc1 but missing in doc2"""
    missing_items = df[df['doc2_cost'].isna()]
    if len(missing_items) == 0:
        return "No missing items identified."
    
    total_missing = float(missing_items['doc1_cost'].sum())
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
    total_diff = float(df['cost_difference'].sum())
    if total_diff >= 0:
        return {
            'amount': 0,
            'confidence': 'N/A',
            'note': 'No underpayment identified'
        }
    
    high_confidence = float(df[
        (df['cost_difference'] < 0) & 
        (df['match_confidence'] > 80)
    ]['cost_difference'].sum())
    
    medium_confidence = float(df[
        (df['cost_difference'] < 0) & 
        (df['match_confidence'].between(50, 80))
    ]['cost_difference'].sum())
    
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

def categorize_item(description):
    """Categorize items based on common terminology and associations"""
    matches = []
    for category, pattern in CATEGORY_PATTERNS.items():
        if re.search(pattern, description):
            matches.append(category)
    
    # Return the first match, or 'UNCATEGORIZED' if no matches
    return matches[0] if matches else 'UNCATEGORIZED'


def create_analysis_ready_dataframe(comparison_results):
    """Convert comparison results into an analysis-friendly format"""
    try:
        df = pd.DataFrame(comparison_results['all_items_comparison'])
        
        # Ensure required columns exist
        if 'unit' not in df.columns:
            df['unit'] = 'EA'  # Default unit if missing
        
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
        df['category'] = df['description'].apply(lambda x: categorize_item(x) if x else 'UNKNOWN')
        df['standardized_unit'] = df['unit'].apply(lambda x: UNIT_STANDARDIZATION.get(x, x))
        df['is_temporary'] = df['description'].str.contains('Temporary', case=False, na=False)
        df['is_labor'] = df['description'].str.contains('labor|hour|technician|supervisor', case=False, na=False)
        
        # Calculate significant difference
        df['significant_difference'] = df['percentage_cost_difference'].apply(
            lambda x: abs(x) > 5 if pd.notnull(x) else False
        )
        return df
    except Exception as e:
        logger.error(f"Error creating analysis-ready dataframe: {str(e)}")
        raise

def extract_text_from_pdf(file, doc_id):
    """Extract text and parse line items from PDF file"""
    text = process_pdf(file)
    items = parse_line_items(text)
    return items

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
        doc1_items = extract_text_from_pdf(file1, 'doc1')
        doc2_items = extract_text_from_pdf(file2, 'doc2')
        
        # Compare items
        comparison_results = compare_line_items(doc1_items, doc2_items)
        
        # Create analysis dataframe
        analysis_df = create_analysis_ready_dataframe(comparison_results)
        
        # Generate insights and summaries
        categorized_items = prepare_categorized_items(analysis_df, comparison_results)
        overall_summary = create_overall_summary(analysis_df)
        ai_insights = generate_ai_insights(analysis_df)
        
        # Prepare response
        response = {
            'comparison_results': comparison_results,
            'categorized_items': categorized_items,
            'overall_summary': overall_summary,
            'ai_insights': ai_insights,
            'file1_count': len(doc1_items),
            'file2_count': len(doc2_items),
            'metadata': {
                'file1_name': file1.filename,
                'file2_name': file2.filename,
                'comparison_date': datetime.now().isoformat()
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({
            'error': str(e),
            'comparison_results': {},
            'categorized_items': {},
            'overall_summary': {
                'total_items': 0,
                'total_discrepancies': 0,
                'total_cost_difference': 0,
                'average_difference_percentage': 0,
                'categories_affected': 0
            },
            'ai_insights': {},
            'file1_count': 0,
            'file2_count': 0,
            'metadata': {
                'file1_name': '',
                'file2_name': '',
                'comparison_date': datetime.now().isoformat()
            }
        }), 500

if __name__ == '__main__':
    app.run(debug=True)