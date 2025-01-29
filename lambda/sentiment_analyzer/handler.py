import os
import json
import logging
import boto3
from typing import TypedDict, Optional
from botocore.exceptions import ClientError
from groq import Groq, AsyncGroq
from groq.types.chat import ChatCompletion

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

async def analyze_sentiment(text: str) -> SentimentResult:
    """Analyze sentiment using Groq API"""
    try:
        # Initialize Groq client
        api_key = get_secret("groq-api-key")
        client = AsyncGroq(api_key=api_key)
        
        # Create chat completion request
        completion: ChatCompletion = await client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": f"Analyze the sentiment of this text: {text}. Return only JSON with 'sentiment' and 'confidence' fields."
            }],
            model="deepseek-r1-distill-llama-70b",
            temperature=0.7,
            max_tokens=100,
            response_format={"type": "json_object"}
        )
        
        # Parse and return the result
        result = json.loads(completion.choices[0].message.content)
        return SentimentResult(
            sentiment=result['sentiment'],
            confidence=result['confidence']
        )
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {e}")
        raise e

async def lambda_handler(event: dict, context: object) -> dict:
    """Main Lambda function handler"""
    try:
        logger.info("Received event: " + json.dumps(event))
        
        # Extract review text from event
        review_text = event.get('review_text', '')
        if not review_text:
            raise ValueError("No review text found in event")
        
        # Perform sentiment analysis
        sentiment_result = await analyze_sentiment(review_text)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'sentiment': sentiment_result['sentiment'],
                'confidence': sentiment_result['confidence']
            })
        }
    except Exception as e:
        logger.error(f"Error in lambda_handler: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error: {str(e)}")
        }