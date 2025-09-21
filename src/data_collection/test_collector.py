"""
4chan Data Collection Script - Small Test Version
This script collects 100 posts from 3 different threads to test the collection pipeline
before scaling up to the full 5,000-10,000 posts required by the project.
"""

import requests
import json
import time
import sys
import os
import re
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import unquote

# Add config to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class FourchanDataCollector:
    """Data collector for 4chan posts with proper rate limiting and error handling"""
    
    def __init__(self):
        self.base_url = "https://a.4cdn.org"
        self.board = "pol"
        self.rate_limit_delay = 1.2  # Conservative rate limiting
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': '4chan Toxicity Analysis Research Project'
        })
        
        # Collection tracking
        self.collected_posts = []
        self.processed_threads = []
        self.collection_start_time = None
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def make_request(self, url: str, max_retries: int = 3) -> Optional[Dict]:
        """Make a rate-limited request to 4chan API with retry logic"""
        for attempt in range(max_retries):
            try:
                self.log(f"Making request to: {url} (attempt {attempt + 1})")
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    self.log(f"✅ Success: {response.status_code}")
                    return response.json()
                elif response.status_code == 404:
                    self.log(f"❌ Thread not found: {response.status_code}", "WARNING")
                    return None
                else:
                    self.log(f"❌ Error: {response.status_code} - {response.text}", "ERROR")
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * self.rate_limit_delay
                        self.log(f"⏳ Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    
            except requests.exceptions.RequestException as e:
                self.log(f"❌ Request failed: {e}", "ERROR")
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * self.rate_limit_delay
                    self.log(f"⏳ Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
            finally:
                # Rate limiting
                time.sleep(self.rate_limit_delay)
        
        self.log(f"❌ Failed after {max_retries} attempts", "ERROR")
        return None
    
    def clean_html_content(self, content: str) -> str:
        """Clean HTML content and extract pure text"""
        if not content:
            return ""
        
        # Remove HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        
        # Decode HTML entities
        content = content.replace('&gt;', '>')
        content = content.replace('&lt;', '<')
        content = content.replace('&amp;', '&')
        content = content.replace('&#039;', "'")
        content = content.replace('&quot;', '"')
        
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content).strip()
        
        return content
    
    def get_active_threads(self, limit: int = 10) -> List[Dict]:
        """Get list of active threads from the board"""
        self.log(f"🔍 Getting {limit} active threads...")
        
        url = f"{self.base_url}/{self.board}/threads.json"
        threads_data = self.make_request(url)
        
        if not threads_data:
            self.log("❌ Failed to get threads data", "ERROR")
            return []
        
        active_threads = []
        for page in threads_data:
            threads = page.get('threads', [])
            for thread in threads:
                replies = thread.get('replies', 0)
                if replies > 20:  # Active threads with good content
                    active_threads.append({
                        'id': thread.get('no'),
                        'replies': replies,
                        'last_modified': thread.get('last_modified', 0)
                    })
        
        # Sort by last modified and limit
        active_threads.sort(key=lambda x: x['last_modified'], reverse=True)
        return active_threads[:limit]
    
    def collect_thread_posts(self, thread_id: int) -> List[Dict]:
        """Collect all posts from a specific thread"""
        self.log(f"📝 Collecting posts from thread {thread_id}...")
        
        url = f"{self.base_url}/{self.board}/thread/{thread_id}.json"
        thread_data = self.make_request(url)
        
        if not thread_data or 'posts' not in thread_data:
            self.log(f"❌ No posts data for thread {thread_id}", "ERROR")
            return []
        
        posts = thread_data['posts']
        self.log(f"📊 Found {len(posts)} posts in thread {thread_id}")
        
        collected_posts = []
        thread_reply_count = len(posts) - 1  # Total replies (excluding OP)
        
        for i, post in enumerate(posts):
            # Clean content
            raw_content = post.get('com', '')
            clean_content = self.clean_html_content(raw_content)
            
            # Create post data
            post_data = {
                'post_id': post.get('no'),
                'thread_id': thread_id,
                'timestamp': post.get('time', 0),
                'content': clean_content,
                'is_op': (i == 0),  # First post is OP
                'country': post.get('country', ''),
                'content_length': len(clean_content),
                'thread_reply_count': thread_reply_count
            }
            
            collected_posts.append(post_data)
            
            # Log progress
            if i == 0:
                self.log(f"📌 OP: {clean_content[:50]}...")
            else:
                self.log(f"💬 Reply {i}: {clean_content[:50]}...")
        
        self.log(f"✅ Collected {len(collected_posts)} posts from thread {thread_id}")
        return collected_posts
    
    def collect_test_data(self, target_posts: int = 100) -> Dict:
        """Collect test data from multiple threads"""
        self.log(f"🚀 Starting test data collection - Target: {target_posts} posts")
        self.log("=" * 60)
        
        self.collection_start_time = datetime.now()
        
        # Get active threads
        active_threads = self.get_active_threads(limit=10)
        if not active_threads:
            self.log("❌ No active threads found", "ERROR")
            return {}
        
        self.log(f"📈 Found {len(active_threads)} active threads")
        
        # Collect posts from threads
        total_collected = 0
        threads_processed = 0
        
        for thread in active_threads:
            if total_collected >= target_posts:
                break
                
            thread_id = thread['id']
            self.log(f"🔄 Processing thread {thread_id} ({thread['replies']} replies)")
            
            # Collect posts from this thread
            thread_posts = self.collect_thread_posts(thread_id)
            
            if thread_posts:
                self.collected_posts.extend(thread_posts)
                self.processed_threads.append({
                    'thread_id': thread_id,
                    'posts_collected': len(thread_posts),
                    'replies': thread['replies']
                })
                
                total_collected += len(thread_posts)
                threads_processed += 1
                
                self.log(f"📊 Progress: {total_collected}/{target_posts} posts collected")
            else:
                self.log(f"⚠️ No posts collected from thread {thread_id}", "WARNING")
        
        # Create collection summary
        collection_duration = (datetime.now() - self.collection_start_time).total_seconds()
        
        collection_info = {
            'total_posts': len(self.collected_posts),
            'collection_date': self.collection_start_time.isoformat(),
            'board': self.board,
            'threads_processed': threads_processed,
            'rate_limit_used': True,
            'collection_duration_minutes': round(collection_duration / 60, 2),
            'target_posts': target_posts
        }
        
        self.log("=" * 60)
        self.log(f"🎉 Test collection completed!")
        self.log(f"📊 Summary:")
        self.log(f"  - Posts collected: {len(self.collected_posts)}")
        self.log(f"  - Threads processed: {threads_processed}")
        self.log(f"  - Collection time: {collection_duration/60:.1f} minutes")
        self.log(f"  - Rate limiting: {self.rate_limit_delay}s between requests")
        
        return {
            'collection_info': collection_info,
            'posts': self.collected_posts
        }
    
    def save_data(self, data: Dict, filename: str = "test_collection.json") -> None:
        """Save collected data to file"""
        self.log(f"💾 Saving data to {filename}...")
        
        # Save to data directory
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        filepath = os.path.join(data_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.log(f"✅ Data saved to {filepath}")
        
        # Show data summary
        posts = data.get('posts', [])
        op_posts = [p for p in posts if p.get('is_op', False)]
        reply_posts = [p for p in posts if not p.get('is_op', False)]
        
        self.log(f"📋 Data Summary:")
        self.log(f"  - Total posts: {len(posts)}")
        self.log(f"  - OP posts: {len(op_posts)}")
        self.log(f"  - Reply posts: {len(reply_posts)}")
        self.log(f"  - File size: {os.path.getsize(filepath) / 1024:.1f} KB")

def main():
    """Main function to run the test collection"""
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
