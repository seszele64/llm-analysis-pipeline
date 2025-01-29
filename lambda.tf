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
      SECRET_NAME = "groq_api_key"
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
