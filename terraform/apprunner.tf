resource "aws_apprunner_auto_scaling_configuration_version" "vendorlens" {
  auto_scaling_configuration_name = "${var.app_name}-scaling"

  # Keep 1 instance warm — App Runner doesn't support true scale-to-zero.
  # Idle cost is ~$0.007/hr (~$5/mo). Run `terraform destroy` after the demo.
  min_size        = 1
  max_size        = 5
  max_concurrency = 10
}

resource "aws_apprunner_service" "vendorlens" {
  service_name = var.app_name

  source_configuration {
    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_ecr_access.arn
    }

    image_repository {
      image_identifier      = "${aws_ecr_repository.vendorlens.repository_url}:latest"
      image_repository_type = "ECR"

      image_configuration {
        port = "8000"

        runtime_environment_variables = {
          S3_BUCKET            = aws_s3_bucket.uploads.bucket
          LANGCHAIN_TRACING_V2 = "true"
          LANGCHAIN_PROJECT    = "vendorlens"
          # Comma-separated allowed CORS origins — add your Vercel URL after deploy
          ALLOWED_ORIGINS = "http://localhost:3000,https://vendorlens-beryl.vercel.app"
        }

        runtime_environment_secrets = {
          ANTHROPIC_API_KEY = aws_ssm_parameter.anthropic_api_key.arn
          LANGCHAIN_API_KEY = aws_ssm_parameter.langchain_api_key.arn
        }
      }
    }

    # Trigger a new deployment automatically when a new image is pushed to ECR
    auto_deployments_enabled = true
  }

  instance_configuration {
    cpu               = "1 vCPU"
    memory            = "2 GB"
    instance_role_arn = aws_iam_role.apprunner_instance.arn
  }

  health_check_configuration {
    path                = "/health"
    protocol            = "HTTP"
    interval            = 20
    timeout             = 5
    healthy_threshold   = 1
    unhealthy_threshold = 5
  }

  auto_scaling_configuration_arn = aws_apprunner_auto_scaling_configuration_version.vendorlens.arn
}
