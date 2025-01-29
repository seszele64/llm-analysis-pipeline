resource "aws_dynamodb_table" "olist_orders" {
  name         = "olist_orders"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "order_id"
  
  attribute {
    name = "order_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "olist_order_reviews" {
  name         = "olist_order_reviews"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "order_id"
  stream_enabled = true
  stream_view_type = "NEW_AND_OLD_IMAGES"
  
  attribute {
    name = "order_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "olist_order_items" {
  name         = "olist_order_items"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "order_id"
  range_key    = "product_id"
  
  attribute {
    name = "order_id"
    type = "S"
  }
  
  attribute {
    name = "product_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "olist_order_payments" {
  name         = "olist_order_payments"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "order_id"
  
  attribute {
    name = "order_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "olist_order_customer" {
  name         = "olist_order_customer"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "customer_id"
  
  attribute {
    name = "customer_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "olist_products" {
  name         = "olist_products"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "product_id"
  
  attribute {
    name = "product_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "olist_sellers" {
  name         = "olist_sellers"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "seller_id"
  
  attribute {
    name = "seller_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "olist_geolocation" {
  name         = "olist_geolocation"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "zip_code_prefix"
  
  attribute {
    name = "zip_code_prefix"
    type = "S"
  }
}

output "olist_order_reviews_stream_arn" {
  value = aws_dynamodb_table.olist_order_reviews.stream_arn
}
