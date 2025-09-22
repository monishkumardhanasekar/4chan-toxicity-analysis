#!/usr/bin/env python3
"""
API Integration - Main Script

This script processes collected 4chan posts through both OpenAI Moderation API
and Google Perspective API for toxicity analysis.

Usage:
    python process_apis.py [--batch-size N] [--resume-from-batch N]

Author: Research Project
Date: 2025
"""

import argparse
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.api_integration.config import config
from src.api_integration.core.batch_processor import APIBatchProcessor
from src.data_collection.utils.helpers import setup_logging, format_duration


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Process 4chan posts through OpenAI and Google Perspective APIs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python process_apis.py                           # Use default settings
    python process_apis.py --batch-size 100          # Process 100 posts per batch
    python process_apis.py --resume-from-batch 5     # Resume from batch 5
    python process_apis.py --validate-only           # Only validate configuration
        """
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Number of posts to process per batch (default: 50)'
    )
    
    parser.add_argument(
        '--resume-from-batch',
        type=int,
        default=0,
        help='Resume processing from specific batch number (default: 0)'
    )
    
    parser.add_argument(
        '--save-interval',
        type=int,
        default=10,
        help='Save progress every N batches (default: 10)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='src/data',
        help='Output directory for results (default: src/data)'
    )
    
    parser.add_argument(
        '--input-file',
        type=str,
        default='src/data/final_collection.json',
        help='Input file with collected posts (default: src/data/final_collection.json)'
    )
    
    parser.add_argument(
        '--openai-rate-limit',
        type=float,
        default=1.0,
        help='OpenAI API rate limit in seconds (default: 1.0)'
    )
    
    parser.add_argument(
        '--google-rate-limit',
        type=float,
        default=1.0,
        help='Google API rate limit in seconds (default: 1.0)'
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
        help='Only validate configuration without processing'
    )
    
    return parser.parse_args()


def validate_configuration() -> bool:
    """
    Validate API configuration.
    
    Returns:
        True if configuration is valid, False otherwise
    """
    print("Validating API configuration...")
    
    if not config.validate():
        return False
    
    print("✓ Configuration validation passed")
    print(f"✓ OpenAI API key: {'Present' if config.openai_api_key else 'Missing'}")
    print(f"✓ Google API key: {'Present' if config.google_perspective_api_key else 'Missing'}")
    print(f"✓ OpenAI rate limit: {config.openai_rate_limit}s")
    print(f"✓ Google rate limit: {config.google_rate_limit}s")
    
    return True


def main():
    """Main function"""
    args = parse_arguments()
    
    # Setup logging
    log_file = os.path.join(args.output_dir, f'api_processing_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    logger = setup_logging(args.log_level, log_file)
    
    logger.info("=" * 60)
    logger.info("API Integration - Research Project")
    logger.info("=" * 60)
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Resume from batch: {args.resume_from_batch}")
    logger.info(f"Save interval: {args.save_interval}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Input file: {args.input_file}")
    logger.info(f"OpenAI rate limit: {args.openai_rate_limit}s")
    logger.info(f"Google rate limit: {args.google_rate_limit}s")
    logger.info(f"Log level: {args.log_level}")
    
    # Update configuration with command line arguments
    config.batch_size = args.batch_size
    config.resume_from_batch = args.resume_from_batch
    config.save_interval = args.save_interval
    config.output_dir = args.output_dir
    config.openai_rate_limit = args.openai_rate_limit
    config.google_rate_limit = args.google_rate_limit
    
    # Validate configuration
    if not validate_configuration():
        logger.error("Configuration validation failed")
        return 1
    
    # Handle validation-only mode
    if args.validate_only:
        logger.info("Validation-only mode completed successfully")
        return 0
    
    # Check if input file exists
    if not os.path.exists(args.input_file):
        logger.error(f"Input file not found: {args.input_file}")
        return 1
    
    try:
        # Initialize batch processor
        logger.info("Initializing API batch processor...")
        
        openai_config = config.get_openai_config()
        google_config = config.get_google_config()
        processing_config = config.get_processing_config()
        
        processor = APIBatchProcessor(processing_config, openai_config, google_config)
        
        # Load collection data
        logger.info("Loading collection data...")
        posts = processor.load_collection_data(args.input_file)
        
        if not posts:
            logger.error("No posts found in collection data")
            return 1
        
        logger.info(f"Loaded {len(posts)} posts for processing")
        
        # Start processing
        logger.info("Starting API processing...")
        start_time = datetime.now()
        
        results = processor.process_all_posts(posts)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Final statistics
        logger.info("=" * 60)
        logger.info("API PROCESSING COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info(f"Total posts processed: {len(results)}")
        logger.info(f"Processing duration: {format_duration(duration)}")
        logger.info(f"Results saved to: {args.output_dir}/api_results.json")
        logger.info(f"Progress saved to: {args.output_dir}/api_progress.json")
        logger.info("=" * 60)
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("Processing interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
