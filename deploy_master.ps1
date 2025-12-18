# deploy_master.ps1
# The definitive deployment script.
# Manually asks for Project ID to ensure we target the one with Billing.

$GCLOUD_PATH = "C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
if (-not (Test-Path $GCLOUD_PATH)) { $GCLOUD_PATH = "gcloud" }

Clear-Host
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   GOOGLE CLOUD RUN - MASTER DEPLOYMENT" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "You must provide the Project ID where billing is ACTIVE." -ForegroundColor Yellow
Write-Host "Find it here: https://console.cloud.google.com/home/dashboard" -ForegroundColor Gray

$PROJECT_ID = Read-Host -Prompt "`nPaste your Project ID here"

if (-not $PROJECT_ID) {
    Write-Host "Error: Project ID cannot be empty." -ForegroundColor Red
    exit 1
}

Write-Host "`n1. Setting Project to '$PROJECT_ID'..." -ForegroundColor Green
& $GCLOUD_PATH config set project $PROJECT_ID

Write-Host "`n2. Enabling APIs (Run, Build, Container)..." -ForegroundColor Green
& $GCLOUD_PATH services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ API Enablement Failed." -ForegroundColor Red
    Write-Host "Reason: Billing is likely NOT enabled for '$PROJECT_ID'."
    Write-Host "Please check: https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n3. Deploying Service (This takes ~2-3 mins)..." -ForegroundColor Green
& $GCLOUD_PATH run deploy pdf-word-converter --source . --platform managed --region us-central1 --allow-unauthenticated --memory 1Gi

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
    Write-Host "Copy the Service URL from the output above." -ForegroundColor Cyan
} else {
    Write-Host "`n❌ Deployment Failed." -ForegroundColor Red
}
