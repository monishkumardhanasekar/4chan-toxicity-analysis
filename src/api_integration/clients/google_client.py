#!/usr/bin/env python3
"""
Google Perspective API Client

This module provides a client for Google's Perspective API with proper
rate limiting, error handling, and retry logic.

Author: Research Project
Date: 2025
"""

import time
import logging
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class GoogleConfig:
    """Configuration for Google Perspective API client"""
    api_key: str
    rate_limit_delay: float = 1.0  # Minimum 1 second between requests
    max_retries: int = 3
    timeout: int = 30
    max_content_length: int = 20480  # Google's limit
    base_url: str = "https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze"


@dataclass
class GoogleResult:
    """Result from Google Perspective API"""
    post_id: int
    toxicity: float
    severe_toxicity: float
    threat: float
    insult: float
    profanity: float
    identity_attack: float
    processing_time: float
    success: bool
    error_message: Optional[str] = None


class GooglePerspectiveClient:
    """
    Client for Google Perspective API.
    
    Handles rate limiting, error recovery, and result processing
    for Google's Perspective API content analysis service.
    """
    
    def __init__(self, config: GoogleConfig):
        """
        Initialize Google Perspective client.
        
        Args:
            config: GoogleConfig object with API settings
        """
        self.config = config
        self.logger = logging.getLogger('google_client')
        
        # Rate limiting
        self.last_request_time = 0
        
        self.logger.info(f"Initialized Google Perspective client with rate limit: {config.rate_limit_delay}s")
    
    def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.config.rate_limit_delay:
            sleep_time = self.config.rate_limit_delay - time_since_last
            self.logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _truncate_content(self, content: str) -> str:
        """
        Truncate content to fit Google's limits.
        
        Args:
            content: Original content
            
        Returns:
            Truncated content
        """
        if len(content) <= self.config.max_content_length:
            return content
        
        # Truncate and add indicator
        truncated = content[:self.config.max_content_length - 3] + "..."
        self.logger.warning(f"Content truncated from {len(content)} to {len(truncated)} chars")
        return truncated
    
    def analyze_text(self, post_id: int, content: str) -> GoogleResult:
        """
        Analyze a single text using Google Perspective API.
        
        Args:
            post_id: Unique identifier for the post
            content: Text content to analyze
            
        Returns:
            GoogleResult object with analysis results
        """
        start_time = time.time()
        
        # Truncate content if needed
        truncated_content = self._truncate_content(content)
        
        # Enforce rate limiting
        self._enforce_rate_limit()
        
        # Prepare request data with all supported attributes
        request_data = {
            "comment": {"text": truncated_content},
            "requestedAttributes": {
                "TOXICITY": {},
                "INSULT": {},
                "SEVERE_TOXICITY": {},
                "THREAT": {},
                "PROFANITY": {},
                "IDENTITY_ATTACK": {}
            },
            "doNotStore": True,
        }
        
        for attempt in range(self.config.max_retries):
            try:
                self.logger.debug(f"Analyzing post {post_id} with Google (attempt {attempt + 1})")
                
                # Make API request
                response = requests.post(
                    self.config.base_url,
                    params={"key": self.config.api_key},
                    json=request_data,
                    timeout=self.config.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract scores for all requested attributes
                    attribute_scores = data.get('attributeScores', {})
                    
                    toxicity = attribute_scores.get('TOXICITY', {}).get('summaryScore', {}).get('value', 0.0)
                    insult = attribute_scores.get('INSULT', {}).get('summaryScore', {}).get('value', 0.0)
                    severe_toxicity = attribute_scores.get('SEVERE_TOXICITY', {}).get('summaryScore', {}).get('value', 0.0)
                    threat = attribute_scores.get('THREAT', {}).get('summaryScore', {}).get('value', 0.0)
                    profanity = attribute_scores.get('PROFANITY', {}).get('summaryScore', {}).get('value', 0.0)
                    identity_attack = attribute_scores.get('IDENTITY_ATTACK', {}).get('summaryScore', {}).get('value', 0.0)
                    
                    processing_time = time.time() - start_time
                    
                    self.logger.debug(f"Post {post_id} analyzed successfully in {processing_time:.2f}s")
                    
                    return GoogleResult(
                        post_id=post_id,
                        toxicity=toxicity,
                        severe_toxicity=severe_toxicity,
                        threat=threat,
                        insult=insult,
                        profanity=profanity,
                        identity_attack=identity_attack,
                        processing_time=processing_time,
                        success=True
                    )
                
                elif response.status_code == 429:  # Rate limited
                    wait_time = (2 ** attempt) * self.config.rate_limit_delay
                    self.logger.warning(f"Rate limited, waiting {wait_time}s")
                    time.sleep(wait_time)
                
                else:
                    self.logger.warning(f"HTTP {response.status_code}: {response.text}")
                    if attempt < self.config.max_retries - 1:
                        wait_time = (2 ** attempt) * self.config.rate_limit_delay
                        time.sleep(wait_time)
                
            except Exception as e:
                self.logger.warning(f"Google API error for post {post_id} (attempt {attempt + 1}): {e}")
                
                if attempt < self.config.max_retries - 1:
                    # Exponential backoff
                    wait_time = (2 ** attempt) * self.config.rate_limit_delay
                    self.logger.debug(f"Retrying in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    # Final attempt failed
                    processing_time = time.time() - start_time
                    return GoogleResult(
                        post_id=post_id,
                        toxicity=0.0,
                        severe_toxicity=0.0,
                        threat=0.0,
                        insult=0.0,
                        profanity=0.0,
                        identity_attack=0.0,
                        processing_time=processing_time,
                        success=False,
                        error_message=str(e)
                    )
        
        # If we get here, all attempts failed
        processing_time = time.time() - start_time
        return GoogleResult(
            post_id=post_id,
            toxicity=0.0,
            severe_toxicity=0.0,
            threat=0.0,
            insult=0.0,
            profanity=0.0,
            identity_attack=0.0,
            processing_time=processing_time,
            success=False,
            error_message="All retry attempts failed"
        )
    
    def analyze_batch(self, posts: List[Dict[str, Any]]) -> List[GoogleResult]:
        """
        Analyze a batch of posts.
        
        Args:
            posts: List of post dictionaries with 'post_id' and 'content'
            
        Returns:
            List of GoogleResult objects
        """
        self.logger.info(f"Processing batch of {len(posts)} posts with Google Perspective")
        
        results = []
        for post in posts:
            result = self.analyze_text(post['post_id'], post['content'])
            results.append(result)
        
        # Log batch statistics
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        self.logger.info(f"Google batch complete: {successful} successful, {failed} failed")
        
        return results
    
    def get_api_info(self) -> Dict[str, Any]:
        """
        Get information about the API client.
        
        Returns:
            Dictionary with API client information
        """
        return {
            'api_name': 'Google Perspective API',
            'rate_limit_delay': self.config.rate_limit_delay,
            'max_retries': self.config.max_retries,
            'timeout': self.config.timeout,
            'max_content_length': self.config.max_content_length,
            'last_request_time': self.last_request_time
        }
