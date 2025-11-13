# PDF Service Error Handling Documentation

## Overview

This document describes the comprehensive error handling implementation for the PDF conversion service (Task 4).

## Error Codes

The service uses specific error codes for different failure scenarios:

| Error Code | HTTP Status | Description |
|-----------|-------------|-------------|
| `MISSING_DOCX_DATA` | 400 | Request body is missing or docx_data field is empty |
| `INVALID_BASE64` | 400 | The docx_data field contains invalid base64 encoding |
| `FILE_TOO_LARGE` | 400 | File size exceeds the 50MB limit |
| `INVALID_DOCX_FORMAT` | 400 | Valid base64 but not a valid DOCX file (missing PK header) |
| `LIBREOFFICE_UNAVAILABLE` | 503 | LibreOffice is not installed or not available |
| `CONVERSION_FAILED` | 500 | PDF conversion process failed |
| `CONVERSION_TIMEOUT` | 500 | Conversion exceeded timeout threshold |
| `INTERNAL_ERROR` | 500 | Unexpected internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service is temporarily unavailable |

## Error Response Format

All errors follow a structured response format:

```json
{
  "success": false,
  "error_code": "MISSING_DOCX_DATA",
  "error_message": "Missing required field: docx_data",
  "details": {
    "received_fields": ["other_field"]
  },
  "timestamp": 1762969249.367514,
  "processing_time_ms": 15
}
```

### Required Fields
- `success`: Always `false` for errors
- `error_code`: Specific error code from the enum
- `error_message`: Human-readable error description
- `timestamp`: Unix timestamp when error occurred

### Optional Fields
- `details`: Additional context about the error (dict)
- `processing_time_ms`: Time spent processing before error (int)

## Request Validation

The service validates all incoming requests with the following checks:

### 1. Request Body Validation
- Checks if request body exists
- Validates JSON format
- Ensures required fields are present

### 2. Base64 Validation
- Validates base64 encoding format
- Attempts to decode the data
- Returns `INVALID_BASE64` error if decoding fails

### 3. File Size Validation
- Maximum file size: 50MB (52,428,800 bytes)
- Returns `FILE_TOO_LARGE` error with size details if exceeded
- Includes both bytes and MB in error details

### 4. DOCX Format Validation
- Checks for PK header (ZIP format signature)
- Validates that the file is a valid DOCX archive
- Returns `INVALID_DOCX_FORMAT` error if validation fails

## Logging System

The service implements comprehensive logging at multiple levels:

### Application Logging
- **Format**: `%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s`
- **Levels**: INFO, WARNING, ERROR
- **Includes**: Request IDs, file sizes, processing times, error details

### Metrics Logging
- **Separate logger**: `metrics_logger`
- **File**: `conversion_metrics.log`
- **Format**: Structured log entries with key metrics

#### Metrics Tracked
```
request_id=req_1762969249367 | docx_size=1024 | pdf_size=2048 | processing_time_ms=2500 | success=True | error_code=NONE
```

Each conversion request logs:
- `request_id`: Unique identifier for the request
- `docx_size_bytes`: Size of input DOCX file
- `pdf_size_bytes`: Size of output PDF file (null if failed)
- `processing_time_ms`: Total processing time in milliseconds
- `success`: Boolean indicating success/failure
- `error_code`: Error code if failed, NONE if successful

### Request Tracking
- Each request gets a unique ID: `req_{timestamp_ms}`
- All log entries for a request include the request ID
- Enables easy tracking of request lifecycle through logs

### Processing Time Tracking
- Start time captured at request entry
- Processing time calculated and included in all responses
- Logged for both successful and failed requests

## Error Handling Flow

```
Request → Validation → Processing → Response
   ↓          ↓            ↓           ↓
 Log      Log Error    Log Error   Return
Start    + Metrics    + Metrics   Structured
                                   Error
```

### Cleanup
- Temporary files are always cleaned up in `finally` block
- Cleanup errors are logged but don't affect response
- Separate cleanup tracking for DOCX and PDF temp files

## Testing

The error handling implementation includes comprehensive tests:

1. **Error Code Validation**: Tests all error codes are returned correctly
2. **Structured Response**: Validates error response format
3. **Request Validation**: Tests all validation scenarios
4. **Logging**: Verifies request IDs and metrics are logged
5. **Processing Time**: Confirms timing is tracked for all requests

Run tests with:
```bash
python pdf/test_service.py
```

## Requirements Coverage

This implementation satisfies the following requirements:

- **Requirement 6.1**: Detailed error logging for all pipeline failures
- **Requirement 6.2**: Request details, processing time, and outcome logging
- **Requirement 6.3**: Meaningful error codes and messages for debugging
- **Requirement 6.4**: Health check with service status and dependency availability
- **Requirement 6.5**: Performance metrics (request volume, conversion times, error rates)

## Usage Examples

### Valid Request
```bash
curl -X POST http://localhost:5000/convert-pdf \
  -H "Content-Type: application/json" \
  -d '{"docx_data": "UEsDBBQABgAIAAAAIQ..."}'
```

### Error Responses

#### Missing Data
```json
{
  "success": false,
  "error_code": "MISSING_DOCX_DATA",
  "error_message": "Missing required field: docx_data",
  "details": {"received_fields": []},
  "timestamp": 1762969249.367514
}
```

#### Invalid Base64
```json
{
  "success": false,
  "error_code": "INVALID_BASE64",
  "error_message": "Invalid base64 encoding",
  "details": {"decode_error": "Invalid base64-encoded string"},
  "timestamp": 1762969249.367514
}
```

#### File Too Large
```json
{
  "success": false,
  "error_code": "FILE_TOO_LARGE",
  "error_message": "File size exceeds maximum limit of 50MB",
  "details": {
    "file_size_bytes": 52428801,
    "max_size_bytes": 52428800,
    "file_size_mb": 50.01,
    "max_size_mb": 50
  },
  "timestamp": 1762969249.367514
}
```

#### LibreOffice Unavailable
```json
{
  "success": false,
  "error_code": "LIBREOFFICE_UNAVAILABLE",
  "error_message": "PDF conversion service requires LibreOffice to be installed",
  "details": {"libreoffice_available": false},
  "timestamp": 1762969249.367514
}
```
