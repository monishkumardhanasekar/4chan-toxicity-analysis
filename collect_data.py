#!/usr/bin/env python3
"""
4chan Data Collection - Main Script

This script performs the full data collection from 4chan's /pol/ board
for toxicity analysis research.

Usage:
    python collect_data.py [--target-posts N] [--output-dir DIR]

Author: Research Project
Date: 2025
"""

import argparse
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data_collection.core.fourchan_collector import FourchanCollector, CollectionConfig
from src.data_collection.config.settings import config
from src.data_collection.utils.helpers import (
    setup_logging, save_json, validate_collection_data, 
    create_summary_report, format_duration
)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Collect data from 4chan's /pol/ board for toxicity analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python collect_data.py                    # Use default settings (7500 posts)
    python collect_data.py --target-posts 5000  # Collect 5000 posts
    python collect_data.py --output-dir data/raw  # Custom output directory
        """
    )
    
    parser.add_argument(
        '--target-posts',
        type=int,
        default=7500,
        help='Target number of posts to collect (default: 7500)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='src/data',
        help='Output directory for collected data (default: src/data)'
    )
    
    parser.add_argument(
        '--rate-limit',
        type=float,
        default=1.2,
        help='Rate limit delay in seconds (default: 1.2)'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=1000,
        help='Save progress every N posts (default: 1000)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate existing data without collecting new data'
    )
    
    return parser.parse_args()


def validate_existing_data(output_dir: str) -> bool:
    """
    Validate existing collection data.
    
    Args:
        output_dir: Directory containing collection data
        
    Returns:
        True if validation successful, False otherwise
    """
    print("Validating existing collection data...")
    
    # Look for collection files
    collection_files = [
        'final_collection.json',
        'collection_progress.json',
        'test_collection.json'
    ]
    
    found_files = []
    for filename in collection_files:
        filepath = os.path.join(output_dir, filename)
        if os.path.exists(filepath):
            found_files.append(filepath)
    
    if not found_files:
        print("No collection data files found")
        return False
    
    # Validate each file
    all_valid = True
    for filepath in found_files:
        print(f"Validating {filepath}...")
        
        from src.data_collection.utils.helpers import load_json
        data = load_json(filepath)
        
        if data is None:
            print(f"Failed to load {filepath}")
            all_valid = False
            continue
        
        if validate_collection_data(data):
            print(f"✓ {filepath} is valid")
        else:
            print(f"✗ {filepath} validation failed")
            all_valid = False
    
    return all_valid


def main():
    """Main function"""
    args = parse_arguments()
    
    # Setup logging
    log_file = os.path.join(args.output_dir, f'collection_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    logger = setup_logging(args.log_level, log_file)
    
    logger.info("=" * 60)
    logger.info("4chan Data Collection - Research Project")
    logger.info("=" * 60)
    logger.info(f"Target posts: {args.target_posts}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Rate limit: {args.rate_limit}s")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Log level: {args.log_level}")
    
    # Validate configuration
    if not config.validate_all():
        logger.error("Configuration validation failed")
        return 1
    
    # Handle validation-only mode
    if args.validate_only:
        logger.info("Validation-only mode")
        if validate_existing_data(args.output_dir):
            logger.info("All data validation passed")
            return 0
        else:
            logger.error("Data validation failed")
            return 1
    
    # Create collection configuration
    collection_config = CollectionConfig(
        target_posts=args.target_posts,
        rate_limit_delay=args.rate_limit,
        output_dir=args.output_dir,
        batch_size=args.batch_size
    )
    
    # Validate collection config
    if not collection_config.validate():
        logger.error("Collection configuration validation failed")
        return 1
    
    try:
        # Initialize collector
        logger.info("Initializing collector...")
        collector = FourchanCollector(collection_config)
        
        # Start collection
        logger.info("Starting data collection...")
        start_time = datetime.now()
        
        collection_data = collector.collect_full_dataset()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Save final data
        final_filepath = os.path.join(args.output_dir, 'final_collection.json')
        json_serializable_data = collector._convert_to_json_serializable(collection_data)
        if save_json(json_serializable_data, final_filepath):
            logger.info(f"Final data saved to {final_filepath}")
        else:
            logger.error("Failed to save final data")
            return 1
        
        # Validate collected data
        logger.info("Validating collected data...")
        if validate_collection_data(json_serializable_data):
            logger.info("✓ Data validation passed")
        else:
            logger.error("✗ Data validation failed")
            return 1
        
        # Create summary report
        summary_filepath = os.path.join(args.output_dir, 'collection_summary.json')
        if create_summary_report(json_serializable_data, summary_filepath):
            logger.info(f"Summary report saved to {summary_filepath}")
        
        # Final statistics
        total_posts = collection_data['collection_info']['total_posts']
        threads_processed = collection_data['collection_info']['threads_processed']
        
        logger.info("=" * 60)
        logger.info("COLLECTION COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info(f"Total posts collected: {total_posts}")
        logger.info(f"Threads processed: {threads_processed}")
        logger.info(f"Collection duration: {format_duration(duration)}")
        logger.info(f"Average posts per thread: {total_posts/threads_processed:.1f}")
        logger.info(f"Data saved to: {final_filepath}")
        logger.info("=" * 60)
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("Collection interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Collection failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
