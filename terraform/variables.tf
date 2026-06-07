variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "app_name" {
  description = "Application name used as a prefix for all resources"
  type        = string
  default     = "vendorlens"
}

variable "environment" {
  description = "Environment label (prod, staging, etc.)"
  type        = string
  default     = "prod"
}

variable "anthropic_api_key" {
  description = "Anthropic API key — stored in SSM SecureString"
  type        = string
  sensitive   = true
}

variable "langchain_api_key" {
  description = "LangSmith API key — stored in SSM SecureString"
  type        = string
  sensitive   = true
}
