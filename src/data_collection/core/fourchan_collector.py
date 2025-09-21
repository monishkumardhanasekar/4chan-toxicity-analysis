#!/usr/bin/env python3
"""
4chan Data Collector - Core Module

This module provides the main data collection functionality for 4chan's /pol/ board.
It implements structured data collection with proper error handling, rate limiting,
and progress tracking.

Author: Research Project
Date: 2025
"""

import json
import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import requests
from dataclasses import dataclass, asdict


@dataclass
class CollectionConfig:
    """Configuration for data collection"""
    target_posts: int = 7500  # Middle of 5K-10K range
    rate_limit_delay: float = 1.2  # Seconds between requests
    max_retries: int = 3
    timeout: int = 30
    board: str = "pol"
    base_url: str = "https://a.4cdn.org"
    output_dir: str = "src/data"
    batch_size: int = 1000  # Save progress every N posts
    
    def validate(self) -> bool:
        """
        Validate configuration parameters.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        if self.target_posts < 1000:
            print(f"Error: target_posts ({self.target_posts}) must be at least 1000")
            return False
        
        if self.rate_limit_delay < 1.0:
            print(f"Error: rate_limit_delay ({self.rate_limit_delay}) must be at least 1.0 second")
            return False
        
        if self.max_retries < 1:
            print(f"Error: max_retries ({self.max_retries}) must be at least 1")
            return False
        
        return True


@dataclass
class ThreadInfo:
    """Thread information from catalog"""
    thread_id: int
    title: str
    replies_count: int
    images_count: int
    last_modified: int
    sticky: bool = False
    closed: bool = False


@dataclass
class PostData:
    """Individual post data structure"""
    post_id: int
    thread_id: int
    timestamp: int
    content: str
    country: str
    content_length: int
    post_position: int
    is_op: bool = False


@dataclass
class ThreadData:
    """Complete thread data structure"""
    thread_id: int
    thread_title: str
    op_post: Optional[PostData]
    replies: List[PostData]
    total_posts: int
    text_posts: int
    skipped_posts: int
    collection_timestamp: int


class FourchanCollector:
    """
    Main 4chan data collector class.
    
    Handles data collection from 4chan's /pol/ board with proper rate limiting,
    error handling, and structured data storage.
    """
    
    def __init__(self, config: CollectionConfig):
        """
        Initialize the collector with configuration.
        
        Args:
            config: CollectionConfig object with collection parameters
        """
        self.config = config
        self.logger = self._setup_logger()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Research Project)'
        })
        
        # Collection state
        self.collected_posts = 0
        self.processed_threads = 0
        self.start_time = None
        self.collection_data = {
            'collection_info': {},
            'threads': []
        }
        
        self.logger.info(f"Initialized collector with target: {config.target_posts} posts")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('fourchan_collector')
        logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        log_file = os.path.join(self.config.output_dir, 'collection.log')
        os.makedirs(self.config.output_dir, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def _make_request(self, url: str, max_retries: Optional[int] = None) -> Optional[Dict]:
        """
        Make a rate-limited request with retry logic.
        
        Args:
            url: URL to request
            max_retries: Maximum number of retry attempts
            
        Returns:
            JSON response data or None if failed
        """
        if max_retries is None:
            max_retries = self.config.max_retries
            
        for attempt in range(max_retries):
            try:
                self.logger.debug(f"Requesting: {url} (attempt {attempt + 1})")
                
                response = self.session.get(
                    url, 
                    timeout=self.config.timeout
                )
                
                if response.status_code == 200:
                    self.logger.debug(f"Success: {response.status_code}")
                    return response.json()
                elif response.status_code == 429:  # Rate limited
                    wait_time = (2 ** attempt) * self.config.rate_limit_delay
                    self.logger.warning(f"Rate limited, waiting {wait_time}s")
                    time.sleep(wait_time)
                else:
                    self.logger.warning(f"HTTP {response.status_code}: {url}")
                    
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request failed: {e}")
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * self.config.rate_limit_delay
                    time.sleep(wait_time)
            
            # Rate limiting
            time.sleep(self.config.rate_limit_delay)
        
        self.logger.error(f"Failed to fetch {url} after {max_retries} attempts")
        return None
    
    def _clean_html_content(self, content: str) -> str:
        """
        Clean HTML content from 4chan posts.
        
        Args:
            content: Raw HTML content
            
        Returns:
            Cleaned text content
        """
        if not content:
            return ""
        
        # Basic HTML cleaning (4chan uses minimal HTML)
        import re
        
        # Remove HTML tags but preserve content
        content = re.sub(r'<[^>]+>', '', content)
        
        # Decode HTML entities
        content = content.replace('&gt;', '>')
        content = content.replace('&lt;', '<')
        content = content.replace('&amp;', '&')
        content = content.replace('&quot;', '"')
        content = content.replace('&#039;', "'")
        
        return content.strip()
    
    def get_active_threads(self, limit: int = 50) -> List[ThreadInfo]:
        """
        Get list of active threads from 4chan catalog.
        
        Args:
            limit: Maximum number of threads to return
            
        Returns:
            List of ThreadInfo objects
        """
        url = f"{self.config.base_url}/{self.config.board}/catalog.json"
        catalog_data = self._make_request(url)
        
        if not catalog_data:
            self.logger.error("Failed to fetch catalog")
            return []
        
        threads = []
        for page in catalog_data:
            for thread_data in page.get('threads', []):
                thread_info = ThreadInfo(
                    thread_id=thread_data['no'],
                    title=thread_data.get('sub', ''),
                    replies_count=thread_data.get('replies', 0),
                    images_count=thread_data.get('images', 0),
                    last_modified=thread_data.get('last_modified', 0),
                    sticky=thread_data.get('sticky', False),
                    closed=thread_data.get('closed', False)
                )
                threads.append(thread_info)
                
                if len(threads) >= limit:
                    break
            
            if len(threads) >= limit:
                break
        
        self.logger.info(f"Found {len(threads)} active threads")
        return threads
    
    def collect_thread_data(self, thread_info: ThreadInfo) -> Optional[ThreadData]:
        """
        Collect all posts from a specific thread.
        
        Args:
            thread_info: ThreadInfo object with thread details
            
        Returns:
            ThreadData object or None if failed
        """
        thread_id = thread_info.thread_id
        self.logger.info(f"Collecting thread {thread_id} ({thread_info.replies_count} replies)")
        
        url = f"{self.config.base_url}/{self.config.board}/thread/{thread_id}.json"
        thread_data = self._make_request(url)
        
        if not thread_data or 'posts' not in thread_data:
            self.logger.error(f"No data for thread {thread_id}")
            return None
        
        posts = thread_data['posts']
        self.logger.debug(f"Found {len(posts)} posts in thread {thread_id}")
        
        # Process posts
        op_post = None
        replies = []
        skipped_posts = 0
        
        for i, post in enumerate(posts):
            # Clean content
            raw_content = post.get('com', '')
            clean_content = self._clean_html_content(raw_content)
            
            # Skip empty posts (image-only)
            if not clean_content.strip():
                skipped_posts += 1
                continue
            
            # Create post data
            post_data = PostData(
                post_id=post.get('no'),
                thread_id=thread_id,
                timestamp=post.get('time', 0),
                content=clean_content,
                country=post.get('country', ''),
                content_length=len(clean_content),
                post_position=i + 1,
                is_op=(i == 0)
            )
            
            if i == 0:
                op_post = post_data
            else:
                replies.append(post_data)
        
        # Create thread data
        thread_data_obj = ThreadData(
            thread_id=thread_id,
            thread_title=thread_info.title,
            op_post=op_post,
            replies=replies,
            total_posts=len(posts),
            text_posts=len(replies) + (1 if op_post else 0),
            skipped_posts=skipped_posts,
            collection_timestamp=int(time.time())
        )
        
        self.logger.info(f"Collected {thread_data_obj.text_posts} posts from thread {thread_id}")
        if skipped_posts > 0:
            self.logger.debug(f"Skipped {skipped_posts} image-only posts")
        
        return thread_data_obj
    
    def save_progress(self, filename: str = "collection_progress.json") -> None:
        """
        Save current collection progress to file.
        
        Args:
            filename: Name of the progress file
        """
        filepath = os.path.join(self.config.output_dir, filename)
        
        # Convert dataclasses to dicts for JSON serialization
        progress_data = {
            'collection_info': {
                'total_posts': self.collected_posts,
                'threads_processed': self.processed_threads,
                'collection_date': datetime.now().isoformat(),
                'board': self.config.board,
                'rate_limit_used': True,
                'collection_duration_minutes': (time.time() - self.start_time) / 60 if self.start_time else 0,
                'target_posts': self.config.target_posts
            },
            'threads': []
        }
        
        # Convert thread data to dicts
        for thread in self.collection_data['threads']:
            thread_dict = asdict(thread)
            progress_data['threads'].append(thread_dict)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Progress saved: {self.collected_posts}/{self.config.target_posts} posts")
    
    def _convert_to_json_serializable(self, data: Dict) -> Dict:
        """
        Convert dataclass objects to JSON-serializable dictionaries.
        
        Args:
            data: Collection data dictionary
            
        Returns:
            JSON-serializable dictionary
        """
        json_data = {
            'collection_info': data['collection_info'],
            'threads': []
        }
        
        # Convert thread data to dicts
        for thread in data['threads']:
            thread_dict = asdict(thread)
            json_data['threads'].append(thread_dict)
        
        return json_data
    
    def collect_full_dataset(self) -> Dict:
        """
        Collect the full dataset (5,000-10,000 posts).
        
        Returns:
            Complete collection data dictionary
        """
        self.start_time = time.time()
        self.logger.info(f"Starting full collection - Target: {self.config.target_posts} posts")
        self.logger.info("=" * 60)
        
        # Get active threads
        threads = self.get_active_threads(limit=100)  # Get more threads for selection
        if not threads:
            self.logger.error("No threads found")
            return {}
        
        # Sort threads by activity (replies count)
        threads.sort(key=lambda x: x.replies_count, reverse=True)
        
        # Collect from threads until target reached
        for thread_info in threads:
            if self.collected_posts >= self.config.target_posts:
                break
            
            # Skip sticky/closed threads for better data quality
            if thread_info.sticky or thread_info.closed:
                continue
            
            # Collect thread data
            thread_data = self.collect_thread_data(thread_info)
            
            if thread_data and thread_data.text_posts > 0:
                self.collection_data['threads'].append(thread_data)
                self.collected_posts += thread_data.text_posts
                self.processed_threads += 1
                
                self.logger.info(f"Progress: {self.collected_posts}/{self.config.target_posts} posts")
                
                # Save progress periodically
                if self.collected_posts % self.config.batch_size == 0:
                    self.save_progress()
            else:
                self.logger.warning(f"No posts collected from thread {thread_info.thread_id}")
        
        # Final save
        self.save_progress("final_collection.json")
        
        # Create final collection info
        collection_duration = time.time() - self.start_time
        self.collection_data['collection_info'] = {
            'total_posts': self.collected_posts,
            'threads_processed': self.processed_threads,
            'collection_date': datetime.now().isoformat(),
            'board': self.config.board,
            'rate_limit_used': True,
            'collection_duration_minutes': collection_duration / 60,
            'target_posts': self.config.target_posts,
            'collection_status': 'completed'
        }
        
        self.logger.info("=" * 60)
        self.logger.info("Collection completed!")
        self.logger.info(f"Total posts: {self.collected_posts}")
        self.logger.info(f"Threads processed: {self.processed_threads}")
        self.logger.info(f"Duration: {collection_duration/60:.1f} minutes")
        
        return self.collection_data
