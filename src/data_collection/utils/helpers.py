#!/usr/bin/env python3
"""
Utility functions for 4chan data collection.

This module provides helper functions for data processing, validation, and file operations.
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Setup logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger('fourchan_research')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def save_json(data: Dict[str, Any], filepath: str, indent: int = 2) -> bool:
    """
    Save data to JSON file with error handling.
    
    Args:
        data: Data to save
        filepath: Output file path
        indent: JSON indentation
        
    Returns:
        True if successful, False otherwise
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"Error saving JSON to {filepath}: {e}")
        return False


def load_json(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Load data from JSON file with error handling.
    
    Args:
        filepath: Input file path
        
    Returns:
        Loaded data or None if failed
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON from {filepath}: {e}")
        return None


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def format_file_size(bytes_size: int) -> str:
    """
    Format file size in bytes to human-readable string.
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f}{unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f}TB"


def validate_collection_data(data: Dict[str, Any]) -> bool:
    """
    Validate collected data structure.
    
    Args:
        data: Collection data dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_keys = ['collection_info', 'threads']
    
    # Check top-level structure
    if not all(key in data for key in required_keys):
        print(f"Missing required keys: {required_keys}")
        return False
    
    collection_info = data['collection_info']
    threads = data['threads']
    
    # Validate collection info
    info_required = ['total_posts', 'collection_date', 'board']
    if not all(key in collection_info for key in info_required):
        print(f"Missing collection_info keys: {info_required}")
        return False
    
    # Validate threads structure
    if not isinstance(threads, list):
        print("Threads must be a list")
        return False
    
    for i, thread in enumerate(threads):
        thread_required = ['thread_id', 'op_post', 'replies', 'text_posts']
        if not all(key in thread for key in thread_required):
            print(f"Thread {i} missing required keys: {thread_required}")
            return False
        
        # Validate OP post
        if thread['op_post']:
            op_required = ['post_id', 'content', 'timestamp']
            if not all(key in thread['op_post'] for key in op_required):
                print(f"Thread {i} OP post missing keys: {op_required}")
                return False
        
        # Validate replies
        if not isinstance(thread['replies'], list):
            print(f"Thread {i} replies must be a list")
            return False
        
        for j, reply in enumerate(thread['replies']):
            reply_required = ['post_id', 'content', 'timestamp']
            if not all(key in reply for key in reply_required):
                print(f"Thread {i} reply {j} missing keys: {reply_required}")
                return False
    
    return True


def calculate_collection_stats(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate statistics from collected data.
    
    Args:
        data: Collection data dictionary
        
    Returns:
        Statistics dictionary
    """
    threads = data['threads']
    
    stats = {
        'total_threads': len(threads),
        'total_posts': sum(thread['text_posts'] for thread in threads),
        'total_op_posts': sum(1 for thread in threads if thread['op_post']),
        'total_reply_posts': sum(len(thread['replies']) for thread in threads),
        'total_skipped_posts': sum(thread.get('skipped_posts', 0) for thread in threads),
        'avg_posts_per_thread': 0,
        'avg_content_length': 0,
        'countries': {},
        'content_length_distribution': {
            'short': 0,    # < 50 chars
            'medium': 0,   # 50-200 chars
            'long': 0      # > 200 chars
        }
    }
    
    if stats['total_threads'] > 0:
        stats['avg_posts_per_thread'] = stats['total_posts'] / stats['total_threads']
    
    # Analyze content and countries
    total_content_length = 0
    content_count = 0
    
    for thread in threads:
        # OP post
        if thread['op_post']:
            content = thread['op_post']['content']
            country = thread['op_post'].get('country', 'Unknown')
            
            stats['countries'][country] = stats['countries'].get(country, 0) + 1
            total_content_length += len(content)
            content_count += 1
            
            # Content length distribution
            if len(content) < 50:
                stats['content_length_distribution']['short'] += 1
            elif len(content) <= 200:
                stats['content_length_distribution']['medium'] += 1
            else:
                stats['content_length_distribution']['long'] += 1
        
        # Replies
        for reply in thread['replies']:
            content = reply['content']
            country = reply.get('country', 'Unknown')
            
            stats['countries'][country] = stats['countries'].get(country, 0) + 1
            total_content_length += len(content)
            content_count += 1
            
            # Content length distribution
            if len(content) < 50:
                stats['content_length_distribution']['short'] += 1
            elif len(content) <= 200:
                stats['content_length_distribution']['medium'] += 1
            else:
                stats['content_length_distribution']['long'] += 1
    
    if content_count > 0:
        stats['avg_content_length'] = total_content_length / content_count
    
    return stats


def create_summary_report(data: Dict[str, Any], output_file: str) -> bool:
    """
    Create a summary report of the collection.
    
    Args:
        data: Collection data dictionary
        output_file: Output report file path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        stats = calculate_collection_stats(data)
        collection_info = data['collection_info']
        
        report = {
            'collection_summary': {
                'collection_date': collection_info['collection_date'],
                'board': collection_info['board'],
                'duration_minutes': collection_info.get('collection_duration_minutes', 0),
                'status': collection_info.get('collection_status', 'unknown')
            },
            'statistics': stats,
            'data_quality': {
                'validation_passed': validate_collection_data(data),
                'completeness_score': (stats['total_posts'] / collection_info['target_posts']) * 100
            }
        }
        
        return save_json(report, output_file)
    except Exception as e:
        print(f"Error creating summary report: {e}")
        return False
