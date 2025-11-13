# PDF Conversion Service

A standalone microservice for converting Word documents (DOCX) to PDF with 100% accuracy using LibreOffice's docx2pdf library.

## Overview

This service is part of the Format-A application ecosystem and provides reliable Word-to-PDF conversion capabilities. It operates as an independent microservice that can be deployed on Railway, Render, or other cloud platforms.

## Features

- **100% Accurate Conversion**: Uses LibreOffice's docx2pdf for pixel-perfect PDF generation
- **REST API**: Simple HTTP endpoints for conversion requests
- **Base64 Support**: Accepts and returns documents as base64-encoded data
- **Health Monitoring**: Built-in health check endpoints
- **Error Handling**: Comprehensive error responses and logging
- **CORS Enabled**: Ready for cross-origin requests from web applications

## API Endpoints

### Health Check
```
GET /health
```
Returns service status and LibreOffice availability.

### Convert to PDF (JSON Response)
```
POST /convert-pdf
Content-Type: application/json

{
  "docx_data": "base64_encoded_docx_content"
}
```
Returns PDF as base64-encoded data in JSON response.

### Convert to PDF (File Download)
```
POST /convert-pdf-download
Content-Type: application/json

{
  "docx_data": "base64_encoded_docx_content"
}
```
Returns PDF as direct file download.

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- LibreOffice (automatically installed on most cloud platforms)

### Local Development

1. **Clone and navigate to the service directory:**
   ```bash
   cd pdf/
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install LibreOffice (if not already installed):**
   
   **Windows:**
   - Download from https://www.libreoffice.org/download/download/
   - Install and ensure it's in your PATH
   
   **macOS:**
   ```bash
   brew install --cask libreoffice
   ```
   
   **Ubuntu/Debian:**
   ```bash
   sudo apt-get update
   sudo apt-get install libreoffice
   ```

5. **Run the service:**
   ```bash
   python app.py
   ```

   The service will start on `http://localhost:5000`

6. **Test the service:**
   ```bash
   curl http://localhost:5000/health
   ```

### Cloud Deployment

#### Railway Deployment

1. **Connect your repository to Railway**
2. **Set environment variables:**
   ```
   PORT=5000
   FLASK_ENV=production
   ```
3. **Deploy** - Railway will automatically detect the Python app and install LibreOffice

#### Render Deployment

1. **Create a new Web Service on Render**
2. **Set build command:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set start command:**
   ```bash
   python app.py
   ```
4. **Set environment variables:**
   ```
   PORT=5000
   FLASK_ENV=production
   ```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Port number for the service | `5000` |
| `FLASK_ENV` | Flask environment mode | `development` |

## Usage Example

### Python Client
```python
import requests
import base64

# Read DOCX file
with open('document.docx', 'rb') as f:
    docx_data = base64.b64encode(f.read()).decode()

# Convert to PDF
response = requests.post('http://localhost:5000/convert-pdf', json={
    'docx_data': docx_data
})

if response.status_code == 200:
    result = response.json()
    if result['success']:
        # Save PDF
        pdf_bytes = base64.b64decode(result['pdf_data'])
        with open('output.pdf', 'wb') as f:
            f.write(pdf_bytes)
        print(f"PDF generated successfully: {result['size']} bytes")
    else:
        print(f"Conversion failed: {result['error']}")
```

### JavaScript/Node.js Client
```javascript
const fs = require('fs');

// Read DOCX file
const docxBuffer = fs.readFileSync('document.docx');
const docxData = docxBuffer.toString('base64');

// Convert to PDF
fetch('http://localhost:5000/convert-pdf', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        docx_data: docxData
    })
})
.then(response => response.json())
.then(result => {
    if (result.success) {
        // Save PDF
        const pdfBuffer = Buffer.from(result.pdf_data, 'base64');
        fs.writeFileSync('output.pdf', pdfBuffer);
        console.log(`PDF generated successfully: ${result.size} bytes`);
    } else {
        console.error(`Conversion failed: ${result.error}`);
    }
});
```

## Architecture

This service is designed to integrate with the Format-A application:

```
Format-A Frontend → Format-A Backend → PDF Service → LibreOffice
                                    ↓
                              PDF Response
```

## Dependencies

- **Flask**: Web framework for the REST API
- **Flask-CORS**: Cross-origin resource sharing support
- **docx2pdf**: LibreOffice-based DOCX to PDF conversion
- **python-docx**: DOCX file handling utilities

## Troubleshooting

### LibreOffice Not Found
If you get errors about LibreOffice not being available:

1. **Verify LibreOffice installation:**
   ```bash
   libreoffice --version
   ```

2. **Check PATH environment variable** includes LibreOffice binary location

3. **On cloud platforms**, LibreOffice is usually pre-installed or automatically installed

### Memory Issues
For large documents or high load:

1. **Increase memory limits** in your deployment platform
2. **Consider implementing request queuing** for high-volume scenarios
3. **Monitor resource usage** through platform dashboards

### Conversion Failures
If conversions fail:

1. **Check input DOCX validity** - ensure the file is not corrupted
2. **Review service logs** for detailed error messages
3. **Test with simple documents** to isolate complex formatting issues

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This service is part of the Format-A project and follows the same licensing terms.