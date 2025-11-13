# PDF Service Deployment Options

This service can be deployed **with or without Docker**. Choose the method that works best for you.

## Quick Comparison

| Platform | Docker Required? | Free Tier | Cold Starts | Setup Time |
|----------|-----------------|-----------|-------------|------------|
| **Render (Python)** | ❌ No | ✅ Yes | ⚠️ Yes (15 min) | 5 min |
| **Render (Docker)** | ✅ Yes | ✅ Yes | ⚠️ Yes (15 min) | 5 min |
| **Railway** | ❌ No | ✅ $5 credit | ❌ No | 3 min |
| **Heroku** | ❌ No | ❌ No ($7/mo) | ❌ No | 10 min |
| **DigitalOcean** | ✅ Yes | ❌ No ($5/mo) | ❌ No | 15 min |

## Option 1: Railway (Easiest - No Docker)

**Best for:** Quick deployment, no Docker knowledge needed

### Files Used:
- `nixpacks.toml` - Tells Railway to install LibreOffice
- `railway.json` - Railway configuration
- `Procfile` - Start command
- `requirements.txt` - Python dependencies

### Steps:

1. **Push to GitHub:**
   ```bash
   cd pdf
   git push origin master
   ```

2. **Deploy:**
   - Go to https://railway.app
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway automatically:
     - Detects Python
     - Installs LibreOffice (via nixpacks.toml)
     - Installs Python packages
     - Starts the service

3. **Get URL:**
   - Click "Generate Domain" in Settings
   - Copy the URL: `https://your-service.railway.app`

4. **Done!** No Docker, no complex setup.

### Cost:
- $5 free credit/month
- ~$0.50-2/month after credit
- No cold starts

---

## Option 2: Render with Python Buildpack (No Docker)

**Best for:** Free tier, automatic deployments

### Files Used:
- `render.yaml` - Render configuration (Python mode)
- `Aptfile` - Tells Render to install LibreOffice
- `Procfile` - Start command
- `requirements.txt` - Python dependencies

### Steps:

1. **Push to GitHub:**
   ```bash
   cd pdf
   git push origin master
   ```

2. **Deploy:**
   - Go to https://render.com
   - Click "New +" → "Web Service"
   - Connect GitHub repository
   - Configure:
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: (auto-detected from Procfile)
   - Render automatically installs LibreOffice from `Aptfile`

3. **Get URL:**
   - After deployment: `https://your-service.onrender.com`

### Cost:
- Free tier available
- 750 hours/month free
- Cold starts after 15 min inactivity

---

## Option 3: Render with Docker

**Best for:** Full control, reproducible builds

### Files Used:
- `Dockerfile` - Docker configuration
- `.dockerignore` - Optimize build
- `requirements.txt` - Python dependencies

### Steps:

1. **Push to GitHub:**
   ```bash
   cd pdf
   git push origin master
   ```

2. **Deploy:**
   - Go to https://render.com
   - Click "New +" → "Web Service"
   - Connect GitHub repository
   - Configure:
     - **Environment**: `Docker`
   - Render auto-detects Dockerfile

3. **Get URL:**
   - After deployment: `https://your-service.onrender.com`

### Cost:
- Same as Python buildpack option
- Free tier available

---

## Option 4: Heroku (No Docker)

**Best for:** Enterprise features, no cold starts

### Files Used:
- `Procfile` - Start command
- `Aptfile` - LibreOffice installation
- `runtime.txt` - Python version
- `requirements.txt` - Python dependencies

### Steps:

1. **Install Heroku CLI:**
   ```bash
   # Windows
   winget install Heroku.HerokuCLI
   
   # macOS
   brew tap heroku/brew && brew install heroku
   
   # Linux
   curl https://cli-assets.heroku.com/install.sh | sh
   ```

2. **Login and Create App:**
   ```bash
   cd pdf
   heroku login
   heroku create pdf-conversion-service
   ```

3. **Add Buildpacks:**
   ```bash
   # Add apt buildpack for LibreOffice
   heroku buildpacks:add --index 1 https://github.com/heroku/heroku-buildpack-apt
   
   # Add Python buildpack
   heroku buildpacks:add --index 2 heroku/python
   ```

4. **Deploy:**
   ```bash
   git push heroku master
   ```

5. **Get URL:**
   ```bash
   heroku open
   # URL: https://pdf-conversion-service.herokuapp.com
   ```

### Cost:
- No free tier (as of Nov 2022)
- Eco plan: $5/month
- Basic plan: $7/month
- No cold starts

---

## Option 5: DigitalOcean App Platform (Docker)

**Best for:** Production, predictable pricing

### Files Used:
- `Dockerfile` - Docker configuration
- `.dockerignore` - Optimize build

### Steps:

1. **Push to GitHub:**
   ```bash
   cd pdf
   git push origin master
   ```

2. **Deploy:**
   - Go to https://cloud.digitalocean.com/apps
   - Click "Create App"
   - Choose GitHub and select repository
   - Configure:
     - **Source Directory**: `/` (root)
     - **Dockerfile Path**: `Dockerfile`
     - **HTTP Port**: `8080`

3. **Get URL:**
   - After deployment: `https://your-service.ondigitalocean.app`

### Cost:
- Basic: $5/month
- Professional: $12/month
- No cold starts

---

## Recommended Setup by Use Case

### Development/Testing
**Use: Railway (No Docker)**
- Fastest setup
- No cold starts
- $5 free credit

### Low Traffic Production
**Use: Render Python (No Docker)**
- Free tier
- Automatic deployments
- Accept cold starts

### Medium Traffic Production
**Use: Railway or Heroku**
- No cold starts
- Reliable
- $5-7/month

### High Traffic Production
**Use: DigitalOcean or Render Pro**
- More resources
- Better performance
- $12-25/month

---

## Configuration Files Summary

### For Non-Docker Deployment:
```
pdf/
├── Procfile              # Start command (all platforms)
├── runtime.txt           # Python version (Heroku, Render)
├── requirements.txt      # Python packages (all platforms)
├── Aptfile              # LibreOffice for Render
├── aptfile              # LibreOffice for Heroku
├── nixpacks.toml        # LibreOffice for Railway
├── railway.json         # Railway config
└── render.yaml          # Render config (Python mode)
```

### For Docker Deployment:
```
pdf/
├── Dockerfile           # Docker image definition
├── .dockerignore       # Optimize Docker build
├── requirements.txt    # Python packages
└── render.yaml         # Render config (Docker mode)
```

---

## Testing Your Deployment

After deploying, test with:

```bash
# Health check
curl https://your-service-url/health

# Should return:
{
  "status": "healthy",
  "service": "PDF Conversion Service",
  "libreoffice": "available"
}
```

---

## Troubleshooting

### LibreOffice Not Found

**Render:**
- Check `Aptfile` exists
- Verify it contains `libreoffice` and `libreoffice-writer`

**Railway:**
- Check `nixpacks.toml` exists
- Verify `aptPkgs` includes LibreOffice

**Heroku:**
- Verify apt buildpack is added first
- Check `Aptfile` exists

### Service Won't Start

**Check logs:**
```bash
# Render: View in dashboard
# Railway: railway logs
# Heroku: heroku logs --tail
```

**Common issues:**
- Missing `gunicorn` in requirements.txt
- Wrong PORT environment variable
- LibreOffice not installed

### Conversion Fails

**Check:**
- LibreOffice is installed (check health endpoint)
- File size is reasonable (< 10MB)
- DOCX file is valid

---

## Next Steps

1. Choose your deployment method
2. Follow the steps above
3. Get your service URL
4. Update backend with `PDF_SERVICE_URL` environment variable
5. Test the full flow

Good luck! 🚀
