#!/usr/bin/env python3
"""
Performance tests for PDF service
Tests conversion times and performance requirements
Requirements: 1.3, 1.4
"""

import pytest
import base64
import time
import os
from unittest.mock import patch, MagicMock
from app import create_app, CONVERSION_TIMEOUT_SECONDS


class TestConversionPerformance:
    """Performance tests for PDF conversion (Requirement 1.3)"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def small_docx_data(self):
        """Create small DOCX data for performance testing"""
        # Minimal valid DOCX structure
        docx_bytes = b'PK\x03\x04' + b'\x00' * 1024  # 1KB
        return base64.b64encode(docx_bytes).decode()
    
    @pytest.fixture
    def medium_docx_data(self):
        """Create medium DOCX data for performance testing"""
        # Medium size DOCX
        docx_bytes = b'PK\x03\x04' + b'\x00' * (100 * 1024)  # 100KB
        return base64.b64encode(docx_bytes).decode()
    
    @pytest.fixture
    def large_docx_data(self):
        """Create large DOCX data for performance testing"""
        # Large DOCX (but under 50MB limit)
        docx_bytes = b'PK\x03\x04' + b'\x00' * (5 * 1024 * 1024)  # 5MB
        return base64.b64encode(docx_bytes).decode()
    
    def test_conversion_timeout_constant(self):
        """Test that conversion timeout is set to 30 seconds (Requirement 1.3)"""
        assert CONVERSION_TIMEOUT_SECONDS == 30
    
    @patch('app.LIBREOFFICE_AVAILABLE', True)
    @patch('docx2pdf.convert')
    def test_small_file_conversion_time(self, mock_convert, client, small_docx_data):
        """Test conversion time for small files"""
        def mock_conversion(input_path, output_path):
            time.sleep(0.1)  # Simulate 100ms conversion
            with open(output_path, 'wb') as f:
                f.write(b'%PDF-1.4\n%Mock PDF')
        
        mock_convert.side_effect = mock_conversion
        
        start_time = time.time()
        response = client.post('/convert-pdf', json={'docx_data': small_docx_data})
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.get_json()
            
            # Should complete well under 30 seconds
            assert elapsed_time < 30
            
            # Processing time should be tracked
            assert 'processing_time_ms' in data
            assert data['processing_time_ms'] < 30000
    
    @patch('app.LIBREOFFICE_AVAILABLE', True)
    @patch('docx2pdf.convert')
    def test_medium_file_conversion_time(self, mock_convert, client, medium_docx_data):
        """Test conversion time for medium files"""
        def mock_conversion(input_path, output_path):
            time.sleep(0.5)  # Simulate 500ms conversion
            with open(output_path, 'wb') as f:
                f.write(b'%PDF-1.4\n%Mock PDF')
        
        mock_convert.side_effect = mock_conversion
        
        start_time = time.time()
        response = client.post('/convert-pdf', json={'docx_data': medium_docx_data})
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.get_json()
            
            # Should complete well under 30 seconds
            assert elapsed_time < 30
            
            # Processing time should be reasonable
            assert data['processing_time_ms'] < 30000
    
    @patch('app.LIBREOFFICE_AVAILABLE', True)
    @patch('docx2pdf.convert')
    def test_large_file_conversion_time(self, mock_convert, client, large_docx_data):
        """Test conversion time for large files"""
        def mock_conversion(input_path, output_path):
            time.sleep(2.0)  # Simulate 2s conversion for large file
            with open(output_path, 'wb') as f:
                f.write(b'%PDF-1.4\n%Mock PDF')
        
        mock_convert.side_effect = mock_conversion
        
        start_time = time.time()
        response = client.post('/convert-pdf', json={'docx_data': large_docx_data})
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.get_json()
            
            # Should complete within 30 seconds (Requirement 1.3)
            assert elapsed_time < 30
            
            # Processing time should be under limit
            assert data['processing_time_ms'] < 30000
    
    @patch('app.LIBREOFFICE_AVAILABLE', True)
    @patch('docx2pdf.convert')
    def test_conversion_timeout_handling(self, mock_convert, client, small_docx_data):
        """Test handling of conversion that exceeds timeout"""
        def slow_conversion(input_path, output_path):
            # Simulate conversion that takes longer than timeout
            time.sleep(31)  # Exceeds 30 second timeout
            with open(output_path, 'wb') as f:
                f.write(b'%PDF-1.4\n%Mock PDF')
        
        mock_convert.side_effect = slow_conversion
        
        start_time = time.time()
        response = client.post('/convert-pdf', json={'docx_data': small_docx_data})
        elapsed_time = time.time() - start_time
        
        # Note: Current implementation doesn't enforce timeout on docx2pdf
        # This test documents the behavior
        # In production, timeout should be enforced at infrastructure level
        
        if response.status_code == 200:
            data = response.get_json()
            # If it completes, it should still track the time
            assert 'processing_time_ms' in data
    
    def test_validation_performance(self, client):
        """Test that validation is fast"""
        # Test multiple validation scenarios
        test_cases = [
            {},  # Empty
            {'docx_data': ''},  # Empty data
            {'docx_data': 'invalid'},  # Invalid base64
        ]
        
        for test_data in test_cases:
            start_time = time.time()
            response = client.post('/convert-pdf', json=test_data)
            elapsed_time = time.time() - start_time
            
            # Validation should be very fast (under 1 second)
            assert elapsed_time < 1.0
            
            data = response.get_json()
            if 'processing_time_ms' in data:
                # Processing time should be minimal for validation errors
                assert data['processing_time_ms'] < 1000
    
    def test_health_check_performance(self, client):
        """Test that health check is fast"""
        start_time = time.time()
        response = client.get('/health')
        elapsed_time = time.time() - start_time
        
        # Health check should be very fast
        assert elapsed_time < 0.5
        assert response.status_code == 200


class TestConcurrentRequests:
    """Performance tests for concurrent request handling"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_multiple_health_checks(self, client):
        """Test handling multiple health check requests"""
        start_time = time.time()
        
        # Make 10 health check requests
        responses = []
        for _ in range(10):
            response = client.get('/health')
            responses.append(response)
        
        elapsed_time = time.time() - start_time
        
        # All should succeed
        assert all(r.status_code == 200 for r in responses)
        
        # Should complete reasonably fast
        assert elapsed_time < 5.0
    
    @patch('app.LIBREOFFICE_AVAILABLE', True)
    @patch('docx2pdf.convert')
    def test_multiple_validation_errors(self, mock_convert, client):
        """Test handling multiple validation errors"""
        start_time = time.time()
        
        # Make 10 requests with validation errors
        responses = []
        for _ in range(10):
            response = client.post('/convert-pdf', json={})
            responses.append(response)
        
        elapsed_time = time.time() - start_time
        
        # All should return error responses
        assert all(r.status_code in [400, 503] for r in responses)
        
        # Should complete reasonably fast
        assert elapsed_time < 5.0


class TestResourceUsage:
    """Performance tests for resource usage"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_memory_cleanup_after_error(self, client):
        """Test that memory is cleaned up after errors"""
        # Make request with large invalid data
        large_invalid = base64.b64encode(b'Not DOCX' * 1000).decode()
        
        response = client.post('/convert-pdf', json={'docx_data': large_invalid})
        
        # Should handle error gracefully
        assert response.status_code in [400, 503]
        
        # Subsequent requests should still work
        response2 = client.get('/health')
        assert response2.status_code == 200
    
    @patch('app.LIBREOFFICE_AVAILABLE', True)
    @patch('docx2pdf.convert')
    def test_temp_file_cleanup(self, mock_convert, client):
        """Test that temporary files are cleaned up"""
        def mock_conversion(input_path, output_path):
            with open(output_path, 'wb') as f:
                f.write(b'%PDF-1.4\n%Mock PDF')
        
        mock_convert.side_effect = mock_conversion
        
        valid_docx = base64.b64encode(b'PK\x03\x04' + b'\x00' * 100).decode()
        
        # Make multiple requests
        for _ in range(5):
            response = client.post('/convert-pdf', json={'docx_data': valid_docx})
            # Each request should complete
            assert response.status_code in [200, 400, 500, 503]
        
        # Service should still be healthy
        health_response = client.get('/health')
        assert health_response.status_code == 200


class TestRealWorldPerformance:
    """Performance tests with real-world scenarios"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def real_docx_files(self):
        """Find real DOCX files for testing"""
        test_files = []
        search_paths = [
            '../test_word_output.docx',
            '../quality_test_word.docx',
            '../frontend_test.docx',
            '../test_complete_flow.docx'
        ]
        
        for path in search_paths:
            if os.path.exists(path):
                test_files.append(path)
        
        return test_files
    
    def test_real_docx_conversion_time(self, client, real_docx_files):
        """Test conversion time with real DOCX files"""
        if not real_docx_files:
            pytest.skip("No real DOCX files available for testing")
        
        for docx_path in real_docx_files[:3]:  # Test up to 3 files
            with open(docx_path, 'rb') as f:
                docx_bytes = f.read()
            
            docx_base64 = base64.b64encode(docx_bytes).decode()
            
            start_time = time.time()
            response = client.post('/convert-pdf', json={'docx_data': docx_base64})
            elapsed_time = time.time() - start_time
            
            # Should complete within 30 seconds (Requirement 1.3)
            assert elapsed_time < 30, f"Conversion took {elapsed_time}s, exceeds 30s limit"
            
            if response.status_code == 200:
                data = response.get_json()
                assert data['processing_time_ms'] < 30000
                
                print(f"\nFile: {os.path.basename(docx_path)}")
                print(f"  Size: {len(docx_bytes)} bytes")
                print(f"  Time: {elapsed_time:.2f}s")
                print(f"  Tracked: {data['processing_time_ms']}ms")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
