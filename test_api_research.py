#!/usr/bin/env python3
"""
Test script for 4chan API research
Run this to test the API endpoints and understand the data structure
"""

import sys
import os

# Add the src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data_collection.api_research import FourchanAPIResearch

def main():
    """Run the API research"""
    print("🧪 4chan API Research Test")
    print("=" * 50)
    
    try:
        researcher = FourchanAPIResearch()
        researcher.run_research()
    except KeyboardInterrupt:
        print("\n⚠️ Research interrupted by user")
    except Exception as e:
        print(f"❌ Research failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
