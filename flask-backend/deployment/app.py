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
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.formparser import RequestEntityTooLarge
import logging
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import gc
import traceback
import pytesseract
from pdf2image import convert_from_path
import tempfile
import os
from PIL import Image
from PyPDF2 import PdfReader
import fitz  # PyMuPDF
import logging.handlers
from PIL import Image, ImageEnhance, ImageFilter, ImageOps  # Add ImageOps import
import shutil
import time

load_dotenv()

# Add at the top of your file, after imports
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Add a file handler if you want to save logs to a file
file_handler = logging.FileHandler('pdf_processing.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

app = Flask(__name__)
CORS(app)

# Increase maximum content length to 1GB
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB
app.config['MAX_CONTENT_PATH'] = None
app.config['REQUEST_TIMEOUT'] = 1200  # 20 minutes for larger files

# Add WSGI middleware to handle large files
app.wsgi_app = ProxyFix(app.wsgi_app)

# Configure maximum request size for werkzeug
app.config['MAX_CONTENT_LENGTH'] = None  # Disable werkzeug's limit

# Update error message for 1GB limit
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        'error': 'File too large. Maximum file size is 1GB.',
        'code': 413,
        'details': str(error)
    }), 413

@app.errorhandler(RequestEntityTooLarge)
def handle_request_entity_too_large(error):
    return jsonify({
        'error': 'File too large for processing.',
        'code': 413,
        'details': str(error)
    }), 413

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



logger = logging.getLogger(__name__)

def preprocess_image(image):
    """Enhanced image preprocessing for better OCR results"""
    try:
        # Convert to grayscale if not already
        if image.mode != 'L':
            gray = image.convert('L')
        else:
            gray = image
        
        # Increase contrast
        enhancer = ImageEnhance.Contrast(gray)
        gray = enhancer.enhance(2.0)
        
        # Add thresholding for cleaner text
        gray = ImageOps.autocontrast(gray)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(gray)
        gray = enhancer.enhance(1.5)
        
        return gray
        
    except Exception as e:
        logger.error(f"Error preprocessing image: {str(e)}")
        return image

def process_page_with_ocr(page, page_num: int) -> str:
    """Process a single page with table-aware OCR"""
    try:
        # Try PyMuPDF first (usually faster and more accurate)
        doc = fitz.open(page.pdf.stream.name)
        try:
            text = doc[page_num - 1].get_text()
            if text and len(text.strip()) > 50:
                lines = []
                for line in text.split('\n'):
                    if re.match(r'^\d+\.', line):
                        line = f"{line} [Page: {page_num}]"
                    lines.append(line)
                return '\n'.join(lines)
        finally:
            doc.close()
    except Exception as e:
        logger.debug(f"PyMuPDF extraction failed for page {page_num}: {str(e)}")

    try:
        # Convert to image
        images = convert_from_path(
            page.pdf.stream.name,
            first_page=page_num,
            last_page=page_num,
            dpi=300,
            grayscale=True
        )
        
        if not images:
            return f"--- Page {page_num} ---\nNo images extracted\n"

        img = preprocess_image(images[0])
        
        # Configure Tesseract
        custom_config = r'--oem 3 --psm 6'
        
        # Get raw text
        raw_text = pytesseract.image_to_string(
            img,
            lang='eng',
            config=custom_config
        )

        # Process text line by line
        lines = []
        current_item = None
        
        for line in raw_text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if re.match(r'^\d+\.', line):
                if current_item:
                    lines.extend(format_table_item(current_item))
                current_item = {'description': line, 'details': []}
            elif current_item and re.match(r'^\d+\.?\d*\s*(?:EA|SF|LF|HR|MO|WK)', line):
                current_item['details'].append(line)
            elif current_item:
                current_item['description'] += ' ' + line
        
        if current_item:
            lines.extend(format_table_item(current_item))
        
        result = '\n'.join(lines)
        
        if result and len(result.strip()) > 50:
            return f"--- Page {page_num} ---\n{result}\n"
            
        return f"--- Page {page_num} ---\nNo structured content extracted\n"

    except Exception as e:
        logger.warning(f"OCR processing failed for page {page_num}: {str(e)}")
        return f"--- Page {page_num} ---\nProcessing failed: {str(e)}\n"

def format_table_item(item):
    """Format a table item with proper spacing"""
    lines = []
    
    # Add description line
    lines.append(item['description'])
    
    # Add details with proper column alignment
    for detail in item['details']:
        # Split the detail line into components
        parts = re.split(r'\s+', detail)
        
        # Format with fixed column widths
        formatted_line = ''
        current_pos = 4  # Initial indent
        
        # Define column widths
        columns = {
            'quantity': 12,
            'unit': 8,
            'tax': 10,
            'op': 10,
            'rcv': 12,
            'age_life': 10,
            'cond': 8,
            'dep': 8,
            'deprec': 12,
            'acv': 12
        }
        
        # Add each part with proper spacing
        for i, part in enumerate(parts):
            if i < len(columns):
                width = list(columns.values())[i]
                formatted_line += part.ljust(width)
            else:
                formatted_line += ' ' + part
        
        lines.append(' ' * 4 + formatted_line.strip())
    
    return lines

def process_pdf_with_ocr(file) -> str:
    """Process PDF with PyMuPDF first, falling back to improved OCR if needed"""
    start_time = time.time()
    temp_file = None
    extracted_text = ""
    
    try:
        # Save to temporary file
        logger.info("Creating temporary file...")
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_pdf:
            temp_file = tmp_pdf.name
            if hasattr(file, 'save'):
                file.save(temp_file)
            else:
                shutil.copyfileobj(file, tmp_pdf)

        # Create output directory if it doesn't exist
        output_dir = os.path.join(os.path.dirname(temp_file), 'ocr_output')
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate unique filename based on timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(output_dir, f'ocr_output_{timestamp}.txt')

        # Try PyMuPDF first
        logger.info("Attempting PyMuPDF extraction...")
        try:
            doc = fitz.open(temp_file)
            text = ""
            total_pages = doc.page_count
            has_text = False
            
            for page_num in range(total_pages):
                logger.info(f"PyMuPDF: Processing page {page_num + 1}/{total_pages}")
                page_text = doc[page_num].get_text()
                if page_text.strip():
                    has_text = True
                    text += f"\n=== Page {page_num + 1} ===\n{page_text}"
            doc.close()
            
            if has_text and len(text.strip()) > 100:
                extracted_text = text
                logger.info("PyMuPDF extraction successful")
                # Save PyMuPDF output
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write("=== PyMuPDF Extraction ===\n")
                    f.write(extracted_text)
                return extracted_text
                
        except Exception as e:
            logger.warning(f"PyMuPDF extraction failed: {str(e)}")

        # Only proceed to OCR if PyMuPDF failed
        if not extracted_text:
            logger.info("Starting improved OCR extraction...")
            # Convert PDF to images
            images = convert_from_path(temp_file, dpi=300)
            all_text = []
            
            for i, image in enumerate(images, 1):
                logger.info(f"Processing page {i} with OCR")
                try:
                    # Preprocess image
                    processed_image = preprocess_image(image)
                    
                    # Perform OCR
                    text = pytesseract.image_to_string(
                        processed_image,
                        lang='eng',
                        config='--oem 3 --psm 6'
                    )
                    
                    if text:  # Remove .strip() to preserve original formatting
                        page_text = f"\n=== Page {i} ===\n{text}"
                        all_text.append(page_text)
                        
                        # Save individual page output
                        with open(output_file, 'a', encoding='utf-8') as f:
                            f.write(page_text)
                        
                except Exception as e:
                    logger.error(f"Error processing page {i}: {str(e)}")
                    continue
            
            extracted_text = "\n".join(all_text) if all_text else ""

        if not extracted_text:
            logger.warning("No text could be extracted from the PDF")
            # Save error message
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("No text could be extracted from the PDF")
            return ""
        
        logger.info(f"OCR output saved to: {output_file}")
        return extracted_text

    except Exception as e:
        logger.error(f"Error in PDF processing: {str(e)}")
        # Save error message
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"Error processing PDF: {str(e)}")
        return ""

    finally:
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
                logger.info("Temporary file cleaned up")
            except Exception as e:
                logger.warning(f"Error cleaning up temporary file: {str(e)}")

def preprocess_image(image):
    """Enhanced image preprocessing for better OCR results"""
    try:
        # Convert to grayscale if not already
        if image.mode != 'L':
            gray = image.convert('L')
        else:
            gray = image
        
        # Increase contrast
        enhancer = ImageEnhance.Contrast(gray)
        gray = enhancer.enhance(2.0)
        
        # Add thresholding for cleaner text
        gray = ImageOps.autocontrast(gray)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(gray)
        gray = enhancer.enhance(1.5)
        
        return gray
        
    except Exception as e:
        logger.error(f"Error preprocessing image: {str(e)}")
        return image

def process_page_alternative(file_path: str, page_num: int) -> str:
    """Alternative method to process a single page using PyMuPDF directly"""
    try:
        doc = fitz.open(file_path)
        try:
            page = doc[page_num - 1]
            
            # Try to get text directly first
            text = page.get_text()
            if text and not text.isspace():
                return f"--- Page {page_num} ---\n{text}\n"
            
            # If no text, try OCR
            zoom = 2.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img = preprocess_image(img)
            
            ocr_text = pytesseract.image_to_string(
                img,
                lang='eng',
                config='--psm 6 --oem 3'
            )
            
            return f"--- Page {page_num} (Alternative OCR) ---\n{ocr_text}\n"
            
        finally:
            doc.close()
            
    except Exception as e:
        logger.error(f"Alternative processing failed for page {page_num}: {str(e)}")
        return f"--- Page {page_num} ---\nFailed to extract text\n"

def process_pdf_alternative(file_path: str) -> list:
    """Process entire PDF using PyMuPDF as an alternative method"""
    all_text = []
    
    try:
        doc = fitz.open(file_path)
        try:
            for page_num in range(doc.page_count):
                text = process_page_alternative(file_path, page_num + 1)
                all_text.append(text)
                gc.collect()
                
        finally:
            doc.close()
            
    except Exception as e:
        logger.error(f"Alternative PDF processing failed: {str(e)}")
        all_text.append(f"Failed to process PDF: {str(e)}")
        
    return all_text

# Create a custom handler to capture warnings
class WarningCaptureHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.warnings = []

    def emit(self, record):
        self.warnings.append(record.getMessage())

def is_valid_pdf(file_path) -> tuple[bool, str]:
    """
    Validate if the file is a valid, readable PDF and check for restrictions.
    Returns (is_valid, error_message)
    """
    # Set up warning capture
    warning_handler = WarningCaptureHandler()
    logging.getLogger('pdfminer').addHandler(warning_handler)
    
    try:
        # First try with PyPDF2
        with open(file_path, 'rb') as file:
            try:
                pdf = PdfReader(file)
                
                # Skip encryption check to allow OCR processing
                # if pdf.is_encrypted:
                #     return False, "PDF is encrypted or password protected"
                    
                # Check for empty document
                if len(pdf.pages) == 0:
                    return False, "PDF contains no pages"
                    
                # Check for warnings that indicate corruption
                if any('Data-loss' in warning or 'corrupted' in warning.lower() 
                      for warning in warning_handler.warnings):
                    return False, "PDF appears to be corrupted or contains data loss"
                    
            except Exception as e:
                logger.warning(f"PyPDF2 validation failed: {str(e)}")
                # If PyPDF2 fails, try with PyMuPDF as fallback
                try:
                    doc = fitz.open(file_path)
                    if doc.needs_pass:
                        doc.close()
                        return False, "PDF is encrypted or password protected"
                    if doc.page_count == 0:
                        doc.close()
                        return False, "PDF contains no pages"
                        
                    # Additional corruption check with PyMuPDF
                    try:
                        # Try to access each page - this can trigger corruption errors
                        for page_num in range(doc.page_count):
                            page = doc[page_num]
                            # Try to get text to check for corruption
                            text = page.get_text()
                    except Exception as page_error:
                        doc.close()
                        return False, f"PDF corruption detected: {str(page_error)}"
                        
                    doc.close()
                except Exception as mupdf_error:
                    return False, f"Invalid or corrupted PDF: {str(mupdf_error)}"

        # Check captured warnings for any corruption indicators
        if warning_handler.warnings:
            corruption_warnings = [w for w in warning_handler.warnings 
                                if 'Data-loss' in w or 'corrupted' in w.lower()]
            if corruption_warnings:
                return False, f"PDF corruption detected: {'; '.join(corruption_warnings)}"

        return True, ""

    except Exception as e:
        return False, f"Error validating PDF: {str(e)}"
        
    finally:
        # Clean up the warning handler
        logging.getLogger('pdfminer').removeHandler(warning_handler)

def extract_text_from_pdf(text, doc_id):
    """Parse line items from text"""
    try:
        # Output raw text to a file
        output_filename = f"{doc_id}_extracted_text.txt"
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(text if text else "No text extracted")
        
        # Continue with parsing if we have text
        if text:
            try:
                items = parse_line_items(text)
                logger.info(f"Processed {len(items)} items from {doc_id}")
                return items
            except Exception as e:
                logger.error(f"Error parsing line items for {doc_id}: {str(e)}")
                return []
        return []
        
    except Exception as e:
        logger.error(f"Error processing text {doc_id}: {str(e)}")
        return []

def clean_item_number(item_number):
    """Clean and standardize item numbers"""
    if not item_number:
        return None
        
    # Extract only the numeric part
    match = re.search(r'(\d+)', str(item_number))
    if match:
        return match.group(1)
    return None

def parse_quantity(quantity_text):
    """Parse quantity value from text that may include unit"""
    if not quantity_text:
        return 0.0
        
    try:
        # Remove any units (SF, EA, LF, etc) and convert to float
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
        # Initialize default values
        item.setdefault('quantity', '0')
        item.setdefault('rcv', '0')
        item.setdefault('item_number', '0')
        item.setdefault('page_number', 1)
        item.setdefault('description', '')
        
        # Format occurrences data
        doc1_occurrences = {
            'total_quantity': float(item.get('quantity', 0)),
            'total_rcv': float(item.get('rcv', 0)),
            'occurrences_detail': []
        }
        
        # Add occurrence detail with proper formatting
        if item.get('occurrence'):
            occurrence_detail = (
                f"Line {item['occurrence'].get('line', '0')} "
                f"(Page {item['occurrence'].get('page', '1')}): "
                f"Qty={float(item.get('quantity', 0))}, "
                f"RCV=${float(item.get('rcv', 0)):.2f}"
            )
            doc1_occurrences['occurrences_detail'].append(occurrence_detail)
        
        item['doc1_occurrences'] = doc1_occurrences
        
        return item
        
    except Exception as e:
        logger.error(f"Error in cleanup_line_item: {str(e)}")
        return {
            'description': item.get('description', ''),
            'quantity': '0',
            'unit': 'EA',
            'rcv': '0',
            'doc1_occurrences': {
                'total_quantity': 0.0,
                'total_rcv': 0.0,
                'occurrences_detail': []
            }
        }

def parse_line_items(text):
    """Parse line items with enhanced page number and line occurrence tracking"""
    line_items = []
    current_page = 1
    current_item = None
    
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        try:
            # Check for page markers in header format "Page: X" or "Page X"
            page_match = re.search(r'Page:?\s*(\d+)', line, re.IGNORECASE)
            if page_match:
                current_page = int(page_match.group(1))
                continue
            
            # Try OCR-specific pattern first - now looking for description with embedded numbers
            ocr_match = re.match(r"""
                ^(.*?)\s+                           # Description (non-greedy, includes item number)
                (\d+\.?\d*)\s*([A-Z]{2})\s+        # Quantity with unit
                (\d+\.?\d*)\s+                      # First number
                (\d+\.?\d*)\s+                      # Second number
                (\d+\.?\d*)\s+                      # Third number
                (\d+\.?\d*)\s+                      # Fourth number
                (\d+\.?\d*)$                        # Final number (RCV)
            """, line.strip(), re.VERBOSE)
            
            if ocr_match:
                # Extract item number and description
                full_desc = ocr_match.group(1).strip()
                item_num_match = re.match(r'^(\d{1,3}(?:,\d{3})*)\.\s+(.*?)$', full_desc)
                
                if item_num_match:
                    item_number = int(item_num_match.group(1).replace(',', ''))
                    description = item_num_match.group(2).strip()
                    quantity = ocr_match.group(2)
                    unit = ocr_match.group(3)
                    rcv = ocr_match.group(8)  # Last number as RCV
                    
                    current_item = {
                        'item_number': item_number,
                        'description': description,
                        'page_number': current_page,
                        'line_number': item_number,
                        'occurrence': {
                            'page': current_page,
                            'line': item_number
                        },
                        'quantity': quantity,
                        'unit': unit,
                        'rcv': rcv
                    }
                    
                    logger.debug(f"Matched OCR line item {item_number}: {description[:50]}...")
                    line_items.append(current_item)
                    current_item = None  # Reset current_item after adding
                    continue
            
            # Rest of the existing code for normal text parsing...
            # If not OCR format, try original pattern
            line_match = re.match(r'^(\d{1,3}(?:,\d{3})*)\.\s+(.*?)$', line.strip())
            if line_match:
                # Save previous item if exists
                if current_item:
                    line_items.append(cleanup_line_item(current_item))
                
                # Convert item number string to integer (remove commas first)
                item_number = int(line_match.group(1).replace(',', ''))
                current_item = {
                    'item_number': item_number,
                    'description': line_match.group(2),
                    'page_number': current_page,
                    'line_number': item_number,
                    'occurrence': {
                        'page': current_page,
                        'line': item_number
                    },
                    'quantity': '0',
                    'unit': 'EA',
                    'rcv': '0'
                }
                continue
            
            # If we have a current item (non-OCR), try to match quantity and values
            if current_item:
                # Match quantity and unit
                qty_unit_match = re.match(r'^([\d,\.]+)\s*([A-Z]{2})\s*$', line.strip())
                if qty_unit_match:
                    current_item['quantity'] = qty_unit_match.group(1).replace(',', '')
                    current_item['unit'] = qty_unit_match.group(2)
                    continue
                
                # Match RCV value
                rcv_match = re.match(r'^([\d,\.]+)$', line.strip())
                if rcv_match:
                    current_item['rcv'] = rcv_match.group(1).replace(',', '')
                    continue
        
        except Exception as e:
            logger.error(f"Error processing line {i}: {str(e)}")
            continue
    
    # Don't forget to append the last item if it's a non-OCR item
    if current_item:
        line_items.append(cleanup_line_item(current_item))
    
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

def clean_description(description):
    """
    Clean description by removing trailing quantity and cost information.
    Example: 'Floor leveling cement - Average 212.83SF 2.36 23.12 105.08 630.48 (0.00) 630.48'
    -> 'Floor leveling cement - Average'
    """
    if not description:
        return ''
        
    # Pattern to match quantity/cost information at the end of description
    # Matches patterns like: 212.83SF 2.36 23.12 105.08 630.48 (0.00) 630.48
    pattern = r'\s+\d+\.?\d*(?:SF|EA|LF|HR|MO|WK|CF|DA|SQ)?\s+[-\d\.,\s\(\)]+$'
    
    # Remove the trailing numbers and units
    cleaned = re.sub(pattern, '', description)
    return cleaned.strip()

def extract_unit(value_str):
    """
    Extract unit from strings like '8.00MO', '120.00LF', or '12 LF'
    """
    if not value_str or pd.isna(value_str):
        return 'EA'  # Default unit
    try:
        # First clean the description if it contains embedded quantities
        value_str = clean_description(str(value_str))
        
        # Extract unit part using regex, handling both cases:
        # - Units directly after number (8.00MO)
        # - Units with space after number (12 LF)
        match = re.search(r'\s*([A-Za-z]+)$', str(value_str))
        if match:
            return match.group(1).upper()
        return 'EA'  # Default unit
    except (ValueError, TypeError):
        return 'EA'  # Default unit

def find_best_match(description: str, items_list: list, threshold: float = 80) -> tuple:
    """
    Find the best matching item from a list based on description similarity.
    Returns tuple of (matched_item, match_ratio).
    """
    try:
        best_match = None
        best_ratio = 0
        
        # Clean the input description
        cleaned_desc = clean_description(description)
        
        # Extract key characteristics from the cleaned description
        desc_specs = extract_specifications(cleaned_desc)
        
        # Get base description without action words for better matching
        base_desc = re.sub(r'^(remove|install|replace|repair)\s+', '', cleaned_desc.lower().strip())
        
        for item in items_list:
            # Clean the comparison description
            cleaned_item_desc = clean_description(item['description'])
            
            # Extract specifications from potential match
            item_specs = extract_specifications(cleaned_item_desc)
            
            # If specifications are different, skip this match
            if not are_specs_compatible(desc_specs, item_specs):
                continue
            
            # Get base description for comparison item
            item_base_desc = re.sub(r'^(remove|install|replace|repair)\s+', '', cleaned_item_desc.lower().strip())
            
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

def compare_line_items(items1, items2):
    """Compare line items with proper occurrence tracking"""
    try:
        logger.info(f"Comparing {len(items1)} items from doc1 with {len(items2)} items from doc2")
        
        comparison_results = {
            'all_items_comparison': [],
            'cost_discrepancies': [],
            'quantity_discrepancies': [],
            'unique_to_doc1': [],
            'unique_to_doc2': []
        }
        
        # Compare items
        for item1 in items1:
            try:
                item1_desc = item1.get('description', '')
                item1_qty = float(item1.get('quantity', '0').replace(',', '') or '0')
                item1_rcv = float(item1.get('rcv', '0').replace(',', '') or '0')
                
                # Create doc1 occurrence data
                doc1_occurrences = [{
                    'page': item1.get('page_number', 1),
                    'line': item1.get('line_number', 0),
                    'quantity': item1_qty,
                    'rcv': item1_rcv,
                    'quantity_line': item1.get('occurrence', {}).get('quantity_line'),
                    'quantity_page': item1.get('occurrence', {}).get('quantity_page'),
                    'rcv_line': item1.get('occurrence', {}).get('rcv_line'),
                    'rcv_page': item1.get('occurrence', {}).get('rcv_page')
                }]
                
                matched_item, match_ratio = find_best_match(item1_desc, items2)
                
                if matched_item:
                    matched_qty = float(matched_item.get('quantity', '0').replace(',', '') or '0')
                    matched_rcv = float(matched_item.get('rcv', '0').replace(',', '') or '0')
                    
                    # Create doc2 occurrence data
                    doc2_occurrences = [{
                        'page': matched_item.get('page_number', 1),
                        'line': matched_item.get('line_number', 0),
                        'quantity': matched_qty,
                        'rcv': matched_rcv,
                        'quantity_line': matched_item.get('occurrence', {}).get('quantity_line'),
                        'quantity_page': matched_item.get('occurrence', {}).get('quantity_page'),
                        'rcv_line': matched_item.get('occurrence', {}).get('rcv_line'),
                        'rcv_page': matched_item.get('occurrence', {}).get('rcv_page')
                    }]
                    
                    comparison_entry = {
                        'description': item1_desc,
                        'doc1_quantity': item1_qty,
                        'doc1_cost': item1_rcv,
                        'doc1_occurrences': doc1_occurrences,
                        'unit': item1.get('unit', 'EA'),
                        'doc2_quantity': matched_qty,
                        'doc2_cost': matched_rcv,
                        'doc2_occurrences': doc2_occurrences,
                        'quantity_difference': item1_qty - matched_qty,
                        'cost_difference': item1_rcv - matched_rcv,
                        'percentage_cost_difference': ((item1_rcv - matched_rcv) / item1_rcv * 100) if item1_rcv != 0 else 0,
                        'match_confidence': match_ratio,
                        'occurrence_summary': {
                            'doc1': {
                                'total_quantity': item1_qty,
                                'total_rcv': item1_rcv,
                                'occurrences_detail': doc1_occurrences
                            },
                            'doc2': {
                                'total_quantity': matched_qty,
                                'total_rcv': matched_rcv,
                                'occurrences_detail': doc2_occurrences
                            }
                        }
                    }
                    
                    comparison_results['all_items_comparison'].append(comparison_entry)
                    
                    if abs(comparison_entry['cost_difference']) > 0.01:
                        comparison_results['cost_discrepancies'].append(comparison_entry)
                    if abs(comparison_entry['quantity_difference']) > 0.01:
                        comparison_results['quantity_discrepancies'].append(comparison_entry)
                else:
                    comparison_results['unique_to_doc1'].append({
                        **item1,
                        'occurrences': doc1_occurrences,
                        'occurrence_summary': {
                            'total_quantity': item1_qty,
                            'total_rcv': item1_rcv,
                            'occurrences_detail': doc1_occurrences
                        }
                    })
            
            except Exception as e:
                logger.error(f"Error comparing item: {str(e)}")
                continue
        
        # Find items unique to doc2
        doc1_descriptions = {item.get('description', '').lower() for item in items1}
        for item2 in items2:
            if item2.get('description', '').lower() not in doc1_descriptions:
                qty = float(item2.get('quantity', '0').replace(',', '') or '0')
                rcv = float(item2.get('rcv', '0').replace(',', '') or '0')
                
                doc2_occurrences = [{
                    'page': item2.get('page_number', 1),
                    'line': item2.get('line_number', 0),
                    'quantity': qty,
                    'rcv': rcv,
                    'quantity_line': item2.get('occurrence', {}).get('quantity_line'),
                    'quantity_page': item2.get('occurrence', {}).get('quantity_page'),
                    'rcv_line': item2.get('occurrence', {}).get('rcv_line'),
                    'rcv_page': item2.get('occurrence', {}).get('rcv_page')
                }]
                
                comparison_results['unique_to_doc2'].append({
                    **item2,
                    'occurrences': doc2_occurrences,
                    'occurrence_summary': {
                        'total_quantity': qty,
                        'total_rcv': rcv,
                        'occurrences_detail': doc2_occurrences
                    }
                })
        
        return comparison_results
        
    except Exception as e:
        logger.error(f"Error in compare_line_items: {str(e)}")
        return {
            'all_items_comparison': [],
            'cost_discrepancies': [],
            'quantity_discrepancies': [],
            'unique_to_doc1': [],
            'unique_to_doc2': []
        }

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

def format_occurrence_data(item, doc_number):
    """Format occurrence data for a single document"""
    try:
        quantity = float(item.get('quantity', 0))
        rcv = float(item.get('rcv', 0))
        page = item.get('page_number', 1)
        line = item.get('item_number', 0)  # Use item_number instead of line_number
        
        return {
            f'doc{doc_number}_occurrences': {
                'total_quantity': quantity,
                'total_rcv': rcv,
                'occurrences_detail': [
                    f"Line {line} (Page {page}): Qty={quantity}, RCV=${rcv:.2f}"
                ]
            }
        }
    except Exception as e:
        logger.error(f"Error formatting occurrence data: {str(e)}")
        return {
            f'doc{doc_number}_occurrences': {
                'total_quantity': 0.0,
                'total_rcv': 0.0,
                'occurrences_detail': []
            }
        }

def prepare_categorized_items(df: pd.DataFrame, comparison_results: dict) -> Dict:
    """Prepare all items organized by category with detailed analysis"""
    try:
        # Define threshold for significant differences
        HIGH_DIFFERENCE_THRESHOLD = 20
        CRITICAL_DIFFERENCE_THRESHOLD = 50

        categorized_items = {}

        # Create a mapping of descriptions to their occurrences from all_items_comparison
        occurrence_mapping = {}
        
        # Process all_items_comparison for both doc1 and doc2 occurrences
        for item in comparison_results['all_items_comparison']:
            desc = item.get('description', '')
            
            # Initialize occurrence data if not exists
            if desc not in occurrence_mapping:
                occurrence_mapping[desc] = {
                    'doc1_occurrences': {
                        'total_quantity': 0,
                        'total_rcv': 0,
                        'occurrences_detail': set()  # Using set to prevent duplicates
                    },
                    'doc2_occurrences': {
                        'total_quantity': 0,
                        'total_rcv': 0,
                        'occurrences_detail': set()  # Using set to prevent duplicates
                    }
                }

            # Process doc1 occurrences
            if 'occurrence_summary' in item and 'doc1' in item['occurrence_summary']:
                doc1_data = item['occurrence_summary']['doc1']
                occurrence_mapping[desc]['doc1_occurrences']['total_quantity'] = doc1_data.get('total_quantity', 0)
                occurrence_mapping[desc]['doc1_occurrences']['total_rcv'] = doc1_data.get('total_rcv', 0)
                
                if 'occurrences_detail' in doc1_data:
                    for occ in doc1_data['occurrences_detail']:
                        if isinstance(occ, dict):
                            line = occ.get('line', '')
                            page = occ.get('page', '')
                            qty = occ.get('quantity', 0)
                            rcv = occ.get('rcv', 0)
                            detail = f"Line {line} (Page {page}): Qty={qty}, RCV=${rcv:.2f}"
                            occurrence_mapping[desc]['doc1_occurrences']['occurrences_detail'].add(detail)

            # Process doc2 occurrences
            if 'occurrence_summary' in item and 'doc2' in item['occurrence_summary']:
                doc2_data = item['occurrence_summary']['doc2']
                occurrence_mapping[desc]['doc2_occurrences']['total_quantity'] = doc2_data.get('total_quantity', 0)
                occurrence_mapping[desc]['doc2_occurrences']['total_rcv'] = doc2_data.get('total_rcv', 0)
                
                if 'occurrences_detail' in doc2_data:
                    for occ in doc2_data['occurrences_detail']:
                        if isinstance(occ, dict):
                            line = occ.get('line', '')
                            page = occ.get('page', '')
                            qty = occ.get('quantity', 0)
                            rcv = occ.get('rcv', 0)
                            detail = f"Line {line} (Page {page}): Qty={qty}, RCV=${rcv:.2f}"
                            occurrence_mapping[desc]['doc2_occurrences']['occurrences_detail'].add(detail)

        # Process categories
        for category in df['category'].unique():
            category_df = df[df['category'] == category]
            
            items = []
            for _, row in category_df.iterrows():
                # Get occurrence data from mapping
                occurrences = occurrence_mapping.get(row['description'], {
                    'doc1_occurrences': {'occurrences_detail': set(), 'total_quantity': 0, 'total_rcv': 0},
                    'doc2_occurrences': {'occurrences_detail': set(), 'total_quantity': 0, 'total_rcv': 0}
                })
                
                # Convert sets to lists for JSON serialization
                doc1_occurrences = {
                    'occurrences_detail': sorted(list(occurrences['doc1_occurrences']['occurrences_detail'])),
                    'total_quantity': occurrences['doc1_occurrences']['total_quantity'],
                    'total_rcv': occurrences['doc1_occurrences']['total_rcv']
                }
                
                doc2_occurrences = {
                    'occurrences_detail': sorted(list(occurrences['doc2_occurrences']['occurrences_detail'])),
                    'total_quantity': occurrences['doc2_occurrences']['total_quantity'],
                    'total_rcv': occurrences['doc2_occurrences']['total_rcv']
                }

                # Calculate severity
                percentage_diff = row['percentage_cost_difference'] if not pd.isna(row['percentage_cost_difference']) else 0
                severity = 'normal'
                if abs(percentage_diff) >= CRITICAL_DIFFERENCE_THRESHOLD:
                    severity = 'critical'
                elif abs(percentage_diff) >= HIGH_DIFFERENCE_THRESHOLD:
                    severity = 'high'

                items.append({
                    'description': row['description'],
                    'doc1_quantity': row['doc1_quantity'],
                    'doc2_quantity': row['doc2_quantity'],
                    'doc1_cost': row['doc1_cost'],
                    'doc2_cost': row['doc2_cost'],
                    'unit': row['unit'],
                    'cost_difference': row['cost_difference'],
                    'percentage_difference': percentage_diff,
                    'is_labor': bool(row['is_labor']),
                    'is_temporary': bool(row['is_temporary']),
                    'severity': severity,
                    'doc1_occurrences': doc1_occurrences,
                    'doc2_occurrences': doc2_occurrences
                })

            categorized_items[category] = {
                'items': items,
                'summary': {
                    'total_items': len(items),
                    'total_doc1_cost': category_df['doc1_cost'].sum(),
                    'total_doc2_cost': category_df['doc2_cost'].sum(),
                    'total_difference': category_df['cost_difference'].sum(),
                    'average_difference_percentage': category_df['percentage_cost_difference'].mean(),
                    'critical_items': len([item for item in items if item['severity'] == 'critical']),
                    'high_difference_items': len([item for item in items if item['severity'] == 'high']),
                    'labor_items': len([item for item in items if item['is_labor']]),
                    'temporary_items': len([item for item in items if item['is_temporary']])
                }
            }

        return categorized_items

    except Exception as e:
        logger.error(f"Error in prepare_categorized_items: {str(e)}")
        raise

def create_overall_summary(analysis_df):
    """Create summary statistics for the entire comparison"""
    return {
        'total_items': int(len(analysis_df)),  # Convert to native Python int
        'total_discrepancies': int(len(analysis_df[analysis_df['cost_difference'].abs() > 0])),
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

def extract_categories_from_recap(text: str) -> dict:
    """Extract categories from recap section with fallback to predefined categories"""
    try:
        # Try to extract categories from text first
        categories = {}
        if text:
            # ... existing category extraction logic ...
            pass
            
        # If no categories were extracted, use predefined categories
        if not categories:
            logger.info("No categories found in text, using predefined categories")
            categories = {
                category: {
                    'pattern': CATEGORY_PATTERNS[category],
                    'original': False,
                    'search_terms': category.lower().split()
                }
                for category in CATEGORY_PATTERNS.keys()
            }
            
        return categories
        
    except Exception as e:
        logger.warning(f"Error extracting categories, falling back to predefined: {str(e)}")
        # Return predefined categories on error
        return {
            category: {
                'pattern': CATEGORY_PATTERNS[category],
                'original': False,
                'search_terms': category.lower().split()
            }
            for category in CATEGORY_PATTERNS.keys()
        }

def categorize_item(description: str, categories: dict) -> str:
    """Improved categorization function"""
    if not description or not isinstance(description, str):
        return 'UNCATEGORIZED'
    
    description = description.lower().strip()
    
    # Try exact matches first
    for category, info in categories.items():
        if re.search(info['pattern'], description):
            return category
    
    # Try partial matches with individual words
    best_match = None
    highest_score = 0
    
    for category, info in categories.items():
        search_terms = info.get('search_terms', category.lower().split())
        description_words = set(description.split())
        
        # Count matching words
        matches = sum(1 for term in search_terms if term in description_words)
        score = matches / len(search_terms) if search_terms else 0
        
        if score > highest_score and score >= 0.4:  # Lower threshold to 40% match
            highest_score = score
            best_match = category
    
    return best_match if best_match else 'UNCATEGORIZED'

def create_analysis_ready_dataframe(comparison_results, categories):
    """Create analysis dataframe with improved categorization"""
    try:
        logger.info(f"Creating analysis DataFrame from {len(comparison_results)} results")
        
        # Check if we have the expected structure
        if not comparison_results or 'all_items_comparison' not in comparison_results:
            logger.warning("No comparison results or missing all_items_comparison")
            # Return empty DataFrame with expected columns
            return pd.DataFrame({
                'description': [],
                'category': [],
                'doc1_quantity': [],
                'doc2_quantity': [],
                'unit': [],
                'doc1_cost': [],
                'doc2_cost': [],
                'quantity_difference': [],
                'cost_difference': [],
                'percentage_cost_difference': [],
                'match_confidence': []
            })

        # Convert comparison results to DataFrame
        items = comparison_results['all_items_comparison']
        logger.info(f"Processing {len(items)} items")
        
        # Create DataFrame with explicit columns and type conversion
        df = pd.DataFrame([{
            'description': str(item.get('description', 'No description')),
            'doc1_quantity': float(item.get('doc1_quantity', 0) or 0),
            'doc2_quantity': float(item.get('doc2_quantity', 0) or 0),
            'unit': str(item.get('unit', 'EA')),
            'doc1_cost': float(item.get('doc1_cost', 0) or 0),
            'doc2_cost': float(item.get('doc2_cost', 0) or 0),
            'quantity_difference': float(item.get('quantity_difference', 0) or 0),
            'cost_difference': float(item.get('cost_difference', 0) or 0),
            'percentage_cost_difference': float(item.get('percentage_cost_difference', 0) or 0),
            'match_confidence': float(item.get('match_confidence', 0) or 0)
        } for item in items])
        
        # Add analysis columns with explicit type conversion
        df['category'] = df['description'].apply(lambda x: categorize_item(x, categories))
        df['is_labor'] = df['description'].str.contains('labor|hour|hr', case=False, na=False).astype(bool)
        df['is_temporary'] = df['description'].str.contains('temp|temporary', case=False, na=False).astype(bool)
        
        logger.info(f"Final DataFrame shape: {df.shape}")
        return df
        
    except Exception as e:
        logger.error(f"Error creating analysis-ready dataframe: {str(e)}")
        logger.error(f"Comparison results sample: {str(comparison_results)[:500]}")
        # Return minimal valid DataFrame
        return pd.DataFrame({
            'description': ['Error processing data'],
            'category': ['Error'],
            'doc1_quantity': [0.0],
            'doc2_quantity': [0.0],
            'unit': ['EA'],
            'doc1_cost': [0.0],
            'doc2_cost': [0.0],
            'quantity_difference': [0.0],
            'cost_difference': [0.0],
            'percentage_cost_difference': [0.0],
            'match_confidence': [0.0],
            'is_labor': [False],
            'is_temporary': [False]
        })

# Constants needed for the function above
UNIT_STANDARDIZATION = {
    'LF': 'LF',
    'SF': 'SF',
    'SY': 'SY',
    'EA': 'EA',
    'HR': 'HR',
    'BG': 'BG',
    'RL': 'RL',
    'PR': 'PR',
    'PK': 'PK',
    'BX': 'BX',
    'GL': 'GL',
    'CF': 'CF',
    'CY': 'CY',
    'PC': 'PC',
    'SET': 'SET',
    'TON': 'TON',
    'SQ': 'SQ',
    'LB': 'LB',
    'GAL': 'GL',
    'EACH': 'EA',
    'FOOT': 'LF',
    'FEET': 'LF',
    'SQUARE': 'SF',
    'YARD': 'SY',
    'HOUR': 'HR',
    'BAG': 'BG',
    'ROLL': 'RL',
    'PAIR': 'PR',
    'PACK': 'PK',
    'BOX': 'BX',
    'GALLON': 'GL'
}

# Update the compare_pdfs route to use extracted categories
@app.route('/api/compare', methods=['POST'])
def compare_pdfs():
    temp_files = []  # Track temp files for cleanup
    try:
        if 'file1' not in request.files or 'file2' not in request.files:
            return jsonify({'error': 'Two PDF files are required'}), 400
            
        file1 = request.files['file1']
        file2 = request.files['file2']
        
        if not file1.filename.endswith('.pdf') or not file2.filename.endswith('.pdf'):
            return jsonify({'error': 'Both files must be PDFs'}), 400

        # Create temporary files with .pdf extension
        temp_file1 = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        temp_file2 = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        temp_files.extend([temp_file1.name, temp_file2.name])

        # Save uploaded files to temporary files
        file1.save(temp_file1.name)
        file2.save(temp_file2.name)
        
        # Close the temporary files to ensure they're properly written
        temp_file1.close()
        temp_file2.close()

        # Validate PDFs before processing
        for pdf_path in [temp_file1.name, temp_file2.name]:
            is_valid, error_message = is_valid_pdf(pdf_path)
            if not is_valid:
                raise ValueError(f"Invalid PDF: {error_message}")

        # Extract text from both files (do this only once)
        with open(temp_file1.name, 'rb') as f1, open(temp_file2.name, 'rb') as f2:
            doc1_text = process_pdf_with_ocr(f1)
            doc2_text = process_pdf_with_ocr(f2)
        
        # Add more detailed logging for category extraction
        logger.info("Starting category extraction...")
        logger.info(f"Doc1 text sample: {doc1_text[:1000]}")  # Log first 1000 chars
        
        doc1_categories = extract_categories_from_recap(doc1_text) or {}
        doc2_categories = extract_categories_from_recap(doc2_text) or {}
        
        # Merge categories from both documents
        merged_categories = {**doc1_categories, **doc2_categories}
        
        # Parse items using the already extracted text
        doc1_items = parse_line_items(doc1_text)
        doc2_items = parse_line_items(doc2_text)
        
        # Continue with comparison
        comparison_results = compare_line_items(doc1_items, doc2_items)
        
        # Create analysis dataframe
        analysis_df = create_analysis_ready_dataframe(comparison_results, merged_categories)
        
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
        
        # After categorization
        category_counts = analysis_df['category'].value_counts()
        logger.info(f"Category distribution: {category_counts.to_dict()}")
        
        # Extract categories with detailed logging
        logger.info("Extracting categories from document 1...")
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}\n{traceback.format_exc()}")
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
        
    finally:
        # Clean up temporary files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except Exception as e:
                logger.warning(f"Error cleaning up temporary file {temp_file}: {str(e)}")

def extract_line_item_details(line: str, page_number: int, line_number: int) -> dict:
    """Extract quantity, unit, and total cost from a line item"""
    try:
        # Pattern to match the entire line structure
        # Matches: quantity/unit at start and final cost at end
        pattern = r"""
            ^                           # Start of line
            (?:(\d+(?:\.\d+)?          # Quantity (numeric)
            \s*                        # Optional space
            (?:[A-Z]{1,3})?           # Optional unit (1-3 uppercase letters)
            )\s+)?                     # End quantity/unit group, make optional
            .*?                        # Any text in between
            (\d{1,3}(?:,\d{3})*(?:\.\d{2})?  # Final cost (with optional commas and decimals)
            $                           # End of line
        """
        
        match = re.search(pattern, line.strip(), re.VERBOSE)
        if match:
            quantity_str = match.group(1) if match.group(1) else ''
            total_cost = float(match.group(2).replace(',', ''))
            
            # Extract unit from quantity string
            unit_match = re.search(r'([A-Z]{1,3})$', quantity_str)
            unit = unit_match.group(1) if unit_match else 'EA'
            
            # Clean quantity to just the numeric value
            quantity = re.match(r'\d+(?:\.\d+)?', quantity_str)
            quantity = float(quantity.group(0)) if quantity else 1.0
            
            return {
                'quantity': quantity,
                'unit': unit,
                'total_cost': total_cost,
                'page_number': page_number,
                'line_number': line_number,
                'raw_text': line.strip()
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error extracting line item details: {str(e)}")
        return None

def process_document_lines(text: str) -> list:
    """Process document and extract all line items with their details"""
    line_items = []
    current_page = 1
    
    # Split text into pages (assuming pages are separated by some marker)
    pages = text.split('Page:')  # Adjust separator based on your document format
    
    for page_num, page_text in enumerate(pages, 1):
        lines = page_text.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            item_details = extract_line_item_details(line, page_num, line_num)
            if item_details:
                line_items.append(item_details)
    
    return line_items

def track_item_occurrences(line_items: list) -> dict:
    """Track occurrences of similar items across the document"""
    occurrences = {}
    
    for item in line_items:
        # Create a key based on quantity and unit
        key = f"{item['quantity']}{item['unit']}"
        
        if key not in occurrences:
            occurrences[key] = {
                'locations': [],
                'total_quantity': 0,
                'total_cost': 0
            }
        
        occurrences[key]['locations'].append({
            'page': item['page_number'],
            'line': item['line_number'],
            'cost': item['total_cost']
        })
        occurrences[key]['total_quantity'] += item['quantity']
        occurrences[key]['total_cost'] += item['total_cost']
    
    return occurrences

def normalize_line_items(text):
    """Extract and normalize line items from insurance estimate sheets"""
    try:
        aggregated_items = {}
        
        for match in re.finditer(line_item_pattern, text, re.MULTILINE | re.VERBOSE):
            # Extract basic info
            line_num = match.group('line_num')
            quantity = float(match.group('quantity').replace(',', ''))
            page_num = match.group('page_num') or '1'
            raw_description = match.group('description').strip()
            unit_cost = float(match.group('unit_cost').replace(',', ''))
            rcv = float(match.group('rcv').replace(',', ''))
            
            # Create occurrence detail for this specific line
            occurrence_detail = f"Line {line_num}, Qty {quantity} Page {page_num}"
            
            if raw_description in aggregated_items:
                # Item exists - add this occurrence and update totals
                item = aggregated_items[raw_description]
                item['quantity'] += quantity
                item['rcv'] += rcv
                item['doc1_occurrences']['occurrences_detail'].append(occurrence_detail)
                item['doc1_occurrences']['total_quantity'] += quantity
                item['doc1_occurrences']['total_rcv'] += rcv
            else:
                # New item - create first occurrence
                aggregated_items[raw_description] = {
                    'description': raw_description,
                    'quantity': quantity,
                    'unit': match.group('unit'),
                    'unit_cost': unit_cost,
                    'rcv': rcv,
                    'doc1_occurrences': {
                        'occurrences_detail': [occurrence_detail],
                        'total_quantity': quantity,
                        'total_rcv': rcv
                    }
                }
        
        return list(aggregated_items.values())

    except Exception as e:
        logger.error(f"Error normalizing line items: {str(e)}")
        raise

def compare_pdfs(doc1_text, doc2_text):
    logger.info("Starting PDF comparison...")
    
    # Initialize default categories as a dictionary
    default_categories = dict.fromkeys([
        'ACCESSORIES - MOBILE HOME',
        'FLOOR COVERING',
        'OFFICE SUPPLIES',
        'PLUMBING',
        'PAINTING',
        'ROOFING',
        'SIDING',
        'SPECIALTY ITEMS',
        'STEEL COMPONENTS',
        'STAIRS',
        'TILE',
        'TOOLS',
        'WINDOWS',
        'APPLIANCES',
        'CABINETRY',
        'CLEANING',
        'CONCRETE & ASPHALT',
        'DOORS',
        'DRYWALL',
        'ELECTRICAL',
        'FENCING',
        'FINISH CARPENTRY',
        'FIREPLACES',
        'FRAMING & CARPENTRY',
        'HVAC',
        'INSULATION',
        'LANDSCAPING',
        'MASONRY'
    ], [])

    # Initialize categories with empty lists
    doc1_categories = default_categories.copy()
    doc2_categories = default_categories.copy()

    # Initialize comparison results
    comparison_results = {
        'matched_items': [],
        'unmatched_items_doc1': [],
        'unmatched_items_doc2': [],
        'error': None
    }

    try:
        logger.info("Processing document texts...")
        
        # Ensure we have text to process
        if not doc1_text or not doc2_text:
            raise ValueError("Missing document text")

        # Process documents
        doc1_items = normalize_line_items(doc1_text) or []
        doc2_items = normalize_line_items(doc2_text) or []

        logger.info(f"Processed items - Doc1: {len(doc1_items)}, Doc2: {len(doc2_items)}")

        # Ensure doc1_categories is properly initialized before categorizing
        if not isinstance(doc1_categories, dict):
            doc1_categories = default_categories.copy()
        
        if not isinstance(doc2_categories, dict):
            doc2_categories = default_categories.copy()

        # Categorize items for doc1
        for item in doc1_items:
            if not item or 'description' not in item:
                continue
                
            categorized = False
            for category, pattern in CATEGORY_PATTERNS.items():
                if category not in doc1_categories:
                    doc1_categories[category] = []
                    
                if re.search(pattern, str(item.get('description', '')), re.IGNORECASE):
                    doc1_categories[category].append(item)
                    categorized = True
                    break
                    
            if not categorized:
                if 'SPECIALTY ITEMS' not in doc1_categories:
                    doc1_categories['SPECIALTY ITEMS'] = []
                doc1_categories['SPECIALTY ITEMS'].append(item)

        # Categorize items for doc2
        for item in doc2_items:
            if not item or 'description' not in item:
                continue
                
            categorized = False
            for category, pattern in CATEGORY_PATTERNS.items():
                if category not in doc2_categories:
                    doc2_categories[category] = []
                    
                if re.search(pattern, str(item.get('description', '')), re.IGNORECASE):
                    doc2_categories[category].append(item)
                    categorized = True
                    break
                    
            if not categorized:
                if 'SPECIALTY ITEMS' not in doc2_categories:
                    doc2_categories['SPECIALTY ITEMS'] = []
                doc2_categories['SPECIALTY ITEMS'].append(item)

        # Update comparison results
        comparison_results.update({
            'unmatched_items_doc1': doc1_items,
            'unmatched_items_doc2': doc2_items
        })

        logger.info(f"Successfully categorized items")
        logger.info(f"Doc1 categories count: {len(doc1_categories)}")
        logger.info(f"Doc2 categories count: {len(doc2_categories)}")

    except Exception as e:
        logger.error(f"Error in compare_pdfs: {str(e)}\n{traceback.format_exc()}")
        comparison_results['error'] = str(e)
    
    finally:
        # Ensure we're returning valid dictionaries
        if not isinstance(doc1_categories, dict):
            doc1_categories = default_categories.copy()
        if not isinstance(doc2_categories, dict):
            doc2_categories = default_categories.copy()
            
        return {
            'doc1_categories': doc1_categories,
            'doc2_categories': doc2_categories,
            'comparison_results': comparison_results
        }

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    app.run(debug=True)