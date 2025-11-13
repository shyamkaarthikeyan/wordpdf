# PDF Service Deployment Guide

This PDF conversion service requires LibreOffice for Word to PDF conversion, which cannot run on Vercel. This guide covers deployment to platforms that support Docker and system dependencies.

## Architecture

```
Frontend (Vercel) → Backend (Vercel) → PDF Service (Render/Railway/etc.)
```

The PDF service is deployed separately because it requires:
- LibreOffice for document conversion
- System-level dependencies
- Long-running processes

## Deployment Options

### Option 1: Render (Recommended - Free Tier Available)

**Why Render?**
- Free tier available
- Supports both Docker and Python buildpacks
- Easy GitHub integration
- Automatic deployments
- Auto-installs LibreOffice

**Steps (Python Buildpack - No Docker Required):**

1. **Push to GitHub** (Already done ✓)
   ```bash
   git push origin master
   ```

2. **Deploy on Render:**
   - Go to https://render.com
   - Sign up/Login with GitHub
   - Click "New +" → "Web Service"
   - Connect your GitHub repository: `shyamkaarthikeyan/wordpdf`
   - Configure:
     - **Name**: `pdf-conversion-service`
     - **Environment**: `Python 3`
     - **Region**: Choose closest to your users
     - **Branch**: `master`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 app:app`
     - **Plan**: Free
   - Click "Advanced" and add:
     - **Native Environment**: Add `libreoffice` and `libreoffice-writer` packages
   - Click "Create Web Service"

3. **Get Your Service URL:**
   - After deployment, you'll get a URL like: `https://pdf-conversion-service.onrender.com`
   - Copy this URL

4. **Update Backend Environment Variable:**
   - In your `format-a-python-backend` Vercel project
   - Add environment variable: `PDF_SERVICE_URL=https://pdf-conversion-service.onrender.com`

**Alternative: Docker Deployment on Render**

If you prefer Docker:
- Choose **Environment**: `Docker`
- Render will auto-detect the Dockerfile
- Everything else is automatic

### Option 2: Railway (No Docker Required)

**Why Railway?**
- $5 credit/month free
- No cold starts
- Auto-detects Python and LibreOffice
- Uses Nixpacks (no Docker needed)

**Steps:**

1. **Deploy on Railway:**
   - Go to https://railway.app
   - Sign up/Login with GitHub
   - Click "New Project" → "Deploy from GitHub repo"
   - Select `shyamkaarthikeyan/wordpdf`
   - Railway will auto-detect Python and install LibreOffice via `nixpacks.toml`

2. **Configure:**
   - Railway automatically sets `PORT`
   - Click "Generate Domain" in Settings to get public URL

3. **Update Backend:**
   - Add `PDF_SERVICE_URL=https://your-service.railway.app` to your backend environment variables

**Note:** Railway uses the `nixpacks.toml` file which automatically installs LibreOffice without Docker.

### Option 3: DigitalOcean App Platform

**Steps:**

1. **Deploy on DigitalOcean:**
   - Go to https://cloud.digitalocean.com/apps
   - Click "Create App"
   - Choose GitHub and select your repository
   - Select the `pdf` folder as source directory
   - Choose "Dockerfile" as build method

2. **Configure:**
   - Set HTTP Port: 8080
   - Choose Basic plan ($5/month minimum)

3. **Update Backend:**
   - Add `PDF_SERVICE_URL` to your backend environment variables

## Environment Variables

The PDF service needs these environment variables:

```bash
PORT=8080                    # Port to run on
FLASK_ENV=production        # Production mode
```

## Health Check

The service includes a health check endpoint:
```
GET /health
```

Returns:
```json
{
  "status": "healthy",
  "service": "PDF Conversion Service",
  "libreoffice": "available"
}
```

## API Endpoints

### Convert Word to PDF
```
POST /convert
Content-Type: multipart/form-data

Body:
- file: Word document (.docx)

Response:
{
  "success": true,
  "pdf_data": "base64_encoded_pdf",
  "message": "Conversion successful"
}
```

## Testing Deployment

After deployment, test with:

```bash
# Health check
curl https://your-service-url.onrender.com/health

# Test conversion (with a test.docx file)
curl -X POST https://your-service-url.onrender.com/convert \
  -F "file=@test.docx"
```

## Monitoring

### Render
- View logs in Render dashboard
- Monitor health checks
- Set up alerts for downtime

### Performance
- First request may be slow (cold start on free tier)
- Subsequent requests are faster
- Consider upgrading to paid tier for production

## Troubleshooting

### Service Not Starting
- Check logs for LibreOffice installation errors
- Verify Dockerfile builds successfully locally
- Ensure all dependencies in requirements.txt

### Conversion Failures
- Check file size limits (max 10MB recommended)
- Verify Word document is valid .docx format
- Check logs for LibreOffice errors

### Timeout Issues
- Increase timeout in gunicorn config (currently 120s)
- Consider upgrading to more powerful instance
- Optimize document complexity

## Cost Considerations

### Free Tier Limitations
- **Render Free**: 
  - Spins down after 15 minutes of inactivity
  - 750 hours/month free
  - Cold starts (10-30 seconds)
  
- **Railway Free**:
  - $5 credit/month
  - No cold starts
  - Better for development

### Production Recommendations
- Use paid tier for production ($7-25/month)
- No cold starts
- Better performance
- More resources

## Security

- CORS configured for your frontend domain
- File size limits enforced
- Temporary files cleaned up after conversion
- No file storage (stateless service)

## Scaling

For high traffic:
1. Upgrade to paid tier with more resources
2. Add horizontal scaling (multiple instances)
3. Consider adding Redis for caching
4. Implement queue system for large batches

## Support

- GitHub Issues: https://github.com/shyamkaarthikeyan/wordpdf/issues
- Check logs in deployment platform dashboard
- Review ERROR_HANDLING.md for common issues
