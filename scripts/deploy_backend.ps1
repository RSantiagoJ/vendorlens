# Deploy backend to AWS App Runner via ECR.
# Run from repo root: .\scripts\deploy_backend.ps1
$ErrorActionPreference = "Stop"

$ECR = "438920434591.dkr.ecr.us-east-1.amazonaws.com/vendorlens-backend"
$SERVICE_ARN = "arn:aws:apprunner:us-east-1:438920434591:service/vendorlens/696cbbb5a5b74503b0819ec443fff652"
$REGION = "us-east-1"

Write-Host "=== VendorLens backend deploy ===" -ForegroundColor Cyan

Write-Host "[1/4] Authenticating with ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR
if (-not $?) { Write-Host "ECR login failed." -ForegroundColor Red; exit 1 }

Write-Host "[2/4] Building image (linux/amd64)..."
docker build --platform linux/amd64 -t vendorlens-backend backend/
if (-not $?) { Write-Host "Docker build failed." -ForegroundColor Red; exit 1 }

Write-Host "[3/4] Tagging and pushing to ECR..."
docker tag vendorlens-backend:latest "$ECR`:latest"
docker push "$ECR`:latest"
if (-not $?) { Write-Host "Docker push failed." -ForegroundColor Red; exit 1 }

Write-Host "[4/4] Triggering App Runner deployment..."
aws apprunner start-deployment --service-arn $SERVICE_ARN --region $REGION
if (-not $?) { Write-Host "App Runner trigger failed." -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "Done. Watch App Runner in the AWS console (~2-3 min to go green)." -ForegroundColor Green
Write-Host "Health check: curl https://brpste4mu9.us-east-1.awsapprunner.com/health"
