#!/usr/bin/env python3
"""
RoomMakeover.AI Setup Script
This script helps set up the project environment and dependencies
"""

import os
import sys
import subprocess
import urllib.request
from pathlib import Path

def print_header():
    """Print welcome header"""
    print("🏡 RoomMakeover.AI - Setup Script")
    print("=" * 50)
    print("This script will help you set up the complete system")
    print()

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    
    if sys.version_info < (3, 9):
        print(f"❌ Python 3.9+ required. Current: {sys.version}")
        print("Please upgrade Python and try again.")
        return False
    
    print(f"✅ Python {sys.version.split()[0]} - Compatible")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing dependencies...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        print("✅ Pip upgraded successfully")
        
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ All dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("Try running manually: pip install -r requirements.txt")
        return False

def setup_environment():
    """Set up environment variables"""
    print("\n🌍 Setting up environment...")
    
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ .env file already exists")
        with open(env_file, 'r') as f:
            content = f.read()
            if "GEMINI_API_KEY" in content:
                print("✅ GEMINI_API_KEY found in .env")
                return True
    
    print("\n🔑 Gemini API Key Setup")
    print("To use this system, you need a Gemini API key from Google AI Studio")
    print("Get your free API key at: https://makersuite.google.com/app")
    print()
    
    api_key = input("Enter your Gemini API key (or press Enter to skip): ").strip()
    
    if api_key:
        with open(env_file, 'a') as f:
            f.write(f"\n# Gemini AI Configuration\n")
            f.write(f"GEMINI_API_KEY={api_key}\n")
        print("✅ API key saved to .env file")
        return True
    else:
        print("⚠️  API key not provided. You can add it later to the .env file")
        with open(env_file, 'a') as f:
            f.write(f"\n# Gemini AI Configuration\n")
            f.write(f"# GEMINI_API_KEY=your_api_key_here\n")
        return False

def download_yolo_model():
    """Download YOLOv8n model if not present"""
    print("\n🔍 Checking YOLOv8 model...")
    
    model_path = Path("yolov8n.pt")
    
    if model_path.exists():
        model_size = model_path.stat().st_size / (1024 * 1024)
        print(f"✅ YOLOv8n model found ({model_size:.1f} MB)")
        return True
    
    print("📥 YOLOv8n model not found. It will be downloaded automatically on first run.")
    print("This is normal - the model will download when you first use the system.")
    return True

def create_sample_structure():
    """Create sample directory structure"""
    print("\n📁 Creating directory structure...")
    
    directories = [
        "sample_data",
        "app/utils",
        "tests"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {directory}/")
    
    # Create sample .gitignore if not exists
    gitignore_path = Path(".gitignore")
    if not gitignore_path.exists():
        gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv/

# Environment
.env
.env.local

# Models
*.pt
!yolov8n.pt

# Data
sample_data/*.jpg
sample_data/*.jpeg
sample_data/*.png

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Temporary files
temp/
tmp/
"""
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content.strip())
        print("✅ Created .gitignore file")
    
    return True

def run_test():
    """Run a quick system test"""
    print("\n🧪 Running system test...")
    
    try:
        result = subprocess.run([sys.executable, "test_system.py"], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ System test passed!")
            return True
        else:
            print(f"⚠️  System test had issues:\n{result.stdout}\n{result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  System test timed out (this is normal if downloading models)")
        return False
    except Exception as e:
        print(f"⚠️  Could not run system test: {e}")
        return False

def print_next_steps(api_key_configured):
    """Print instructions for next steps"""
    print("\n🎉 Setup Complete!")
    print("=" * 30)
    
    if not api_key_configured:
        print("⚠️  IMPORTANT: Add your Gemini API key to the .env file:")
        print("   1. Get a free API key: https://makersuite.google.com/app")
        print("   2. Add to .env file: GEMINI_API_KEY=your_key_here")
        print()
    
    print("🚀 Ready to start! Choose your interface:")
    print()
    print("   Streamlit Web App (Recommended):")
    print("   └─ streamlit run streamlit_app.py")
    print("   └─ Opens at: http://localhost:8501")
    print()
    print("   FastAPI Backend (For developers):")
    print("   └─ python app/main.py")
    print("   └─ API docs at: http://localhost:8000/docs")
    print()
    print("📸 Sample images:")
    print("   └─ Add room images to sample_data/ for testing")
    print()
    print("🧪 Test system:")
    print("   └─ python test_system.py")
    print()
    print("📚 Full documentation: README.md")

def main():
    """Main setup function"""
    print_header()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed at dependency installation")
        sys.exit(1)
    
    # Setup environment
    api_key_configured = setup_environment()
    
    # Download YOLO model
    download_yolo_model()
    
    # Create directory structure
    create_sample_structure()
    
    # Run test (optional)
    if api_key_configured:
        run_test()
    
    # Print next steps
    print_next_steps(api_key_configured)

if __name__ == "__main__":
    main()