resource "aws_ssm_parameter" "anthropic_api_key" {
  name  = "/${var.app_name}/ANTHROPIC_API_KEY"
  type  = "SecureString"
  value = var.anthropic_api_key

  lifecycle {
    # Prevent Terraform from overwriting a value updated outside of Terraform
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "langchain_api_key" {
  name  = "/${var.app_name}/LANGCHAIN_API_KEY"
  type  = "SecureString"
  value = var.langchain_api_key

  lifecycle {
    ignore_changes = [value]
  }
}
