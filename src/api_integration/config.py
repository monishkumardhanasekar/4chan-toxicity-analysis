#!/usr/bin/env python3
"""
API Integration Configuration

This module provides configuration management for API integration
with proper validation and environment variable handling.

Author: Research Project
Date: 2025
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv


@dataclass
class APIIntegrationConfig:
    """Configuration for API integration"""
    # API Keys
    openai_api_key: Optional[str] = None
    google_perspective_api_key: Optional[str] = None
    
    # Rate Limiting (minimum 1 second per project requirements)
    openai_rate_limit: float = 1.0
    google_rate_limit: float = 1.0
    
    # Processing Configuration
    batch_size: int = 50
    save_interval: int = 10
    max_retries: int = 3
    timeout: int = 30
    
    # Content Limits
    max_content_length: int = 8000
    
    # Output Configuration
    output_dir: str = "src/data"
    resume_from_batch: int = 0
    
    def __post_init__(self):
        """Load configuration from environment variables"""
        load_dotenv()
        
        if not self.openai_api_key:
            self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if not self.google_perspective_api_key:
            self.google_perspective_api_key = os.getenv('GOOGLE_PERSPECTIVE_API_KEY')
    
    def validate(self) -> bool:
        """
        Validate configuration parameters.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        errors = []
        
        # Check API keys
        if not self.openai_api_key:
            errors.append("OPENAI_API_KEY not found in environment")
        
        if not self.google_perspective_api_key:
            errors.append("GOOGLE_PERSPECTIVE_API_KEY not found in environment")
        
        # Check rate limiting (minimum 1 second per project requirements)
        if self.openai_rate_limit < 1.0:
            errors.append(f"OpenAI rate limit ({self.openai_rate_limit}) must be at least 1.0 second")
        
        if self.google_rate_limit < 1.0:
            errors.append(f"Google rate limit ({self.google_rate_limit}) must be at least 1.0 second")
        
        # Check processing parameters
        if self.batch_size < 1:
            errors.append(f"Batch size ({self.batch_size}) must be at least 1")
        
        if self.max_retries < 1:
            errors.append(f"Max retries ({self.max_retries}) must be at least 1")
        
        if self.timeout < 1:
            errors.append(f"Timeout ({self.timeout}) must be at least 1 second")
        
        # Print errors
        if errors:
            print("Configuration validation failed:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True
    
    def get_openai_config(self):
        """Get OpenAI client configuration"""
        from .clients.openai_client import OpenAIConfig
        
        return OpenAIConfig(
            api_key=self.openai_api_key,
            rate_limit_delay=self.openai_rate_limit,
            max_retries=self.max_retries,
            timeout=self.timeout,
            max_content_length=self.max_content_length
        )
    
    def get_google_config(self):
        """Get Google client configuration"""
        from .clients.google_client import GoogleConfig
        
        return GoogleConfig(
            api_key=self.google_perspective_api_key,
            rate_limit_delay=self.google_rate_limit,
            max_retries=self.max_retries,
            timeout=self.timeout,
            max_content_length=self.max_content_length
        )
    
    def get_processing_config(self):
        """Get batch processing configuration"""
        from .core.batch_processor import ProcessingConfig
        
        return ProcessingConfig(
            batch_size=self.batch_size,
            save_interval=self.save_interval,
            output_dir=self.output_dir,
            resume_from_batch=self.resume_from_batch,
            max_content_length=self.max_content_length
        )


# Global configuration instance
config = APIIntegrationConfig()
