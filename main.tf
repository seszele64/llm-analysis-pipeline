resource "aws_s3_bucket" "input_bucket" {
  bucket = "groq-llm-analysis-pipeline-input"
}

resource "aws_s3_bucket" "output_bucket" {
  bucket = "groq-llm-analysis-pipeline-output"
}

resource "aws_dynamodb_table" "classification_results" {
  name         = "classification_results"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  
  attribute {
    name = "id"
    type = "S"
  }
}

resource "aws_iam_role" "lambda_role" {
  name = "classification_lambda_role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}
