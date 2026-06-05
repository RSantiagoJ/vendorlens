resource "aws_ecr_repository" "vendorlens" {
  name                 = "${var.app_name}-backend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  # Allow terraform destroy to clean up the repo even if images exist
  force_delete = true
}
