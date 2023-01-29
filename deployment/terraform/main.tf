terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.16"
    }
  }
  required_version = ">= 1.2.0"
}

variable "stage_name" {
  default = "prod"
  type    = string
}

provider "aws" {
  region = "ap-southeast-2"
}

# Create an AWS Lambda function resource
resource "aws_lambda_function" "ml_sm_studio_sso_lambda" {
  function_name = "ml_sm_studio_sso_lambda"
  filename      = "lambda.zip"
  handler       = "lambda_function.lambda_handler"
  role          = aws_iam_role.ml_sm_studio_sso_lambda_execution_role.arn
  runtime       = "python3.9"
  timeout       = 29
}

# Create iam role for the lambda
resource "aws_iam_role" "ml_sm_studio_sso_lambda_execution_role" {
  name               = "ml_sm_studio_sso_lambda_execution_role"
  assume_role_policy = <<-EOT
    {
        "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Effect": "Allow",
                    "Sid": ""
                }
            ]
      }
EOT
}

# Create iam policy for the lambda execution role
resource "aws_iam_role_policy" "ml_sm_studio_sso_lambda_execution_policy" {
  name = "ml_sm_studio_sso_lambda_execution_policy"
  role = aws_iam_role.ml_sm_studio_sso_lambda_execution_role.id

  policy = <<-EOT
    {
        "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:*",
                        "sagemaker:CreatePresignedDomainUrl",
                        "sagemaker:DescribeUserProfile",
                        "sagemaker:CreateUserProfile"
                    ],
                    "Resource": ["arn:aws:logs:*:*:*", "arn:aws:sagemaker:*:*:*"]
                }
            ]
    }
    EOT
}

resource "aws_api_gateway_rest_api" "ml_sm_studio_sso_custom_app_api" {
  name = "ml_sm_studio_sso_custom_app_api"
}

resource "aws_api_gateway_resource" "saml" {
  rest_api_id = aws_api_gateway_rest_api.ml_sm_studio_sso_custom_app_api.id
  parent_id   = aws_api_gateway_rest_api.ml_sm_studio_sso_custom_app_api.root_resource_id
  path_part   = "saml"
}


resource "aws_api_gateway_method" "saml_post" {
  rest_api_id   = aws_api_gateway_rest_api.ml_sm_studio_sso_custom_app_api.id
  resource_id   = aws_api_gateway_resource.saml.id
  http_method   = "POST"
  authorization = "NONE"

  request_parameters = {
    "method.request.header.Content-Type" = true
  }
}

resource "aws_api_gateway_integration" "saml_integration" {
  rest_api_id             = aws_api_gateway_rest_api.ml_sm_studio_sso_custom_app_api.id
  resource_id             = aws_api_gateway_resource.saml.id
  http_method             = aws_api_gateway_method.saml_post.http_method
  integration_http_method = aws_api_gateway_method.saml_post.http_method
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.ml_sm_studio_sso_lambda.invoke_arn
}

resource "aws_api_gateway_deployment" "saml_gateway" {
  rest_api_id = aws_api_gateway_rest_api.ml_sm_studio_sso_custom_app_api.id
  stage_name  = var.stage_name
}


resource "aws_cloudwatch_log_group" "apigateway_execution_logs" {
  name              = "API-Gateway-Execution-Logs_${aws_api_gateway_rest_api.ml_sm_studio_sso_custom_app_api.id}/${var.stage_name}"
  retention_in_days = 7
}

resource "aws_api_gateway_stage" "prod" {
  stage_name    = var.stage_name
  deployment_id = aws_api_gateway_deployment.saml_gateway.id
  rest_api_id   = aws_api_gateway_rest_api.ml_sm_studio_sso_custom_app_api.id
}

resource "aws_api_gateway_method_settings" "example" {
  rest_api_id = aws_api_gateway_rest_api.ml_sm_studio_sso_custom_app_api.id
  stage_name  = aws_api_gateway_stage.prod.stage_name
  method_path = "*/*"

  settings {
    metrics_enabled = true
    logging_level   = "INFO"
  }
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ml_sm_studio_sso_lambda.function_name
  principal     = "apigateway.amazonaws.com"

  # The /*/* portion grants access from any method on any resource
  # within the API Gateway "REST API".
  source_arn = "${aws_api_gateway_rest_api.ml_sm_studio_sso_custom_app_api.execution_arn}/*/*"
}

output "api_endpoint" {
  value = aws_api_gateway_deployment.saml_gateway.invoke_url
}

