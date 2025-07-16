# tests/test_image.py

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.image_processor import detect_objects, generate_room_description

# ✅ Option 1: Using forward slashes (recommended)
image_path = "sample_data/room.jpeg"

# ✅ Option 2: Raw string for absolute Windows path (if Option 1 fails)
# image_path = r"C:\Users\SNEHALA A\Documents\practice folders\project 1\sample_data\room.jpeg"

try:
    items = detect_objects(image_path)
    print("🪄 Detected Objects:", items)

    description = generate_room_description(items)
    print("📝 Generated Room Description:")
    print(description)

except Exception as e:
    print("❌ Error:", str(e))
