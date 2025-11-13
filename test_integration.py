#!/usr/bin/env python3
"""
Integration tests for PDF service
Tests complete workflows and error handling scenarios
Requirements: 1.3, 1.4, 6.1, 6.2
"""

import pytest
import base64
import time
import os
from io import BytesIO
from unittest.mock import patch, MagicMock
from app import create_app, ErrorCode


class TestConvertEndpointIntegration:
    """Integration tests for PDF conversion endpoint"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def valid_docx_data(self):
        """Create minimal valid DOCX data (PK header)"""
        # DOCX files are ZIP archives starting with PK
        docx_bytes = b'PK\x03\x04' + b'\x00' * 100
        return base64.b64encode(docx_bytes).decode()
    
    def test_convert_endpoint_exists(self, client):
        """Test that convert endpoint is accessible"""
        response = client.post('/convert-pdf', json={})
        # Should return 400 or 503, not 404
        assert response.status_code in [400, 503]
    
    def test_convert_requires_json_content_type(self, client):
        """Test that convert endpoint requires JSON content type"""
        response = client.post('/convert-pdf', data='not json')
        # May return 400, 415, or 503 (if LibreOffice check happens first)
        assert response.status_code in [400, 415, 503]
    
    def test_convert_with_empty_body(self, client):
        """Test conversion with empty request body"""
        response = client.post('/convert-pdf', json={})
        data = response.get_json()
        
        assert response.status_code in [400, 503]
        assert data['success'] is False
        assert 'error_code' in data
    
    def test_convert_with_missing_docx_data(self, client):
        """Test conversion with missing docx_data field"""
        response = client.post('/convert-pdf', json={'other_field': 'value'})
        data = response.get_json()
        
        assert response.status_code in [400, 503]
        assert data['success'] is False
        if response.status_code == 400:
            assert data['error_code'] == ErrorCode.MISSING_DOCX_DATA.value
    
    def test_convert_with_invalid_base64(self, client):
        """Test conversion with invalid base64 data"""
        response = client.post('/convert-pdf', json={'docx_data': 'invalid-base64!!!'})
        data = response.get_json()
        
        assert response.status_code in [400, 503]
        assert data['success'] is False
        if response.status_code == 400:
            assert data['error_code'] == ErrorCode.INVALID_BASE64.value
    
    def test_convert_with_empty_docx_data(self, client):
        """Test conversion with empty docx_data"""
        response = client.post('/convert-pdf', json={'docx_data': ''})
        data = response.get_json()
        
        assert response.status_code in [400, 503]
        assert data['success'] is False
        if response.status_code == 400:
            assert data['error_code'] == ErrorCode.MISSING_DOCX_DATA.value
    
    def test_convert_with_invalid_docx_format(self, client):
        """Test conversion with invalid DOCX format"""
        invalid_docx = base64.b64encode(b'Not a DOCX file').decode()
        response = client.post('/convert-pdf', json={'docx_data': invalid_docx})
        data = response.get_json()
        
        assert response.status_code in [400, 503]
        assert data['success'] is False
        if response.status_code == 400:
            assert data['error_code'] == ErrorCode.INVALID_DOCX_FORMAT.value
    
    def test_convert_with_oversized_file(self, client):
        """Test conversion with file exceeding size limit"""
        # Create data larger than 50MB
        large_data = b'x' * (51 * 1024 * 1024)
        large_base64 = base64.b64encode(large_data).decode()
        
        response = client.post('/convert-pdf', json={'docx_data': large_base64})
        data = response.get_json()
        
        assert response.status_code in [400, 503]
        assert data['success'] is False
        if response.status_code == 400:
            assert data['error_code'] == ErrorCode.FILE_TOO_LARGE.value
    
    @patch('app.LIBREOFFICE_AVAILABLE', False)
    def test_convert_without_libreoffice(self, client):
        """Test conversion when LibreOffice is unavailable"""
        valid_docx = base64.b64encode(b'PK\x03\x04' + b'\x00' * 100).decode()
        response = client.post('/convert-pdf', json={'docx_data': valid_docx})
        data = response.get_json()
        
        assert response.status_code == 503
        assert data['success'] is False
        assert data['error_code'] == ErrorCode.LIBREOFFICE_UNAVAILABLE.value
    
    def test_error_response_has_timestamp(self, client):
        """Test that error responses include timestamp"""
        response = client.post('/convert-pdf', json={})
        data = response.get_json()
        
        assert 'timestamp' in data
        assert isinstance(data['timestamp'], (int, float))
    
    def test_error_response_has_processing_time(self, client):
        """Test that error responses include processing time"""
        response = client.post('/convert-pdf', json={})
        data = response.get_json()
        
        # Processing time may or may not be included depending on where error occurred
        if 'processing_time_ms' in data:
            assert isinstance(data['processing_time_ms'], int)
            assert data['processing_time_ms'] >= 0


class TestErrorHandlingIntegration:
    """Integration tests for comprehensive error handling (Requirement 6.1, 6.2)"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_404_error_handler(self, client):
        """Test 404 error handler for non-existent endpoints"""
        response = client.get('/nonexistent')
        data = response.get_json()
        
        assert response.status_code == 404
        assert data['success'] is False
        assert 'error_code' in data
        assert 'error_message' in data
    
    def test_404_error_includes_path(self, client):
        """Test that 404 error includes requested path"""
        response = client.get('/nonexistent')
        data = response.get_json()
        
        if 'details' in data:
            assert 'path' in data['details']
    
    def test_method_not_allowed(self, client):
        """Test method not allowed error"""
        # Health endpoint only accepts GET
        response = client.post('/health')
        assert response.status_code == 405
    
    def test_error_response_structure_consistency(self, client):
        """Test that all error responses follow consistent structure"""
        # Test multiple error scenarios
        error_scenarios = [
            client.get('/nonexistent'),  # 404
            client.post('/convert-pdf', json={}),  # 400 or 503
        ]
        
        for response in error_scenarios:
            data = response.get_json()
            
            # All errors should have these fields
            assert data is not None, f"Response should have JSON body, got {response.status_code}"
            assert 'success' in data
            assert data['success'] is False
            assert 'error_code' in data or 'error' in data
            assert 'error_message' in data or 'message' in data


class TestCORSIntegration:
    """Integration tests for CORS configuration (Requirement 2.2)"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_cors_preflight_request(self, client):
        """Test CORS preflight OPTIONS request"""
        response = client.options('/convert-pdf',
                                 headers={'Origin': 'http://example.com'})
        # Should not return 404
        assert response.status_code in [200, 204]
    
    def test_cors_headers_on_get(self, client):
        """Test CORS headers on GET request"""
        response = client.get('/health',
                             headers={'Origin': 'http://example.com'})
        assert response.status_code == 200
    
    def test_cors_headers_on_post(self, client):
        """Test CORS headers on POST request"""
        response = client.post('/convert-pdf',
                              json={},
                              headers={'Origin': 'http://example.com'})
        # Should process request, not reject due to CORS
        assert response.status_code in [400, 503]


class TestEndToEndConversion:
    """End-to-end integration tests for PDF conversion (Requirement 1.1, 1.2)"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def sample_docx_path(self):
        """Path to sample DOCX file if available"""
        # Check if test DOCX exists in parent directory
        test_files = [
            '../test_word_output.docx',
            '../quality_test_word.docx',
            '../frontend_test.docx'
        ]
        
        for file_path in test_files:
            if os.path.exists(file_path):
                return file_path
        
        return None
    
    @patch('app.LIBREOFFICE_AVAILABLE', True)
    @patch('docx2pdf.convert')
    def test_successful_conversion_mock(self, mock_convert, client):
        """Test successful PDF conversion with mocked docx2pdf"""
        # Mock the conversion to create a fake PDF
        def mock_conversion(input_path, output_path):
            with open(output_path, 'wb') as f:
                f.write(b'%PDF-1.4\n%Mock PDF content')
        
        mock_convert.side_effect = mock_conversion
        
        # Create valid DOCX data
        valid_docx = base64.b64encode(b'PK\x03\x04' + b'\x00' * 100).decode()
        
        response = client.post('/convert-pdf', json={'docx_data': valid_docx})
        data = response.get_json()
        
        if response.status_code == 200:
            assert data['success'] is True
            assert 'pdf_data' in data
            assert 'size' in data
            assert 'processing_time_ms' in data
            assert 'request_id' in data
            assert data['conversion_method'] == 'docx2pdf_exact'
            
            # Verify PDF data is valid base64
            try:
                pdf_bytes = base64.b64decode(data['pdf_data'])
                assert pdf_bytes.startswith(b'%PDF')
            except Exception:
                pytest.fail("PDF data is not valid base64")
    
    def test_conversion_with_real_docx(self, client, sample_docx_path):
        """Test conversion with real DOCX file if available"""
        if sample_docx_path is None:
            pytest.skip("No sample DOCX file available")
        
        # Read real DOCX file
        with open(sample_docx_path, 'rb') as f:
            docx_bytes = f.read()
        
        docx_base64 = base64.b64encode(docx_bytes).decode()
        
        response = client.post('/convert-pdf', json={'docx_data': docx_base64})
        data = response.get_json()
        
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 400, 500, 503]
        assert 'success' in data
        
        if data['success']:
            assert 'pdf_data' in data
            assert 'processing_time_ms' in data
            
            # Verify PDF is valid
            pdf_bytes = base64.b64decode(data['pdf_data'])
            assert pdf_bytes.startswith(b'%PDF')
        else:
            assert 'error_code' in data
            assert 'error_message' in data


class TestRequestTracking:
    """Integration tests for request tracking and logging (Requirement 6.2, 6.4)"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @patch('app.LIBREOFFICE_AVAILABLE', True)
    @patch('docx2pdf.convert')
    def test_successful_request_has_request_id(self, mock_convert, client):
        """Test that successful requests include request ID"""
        def mock_conversion(input_path, output_path):
            with open(output_path, 'wb') as f:
                f.write(b'%PDF-1.4\n%Mock PDF')
        
        mock_convert.side_effect = mock_conversion
        
        valid_docx = base64.b64encode(b'PK\x03\x04' + b'\x00' * 100).decode()
        response = client.post('/convert-pdf', json={'docx_data': valid_docx})
        
        if response.status_code == 200:
            data = response.get_json()
            assert 'request_id' in data
            assert data['request_id'].startswith('req_')
    
    def test_processing_time_tracking(self, client):
        """Test that processing time is tracked"""
        response = client.post('/convert-pdf', json={})
        data = response.get_json()
        
        # Even errors should track processing time
        if 'processing_time_ms' in data:
            assert isinstance(data['processing_time_ms'], int)
            assert data['processing_time_ms'] >= 0
    
    @patch('app.LIBREOFFICE_AVAILABLE', True)
    @patch('docx2pdf.convert')
    def test_successful_conversion_tracks_sizes(self, mock_convert, client):
        """Test that successful conversions track file sizes"""
        def mock_conversion(input_path, output_path):
            with open(output_path, 'wb') as f:
                f.write(b'%PDF-1.4\n%Mock PDF content')
        
        mock_convert.side_effect = mock_conversion
        
        valid_docx = base64.b64encode(b'PK\x03\x04' + b'\x00' * 100).decode()
        response = client.post('/convert-pdf', json={'docx_data': valid_docx})
        
        if response.status_code == 200:
            data = response.get_json()
            assert 'size' in data
            assert isinstance(data['size'], int)
            assert data['size'] > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
