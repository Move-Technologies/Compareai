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

import tempfile
import os
from PIL import Image
from PyPDF2 import PdfReader
import fitz  # PyMuPDF
import logging.handlers
from PIL import Image, ImageEnhance, ImageFilter, ImageOps  # Add ImageOps import
import shutil
import time
import pymupdf
import csv
from io import BytesIO

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
        recap_comparison = compare_recap_categories(temp_file1.name, temp_file2.name)

        # Close the temporary files to ensure they're properly written
        temp_file1.close()
        temp_file2.close()

        # Validate PDFs before processing
        for pdf_path in [temp_file1.name, temp_file2.name]:
            is_valid, error_message = is_valid_pdf(pdf_path)
            if not is_valid:
                raise ValueError(f"Invalid PDF: {error_message}")

        # Extract text from both files (do this only once)
    

    

      

      

        # Search for the pattern in the text
       
        response = {
            # 'comparison_results': comparison_results,
            # 'categorized_items': categorized_items,
            # 'overall_summary': overall_summary,
            # 'ai_insights': ai_insights,
            # 'file1_count': len(doc1_items),
            # 'file2_count': len(doc2_items),
            'recap_comparison': recap_comparison,
            # 'metadata': {
            #     'file1_name': file1.filename,
            #     'file2_name': file2.filename,
            #     'comparison_date': datetime.now().isoformat()
            # }
        }

        # After categorization
        


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
            'recap_comparison':{},
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




def compare_recap_categories(file1_path, file2_path):
    """Compare recap categories between two PDF files"""
    o_and_p_items = (
        'ACOUSTICAL TREATMENTS', 'APPLIANCES', 'CABINETRY', 'CLEANING', 
        'GENERAL DEMOLITION', 'DOORS', 'DRYWALL', 'ELECTRICAL', 
        'FLOOR COVERING - CARPET', 'FLOOR COVERING - STONE', 
        'FLOOR COVERING - CERAMIC TILE', 'FINISH CARPENTRY / TRIMWORK', 
        'FINISH HARDWARE', 'FIREPLACES', 'FRAMING & ROUGH CARPENTRY', 
        'HAZARDOUS MATERIAL REMEDIATION', 'HEAT,  VENT & AIR CONDITIONING', 
        'INSULATION', 'LABOR ONLY', 'LIGHT FIXTURES', 
        'MARBLE - CULTURED OR NATURAL', 'MOISTURE PROTECTION', 
        'MIRRORS & SHOWER DOORS', 'PLUMBING', 'PAINTING', 'ROOFING', 
        'SCAFFOLDING', 'SIDING', 'TILE', 'TEMPORARY REPAIRS', 
        'USER DEFINED ITEMS', 'WINDOWS - ALUMINUM', 
        'WINDOWS - SLIDING PATIO DOORS', 'WINDOW TREATMENT', 
        'EXTERIOR STRUCTURES'
    )

    def extract_recap_data(pdf_path):
        pdf_op = pymupdf.open(pdf_path)
        col_data = {}
        
        try:
            # Find the recap page
            tar_table_ind = None
            for pg in pdf_op:
                if pg.search_for('Recap by Category with Depreciation'):
                    tar_table_ind = pg.number
                    break
                if pg.search_for('Recap by Category'):
                    tar_table_ind = pg.number
                    break
            
            if tar_table_ind is not None:
                # Extract data from recap pages
                tab_pg_1 = pdf_op[tar_table_ind]
                tab_pg_2 = pdf_op[tar_table_ind + 1] if tar_table_ind + 1 < pdf_op.page_count else None

                pages_to_check = [tab_pg_1]
                if tab_pg_2:
                    pages_to_check.append(tab_pg_2)

                for o_and_p_item in o_and_p_items:
                    for page in pages_to_check:
                        for text_block in page.get_text('blocks'):
                            if text_block[4].startswith(o_and_p_item):
                                vals = text_block[4].split('\n')
                                if len(vals) >= 6:
                                    result_dict = {}
                                    i = 0
                                    while i < len(vals):
                                       item = vals[i]
                                       if item in o_and_p_items:
                                       # Get the value next to the item and convert it to a float
                                          value = float(vals[i + 1].replace(',', ''))
                                          result_dict[item] = value
                                          i += 2
                                       i += 1
                                    
                                    return result_dict 
                                col_data[vals[0]] = float(vals[1].replace(',', ''))

        finally:
            pdf_op.close()
        
        return col_data

    # Extract data from both PDFs
    
    your_estimate_col_data = extract_recap_data(file1_path)
    carrier_estimate_col_data = extract_recap_data(file2_path)

    # Prepare comparison results
    comparison_results = []
    total_difference = 0

    for o_and_p_item in o_and_p_items:
        your_val = your_estimate_col_data.get(o_and_p_item, 'N/A')
        carrier_val = carrier_estimate_col_data.get(o_and_p_item, 'N/A')

        if 'N/A' in [your_val, carrier_val]:
            difference = 'N/A'
        else:
            difference = carrier_val - your_val
            if isinstance(difference, (int, float)):
                total_difference += difference

        comparison_results.append({
            'category': o_and_p_item,
            'your_estimate': your_val,
            'carrier_estimate': carrier_val,
            'difference': difference
        })

    return {
        'comparison_results': comparison_results,
        'total_difference': total_difference,
        'summary': {
            'categories_compared': len(o_and_p_items),
            'categories_with_differences': sum(1 for r in comparison_results if r['difference'] != 0 and r['difference'] != 'N/A')
        }
    }





if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    app.run(debug=True)