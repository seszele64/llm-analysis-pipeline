resource "aws_s3_bucket" "raw_data" {
  bucket = "llm-analysis-pipeline"  # Your specified bucket name
  
  tags = {
    Environment = "dev"
    Project     = "text-classification"
  }
}

resource "aws_s3_bucket_versioning" "raw_data_versioning" {
  bucket = aws_s3_bucket.raw_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "raw_data_encryption" {
  bucket = aws_s3_bucket.raw_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block all public access
resource "aws_s3_bucket_public_access_block" "raw_data_public_access_block" {
  bucket = aws_s3_bucket.raw_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle rules for managing objects
resource "aws_s3_bucket_lifecycle_configuration" "raw_data_lifecycle" {
  bucket = aws_s3_bucket.raw_data.id

  rule {
    id     = "cleanup_old_files"
    status = "Enabled"

    expiration {
      days = 90  # Adjust retention period as needed
    }
  }
}

# Optional: Bucket Policy
resource "aws_s3_bucket_policy" "raw_data_policy" {
  bucket = aws_s3_bucket.raw_data.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "EnforceTLS"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.raw_data.arn,
          "${aws_s3_bucket.raw_data.arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}

# Enable S3 bucket logging (optional)
resource "aws_s3_bucket_logging" "raw_data_logging" {
  bucket = aws_s3_bucket.raw_data.id

  target_bucket = aws_s3_bucket.raw_data.id
  target_prefix = "log/"
}

# CORS configuration (if needed)
resource "aws_s3_bucket_cors_configuration" "raw_data_cors" {
  bucket = aws_s3_bucket.raw_data.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST"]
    allowed_origins = ["*"]  # Consider restricting this to specific domains
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# Create `raw` folder in s3
resource "aws_s3_object" "raw_folder" {
  bucket = aws_s3_bucket.raw_data.id
  key    = "raw/"
  content_type = "application/x-directory"
}

