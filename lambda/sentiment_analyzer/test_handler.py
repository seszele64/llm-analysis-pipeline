import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from . import handler
import json

class TestSentimentAnalyzer(unittest.TestCase):
    
    @patch('lambda.sentiment_analyzer.handler.boto3.client')
    @patch('lambda.sentiment_analyzer.handler.AsyncGroq')
    async def test_successful_analysis(self, mock_groq, mock_secretsmanager):
        # Mock Secrets Manager response
        mock_secretsmanager.return_value.get_secret_value.return_value = {
            'SecretString': '{"api_key": "test_key"}'
        }
        
        # Mock Groq API response
        mock_groq.return_value.chat.completions.create = AsyncMock(return_value=MagicMock(
            choices=[MagicMock(message=MagicMock(content=json.dumps({
                'sentiment': 'positive',
                'confidence': 0.95
            })))]
        ))
        
        # Test event
        event = {
            'review_text': 'I love this product!'
        }
        
        result = await handler.lambda_handler(event, None)
        self.assertEqual(result['statusCode'], 200)
        self.assertEqual(json.loads(result['body'])['sentiment'], 'positive')
    
    async def test_invalid_input(self):
        event = {}
        result = await handler.lambda_handler(event, None)
        self.assertEqual(result['statusCode'], 400)
        self.assertIn('error', json.loads(result['body']))
    
    @patch('lambda.sentiment_analyzer.handler.boto3.client')
    @patch('lambda.sentiment_analyzer.handler.AsyncGroq')
    async def test_api_failure(self, mock_groq, mock_secretsmanager):
        mock_secretsmanager.return_value.get_secret_value.return_value = {
            'SecretString': '{"api_key": "test_key"}'
        }
        
        mock_groq.return_value.chat.completions.create = AsyncMock(side_effect=Exception('API Error'))
        
        event = {
            'review_text': 'This should fail'
        }
        
        result = await handler.lambda_handler(event, None)
        self.assertEqual(result['statusCode'], 500)
        self.assertIn('error', json.loads(result['body']))

if __name__ == '__main__':
    unittest.main()
