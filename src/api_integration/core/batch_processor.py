#!/usr/bin/env python3
"""
API Batch Processing System

This module handles batch processing of posts through both APIs
with progress tracking, error handling, and resumability.

Author: Research Project
Date: 2025
"""

import json
import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

from ..clients.openai_client import OpenAIModerationClient, OpenAIConfig, OpenAIResult
from ..clients.google_client import GooglePerspectiveClient, GoogleConfig, GoogleResult


@dataclass
class ProcessingConfig:
    """Configuration for batch processing"""
    batch_size: int = 50  # Posts per batch
    save_interval: int = 10  # Save progress every N batches
    output_dir: str = "src/data"
    resume_from_batch: int = 0
    max_content_length: int = 8000  # Truncate longer posts


@dataclass
class ProcessingStats:
    """Statistics for processing progress"""
    total_posts: int = 0
    processed_posts: int = 0
    successful_posts: int = 0
    failed_posts: int = 0
    openai_success: int = 0
    google_success: int = 0
    start_time: float = 0
    current_batch: int = 0
    total_batches: int = 0


class APIBatchProcessor:
    """
    Handles batch processing of posts through both APIs.
    
    Provides progress tracking, error recovery, and resumability.
    """
    
    def __init__(self, config: ProcessingConfig, openai_config: OpenAIConfig, google_config: GoogleConfig):
        """
        Initialize batch processor.
        
        Args:
            config: Processing configuration
            openai_config: OpenAI API configuration
            google_config: Google API configuration
        """
        self.config = config
        
        # Setup dedicated API processing log file
        self._setup_api_logging()
        
        # Initialize API clients
        self.openai_client = OpenAIModerationClient(openai_config)
        self.google_client = GooglePerspectiveClient(google_config)
        
        # Processing state
        self.stats = ProcessingStats()
        self.results = []
        
        # Ensure output directory exists
        os.makedirs(config.output_dir, exist_ok=True)
        
        self.logger.info(f"Initialized batch processor with batch size: {config.batch_size}")
    
    def _setup_api_logging(self):
        """Setup dedicated logging for API processing phase"""
        # Create API processing log file
        log_file = os.path.join(self.config.output_dir, 'api_processing.log')
        
        # Setup logger for API processing
        self.logger = logging.getLogger('api_processing')
        self.logger.setLevel(logging.INFO)
        
        # Remove any existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create file handler for API processing log
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
        
        # Log processing start
        self.logger.info("=" * 80)
        self.logger.info("API PROCESSING PHASE STARTED")
        self.logger.info("=" * 80)
    
    def _log_progress_update(self, threshold: int = 100):
        """Log progress update with thresholds"""
        if self.stats.processed_posts % threshold == 0 and self.stats.processed_posts > 0:
            # Calculate progress metrics
            progress_percent = (self.stats.processed_posts / self.stats.total_posts) * 100
            success_rate = (self.stats.successful_posts / self.stats.processed_posts) * 100 if self.stats.processed_posts > 0 else 0
            
            # Calculate time metrics
            elapsed_time = time.time() - self.stats.start_time
            elapsed_hours = elapsed_time / 3600
            
            # Estimate remaining time
            if self.stats.processed_posts > 0:
                avg_time_per_post = elapsed_time / self.stats.processed_posts
                remaining_posts = self.stats.total_posts - self.stats.processed_posts
                estimated_remaining_time = remaining_posts * avg_time_per_post
                estimated_remaining_hours = estimated_remaining_time / 3600
            else:
                estimated_remaining_hours = 0
            
            # Log progress update
            self.logger.info(f"PROGRESS UPDATE: {self.stats.processed_posts:,} posts processed ({progress_percent:.1f}% complete)")
            self.logger.info(f"  Success Rate: {success_rate:.1f}% ({self.stats.successful_posts:,} successful, {self.stats.failed_posts:,} failed)")
            self.logger.info(f"  Time Elapsed: {elapsed_hours:.1f} hours")
            self.logger.info(f"  Estimated Time Remaining: {estimated_remaining_hours:.1f} hours")
            self.logger.info(f"  Google API Success: {self.stats.google_success:,}")
            self.logger.info(f"  OpenAI API Success: {self.stats.openai_success:,}")
            self.logger.info("-" * 60)
    
    def _log_milestone(self, milestone: int):
        """Log major milestone"""
        progress_percent = (self.stats.processed_posts / self.stats.total_posts) * 100
        elapsed_time = time.time() - self.stats.start_time
        elapsed_hours = elapsed_time / 3600
        
        self.logger.info("=" * 80)
        self.logger.info(f"MILESTONE REACHED: {milestone:,} POSTS PROCESSED")
        self.logger.info("=" * 80)
        self.logger.info(f"Progress: {progress_percent:.1f}% complete ({self.stats.processed_posts:,}/{self.stats.total_posts:,})")
        self.logger.info(f"Success Rate: {(self.stats.successful_posts/self.stats.processed_posts)*100:.1f}%")
        self.logger.info(f"Time Elapsed: {elapsed_hours:.1f} hours")
        self.logger.info(f"Google API Success: {self.stats.google_success:,}")
        self.logger.info(f"OpenAI API Success: {self.stats.openai_success:,}")
        
        # Calculate processing rate
        posts_per_hour = self.stats.processed_posts / elapsed_hours if elapsed_hours > 0 else 0
        self.logger.info(f"Processing Rate: {posts_per_hour:.1f} posts/hour")
        
        # Estimate completion time
        if self.stats.processed_posts > 0:
            avg_time_per_post = elapsed_time / self.stats.processed_posts
            remaining_posts = self.stats.total_posts - self.stats.processed_posts
            estimated_remaining_time = remaining_posts * avg_time_per_post
            estimated_remaining_hours = estimated_remaining_time / 3600
            self.logger.info(f"Estimated Time Remaining: {estimated_remaining_hours:.1f} hours")
        
        self.logger.info("=" * 80)
    
    def load_collection_data(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Load collected data and extract posts for processing.
        
        Args:
            filepath: Path to final_collection.json
            
        Returns:
            List of post dictionaries
        """
        self.logger.info(f"Loading collection data from {filepath}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            posts = []
            
            # Extract posts from threads
            for thread in data.get('threads', []):
                # Add OP post
                if thread.get('op_post'):
                    op_post = thread['op_post']
                    posts.append({
                        'post_id': op_post['post_id'],
                        'content': op_post['content'],
                        'thread_id': op_post['thread_id'],
                        'is_op': True,
                        'timestamp': op_post['timestamp'],
                        'country': op_post.get('country', ''),
                        'content_length': op_post['content_length']
                    })
                
                # Add replies
                for reply in thread.get('replies', []):
                    posts.append({
                        'post_id': reply['post_id'],
                        'content': reply['content'],
                        'thread_id': reply['thread_id'],
                        'is_op': False,
                        'timestamp': reply['timestamp'],
                        'country': reply.get('country', ''),
                        'content_length': reply['content_length']
                    })
            
            self.stats.total_posts = len(posts)
            self.stats.total_batches = (len(posts) + self.config.batch_size - 1) // self.config.batch_size
            
            self.logger.info(f"Loaded {len(posts)} posts for processing")
            self.logger.info(f"Will process in {self.stats.total_batches} batches")
            
            return posts
            
        except Exception as e:
            self.logger.error(f"Failed to load collection data: {e}")
            raise
    
    def load_progress(self) -> bool:
        """
        Load previous progress if resuming.
        
        Returns:
            True if progress loaded successfully, False otherwise
        """
        progress_file = os.path.join(self.config.output_dir, 'api_progress.json')
        
        if not os.path.exists(progress_file):
            self.logger.info("No previous progress found, starting fresh")
            return False
        
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
            
            self.stats.processed_posts = progress_data.get('processed_posts', 0)
            self.stats.successful_posts = progress_data.get('successful_posts', 0)
            self.stats.failed_posts = progress_data.get('failed_posts', 0)
            self.stats.openai_success = progress_data.get('openai_success', 0)
            self.stats.google_success = progress_data.get('google_success', 0)
            self.stats.current_batch = progress_data.get('current_batch', 0)
            
            self.logger.info(f"Resuming from batch {self.stats.current_batch}")
            self.logger.info(f"Previously processed: {self.stats.processed_posts} posts")
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Failed to load progress: {e}")
            return False
    
    def save_progress(self) -> None:
        """Save current progress to file"""
        progress_file = os.path.join(self.config.output_dir, 'api_progress.json')
        
        progress_data = {
            'processed_posts': self.stats.processed_posts,
            'successful_posts': self.stats.successful_posts,
            'failed_posts': self.stats.failed_posts,
            'openai_success': self.stats.openai_success,
            'google_success': self.stats.google_success,
            'current_batch': self.stats.current_batch,
            'last_saved': datetime.now().isoformat(),
            'processing_config': asdict(self.config)
        }
        
        try:
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"Progress saved: {self.stats.processed_posts}/{self.stats.total_posts} posts")
            
        except Exception as e:
            self.logger.error(f"Failed to save progress: {e}")
    
    def load_existing_results(self) -> List[Dict[str, Any]]:
        """Load existing results if resuming"""
        results_file = os.path.join(self.config.output_dir, 'api_results.json')
        
        if not os.path.exists(results_file):
            return []
        
        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            existing_results = data.get('results', [])
            self.logger.info(f"Loaded {len(existing_results)} existing results")
            return existing_results
            
        except Exception as e:
            self.logger.warning(f"Failed to load existing results: {e}")
            return []
    
    def save_results(self) -> None:
        """Save current results to file (append mode for resume)"""
        results_file = os.path.join(self.config.output_dir, 'api_results.json')
        
        # Load existing results if resuming
        existing_results = []
        if self.config.resume_from_batch > 0:
            existing_results = self.load_existing_results()
        
        # Combine existing and new results
        all_results = existing_results + self.results
        
        results_data = {
            'processing_info': {
                'total_posts': self.stats.total_posts,
                'processed_posts': self.stats.processed_posts,
                'successful_posts': self.stats.successful_posts,
                'failed_posts': self.stats.failed_posts,
                'openai_success_rate': self.stats.openai_success / max(self.stats.processed_posts, 1),
                'google_success_rate': self.stats.google_success / max(self.stats.processed_posts, 1),
                'processing_duration_minutes': (time.time() - self.stats.start_time) / 60,
                'completed_at': datetime.now().isoformat()
            },
            'results': all_results
        }
        
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Results saved to {results_file} ({len(all_results)} total results)")
            
        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")
    
    def process_batch(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a batch of posts through both APIs with Google API as primary filter.
        
        Args:
            posts: List of post dictionaries
            
        Returns:
            List of results with both API scores
        """
        batch_start_time = time.time()
        
        self.logger.info(f"Processing batch {self.stats.current_batch + 1}/{self.stats.total_batches} "
                        f"({len(posts)} posts)")
        
        # Step 1: Process with Google API first (all attributes)
        self.logger.debug("Processing with Google Perspective API")
        google_results = self.google_client.analyze_batch(posts)
        
        # Step 2: Process with OpenAI only for posts where Google succeeded
        self.logger.debug("Processing with OpenAI Moderation API")
        openai_candidates = []
        openai_candidate_indices = []
        
        for i, google_result in enumerate(google_results):
            if google_result.success:
                openai_candidates.append(posts[i])
                openai_candidate_indices.append(i)
        
        self.logger.info(f"Google API success: {len(openai_candidates)}/{len(posts)} posts "
                        f"({len(openai_candidates)/len(posts)*100:.1f}%)")
        
        openai_results = []
        if openai_candidates:
            openai_results = self.openai_client.moderate_batch(openai_candidates)
        
        # Step 3: Combine results
        batch_results = []
        openai_result_index = 0
        
        for i, post in enumerate(posts):
            google_result = google_results[i] if i < len(google_results) else None
            
            # Get OpenAI result if available
            openai_result = None
            if i in openai_candidate_indices and openai_result_index < len(openai_results):
                openai_result = openai_results[openai_result_index]
                openai_result_index += 1
            
            # Create combined result
            result = {
                'post_id': post['post_id'],
                'content': post['content'],
                'thread_id': post['thread_id'],
                'is_op': post['is_op'],
                'timestamp': post['timestamp'],
                'country': post['country'],
                'content_length': post['content_length'],
                'google_result': asdict(google_result) if google_result else None,
                'openai_result': asdict(openai_result) if openai_result else None,
                'processing_timestamp': datetime.now().isoformat()
            }
            
            batch_results.append(result)
            
            # Update statistics
            self.stats.processed_posts += 1
            
            if openai_result and openai_result.success:
                self.stats.openai_success += 1
            
            if google_result and google_result.success:
                self.stats.google_success += 1
            
            if (openai_result and openai_result.success) or (google_result and google_result.success):
                self.stats.successful_posts += 1
            else:
                self.stats.failed_posts += 1
            
            # Log progress updates with thresholds
            self._log_progress_update(threshold=100)  # Every 100 posts
            
            # Log milestones
            if self.stats.processed_posts in [1000, 2000, 3000, 4000, 5000, 6000, 7000]:
                self._log_milestone(self.stats.processed_posts)
        
        batch_duration = time.time() - batch_start_time
        self.logger.info(f"Batch {self.stats.current_batch + 1} completed in {batch_duration:.2f}s")
        self.logger.info(f"  Google success: {sum(1 for r in google_results if r.success)}/{len(google_results)}")
        self.logger.info(f"  OpenAI success: {sum(1 for r in openai_results if r.success)}/{len(openai_results)}")
        
        return batch_results
    
    def process_all_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process all posts through both APIs.
        
        Args:
            posts: List of all posts to process
            
        Returns:
            Complete results list
        """
        self.stats.start_time = time.time()
        
        # Load previous progress if resuming
        if self.config.resume_from_batch > 0:
            self.load_progress()
            # Load existing results when resuming
            self.results = self.load_existing_results()
        
        # Start from the specified batch
        start_batch = self.stats.current_batch
        
        self.logger.info("=" * 80)
        self.logger.info("STARTING API PROCESSING")
        self.logger.info("=" * 80)
        self.logger.info(f"Total posts to process: {self.stats.total_posts:,}")
        self.logger.info(f"Batch size: {self.config.batch_size}")
        self.logger.info(f"Total batches: {self.stats.total_batches:,}")
        self.logger.info(f"Starting from batch: {start_batch + 1}")
        self.logger.info(f"Resume mode: {'Yes' if self.config.resume_from_batch > 0 else 'No'}")
        self.logger.info(f"Rate limiting: 1 request per second (Google API compliance)")
        self.logger.info("=" * 80)
        
        try:
            # Process posts in batches
            for batch_num in range(start_batch, self.stats.total_batches):
                self.stats.current_batch = batch_num
                
                # Get batch of posts
                start_idx = batch_num * self.config.batch_size
                end_idx = min(start_idx + self.config.batch_size, len(posts))
                batch_posts = posts[start_idx:end_idx]
                
                # Process batch
                batch_results = self.process_batch(batch_posts)
                self.results.extend(batch_results)
                
                # Save progress periodically
                if (batch_num + 1) % self.config.save_interval == 0:
                    self.save_progress()
                    self.save_results()
                
                # Log progress
                progress_pct = (self.stats.processed_posts / self.stats.total_posts) * 100
                self.logger.info(f"Progress: {self.stats.processed_posts}/{self.stats.total_posts} "
                               f"({progress_pct:.1f}%)")
            
            # Final save
            self.save_progress()
            self.save_results()
            
            # Final statistics
            total_duration = time.time() - self.stats.start_time
            total_hours = total_duration / 3600
            
            self.logger.info("=" * 80)
            self.logger.info("API PROCESSING COMPLETED SUCCESSFULLY")
            self.logger.info("=" * 80)
            self.logger.info(f"Total posts processed: {self.stats.processed_posts:,}")
            self.logger.info(f"Successful posts: {self.stats.successful_posts:,}")
            self.logger.info(f"Failed posts: {self.stats.failed_posts:,}")
            self.logger.info(f"Success rate: {(self.stats.successful_posts/self.stats.processed_posts)*100:.1f}%")
            self.logger.info(f"Google API success: {self.stats.google_success:,}")
            self.logger.info(f"OpenAI API success: {self.stats.openai_success:,}")
            self.logger.info(f"Total processing time: {total_hours:.1f} hours")
            self.logger.info(f"Average processing rate: {self.stats.processed_posts/total_hours:.1f} posts/hour")
            self.logger.info(f"Data saved to: {self.config.output_dir}/api_results.json")
            self.logger.info("=" * 80)
            self.logger.info("API PROCESSING PHASE COMPLETED")
            self.logger.info("=" * 80)
            
            return self.results
            
        except KeyboardInterrupt:
            self.logger.warning("Processing interrupted by user")
            self.save_progress()
            self.save_results()
            raise
        except Exception as e:
            self.logger.error(f"Processing failed: {e}")
            self.save_progress()
            self.save_results()
            raise
