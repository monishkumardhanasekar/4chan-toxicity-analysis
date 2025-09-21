#!/usr/bin/env python3
"""
Configuration module for 4chan data collection.

This module provides configuration management and validation for the data collection system.
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv


@dataclass
class APIConfig:
    """API configuration settings"""
    openai_api_key: Optional[str] = None
    google_perspective_api_key: Optional[str] = None
    
    def __post_init__(self):
        """Load API keys from environment variables"""
        load_dotenv()
        
        if not self.openai_api_key:
            self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if not self.google_perspective_api_key:
            self.google_perspective_api_key = os.getenv('GOOGLE_PERSPECTIVE_API_KEY')


@dataclass
class CollectionConfig:
    """Data collection configuration"""
    # Collection parameters
    target_posts: int = 7500  # Middle of 5K-10K range
    min_posts: int = 5000
    max_posts: int = 10000
    
    # Rate limiting
    rate_limit_delay: float = 1.2  # Seconds between requests
    max_retries: int = 3
    timeout: int = 30
    
    # 4chan settings
    board: str = "pol"
    base_url: str = "https://a.4cdn.org"
    
    # Output settings
    output_dir: str = "src/data"
    batch_size: int = 1000  # Save progress every N posts
    
    # Quality filters
    min_content_length: int = 1  # Minimum characters (no filtering)
    skip_sticky_threads: bool = True
    skip_closed_threads: bool = True
    
    def validate(self) -> bool:
        """
        Validate configuration parameters.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        if self.target_posts < self.min_posts or self.target_posts > self.max_posts:
            print(f"Error: target_posts ({self.target_posts}) must be between {self.min_posts} and {self.max_posts}")
            return False
        
        if self.rate_limit_delay < 1.0:
            print(f"Error: rate_limit_delay ({self.rate_limit_delay}) must be at least 1.0 second")
            return False
        
        if self.max_retries < 1:
            print(f"Error: max_retries ({self.max_retries}) must be at least 1")
            return False
        
        return True


@dataclass
class AnalysisConfig:
    """Analysis configuration settings"""
    # Statistical analysis
    confidence_level: float = 0.95
    significance_threshold: float = 0.05
    
    # Correlation analysis
    correlation_method: str = "pearson"  # pearson, spearman, kendall
    
    # Visualization settings
    figure_size: tuple = (12, 8)
    dpi: int = 300
    style: str = "whitegrid"
    
    # Output settings
    output_dir: str = "results"
    report_format: str = "pdf"  # pdf, html, latex


class ConfigManager:
    """Configuration manager for the entire project"""
    
    def __init__(self):
        """Initialize configuration manager"""
        self.api = APIConfig()
        self.collection = CollectionConfig()
        self.analysis = AnalysisConfig()
    
    def validate_all(self) -> bool:
        """
        Validate all configuration sections.
        
        Returns:
            True if all configurations are valid, False otherwise
        """
        print("Validating configuration...")
        
        if not self.collection.validate():
            return False
        
        if not self.api.openai_api_key:
            print("Warning: OPENAI_API_KEY not found in environment")
        
        if not self.api.google_perspective_api_key:
            print("Warning: GOOGLE_PERSPECTIVE_API_KEY not found in environment")
        
        print("Configuration validation completed")
        return True
    
    def get_collection_config(self) -> CollectionConfig:
        """Get collection configuration"""
        return self.collection
    
    def get_api_config(self) -> APIConfig:
        """Get API configuration"""
        return self.api
    
    def get_analysis_config(self) -> AnalysisConfig:
        """Get analysis configuration"""
        return self.analysis


# Global configuration instance
config = ConfigManager()
