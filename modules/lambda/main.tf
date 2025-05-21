resource "aws_lambda_function" "sensor_handler" {
  filename         = var.filename
  function_name    = var.function_name
  role             = var.role_arn
  handler          = var.handler
  runtime          = var.runtime
  source_code_hash = var.source_code_hash
}
