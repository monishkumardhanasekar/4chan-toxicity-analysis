#!/usr/bin/env python3
"""
Setup script for 4chan Toxicity Analysis Project
This script helps set up the development environment and test API connectivity.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def check_git():
    """Check if Git is installed"""
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        print("✅ Git is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Git is not installed or not in PATH")
        return False

def check_env_file():
    """Check if .env file exists and has required keys"""
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env file not found")
        print("Please create a .env file with your API keys:")
        print("OPENAI_API_KEY=your_key_here")
        print("GOOGLE_APPLICATION_CREDENTIALS=path_to_credentials.json")
        return False
    
    with open(env_path) as f:
        content = f.read()
        if "OPENAI_API_KEY" not in content:
            print("❌ OPENAI_API_KEY not found in .env file")
            return False
        if "GOOGLE_APPLICATION_CREDENTIALS" not in content:
            print("❌ GOOGLE_APPLICATION_CREDENTIALS not found in .env file")
            return False
    
    print("✅ .env file found with required keys")
    return True

def install_requirements():
    """Install Python requirements"""
    try:
        print("📦 Installing Python packages...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True)
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def test_api_connectivity():
    """Test API connectivity"""
    try:
        print("🧪 Testing API connectivity...")
        result = subprocess.run([sys.executable, "src/api_test.py"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ API tests passed")
            return True
        else:
            print(f"❌ API tests failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error running API tests: {e}")
        return False

def main():
    """Main setup function"""
    print(" Setting up 4chan Toxicity Analysis Project")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Git Installation", check_git),
        ("Environment File", check_env_file),
        ("Requirements Installation", install_requirements),
        ("API Connectivity", test_api_connectivity),
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        print(f"\n🔍 Checking {check_name}...")
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ Setup completed successfully!")
        print("You're ready to start Phase 2: Data Collection")
    else:
        print("❌  Setup incomplete. Please fix the issues above.")
        print("Refer to the README.md for detailed setup instructions.")

if __name__ == "__main__":
    main()



