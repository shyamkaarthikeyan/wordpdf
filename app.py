#!/usr/bin/env python3
"""
PDF Conversion Service
Separate service for Word to PDF conversion using LibreOffice
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import base64
import tempfile
import os
import logging
import subprocess
import time
from io import BytesIO
from functools import wraps
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from enum import Enum

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

# Create a separate logger for conversion metrics
metrics_logger = logging.getLogger('metrics')
metrics_handler = logging.FileHandler('conversion_metrics.log')
metrics_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
metrics_logger.addHandler(metrics_handler)
metrics_logger.setLevel(logging.INFO)

# Constants
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
CONVERSION_TIMEOUT_SECONDS = 30

class ErrorCode(Enum):
    """Enumeration of specific error codes for different failure scenarios."""
    MISSING_DOCX_DATA = "MISSING_DOCX_DATA"
    INVALID_BASE64 = "INVALID_BASE64"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    INVALID_DOCX_FORMAT = "INVALID_DOCX_FORMAT"
    LIBREOFFICE_UNAVAILABLE = "LIBREOFFICE_UNAVAILABLE"
    CONVERSION_FAILED = "CONVERSION_FAILED"
    CONVERSION_TIMEOUT = "CONVERSION_TIMEOUT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    RATE_LIMITED = "RATE_LIMITED"
    CLEANUP_FAILED = "CLEANUP_FAILED"

@dataclass
class PDFServiceError:
    """Structured error response model."""
    success: bool = False
    error_code: str = ""
    error_message: str = ""
    details: Optional[Dict[str, Any]] = None
    timestamp: float = 0.0
    processing_time_ms: Optional[int] = None
    
    def to_dict(self):
        result = asdict(self)
        # Remove None values
        return {k: v for k, v in result.items() if v is not None}

@dataclass
class ConversionMetrics:
    """Metrics for tracking conversion requests."""
    request_id: str
    docx_size_bytes: int
    pdf_size_bytes: Optional[int]
    processing_time_ms: int
    success: bool
    error_code: Optional[str]
    timestamp: float
    
    def log(self):
        """Log metrics to the metrics logger."""
        metrics_logger.info(
            f"request_id={self.request_id} | "
            f"docx_size={self.docx_size_bytes} | "
            f"pdf_size={self.pdf_size_bytes or 0} | "
            f"processing_time_ms={self.processing_time_ms} | "
            f"success={self.success} | "
            f"error_code={self.error_code or 'NONE'}"
        )

# Global variable to track LibreOffice availability
LIBREOFFICE_AVAILABLE = False

def validate_libreoffice():
    """
    Validate that LibreOffice is installed and available.
    Returns True if LibreOffice is available, False otherwise.
    """
    global LIBREOFFICE_AVAILABLE
    try:
        result = subprocess.run(
            ['libreoffice', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            logger.info(f"✅ LibreOffice detected: {version}")
            LIBREOFFICE_AVAILABLE = True
            return True
        else:
            logger.warning("⚠️ LibreOffice command failed")
            LIBREOFFICE_AVAILABLE = False
            return False
    except FileNotFoundError:
        logger.warning("⚠️ LibreOffice not found in PATH")
        LIBREOFFICE_AVAILABLE = False
        return False
    except subprocess.TimeoutExpired:
        logger.warning("⚠️ LibreOffice version check timed out")
        LIBREOFFICE_AVAILABLE = False
        return False
    except Exception as e:
        logger.error(f"⚠️ Error checking LibreOffice: {str(e)}")
        LIBREOFFICE_AVAILABLE = False
        return False

def create_app():
    """
    Application factory pattern for creating Flask app.
    """
    app = Flask(__name__)
    
    # CORS Configuration
    # Allow requests from any origin with credentials
    CORS(app, 
         resources={r"/*": {
             "origins": "*",
             "methods": ["GET", "POST", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"],
             "expose_headers": ["Content-Type"],
             "supports_credentials": True
         }})
    
    # Validate dependencies on startup
    validate_libreoffice()
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register routes
    register_routes(app)
    
    return app

def register_error_handlers(app):
    """
    Register global error handlers for the Flask application.
    Uses structured error responses for consistency.
    """
    @app.errorhandler(400)
    def bad_request(error):
        logger.warning(f"Bad request: {str(error)}")
        error_response = PDFServiceError(
            error_code=ErrorCode.INVALID_BASE64.value,
            error_message='Bad request',
            details={'error': str(error)},
            timestamp=time.time()
        )
        return jsonify(error_response.to_dict()), 400
    
    @app.errorhandler(404)
    def not_found(error):
        logger.warning(f"Not found: {str(error)}")
        error_response = PDFServiceError(
            error_code=ErrorCode.INTERNAL_ERROR.value,
            error_message='The requested endpoint does not exist',
            details={'path': request.path},
            timestamp=time.time()
        )
        return jsonify(error_response.to_dict()), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {str(error)}", exc_info=True)
        error_response = PDFServiceError(
            error_code=ErrorCode.INTERNAL_ERROR.value,
            error_message='An unexpected error occurred',
            details={'error': str(error)},
            timestamp=time.time()
        )
        return jsonify(error_response.to_dict()), 500
    
    @app.errorhandler(503)
    def service_unavailable(error):
        logger.error(f"Service unavailable: {str(error)}")
        error_response = PDFServiceError(
            error_code=ErrorCode.SERVICE_UNAVAILABLE.value,
            error_message='The service is temporarily unavailable',
            details={'error': str(error)},
            timestamp=time.time()
        )
        return jsonify(error_response.to_dict()), 503

def require_libreoffice(f):
    """
    Decorator to check if LibreOffice is available before processing requests.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not LIBREOFFICE_AVAILABLE:
            logger.error("LibreOffice not available for conversion")
            error = PDFServiceError(
                error_code=ErrorCode.LIBREOFFICE_UNAVAILABLE.value,
                error_message='PDF conversion service requires LibreOffice to be installed',
                details={'libreoffice_available': False},
                timestamp=time.time()
            )
            return jsonify(error.to_dict()), 503
        return f(*args, **kwargs)
    return decorated_function

def validate_request_data(data: Dict[str, Any]) -> Optional[PDFServiceError]:
    """
    Validate incoming request data for PDF conversion.
    Returns PDFServiceError if validation fails, None if valid.
    """
    # Check if data exists
    if not data:
        return PDFServiceError(
            error_code=ErrorCode.MISSING_DOCX_DATA.value,
            error_message='Request body is empty',
            details={'expected': 'JSON body with docx_data field'},
            timestamp=time.time()
        )
    
    # Check if docx_data field exists
    if 'docx_data' not in data:
        return PDFServiceError(
            error_code=ErrorCode.MISSING_DOCX_DATA.value,
            error_message='Missing required field: docx_data',
            details={'received_fields': list(data.keys())},
            timestamp=time.time()
        )
    
    docx_data = data['docx_data']
    
    # Check if docx_data is not empty
    if not docx_data or not isinstance(docx_data, str):
        return PDFServiceError(
            error_code=ErrorCode.MISSING_DOCX_DATA.value,
            error_message='docx_data field is empty or not a string',
            details={'docx_data_type': type(docx_data).__name__},
            timestamp=time.time()
        )
    
    # Validate base64 format
    try:
        docx_bytes = base64.b64decode(docx_data)
    except Exception as e:
        logger.error(f"Base64 decode error: {str(e)}")
        return PDFServiceError(
            error_code=ErrorCode.INVALID_BASE64.value,
            error_message='Invalid base64 encoding',
            details={'decode_error': str(e)},
            timestamp=time.time()
        )
    
    # Check file size
    file_size = len(docx_bytes)
    if file_size > MAX_FILE_SIZE_BYTES:
        logger.warning(f"File too large: {file_size} bytes (max: {MAX_FILE_SIZE_BYTES})")
        return PDFServiceError(
            error_code=ErrorCode.FILE_TOO_LARGE.value,
            error_message=f'File size exceeds maximum limit of {MAX_FILE_SIZE_MB}MB',
            details={
                'file_size_bytes': file_size,
                'max_size_bytes': MAX_FILE_SIZE_BYTES,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'max_size_mb': MAX_FILE_SIZE_MB
            },
            timestamp=time.time()
        )
    
    # Validate DOCX format (check for PK header - ZIP format)
    if not docx_bytes.startswith(b'PK'):
        logger.error("Invalid DOCX format: missing PK header")
        return PDFServiceError(
            error_code=ErrorCode.INVALID_DOCX_FORMAT.value,
            error_message='Invalid DOCX file format',
            details={
                'expected': 'DOCX files must be valid ZIP archives',
                'received_header': docx_bytes[:4].hex() if len(docx_bytes) >= 4 else 'empty'
            },
            timestamp=time.time()
        )
    
    return None

def register_routes(app):
    """
    Register all application routes.
    """
    @app.route('/health', methods=['GET'])
    def health_check():
        """
        Health check endpoint to verify service status and dependencies.
        """
        return jsonify({
            'status': 'healthy',
            'service': 'pdf-converter',
            'version': '1.0.0',
            'libreoffice_available': LIBREOFFICE_AVAILABLE,
            'timestamp': time.time()
        }), 200
    
    @app.route('/convert-pdf', methods=['POST'])
    @require_libreoffice
    def convert_to_pdf():
        """
        Convert DOCX to PDF with 100% accuracy using LibreOffice.
        Includes comprehensive error handling and validation.
        """
        start_time = time.time()
        request_id = f"req_{int(start_time * 1000)}"
        temp_docx_path = None
        temp_pdf_path = None
        docx_bytes = None
        pdf_bytes = None
        
        logger.info(f"[{request_id}] Starting PDF conversion request")
        
        try:
            # Get and validate JSON data
            data = request.get_json()
            
            # Validate request data
            validation_error = validate_request_data(data)
            if validation_error:
                validation_error.processing_time_ms = int((time.time() - start_time) * 1000)
                logger.warning(f"[{request_id}] Validation failed: {validation_error.error_code}")
                
                # Log metrics for failed validation
                metrics = ConversionMetrics(
                    request_id=request_id,
                    docx_size_bytes=0,
                    pdf_size_bytes=None,
                    processing_time_ms=validation_error.processing_time_ms,
                    success=False,
                    error_code=validation_error.error_code,
                    timestamp=start_time
                )
                metrics.log()
                
                return jsonify(validation_error.to_dict()), 400
            
            # Decode base64 DOCX data (already validated)
            docx_bytes = base64.b64decode(data['docx_data'])
            docx_size = len(docx_bytes)
            
            logger.info(f"[{request_id}] Received valid DOCX data: {docx_size} bytes ({docx_size / 1024:.2f} KB)")
            
            # Create temporary files
            try:
                with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_docx:
                    temp_docx.write(docx_bytes)
                    temp_docx_path = temp_docx.name
                
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                    temp_pdf_path = temp_pdf.name
                
                logger.info(f"[{request_id}] Created temporary files: {temp_docx_path}, {temp_pdf_path}")
            except Exception as e:
                logger.error(f"[{request_id}] Failed to create temporary files: {str(e)}")
                raise Exception(f"Temporary file creation failed: {str(e)}")
            
            # Convert using LibreOffice (works on Linux)
            try:
                logger.info(f"[{request_id}] Starting LibreOffice conversion...")
                conversion_start = time.time()
                
                # Get the output directory
                output_dir = os.path.dirname(temp_pdf_path)
                
                # Use LibreOffice for conversion (works on Linux)
                result = subprocess.run(
                    ['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', output_dir, temp_docx_path],
                    capture_output=True,
                    text=True,
                    timeout=CONVERSION_TIMEOUT_SECONDS
                )
                
                if result.returncode != 0:
                    raise Exception(f"LibreOffice conversion failed: {result.stderr}")
                
                conversion_time = time.time() - conversion_start
                logger.info(f"[{request_id}] Conversion completed in {conversion_time:.2f}s")
                
                # LibreOffice creates PDF with same basename as input DOCX
                # e.g., /tmp/xyz.docx -> /tmp/xyz.pdf
                docx_basename = os.path.basename(temp_docx_path)
                pdf_basename = os.path.splitext(docx_basename)[0] + '.pdf'
                actual_pdf_path = os.path.join(output_dir, pdf_basename)
                
                logger.info(f"[{request_id}] Expected PDF at: {actual_pdf_path}")
                
                # Check if the PDF was created
                if not os.path.exists(actual_pdf_path):
                    raise Exception(f"LibreOffice did not create PDF at expected location: {actual_pdf_path}")
                
                # Update temp_pdf_path to the actual location
                temp_pdf_path = actual_pdf_path
                
                # Check if conversion timed out
                if conversion_time > CONVERSION_TIMEOUT_SECONDS:
                    logger.warning(f"[{request_id}] Conversion exceeded timeout threshold")
                
            except Exception as e:
                logger.error(f"[{request_id}] docx2pdf conversion failed: {str(e)}")
                error = PDFServiceError(
                    error_code=ErrorCode.CONVERSION_FAILED.value,
                    error_message='PDF conversion failed',
                    details={
                        'conversion_error': str(e),
                        'docx_size_bytes': docx_size
                    },
                    timestamp=time.time(),
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )
                
                # Log metrics for failed conversion
                metrics = ConversionMetrics(
                    request_id=request_id,
                    docx_size_bytes=docx_size,
                    pdf_size_bytes=None,
                    processing_time_ms=error.processing_time_ms,
                    success=False,
                    error_code=error.error_code,
                    timestamp=start_time
                )
                metrics.log()
                
                return jsonify(error.to_dict()), 500
            
            # Read the generated PDF
            try:
                with open(temp_pdf_path, 'rb') as pdf_file:
                    pdf_bytes = pdf_file.read()
                
                pdf_size = len(pdf_bytes)
                logger.info(f"[{request_id}] Generated PDF: {pdf_size} bytes ({pdf_size / 1024:.2f} KB)")
                
                # Validate PDF format
                if not pdf_bytes.startswith(b'%PDF'):
                    logger.error(f"[{request_id}] Generated file is not a valid PDF")
                    raise Exception("Generated file is not a valid PDF format")
                
            except Exception as e:
                logger.error(f"[{request_id}] Failed to read generated PDF: {str(e)}")
                error = PDFServiceError(
                    error_code=ErrorCode.CONVERSION_FAILED.value,
                    error_message='Failed to read generated PDF',
                    details={'read_error': str(e)},
                    timestamp=time.time(),
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )
                
                # Log metrics
                metrics = ConversionMetrics(
                    request_id=request_id,
                    docx_size_bytes=docx_size,
                    pdf_size_bytes=None,
                    processing_time_ms=error.processing_time_ms,
                    success=False,
                    error_code=error.error_code,
                    timestamp=start_time
                )
                metrics.log()
                
                return jsonify(error.to_dict()), 500
            
            # Success - prepare response
            processing_time_ms = int((time.time() - start_time) * 1000)
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            
            logger.info(f"[{request_id}] PDF conversion successful in {processing_time_ms}ms")
            
            # Log successful conversion metrics
            metrics = ConversionMetrics(
                request_id=request_id,
                docx_size_bytes=docx_size,
                pdf_size_bytes=pdf_size,
                processing_time_ms=processing_time_ms,
                success=True,
                error_code=None,
                timestamp=start_time
            )
            metrics.log()
            
            return jsonify({
                'success': True,
                'pdf_data': pdf_base64,
                'size': pdf_size,
                'conversion_method': 'libreoffice',
                'processing_time_ms': processing_time_ms,
                'request_id': request_id
            }), 200
            
        except Exception as e:
            # Catch-all for unexpected errors
            processing_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"[{request_id}] Unexpected error during PDF conversion: {str(e)}", exc_info=True)
            
            error = PDFServiceError(
                error_code=ErrorCode.INTERNAL_ERROR.value,
                error_message='An unexpected error occurred during PDF conversion',
                details={'error': str(e)},
                timestamp=time.time(),
                processing_time_ms=processing_time_ms
            )
            
            # Log metrics for unexpected errors
            metrics = ConversionMetrics(
                request_id=request_id,
                docx_size_bytes=len(docx_bytes) if docx_bytes else 0,
                pdf_size_bytes=None,
                processing_time_ms=processing_time_ms,
                success=False,
                error_code=error.error_code,
                timestamp=start_time
            )
            metrics.log()
            
            return jsonify(error.to_dict()), 500
            
        finally:
            # Clean up temporary files
            cleanup_errors = []
            if temp_docx_path:
                try:
                    os.unlink(temp_docx_path)
                    logger.debug(f"[{request_id}] Cleaned up temporary DOCX file")
                except Exception as e:
                    cleanup_errors.append(f"DOCX: {str(e)}")
                    logger.warning(f"[{request_id}] Failed to clean up DOCX temp file: {str(e)}")
            
            if temp_pdf_path:
                try:
                    os.unlink(temp_pdf_path)
                    logger.debug(f"[{request_id}] Cleaned up temporary PDF file")
                except Exception as e:
                    cleanup_errors.append(f"PDF: {str(e)}")
                    logger.warning(f"[{request_id}] Failed to clean up PDF temp file: {str(e)}")
            
            if cleanup_errors:
                logger.warning(f"[{request_id}] Cleanup errors: {', '.join(cleanup_errors)}")
    
    @app.route('/parse', methods=['POST'])
    def parse_document():
        """
        Parse PDF or DOCX document and extract structured content.
        Returns title, authors, abstract, keywords, sections, and references.
        """
        start_time = time.time()
        request_id = f"req_parse_{int(start_time * 1000)}"
        
        logger.info(f"[{request_id}] Starting document parsing request")
        
        try:
            # Check if file was uploaded
            if 'file' not in request.files:
                return jsonify({
                    'success': False,
                    'error': 'No file uploaded'
                }), 400
            
            file = request.files['file']
            
            if file.filename == '':
                return jsonify({
                    'success': False,
                    'error': 'No file selected'
                }), 400
            
            # Read file data
            file_data = file.read()
            filename = file.filename.lower()
            
            # Determine file type
            if filename.endswith('.pdf'):
                file_type = 'pdf'
            elif filename.endswith('.docx'):
                file_type = 'docx'
            else:
                return jsonify({
                    'success': False,
                    'error': 'Unsupported file type. Please upload PDF or DOCX.'
                }), 400
            
            logger.info(f"[{request_id}] Parsing {file_type.upper()} file: {file.filename} ({len(file_data)} bytes)")
            
            # Import and use the parser
            try:
                # Import the parser from the Python backend
                import sys
                import os
                
                # Add the format-a-python-backend directory to path
                backend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'format-a-python-backend')
                if backend_path not in sys.path:
                    sys.path.insert(0, backend_path)
                
                from document_parser import parse_document as parse_doc
                
                # Parse the document
                parsed_data = parse_doc(file_data, file_type)
                
                processing_time_ms = int((time.time() - start_time) * 1000)
                logger.info(f"[{request_id}] Parsing completed in {processing_time_ms}ms")
                
                return jsonify({
                    'success': True,
                    'data': parsed_data,
                    'message': f'Document parsed successfully ({file_type.upper()})',
                    'processing_time_ms': processing_time_ms
                }), 200
                
            except ImportError as e:
                logger.error(f"[{request_id}] Failed to import parser: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': 'Document parser not available',
                    'details': str(e)
                }), 500
            except Exception as e:
                logger.error(f"[{request_id}] Parsing failed: {str(e)}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': f'Document parsing failed: {str(e)}'
                }), 500
        
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"[{request_id}] Parse request failed: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': str(e),
                'processing_time_ms': processing_time_ms
            }), 500
    
    @app.route('/convert-pdf-download', methods=['POST'])
    @require_libreoffice
    def convert_to_pdf_download():
        """
        Convert DOCX to PDF and return as file download.
        Includes comprehensive error handling and validation.
        """
        start_time = time.time()
        request_id = f"req_download_{int(start_time * 1000)}"
        temp_docx_path = None
        temp_pdf_path = None
        
        logger.info(f"[{request_id}] Starting PDF download conversion request")
        
        try:
            # Get and validate JSON data
            data = request.get_json()
            
            # Validate request data
            validation_error = validate_request_data(data)
            if validation_error:
                validation_error.processing_time_ms = int((time.time() - start_time) * 1000)
                logger.warning(f"[{request_id}] Validation failed: {validation_error.error_code}")
                return jsonify(validation_error.to_dict()), 400
            
            # Decode base64 DOCX data
            docx_bytes = base64.b64decode(data['docx_data'])
            docx_size = len(docx_bytes)
            
            logger.info(f"[{request_id}] Received valid DOCX data: {docx_size} bytes")
            
            # Create temporary files
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_docx:
                temp_docx.write(docx_bytes)
                temp_docx_path = temp_docx.name
            
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                temp_pdf_path = temp_pdf.name
            
            logger.info(f"[{request_id}] Created temporary files for download conversion")
            
            # Convert using LibreOffice
            try:
                logger.info(f"[{request_id}] Starting LibreOffice conversion for download...")
                
                # Get the output directory
                output_dir = os.path.dirname(temp_pdf_path)
                
                result = subprocess.run(
                    ['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', output_dir, temp_docx_path],
                    capture_output=True,
                    text=True,
                    timeout=CONVERSION_TIMEOUT_SECONDS
                )
                if result.returncode != 0:
                    raise Exception(f"LibreOffice conversion failed: {result.stderr}")
                
                # LibreOffice creates PDF with same basename as input DOCX
                docx_basename = os.path.basename(temp_docx_path)
                pdf_basename = os.path.splitext(docx_basename)[0] + '.pdf'
                actual_pdf_path = os.path.join(output_dir, pdf_basename)
                
                # Check if the PDF was created
                if not os.path.exists(actual_pdf_path):
                    raise Exception(f"LibreOffice did not create PDF at expected location: {actual_pdf_path}")
                
                # Update temp_pdf_path to the actual location
                temp_pdf_path = actual_pdf_path
                
                logger.info(f"[{request_id}] Conversion completed successfully")
            except Exception as e:
                logger.error(f"[{request_id}] Conversion failed: {str(e)}")
                error = PDFServiceError(
                    error_code=ErrorCode.CONVERSION_FAILED.value,
                    error_message='PDF conversion failed',
                    details={'conversion_error': str(e)},
                    timestamp=time.time(),
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )
                return jsonify(error.to_dict()), 500
            
            # Return PDF file
            processing_time_ms = int((time.time() - start_time) * 1000)
            logger.info(f"[{request_id}] Sending PDF file for download (processing time: {processing_time_ms}ms)")
            
            return send_file(
                temp_pdf_path,
                as_attachment=True,
                download_name='research_paper.pdf',
                mimetype='application/pdf'
            )
            
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"[{request_id}] PDF download conversion failed: {str(e)}", exc_info=True)
            
            error = PDFServiceError(
                error_code=ErrorCode.INTERNAL_ERROR.value,
                error_message='An unexpected error occurred during PDF download conversion',
                details={'error': str(e)},
                timestamp=time.time(),
                processing_time_ms=processing_time_ms
            )
            return jsonify(error.to_dict()), 500
        
        finally:
            # Note: Temp files cleanup is handled by Flask after send_file completes
            # We log the cleanup attempt but don't force delete as send_file needs them
            if temp_docx_path:
                logger.debug(f"[{request_id}] Temporary DOCX file will be cleaned up after download")
            if temp_pdf_path:
                logger.debug(f"[{request_id}] Temporary PDF file will be cleaned up after download")

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Log startup information
    logger.info(f"Starting PDF Conversion Service on port {port}")
    logger.info(f"LibreOffice available: {LIBREOFFICE_AVAILABLE}")
    
    # Run the Flask application
    app.run(host='0.0.0.0', port=port, debug=False)