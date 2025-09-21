"""
4chan API Research Script
This script tests 4chan's JSON API endpoints to understand the data structure
and validate our collection approach before building the full system.
"""

import requests
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional

# Add config to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class FourchanAPIResearch:
    """Research class for understanding 4chan API structure"""
    
    def __init__(self):
        self.base_url = "https://a.4cdn.org"
        self.board = "pol"
        self.rate_limit_delay = 1.0  # 1 second minimum
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': '4chan Toxicity Analysis Research Project'
        })
    
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def make_request(self, url: str) -> Optional[Dict]:
        """Make a rate-limited request to 4chan API"""
        try:
            self.log(f"Making request to: {url}")
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                self.log(f"✅ Success: {response.status_code}")
                return response.json()
            else:
                self.log(f"❌ Error: {response.status_code} - {response.text}", "ERROR")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed: {e}", "ERROR")
            return None
        finally:
            # Rate limiting
            time.sleep(self.rate_limit_delay)
    
    def test_board_threads(self) -> Optional[Dict]:
        """Test the board threads endpoint"""
        self.log("🔍 Testing board threads endpoint...")
        url = f"{self.base_url}/{self.board}/threads.json"
        return self.make_request(url)
    
    def test_thread_posts(self, thread_id: int) -> Optional[Dict]:
        """Test the thread posts endpoint"""
        self.log(f"🔍 Testing thread posts endpoint for thread {thread_id}...")
        url = f"{self.base_url}/{self.board}/thread/{thread_id}.json"
        return self.make_request(url)
    
    def test_board_catalog(self) -> Optional[Dict]:
        """Test the board catalog endpoint"""
        self.log("🔍 Testing board catalog endpoint...")
        url = f"{self.base_url}/{self.board}/catalog.json"
        return self.make_request(url)
    
    def analyze_threads_structure(self, threads_data: Dict) -> None:
        """Analyze the structure of threads data"""
        self.log("📊 Analyzing threads data structure...")
        
        if not threads_data:
            self.log("❌ No threads data to analyze", "ERROR")
            return
        
        self.log(f"📈 Found {len(threads_data)} pages")
        
        total_threads = 0
        active_threads = []
        
        for page in threads_data:
            page_num = page.get('page', 'unknown')
            threads = page.get('threads', [])
            total_threads += len(threads)
            
            self.log(f"📄 Page {page_num}: {len(threads)} threads")
            
            for thread in threads:
                thread_id = thread.get('no')
                replies = thread.get('replies', 0)
                last_modified = thread.get('last_modified', 0)
                
                if replies > 10:  # Active threads
                    active_threads.append({
                        'id': thread_id,
                        'replies': replies,
                        'last_modified': last_modified
                    })
        
        self.log(f"📊 Total threads: {total_threads}")
        self.log(f"🔥 Active threads (>10 replies): {len(active_threads)}")
        
        # Sort by last modified and show top 5
        active_threads.sort(key=lambda x: x['last_modified'], reverse=True)
        self.log("🏆 Top 5 most recent active threads:")
        for i, thread in enumerate(active_threads[:5]):
            modified_time = datetime.fromtimestamp(thread['last_modified'])
            self.log(f"  {i+1}. Thread {thread['id']}: {thread['replies']} replies, last modified: {modified_time}")
        
        return active_threads
    
    def analyze_posts_structure(self, posts_data: Dict) -> None:
        """Analyze the structure of posts data"""
        self.log("📊 Analyzing posts data structure...")
        
        if not posts_data or 'posts' not in posts_data:
            self.log("❌ No posts data to analyze", "ERROR")
            return
        
        posts = posts_data['posts']
        self.log(f"📈 Found {len(posts)} posts in thread")
        
        # Analyze post structure
        if posts:
            sample_post = posts[0]
            self.log("📋 Sample post structure:")
            for key, value in sample_post.items():
                if isinstance(value, str) and len(value) > 50:
                    self.log(f"  {key}: {value[:50]}...")
                else:
                    self.log(f"  {key}: {value}")
        
        # Analyze content quality
        posts_with_content = [p for p in posts if p.get('com') and len(p.get('com', '')) > 10]
        self.log(f"📝 Posts with meaningful content (>10 chars): {len(posts_with_content)}")
        
        # Show sample content
        if posts_with_content:
            self.log("📄 Sample post content:")
            sample_content = posts_with_content[0].get('com', '')
            self.log(f"  Content: {sample_content[:200]}...")
    
    def collect_sample_posts(self, active_threads: List[Dict], max_posts: int = 20) -> List[Dict]:
        """Collect a small sample of posts for analysis"""
        self.log(f"🔍 Collecting sample of {max_posts} posts...")
        
        collected_posts = []
        posts_collected = 0
        
        for thread in active_threads:
            if posts_collected >= max_posts:
                break
                
            thread_id = thread['id']
            posts_data = self.test_thread_posts(thread_id)
            
            if posts_data and 'posts' in posts_data:
                posts = posts_data['posts']
                
                for post in posts:
                    if posts_collected >= max_posts:
                        break
                    
                    # Extract essential fields
                    if post.get('com') and len(post.get('com', '')) > 10:
                        collected_post = {
                            'post_id': post.get('no'),
                            'thread_id': thread_id,
                            'timestamp': post.get('time'),
                            'content': post.get('com'),
                            'subject': post.get('sub', ''),
                            'name': post.get('name', 'Anonymous'),
                            'trip': post.get('trip', ''),
                            'country': post.get('country', ''),
                            'filename': post.get('filename', ''),
                            'ext': post.get('ext', ''),
                            'replies': post.get('replies', 0),
                            'last_modified': post.get('last_modified', 0)
                        }
                        
                        collected_posts.append(collected_post)
                        posts_collected += 1
                        
                        self.log(f"📝 Collected post {posts_collected}: {post.get('com', '')[:50]}...")
        
        self.log(f"✅ Collected {len(collected_posts)} posts total")
        return collected_posts
    
    def save_sample_data(self, posts: List[Dict], filename: str = "sample_posts.json") -> None:
        """Save sample data to file for analysis"""
        self.log(f"💾 Saving sample data to {filename}...")
        
        sample_data = {
            'collection_info': {
                'total_posts': len(posts),
                'collection_date': datetime.now().isoformat(),
                'board': self.board,
                'rate_limit_used': True
            },
            'posts': posts
        }
        
        # Save to data directory
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        filepath = os.path.join(data_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, indent=2, ensure_ascii=False)
        
        self.log(f"✅ Sample data saved to {filepath}")
    
    def run_research(self) -> None:
        """Run the complete API research process"""
        self.log("🚀 Starting 4chan API research...")
        self.log("=" * 60)
        
        # Test board threads
        threads_data = self.test_board_threads()
        if not threads_data:
            self.log("❌ Failed to get threads data", "ERROR")
            return
        
        # Analyze threads structure
        active_threads = self.analyze_threads_structure(threads_data)
        if not active_threads:
            self.log("❌ No active threads found", "ERROR")
            return
        
        # Test thread posts with first active thread
        first_thread = active_threads[0]
        posts_data = self.test_thread_posts(first_thread['id'])
        if posts_data:
            self.analyze_posts_structure(posts_data)
        
        # Collect sample posts
        sample_posts = self.collect_sample_posts(active_threads, max_posts=20)
        
        # Save sample data
        if sample_posts:
            self.save_sample_data(sample_posts)
        
        self.log("=" * 60)
        self.log("🎉 API research completed successfully!")
        self.log(f"📊 Summary: Found {len(active_threads)} active threads, collected {len(sample_posts)} sample posts")

def main():
    """Main function to run the research"""
    try:
        researcher = FourchanAPIResearch()
        researcher.run_research()
    except KeyboardInterrupt:
        print("\n⚠️ Research interrupted by user")
    except Exception as e:
        print(f"❌ Research failed: {e}")

if __name__ == "__main__":
    main()
