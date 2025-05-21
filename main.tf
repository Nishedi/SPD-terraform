provider "aws" {
  region = "us-east-1"
}

# Użycie roli LabRole (dostępnej w środowisku edukacyjnym)
data "aws_iam_role" "lab_role" {
  name = "LabRole"
}

resource "aws_lambda_function" "sensor_handler" {
  filename         = "lambda.zip"
  function_name    = "sensor_handler"
  role             = data.aws_iam_role.lab_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.12"
  source_code_hash = filebase64sha256("lambda.zip")
}

resource "aws_s3_bucket" "sensor_bucket_terraform" {
  bucket = "sensor-status-bucket-terraform-kp-1023"
}

resource "aws_dynamodb_table" "sensor_status_terraform" {
  name         = "SensorStatusTable"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "sensor_id"

  attribute {
    name = "sensor_id"
    type = "S"
  }
}

resource "aws_sns_topic" "alerts" {
  name = "TemperatureAlerts"
}

resource "aws_dynamodb_table" "terraform_locks" {
  name         = "terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }
}
