#!/usr/bin/env python3
"""
Unit tests for PDF service
Tests individual components and functions in isolation
Requirements: 1.3, 1.4, 6.1, 6.2
"""

import pytest
import base64
import time
from unittest.mock import patch, MagicMock
from app import (
    create_app, 
    validate_libreoffice, 
    validate_request_data,
    PDFServiceError,
    ErrorCode,
    ConversionMetrics,
    MAX_FILE_SIZE_BYTES
)


class TestHealthCheckEndpoint:
    """Unit tests for health check endpoint (Requirement 6.4)"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_health_check_returns_200(self, client):
        """Test that health check returns 200 status code"""
        response = client.get('/health')
        assert response.status_code == 200
    
    def test_health_check_returns_json(self, client):
        """Test that health check returns JSON response"""
        response = client.get('/health')
        assert response.content_type == 'application/json'
    
    def test_health_check_has_required_fields(self, client):
        """Test that health check response contains all required fields"""
        response = client.get('/health')
        data = response.get_json()
        
        assert 'status' in data
        assert 'service' in data
        assert 'version' in data
        assert 'libreoffice_available' in data
        assert 'timestamp' in data
    
    def test_health_check_status_is_healthy(self, client):
        """Test that health check reports healthy status"""
        response = client.get('/health')
        data = response.get_json()
        
        assert data['status'] == 'healthy'
    
    def test_health_check_service_name(self, client):
        """Test that health check reports correct service name"""
        response = client.get('/health')
        data = response.get_json()
        
        assert data['service'] == 'pdf-converter'
    
    def test_health_check_version(self, client):
        """Test that health check reports version"""
        response = client.get('/health')
        data = response.get_json()
        
        assert data['version'] == '1.0.0'
    
    def test_health_check_libreoffice_status(self, client):
        """Test that health check reports LibreOffice availability"""
        response = client.get('/health')
        data = response.get_json()
        
        assert isinstance(data['libreoffice_available'], bool)
    
    def test_health_check_timestamp_is_recent(self, client):
        """Test that health check timestamp is current"""
        before = time.time()
        response = client.get('/health')
        after = time.time()
        
        data = response.get_json()
        timestamp = data['timestamp']
        
        assert before <= timestamp <= after


class TestLibreOfficeValidation:
    """Unit tests for LibreOffice dependency validation (Requirement 2.1, 5.4)"""
    
    @patch('subprocess.run')
    def test_validate_libreoffice_success(self, mock_run):
        """Test successful LibreOffice validation"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='LibreOffice 7.0.0.0'
        )
        
        result = validate_libreoffice()
        assert result is True
    
    @patch('subprocess.run')
    def test_validate_libreoffice_not_found(self, mock_run):
        """Test LibreOffice validation when not installed"""
        mock_run.side_effect = FileNotFoundError()
        
        result = validate_libreoffice()
        assert result is False
    
    @patch('subprocess.run')
    def test_validate_libreoffice_timeout(self, mock_run):
        """Test LibreOffice validation timeout handling"""
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired('libreoffice', 5)
        
        result = validate_libreoffice()
        assert result is False
    
    @patch('subprocess.run')
    def test_validate_libreoffice_command_fails(self, mock_run):
        """Test LibreOffice validation when command fails"""
        mock_run.return_value = MagicMock(returncode=1)
        
        result = validate_libreoffice()
        assert result is False


class TestRequestValidation:
    """Unit tests for request data validation (Requirement 6.2)"""
    
    def test_validate_empty_request(self):
        """Test validation of empty request"""
        error = validate_request_data({})
        
        assert error is not None
        assert error.error_code == ErrorCode.MISSING_DOCX_DATA.value
    
    def test_validate_none_request(self):
        """Test validation of None request"""
        error = validate_request_data(None)
        
        assert error is not None
        assert error.error_code == ErrorCode.MISSING_DOCX_DATA.value
    
    def test_validate_missing_docx_data_field(self):
        """Test validation when docx_data field is missing"""
        error = validate_request_data({'other_field': 'value'})
        
        assert error is not None
        assert error.error_code == ErrorCode.MISSING_DOCX_DATA.value
        assert 'docx_data' in error.error_message
    
    def test_validate_empty_docx_data(self):
        """Test validation of empty docx_data"""
        error = validate_request_data({'docx_data': ''})
        
        assert error is not None
        assert error.error_code == ErrorCode.MISSING_DOCX_DATA.value
    
    def test_validate_invalid_base64(self):
        """Test validation of invalid base64 data"""
        error = validate_request_data({'docx_data': 'not-valid-base64!!!'})
        
        assert error is not None
        assert error.error_code == ErrorCode.INVALID_BASE64.value
    
    def test_validate_file_too_large(self):
        """Test validation of file size limit"""
        # Create data larger than MAX_FILE_SIZE_BYTES
        large_data = b'x' * (MAX_FILE_SIZE_BYTES + 1)
        large_base64 = base64.b64encode(large_data).decode()
        
        error = validate_request_data({'docx_data': large_base64})
        
        assert error is not None
        assert error.error_code == ErrorCode.FILE_TOO_LARGE.value
    
    def test_validate_invalid_docx_format(self):
        """Test validation of invalid DOCX format (missing PK header)"""
        invalid_docx = base64.b64encode(b'This is not a DOCX file').decode()
        
        error = validate_request_data({'docx_data': invalid_docx})
        
        assert error is not None
        assert error.error_code == ErrorCode.INVALID_DOCX_FORMAT.value
    
    def test_validate_valid_docx_data(self):
        """Test validation of valid DOCX data"""
        # DOCX files start with PK (ZIP format)
        valid_docx = base64.b64encode(b'PK\x03\x04' + b'\x00' * 100).decode()
        
        error = validate_request_data({'docx_data': valid_docx})
        
        assert error is None


class TestErrorResponseStructure:
    """Unit tests for structured error responses (Requirement 6.1, 6.3)"""
    
    def test_pdf_service_error_structure(self):
        """Test PDFServiceError data structure"""
        error = PDFServiceError(
            error_code=ErrorCode.CONVERSION_FAILED.value,
            error_message='Test error',
            timestamp=time.time()
        )
        
        error_dict = error.to_dict()
        
        assert error_dict['success'] is False
        assert error_dict['error_code'] == ErrorCode.CONVERSION_FAILED.value
        assert error_dict['error_message'] == 'Test error'
        assert 'timestamp' in error_dict
    
    def test_error_with_details(self):
        """Test error response with additional details"""
        error = PDFServiceError(
            error_code=ErrorCode.CONVERSION_FAILED.value,
            error_message='Test error',
            details={'extra': 'info'},
            timestamp=time.time()
        )
        
        error_dict = error.to_dict()
        
        assert 'details' in error_dict
        assert error_dict['details']['extra'] == 'info'
    
    def test_error_with_processing_time(self):
        """Test error response with processing time"""
        error = PDFServiceError(
            error_code=ErrorCode.CONVERSION_FAILED.value,
            error_message='Test error',
            processing_time_ms=1500,
            timestamp=time.time()
        )
        
        error_dict = error.to_dict()
        
        assert 'processing_time_ms' in error_dict
        assert error_dict['processing_time_ms'] == 1500


class TestConversionMetrics:
    """Unit tests for conversion metrics logging (Requirement 6.2, 6.4)"""
    
    def test_metrics_structure(self):
        """Test ConversionMetrics data structure"""
        metrics = ConversionMetrics(
            request_id='test_123',
            docx_size_bytes=1024,
            pdf_size_bytes=2048,
            processing_time_ms=1500,
            success=True,
            error_code=None,
            timestamp=time.time()
        )
        
        assert metrics.request_id == 'test_123'
        assert metrics.docx_size_bytes == 1024
        assert metrics.pdf_size_bytes == 2048
        assert metrics.processing_time_ms == 1500
        assert metrics.success is True
        assert metrics.error_code is None
    
    def test_metrics_for_failed_conversion(self):
        """Test metrics structure for failed conversions"""
        metrics = ConversionMetrics(
            request_id='test_456',
            docx_size_bytes=1024,
            pdf_size_bytes=None,
            processing_time_ms=500,
            success=False,
            error_code=ErrorCode.CONVERSION_FAILED.value,
            timestamp=time.time()
        )
        
        assert metrics.success is False
        assert metrics.error_code == ErrorCode.CONVERSION_FAILED.value
        assert metrics.pdf_size_bytes is None


class TestErrorCodes:
    """Unit tests for error code enumeration (Requirement 6.3)"""
    
    def test_all_error_codes_defined(self):
        """Test that all required error codes are defined"""
        required_codes = [
            'MISSING_DOCX_DATA',
            'INVALID_BASE64',
            'FILE_TOO_LARGE',
            'INVALID_DOCX_FORMAT',
            'LIBREOFFICE_UNAVAILABLE',
            'CONVERSION_FAILED',
            'CONVERSION_TIMEOUT',
            'INTERNAL_ERROR',
            'SERVICE_UNAVAILABLE'
        ]
        
        for code in required_codes:
            assert hasattr(ErrorCode, code)
    
    def test_error_code_values(self):
        """Test that error codes have correct string values"""
        assert ErrorCode.MISSING_DOCX_DATA.value == 'MISSING_DOCX_DATA'
        assert ErrorCode.INVALID_BASE64.value == 'INVALID_BASE64'
        assert ErrorCode.CONVERSION_FAILED.value == 'CONVERSION_FAILED'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
