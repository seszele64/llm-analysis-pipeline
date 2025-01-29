resource "aws_secretsmanager_secret" "groq_api_key" {
  name = "groq-api-key"
}

resource "aws_secretsmanager_secret_version" "groq_api_key_version" {
  secret_id     = aws_secretsmanager_secret.groq_api_key.id
  secret_string = "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"
}

resource "aws_lambda_function" "sentiment_analyzer" {
  function_name = "sentiment_analyzer"
  handler       = "handler.lambda_handler"
  runtime       = "python3.9"
  timeout       = 30

  role = aws_iam_role.lambda_role.arn

  filename         = "lambda/sentiment_analyzer/function.zip"
  source_code_hash = filebase64sha256("lambda/sentiment_analyzer/function.zip")

  environment {
    variables = {
      SECRET_NAME = "groq-api-key"
    }
  }
}

resource "aws_iam_role_policy" "lambda_secrets_manager" {
  name = "lambda_secrets_manager_policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = "*"
      }
    ]
  })
}

# DynamoDB Stream Trigger Configuration
resource "aws_dynamodb_table" "olist_order_reviews" {
  name           = "olist_order_reviews"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "review_id"

  attribute {
    name = "review_id"
    type = "S"
  }

  stream_enabled   = true
  stream_view_type = "NEW_IMAGE"
}

resource "aws_lambda_event_source_mapping" "dynamodb_trigger" {
  event_source_arn  = aws_dynamodb_table.olist_order_reviews.stream_arn
  function_name     = aws_lambda_function.sentiment_analyzer.arn
  starting_position = "LATEST"
}

resource "aws_iam_role_policy" "lambda_dynamodb_stream" {
  name = "lambda_dynamodb_stream_policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetRecords",
          "dynamodb:GetShardIterator",
          "dynamodb:DescribeStream",
          "dynamodb:ListStreams"
        ]
        Resource = aws_dynamodb_table.olist_order_reviews.stream_arn
      }
    ]
  })
}
