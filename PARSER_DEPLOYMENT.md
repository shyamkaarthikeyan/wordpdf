# Document Parser Deployment on Railway

## Overview

The PDF service on Railway now includes a document parser endpoint that extracts structured content from PDF and DOCX files.

## What's Added

### New Endpoint: `/parse`

**Method:** POST  
**Content-Type:** multipart/form-data  
**Parameter:** `file` (PDF or DOCX file)

**Response:**
```json
{
  "success": true,
  "data": {
    "title": "Paper Title",
    "authors": [{name, email, affiliation}],
    "abstract": "Abstract text...",
    "keywords": "keyword1, keyword2",
    "sections": [{title, number, contentBlocks}],
    "references": [{text, order}]
  },
  "message": "Document parsed successfully (PDF)",
  "processing_time_ms": 1234
}
```

## Files Added

1. **`document_parser.py`** - Full parser implementation with:
   - Sequential extraction (Title → Authors → Abstract → Keywords → Sections → References)
   - PDF parsing with pdfplumber
   - DOCX parsing with python-docx
   - Image/table/equation detection
   - IEEE section numbering support

2. **`app.py`** - Updated with `/parse` endpoint

## Deployment Steps

### 1. Update Requirements

Add to `requirements.txt` (if not already there):
```txt
pdfplumber==0.10.3
PyMuPDF==1.23.8
pdf2image==1.16.3
Pillow==10.1.0
pytesseract==0.3.10
```

### 2. Deploy to Railway

```bash
# In the pdf/ directory
git add .
git commit -m "Add document parser endpoint"
git push railway main
```

Or if using Railway CLI:
```bash
railway up
```

### 3. Get Railway URL

After deployment, get your service URL from Railway dashboard:
```
https://your-service-name.railway.app
```

### 4. Configure Frontend

In your Format-A project, create `.env.local`:
```bash
VITE_PARSER_API_URL=https://your-service-name.railway.app
```

### 5. Test the Parser

```bash
# Test with curl
curl -X POST https://your-service-name.railway.app/parse \
  -F "file=@sample.pdf"
```

## How It Works

### Frontend Flow

1. User uploads PDF/DOCX in the import modal
2. Frontend checks if `VITE_PARSER_API_URL` is set
3. If set: Calls Railway `/parse` endpoint (backend parsing)
4. If not set: Uses client-side browser parsing (fallback)

### Backend Parsing (Railway)

**Advantages:**
- ✅ More accurate extraction
- ✅ Better layout analysis
- ✅ Image extraction support
- ✅ Table detection
- ✅ Equation recognition
- ✅ Multi-column layout handling

**Process:**
1. Receives file upload
2. Detects file type (PDF/DOCX)
3. Extracts text with layout information
4. Parses structure sequentially
5. Returns JSON matching form schema

### Client-Side Parsing (Fallback)

**Advantages:**
- ✅ No backend needed
- ✅ Works immediately
- ✅ Fast for simple documents
- ✅ Privacy (files never leave browser)

**Limitations:**
- ❌ Basic text extraction only
- ❌ No image extraction
- ❌ Limited layout analysis
- ❌ No OCR support

## Testing

### Test Backend Parser

```python
import requests

url = "https://your-service-name.railway.app/parse"

with open('sample.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post(url, files=files)
    
print(response.json())
```

### Test Frontend Integration

1. Set `VITE_PARSER_API_URL` in `.env.local`
2. Restart dev server: `npm run dev`
3. Upload a document in the import modal
4. Check browser console for API calls

## Monitoring

### Check Service Health

```bash
curl https://your-service-name.railway.app/health
```

Response:
```json
{
  "status": "healthy",
  "service": "pdf-converter",
  "version": "1.0.0",
  "libreoffice_available": true,
  "timestamp": 1234567890.123
}
```

### View Logs

In Railway dashboard:
1. Go to your service
2. Click "Deployments"
3. Click "View Logs"
4. Look for `[req_parse_*]` entries

## Troubleshooting

### Parser Not Working

**Check:**
1. Railway service is deployed and running
2. `VITE_PARSER_API_URL` is set correctly
3. CORS is configured (already done in `app.py`)
4. File size is under 50MB

**Test:**
```bash
# Check if endpoint exists
curl https://your-service-name.railway.app/parse

# Should return 405 Method Not Allowed (means endpoint exists)
```

### Dependencies Not Installing

Railway should auto-install from `requirements.txt`. If issues:

1. Check Railway build logs
2. Verify `requirements.txt` is in `pdf/` directory
3. Check Python version in `runtime.txt`

### Parsing Errors

Check Railway logs for detailed error messages:
```
[req_parse_123] Parsing failed: <error details>
```

Common issues:
- Corrupted PDF/DOCX file
- Password-protected PDF
- Scanned PDF (no text layer)
- Unsupported file format

## Cost

Railway pricing:
- **Free tier**: $5 credit/month (usually enough for testing)
- **Pro plan**: $5/month + usage
- **Parsing cost**: ~$0.01 per 1000 requests

Estimated monthly cost for moderate use: **$5-10**

## Security

- ✅ Files are processed in memory
- ✅ Temporary files cleaned up immediately
- ✅ No permanent storage
- ✅ CORS configured for your domain
- ✅ File size limits enforced (50MB)

## Future Enhancements

Planned improvements:
- [ ] Image extraction and OCR
- [ ] Table structure preservation
- [ ] Equation LaTeX conversion
- [ ] Citation linking
- [ ] Confidence scoring
- [ ] Batch processing

## Support

For issues:
1. Check Railway logs
2. Test with simple documents first
3. Verify environment variables
4. Check CORS configuration

---

**Status:** ✅ Ready to deploy
**Estimated setup time:** 10 minutes
**Recommended:** Deploy to Railway for best parsing quality
