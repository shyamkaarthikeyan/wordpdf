# PDF Service Test Documentation

## Overview

This document describes the comprehensive test suite for the PDF service, implementing Task 8 requirements.

## Test Requirements

Task 8 requires:
- ✅ Unit tests for health check endpoint and PDF conversion functionality
- ✅ Integration tests for invalid input handling and error response validation
- ✅ Performance tests to verify conversion times meet requirements (30 seconds)
- ✅ Coverage of Requirements: 1.3, 1.4, 6.1, 6.2

## Test Files

### 1. `test_unit.py` - Unit Tests

Tests individual components and functions in isolation.

**Test Classes:**
- `TestHealthCheckEndpoint` - Health check endpoint functionality
  - Returns 200 status code
  - Returns JSON response
  - Contains required fields (status, service, version, libreoffice_available, timestamp)
  - Reports correct service name and version
  - Timestamp is current

- `TestLibreOfficeValidation` - LibreOffice dependency validation
  - Successful validation when LibreOffice is installed
  - Handles LibreOffice not found
  - Handles validation timeout
  - Handles command failures

- `TestRequestValidation` - Request data validation (Requirement 6.2)
  - Empty request validation
  - Missing docx_data field
  - Empty docx_data
  - Invalid base64 encoding
  - File size limit validation (50MB)
  - Invalid DOCX format (missing PK header)
  - Valid DOCX data acceptance

- `TestErrorResponseStructure` - Structured error responses (Requirement 6.1, 6.3)
  - PDFServiceError data structure
  - Error responses with details
  - Error responses with processing time

- `TestConversionMetrics` - Conversion metrics logging (Requirement 6.2, 6.4)
  - Metrics data structure
  - Metrics for successful conversions
  - Metrics for failed conversions

- `TestErrorCodes` - Error code enumeration (Requirement 6.3)
  - All required error codes defined
  - Error code string values

**Total Unit Tests:** 30+

### 2. `test_integration.py` - Integration Tests

Tests complete workflows and error handling scenarios.

**Test Classes:**
- `TestConvertEndpointIntegration` - PDF conversion endpoint
  - Endpoint accessibility
  - JSON content type requirement
  - Empty request body handling
  - Missing docx_data field
  - Invalid base64 data
  - Empty docx_data
  - Invalid DOCX format
  - Oversized file handling
  - LibreOffice unavailable scenario
  - Error response timestamp
  - Error response processing time

- `TestErrorHandlingIntegration` - Comprehensive error handling (Requirement 6.1, 6.2)
  - 404 error handler
  - 404 error includes path
  - Method not allowed (405)
  - Error response structure consistency

- `TestCORSIntegration` - CORS configuration (Requirement 2.2)
  - CORS preflight OPTIONS request
  - CORS headers on GET requests
  - CORS headers on POST requests

- `TestEndToEndConversion` - End-to-end conversion (Requirement 1.1, 1.2)
  - Successful conversion with mocked docx2pdf
  - Conversion with real DOCX files (if available)
  - PDF validation (starts with %PDF)

- `TestRequestTracking` - Request tracking and logging (Requirement 6.2, 6.4)
  - Request ID generation
  - Processing time tracking
  - File size tracking

**Total Integration Tests:** 25+

### 3. `test_performance.py` - Performance Tests

Tests conversion times and performance requirements.

**Test Classes:**
- `TestConversionPerformance` - Conversion performance (Requirement 1.3)
  - Conversion timeout constant (30 seconds)
  - Small file conversion time
  - Medium file conversion time
  - Large file conversion time (under 30s requirement)
  - Conversion timeout handling
  - Validation performance (under 1 second)
  - Health check performance (under 0.5 seconds)

- `TestConcurrentRequests` - Concurrent request handling
  - Multiple health check requests
  - Multiple validation errors

- `TestResourceUsage` - Resource usage
  - Memory cleanup after errors
  - Temporary file cleanup
  - Service stability after multiple requests

- `TestRealWorldPerformance` - Real-world scenarios
  - Real DOCX file conversion times (under 30s requirement)

**Total Performance Tests:** 15+

## Running Tests

### Run All Tests
```bash
python run_tests.py
```

### Run Specific Test Suite
```bash
# Unit tests only
pytest test_unit.py -v

# Integration tests only
pytest test_integration.py -v

# Performance tests only
pytest test_performance.py -v
```

### Run with Coverage
```bash
pytest test_unit.py test_integration.py test_performance.py --cov=app --cov-report=html
```

### Run Specific Test Class
```bash
pytest test_unit.py::TestHealthCheckEndpoint -v
```

### Run Specific Test
```bash
pytest test_unit.py::TestHealthCheckEndpoint::test_health_check_returns_200 -v
```

## Test Coverage

The comprehensive test suite covers:

### Requirements Coverage
- **Requirement 1.3** - Conversion within 30 seconds
  - Performance tests verify conversion times
  - Timeout constant validation
  - Real-world file conversion timing

- **Requirement 1.4** - Clear error messages on failure
  - Integration tests for error scenarios
  - Error message validation
  - User-friendly error responses

- **Requirement 6.1** - Detailed error logging
  - Unit tests for error structures
  - Integration tests for error responses
  - Error code validation

- **Requirement 6.2** - Request logging with details
  - Unit tests for metrics structure
  - Integration tests for request tracking
  - Processing time tracking

### Functionality Coverage
- ✅ Health check endpoint
- ✅ PDF conversion endpoint
- ✅ Request validation
- ✅ Error handling
- ✅ CORS configuration
- ✅ LibreOffice dependency validation
- ✅ File size limits
- ✅ Base64 encoding/decoding
- ✅ DOCX format validation
- ✅ Temporary file management
- ✅ Request tracking and logging
- ✅ Performance requirements

## Test Strategy

### Unit Tests
- Test individual functions and components in isolation
- Use mocking to isolate dependencies
- Focus on edge cases and error conditions
- Fast execution (< 1 second per test)

### Integration Tests
- Test complete request/response workflows
- Test error handling end-to-end
- Validate API contracts
- Test CORS and security configurations

### Performance Tests
- Verify 30-second conversion requirement (Requirement 1.3)
- Test with various file sizes
- Measure resource usage
- Test concurrent request handling
- Validate cleanup and stability

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# Example CI configuration
test:
  script:
    - pip install -r requirements.txt
    - python run_tests.py
  coverage: '/TOTAL.*\s+(\d+%)$/'
```

## Test Maintenance

### Adding New Tests
1. Identify the requirement being tested
2. Choose appropriate test file (unit/integration/performance)
3. Add test to relevant test class
4. Follow naming convention: `test_<functionality>_<scenario>`
5. Include docstring explaining what is tested
6. Update this documentation

### Test Naming Convention
- `test_<component>_<expected_behavior>`
- Example: `test_health_check_returns_200`
- Example: `test_convert_with_invalid_base64`

### Mocking Guidelines
- Mock external dependencies (docx2pdf, subprocess)
- Don't mock the code under test
- Use realistic mock data
- Verify mock calls when relevant

## Known Limitations

1. **LibreOffice Dependency**: Some tests require LibreOffice to be installed
   - Tests gracefully skip or adapt when LibreOffice is unavailable
   - Mock-based tests provide coverage without LibreOffice

2. **Real DOCX Files**: Some integration tests look for real DOCX files
   - Tests skip if files are not available
   - Mock-based tests provide baseline coverage

3. **Timeout Testing**: Actual timeout enforcement is infrastructure-level
   - Tests document expected behavior
   - Mock-based tests simulate timeout scenarios

## Success Criteria

Task 8 is complete when:
- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ All performance tests pass
- ✅ Test coverage > 80% for app.py
- ✅ All requirements (1.3, 1.4, 6.1, 6.2) are tested
- ✅ Tests run successfully in CI/CD pipeline

## Related Documentation

- `README.md` - PDF service overview
- `ERROR_HANDLING.md` - Error handling details
- `app.py` - Service implementation
- `.kiro/specs/pdf-service-integration/requirements.md` - Requirements
- `.kiro/specs/pdf-service-integration/design.md` - Design document
