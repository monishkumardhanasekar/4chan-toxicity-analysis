"""
API Test Script - Verify OpenAI and Google Perspective API connectivity
"""
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config.settings import Config
import openai
from google.cloud import language_v1
import json

def test_openai_api():
    """Test OpenAI Moderation API"""
    try:
        client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Test with a sample text
        test_text = "This is a test message to check if the API is working."
        
        response = client.moderations.create(input=test_text)
        
        print("✅ OpenAI API Test Successful!")
        print(f"Response: {response.results[0]}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API Test Failed: {e}")
        return False

def test_google_perspective_api():
    """Test Google Perspective API"""
    try:
        import requests
        
        # Test with a sample text
        test_text = "This is a test message to check if the API is working."
        
        # Google Perspective API endpoint
        url = "https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze"
        
        # API request data
        data = {
            "comment": {"text": test_text},
            "requestedAttributes": {"TOXICITY": {}},
            "doNotStore": True
        }
        
        # Make API request
        response = requests.post(
            url, 
            params={"key": Config.GOOGLE_PERSPECTIVE_API_KEY}, 
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            toxicity_score = result.get('attributeScores', {}).get('TOXICITY', {}).get('summaryScore', {}).get('value', 'N/A')
            
            print("✅ Google Perspective API Test Successful!")
            print(f"Toxicity Score: {toxicity_score}")
            return True
        else:
            print(f"❌ Google Perspective API Test Failed: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
    except Exception as e:
        print(f"❌ Google Perspective API Test Failed: {e}")
        return False

def main():
    """Run all API tests"""
    print("🧪 Testing API Connectivity...")
    print("=" * 50)
    
    # Validate configuration
    try:
        Config.validate_config()
        print("✅ Configuration validation passed")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return
    
    # Test APIs
    openai_success = test_openai_api()
    google_success = test_google_perspective_api()
    
    print("=" * 50)
    if openai_success and google_success:
        print("✅ All API tests passed! Ready to proceed.")
    else:
        print("⚠️  Some API tests failed. Please check your configuration.")

if __name__ == "__main__":
    main()
