#!/usr/bin/env python3
"""
OpenAI Moderation API Client

This module provides a client for OpenAI's Moderation API with proper
rate limiting, error handling, and retry logic.

Author: Research Project
Date: 2025
"""

import time
import logging
from typing import Dict, List, Optional, Any
import openai
from dataclasses import dataclass


@dataclass
class OpenAIConfig:
    """Configuration for OpenAI API client"""
    api_key: str
    rate_limit_delay: float = 1.0  # Minimum 1 second between requests
    max_retries: int = 3
    timeout: int = 30
    max_content_length: int = 8192  # OpenAI's limit


@dataclass
class OpenAIResult:
    """Result from OpenAI Moderation API"""
    post_id: int
    flagged: bool
    categories: Dict[str, float]
    category_scores: Dict[str, float]
    processing_time: float
    success: bool
    error_message: Optional[str] = None


class OpenAIModerationClient:
    """
    Client for OpenAI Moderation API.
    
    Handles rate limiting, error recovery, and result processing
    for OpenAI's content moderation service.
    """
    
    def __init__(self, config: OpenAIConfig):
        """
        Initialize OpenAI client.
        
        Args:
            config: OpenAIConfig object with API settings
        """
        self.config = config
        self.logger = logging.getLogger('openai_client')
        
        # Set up OpenAI client
        self.client = openai.OpenAI(api_key=config.api_key)
        
        # Rate limiting
        self.last_request_time = 0
        
        self.logger.info(f"Initialized OpenAI client with rate limit: {config.rate_limit_delay}s")
    
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
        Truncate content to fit OpenAI's limits.
        
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
    
    def moderate_text(self, post_id: int, content: str) -> OpenAIResult:
        """
        Moderate a single text using OpenAI API.
        
        Args:
            post_id: Unique identifier for the post
            content: Text content to moderate
            
        Returns:
            OpenAIResult object with moderation results
        """
        start_time = time.time()
        
        # Truncate content if needed
        truncated_content = self._truncate_content(content)
        
        # Enforce rate limiting
        self._enforce_rate_limit()
        
        for attempt in range(self.config.max_retries):
            try:
                self.logger.debug(f"Moderating post {post_id} (attempt {attempt + 1})")
                
                # Call OpenAI API
                response = self.client.moderations.create(
                    input=truncated_content,
                    timeout=self.config.timeout
                )
                
                # Process response
                result = response.results[0]
                
                # Extract categories and scores
                categories = {}
                category_scores = {}
                
                # Convert categories to dict
                categories_dict = result.categories.model_dump()
                for category, flagged in categories_dict.items():
                    categories[category] = flagged
                
                # Convert category scores to dict
                scores_dict = result.category_scores.model_dump()
                for score, value in scores_dict.items():
                    category_scores[score] = value
                
                processing_time = time.time() - start_time
                
                self.logger.debug(f"Post {post_id} moderated successfully in {processing_time:.2f}s")
                
                return OpenAIResult(
                    post_id=post_id,
                    flagged=result.flagged,
                    categories=categories,
                    category_scores=category_scores,
                    processing_time=processing_time,
                    success=True
                )
                
            except Exception as e:
                self.logger.warning(f"OpenAI API error for post {post_id} (attempt {attempt + 1}): {e}")
                
                if attempt < self.config.max_retries - 1:
                    # Exponential backoff
                    wait_time = (2 ** attempt) * self.config.rate_limit_delay
                    self.logger.debug(f"Retrying in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    # Final attempt failed
                    processing_time = time.time() - start_time
                    return OpenAIResult(
                        post_id=post_id,
                        flagged=False,
                        categories={},
                        category_scores={},
                        processing_time=processing_time,
                        success=False,
                        error_message=str(e)
                    )
    
    def moderate_batch(self, posts: List[Dict[str, Any]]) -> List[OpenAIResult]:
        """
        Moderate a batch of posts.
        
        Args:
            posts: List of post dictionaries with 'post_id' and 'content'
            
        Returns:
            List of OpenAIResult objects
        """
        self.logger.info(f"Processing batch of {len(posts)} posts with OpenAI")
        
        results = []
        for post in posts:
            result = self.moderate_text(post['post_id'], post['content'])
            results.append(result)
        
        # Log batch statistics
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        self.logger.info(f"OpenAI batch complete: {successful} successful, {failed} failed")
        
        return results
    
    def get_api_info(self) -> Dict[str, Any]:
        """
        Get information about the API client.
        
        Returns:
            Dictionary with API client information
        """
        return {
            'api_name': 'OpenAI Moderation API',
            'rate_limit_delay': self.config.rate_limit_delay,
            'max_retries': self.config.max_retries,
            'timeout': self.config.timeout,
            'max_content_length': self.config.max_content_length,
            'last_request_time': self.last_request_time
        }
