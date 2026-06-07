#!/usr/bin/env bash
# Deploy backend to AWS App Runner via ECR.
# Run from repo root: bash scripts/deploy_backend.sh
set -euo pipefail

ECR="438920434591.dkr.ecr.us-east-1.amazonaws.com/vendorlens-backend"
SERVICE_ARN="arn:aws:apprunner:us-east-1:438920434591:service/vendorlens/696cbbb5a5b74503b0819ec443fff652"
AWS="$HOME/.local/bin/aws"
REGION="us-east-1"

echo "=== VendorLens backend deploy ==="

echo "[1/4] Authenticating with ECR..."
"$AWS" ecr get-login-password --region "$REGION" \
  | sudo docker login --username AWS --password-stdin "$ECR"

echo "[2/4] Building image (linux/amd64)..."
sudo docker build --platform linux/amd64 -t vendorlens-backend backend/

echo "[3/4] Tagging and pushing to ECR..."
sudo docker tag vendorlens-backend:latest "$ECR:latest"
sudo docker push "$ECR:latest"

echo "[4/4] Triggering App Runner deployment..."
"$AWS" apprunner start-deployment \
  --service-arn "$SERVICE_ARN" \
  --region "$REGION"

echo ""
echo "Done. Watch App Runner in the AWS console (~2-3 min to go green)."
echo "Then validate: API=https://brpste4mu9.us-east-1.awsapprunner.com ./scripts/test_api.sh"
