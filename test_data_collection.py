#!/usr/bin/env python3
"""
Test script for 4chan data collection
Run this to test the collection pipeline with 100 posts from 3 threads
"""

import sys
import os

# Add the src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data_collection.test_collector import FourchanDataCollector

def main():
    """Run the test collection"""
    print("🧪 4chan Data Collection Test")
    print("=" * 50)
    
    try:
        collector = FourchanDataCollector()
        
        # Collect test data
        data = collector.collect_test_data(target_posts=100)
        
        if data and data.get('posts'):
            # Save data
            collector.save_data(data)
            
            # Show sample posts
            collector.log("📄 Sample posts:")
            for i, post in enumerate(data['posts'][:5]):
                collector.log(f"  {i+1}. {'[OP]' if post['is_op'] else '[REPLY]'} {post['content'][:60]}...")
        else:
            collector.log("❌ No data collected", "ERROR")
            
    except KeyboardInterrupt:
        print("\n⚠️ Collection interrupted by user")
    except Exception as e:
        print(f"❌ Collection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
