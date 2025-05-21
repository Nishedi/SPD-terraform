terraform {
  backend "s3" {
    bucket         = "sensor-status-bucket-terraform-kp-1023"
    key            = "terraform/state.json"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
