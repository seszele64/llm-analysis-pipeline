import os
import json
import logging
import requests
import boto3
import time
from typing import TypedDict, Optional
from botocore.exceptions import ClientError
from decimal import Decimal

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class SentimentResult(TypedDict):
    sentiment: str
    confidence: float

def get_secret(secret_name: str) -> str:
    """Retrieve secret from AWS Secrets Manager"""
    client = boto3.client('secretsmanager')
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return response['SecretString']
    except ClientError as e:
        logger.error(f"Error retrieving secret: {e}")
        raise e

def write_to_dynamodb(review_id: str, sentiment: str, confidence: float) -> None:
    """Write sentiment analysis results to DynamoDB"""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('classification_results')  # Make sure this matches your table name
    
    try:
        response = table.put_item(
            Item={
                'id': review_id,
                'Sentiment': sentiment,
                'Confidence': Decimal(str(confidence)),  # Convert float to Decimal
                'Timestamp': Decimal(str(int(time.time())))  # Convert timestamp to Decimal as well
            }
        )
        logger.info(f"Successfully wrote to DynamoDB for review_id: {review_id}")
    except ClientError as e:
        logger.error(f"Error writing to DynamoDB: {e}")
        raise e

def analyze_sentiment(text: str) -> SentimentResult:
    """Analyze sentiment using OpenRouter API"""
    try:
        # Initialize API configuration
        api_key = get_secret("groq-api-key")
        logger.info(f"API key retrieved successfully (length: {len(api_key)})")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Log the input text (truncated for safety)
        truncated_text = text[:100] + "..." if len(text) > 100 else text
        logger.info(f"Analyzing sentiment for text: {truncated_text}")
        
        # Prepare the request payload
        payload = {
            "model": "microsoft/phi-4",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a sentiment analyzer. You must respond with valid JSON containing exactly two fields: 'sentiment' (string: positive, negative, or neutral) and 'confidence' (float between 0 and 1)."
                },
                {
                    "role": "user",
                    "content": f"Analyze the sentiment of this text: {text}"
                }
            ],
            "temperature": 0.3,
            "max_tokens": 100,
            "response_format": {"type": "json_object"}
        }
        
        logger.info("Making API request to OpenRouter...")
        
        # Make the API request
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            logger.error(f"API request failed with status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            raise Exception(f"API request failed: {response.status_code}")
        
        # Parse the response
        response_json = response.json()
        sentiment_data = json.loads(response_json['choices'][0]['message']['content'])
        
        return {
            'sentiment': sentiment_data['sentiment'],
            'confidence': float(sentiment_data['confidence'])
        }
    except Exception as e:
        logger.error(f"Error in analyze_sentiment: {e}")
        raise e

def lambda_handler(event, context):
    """Lambda function handler"""
    try:
        results = []
        
        # Process each record in the event
        for record in event.get('Records', []):
            if record.get('eventName') == 'INSERT':
                new_image = record.get('dynamodb', {}).get('NewImage', {})
                review_text = new_image.get('review_comment_message', {}).get('S', '')
                review_id = new_image.get('review_id', {}).get('S', '')
                
                logger.info(f"Processing review_id: {review_id}")
                logger.info(f"Review text: {review_text[:200]}...")  # Log first 200 chars
                
                if not review_text:
                    logger.warning(f"No review text found for review_id: {review_id}")
                    continue
                
                # Perform sentiment analysis
                logger.info(f"Starting sentiment analysis for review_id: {review_id}")
                sentiment_result = analyze_sentiment(review_text)
                logger.info(f"Sentiment analysis completed for review_id: {review_id}. Result: {sentiment_result}")
                
                # Write results to DynamoDB
                try:
                    write_to_dynamodb(review_id, sentiment_result['sentiment'], sentiment_result['confidence'])
                except Exception as e:
                    logger.error(f"Failed to write to DynamoDB for review_id: {review_id}. Error: {e}")
                    raise e
                
                results.append({
                    'review_id': review_id,
                    'review_text': review_text,
                    'sentiment': sentiment_result['sentiment'],
                    'confidence': sentiment_result['confidence']
                })
        
        if results:
            logger.info(f"Successfully processed {len(results)} records")
            logger.info(f"Final results: {json.dumps(results)}")
            return {
                'statusCode': 200,
                'body': json.dumps({'results': results})
            }
        
        logger.warning("No valid records found to process")
        return {
            'statusCode': 400,
            'body': json.dumps("No valid records found")
        }
    except Exception as e:
        logger.error(f"Error in lambda_handler: {e}")
        logger.error(f"Full error traceback:", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error: {str(e)}")
        }
