import os
import json
import logging
import requests
import boto3
from typing import TypedDict, Optional
from botocore.exceptions import ClientError

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
        
        # Log the raw response
        logger.info(f"API Response Status Code: {response.status_code}")
        logger.info(f"API Raw Response: {response.text[:500]}...")  # Truncated for readability
        
        # Check response status
        response.raise_for_status()
        
        # Parse response
        result = response.json()
        content = json.loads(result['choices'][0]['message']['content'])
        
        logger.info(f"Parsed sentiment result: {content}")
        
        return SentimentResult(
            sentiment=content['sentiment'],
            confidence=content['confidence']
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        logger.error(f"Response content: {getattr(e.response, 'text', 'No response content')}")
        raise e
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        logger.error(f"Problematic JSON content: {response.text}")
        raise e
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {e}")
        raise e

def lambda_handler(event: dict, context: object) -> dict:
    """Main Lambda function handler"""
    try:
        logger.info("Received event: " + json.dumps(event))
        
        results = []
        # Process DynamoDB stream records
        for record in event.get('Records', []):
            logger.info(f"Processing record: {json.dumps(record)}")
            
            if record['eventName'] in ('INSERT', 'MODIFY'):
                # Extract review text from NewImage
                new_image = record['dynamodb'].get('NewImage', {})
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
