#!/usr/bin/env python3
"""
Test script for RoomMakeover.AI system
This script tests the complete pipeline with sample data
"""

import os
import sys
import glob
from app.pipeline import image_to_makeover

def test_system():
    """Test the complete RoomMakeover.AI system"""
    
    print("🏡 RoomMakeover.AI - System Test")
    print("=" * 50)
    
    # Check if sample data exists
    sample_dir = "sample_data"
    if not os.path.exists(sample_dir):
        print(f"❌ Sample data directory '{sample_dir}' not found")
        print("Please add some room images to the sample_data/ directory")
        return
    
    # Find sample images
    image_extensions = ['*.jpg', '*.jpeg', '*.png']
    sample_images = []
    for ext in image_extensions:
        sample_images.extend(glob.glob(os.path.join(sample_dir, ext)))
    
    if not sample_images:
        print(f"❌ No sample images found in '{sample_dir}'")
        print("Please add some room images (.jpg, .jpeg, .png) to test with")
        return
    
    print(f"📸 Found {len(sample_images)} sample images")
    print()
    
    # Test configurations
    test_configs = [
        {"budget": 5000, "style": "Modern"},
        {"budget": 3000, "style": "Minimalist"},
        {"budget": 8000, "style": "Scandinavian"},
        {"budget": 2000, "style": "Any"}
    ]
    
    # Test each configuration with the first available image
    test_image = sample_images[0]
    print(f"🔍 Testing with image: {os.path.basename(test_image)}")
    print()
    
    for i, config in enumerate(test_configs, 1):
        print(f"Test {i}: Budget ₹{config['budget']:,}, Style: {config['style']}")
        print("-" * 40)
        
        try:
            result = image_to_makeover(test_image, config['budget'], config['style'])
            
            if result.get("status") == "error":
                print(f"❌ Error: {result.get('message')}")
                continue
            
            # Display results
            print(f"✅ Room Type: {result['detection_result']['room_type']}")
            print(f"✅ Objects Detected: {result['detection_result']['total_objects']}")
            print(f"✅ Room Description: {result['room_description'][:100]}...")
            
            llm_response = result.get('llm_response', {})
            if llm_response.get('status') == 'success':
                parsed = llm_response.get('parsed_response', {})
                if parsed:
                    items_count = len(parsed.get('items', []))
                    total_price = parsed.get('total_price', 'N/A')
                    print(f"✅ Suggested Items: {items_count}")
                    print(f"✅ Total Cost: ₹{total_price}")
                    
                    if 'makeover_summary' in parsed:
                        print(f"✅ Summary: {parsed['makeover_summary'][:80]}...")
                else:
                    print("⚠️  JSON parsing needed - raw response received")
            else:
                print(f"❌ LLM Error: {llm_response.get('message', 'Unknown')}")
                
        except Exception as e:
            print(f"❌ System Error: {str(e)}")
        
        print()
    
    print("🎉 System test completed!")
    print()
    print("To run the full application:")
    print("  Streamlit: streamlit run streamlit_app.py")
    print("  FastAPI:   python app/main.py")

def check_dependencies():
    """Check if all required dependencies are installed"""
    
    print("🔧 Checking Dependencies")
    print("-" * 30)
    
    required_packages = [
        'streamlit',
        'fastapi',
        'ultralytics', 
        'google.generativeai',
        'langchain',
        'opencv-python',
        'numpy',
        'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'opencv-python':
                import cv2
                print(f"✅ OpenCV: {cv2.__version__}")
            elif package == 'google.generativeai':
                import google.generativeai as genai
                print(f"✅ Google Generative AI: Available")
            else:
                exec(f"import {package}")
                if hasattr(eval(package), '__version__'):
                    version = eval(f"{package}.__version__")
                    print(f"✅ {package}: {version}")
                else:
                    print(f"✅ {package}: Available")
        except ImportError:
            print(f"❌ {package}: Not installed")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    print("\n✅ All dependencies are installed!")
    return True

def check_environment():
    """Check environment configuration"""
    
    print("\n🌍 Checking Environment")
    print("-" * 25)
    
    # Check for API key
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key:
        print("✅ GEMINI_API_KEY: Set")
        print(f"   Key preview: {api_key[:10]}...")
    else:
        print("⚠️  GEMINI_API_KEY: Not set in environment")
        print("   Add to .env file or set as environment variable")
    
    # Check for YOLOv8 model
    if os.path.exists('yolov8n.pt'):
        model_size = os.path.getsize('yolov8n.pt') / (1024 * 1024)
        print(f"✅ YOLOv8 Model: Found ({model_size:.1f} MB)")
    else:
        print("⚠️  YOLOv8 Model: yolov8n.pt not found")
        print("   Model will be downloaded on first run")
    
    return True

if __name__ == "__main__":
    print("🏡 RoomMakeover.AI - Complete System Test\n")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment
    check_environment()
    
    # Run system test
    print()
    test_system()