"""
Configuration settings for 4chan Toxicity Analysis Project
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for API keys and settings"""
    
    # API Keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    GOOGLE_PERSPECTIVE_API_KEY = os.getenv('GOOGLE_PERSPECTIVE_API_KEY')
    
    # 4chan API Settings
    FOURCHAN_BASE_URL = "https://a.4cdn.org"
    FOURCHAN_BOARD = "pol"
    RATE_LIMIT_DELAY = 1.0  # seconds between requests
    
    # Data Collection Settings
    MIN_POSTS = 5000
    MAX_POSTS = 10000
    BATCH_SIZE = 100
    
    # API Rate Limits
    OPENAI_RATE_LIMIT = 60  # requests per minute
    GOOGLE_RATE_LIMIT = 100  # requests per minute
    
    # File Paths
    DATA_DIR = "data"
    PROCESSED_DATA_DIR = "processed_data"
    RESULTS_DIR = "results"
    REPORTS_DIR = "reports"
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_FILE = "project.log"
    
    @classmethod
    def validate_config(cls):
        """Validate that required configuration is present"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        if not cls.GOOGLE_PERSPECTIVE_API_KEY:
            raise ValueError("GOOGLE_PERSPECTIVE_API_KEY not found in environment variables")
        return True
