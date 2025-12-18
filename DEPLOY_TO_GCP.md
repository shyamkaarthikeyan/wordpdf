# Deploying to Google Cloud Run (Free Tier)

This service is optimized to run on Google Cloud Run's fully managed platform. This allows it to automatically scale to zero (costing nothing) when not in use, and scale up to handle 1000+ users instantly.

## Prerequisites
1.  **Google Cloud Account**: [Create one here](https://console.cloud.google.com/) (Free Trial includes $300 credit).
2.  **Google Cloud SDK**: You MUST install the `gcloud` CLI tool.
    *   [Download Installer for Windows](https://cloud.google.com/sdk/docs/install#windows)
    *   Run the installer and follow the setup instructions.

## Deployment Steps

We have provided a script to automate the entire process.

1.  Open your terminal (PowerShell) in this directory:
    ```powershell
    cd c:\Users\shyam\Downloads\new\pdf\wordpdf
    ```

2.  Run the deployment script:
    ```powershell
    .\deploy_to_cloud_run.ps1
    ```

3.  Follow the prompts:
    *   Sign in to your Google account when the browser opens.
    *   Enter your **Project ID** when asked (found on the Google Cloud Console dashboard).
    *   Wait for the build and deployment to finish (approx. 3-5 minutes).

4.  **Done!** The script will output a URL (e.g., `https://pdf-word-converter-xyz-uc.a.run.app`). Use this URL in your frontend application.

## Manual Commands (if script fails)

If you prefer running commands manually:

```bash
# 1. Login
gcloud auth login

# 2. Set Project
gcloud config set project YOUR_PROJECT_ID

# 3. Deploy (Builds source + Deploys)
gcloud run deploy pdf-service \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi
```
