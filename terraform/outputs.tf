output "app_runner_url" {
  description = "Live demo URL for the VendorLens backend"
  value       = "https://${aws_apprunner_service.vendorlens.service_url}"
}

output "ecr_repository_url" {
  description = "ECR repository URL — use this to tag and push the Docker image"
  value       = aws_ecr_repository.vendorlens.repository_url
}

output "uploads_bucket" {
  description = "S3 bucket name for uploaded vendor proposals"
  value       = aws_s3_bucket.uploads.bucket
}
