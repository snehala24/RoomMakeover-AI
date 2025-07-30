# app/image_processor.py

import os
import cv2
from ultralytics import YOLO
from collections import Counter

# Comprehensive indoor objects categorized by room function
INDOOR_OBJECTS = {
    # Furniture
    "bed", "chair", "sofa", "couch", "table", "desk", "dining table", "coffee table",
    "bookshelf", "cabinet", "wardrobe", "dresser", "nightstand", "ottoman", "bench",
    "armchair", "recliner", "stool", "sideboard", "console table",
    
    # Electronics & Appliances
    "tv", "television", "laptop", "computer", "monitor", "speaker", "clock",
    "microwave", "refrigerator", "washing machine", "air conditioner",
    
    # Decor & Accessories
    "lamp", "table lamp", "floor lamp", "mirror", "painting", "picture frame",
    "vase", "candle", "pillow", "cushion", "blanket", "throw", "curtain",
    "rug", "carpet", "plant", "potted plant", "flower pot", "decorative bowl",
    
    # Storage & Organization
    "box", "basket", "bag", "suitcase", "backpack", "handbag",
    
    # Structural Elements
    "window", "door", "ceiling fan", "light fixture", "radiator",
    
    # Bedroom Specific
    "mattress", "pillow case", "bed sheet", "comforter", "duvet",
    
    # Kitchen & Dining
    "plate", "bowl", "cup", "glass", "bottle", "fork", "knife", "spoon",
    
    # Bathroom
    "towel", "soap", "toothbrush", "toilet paper",
    
    # Living Room
    "remote control", "magazine", "book", "newspaper"
}

# Room type classification based on detected objects
ROOM_INDICATORS = {
    "bedroom": ["bed", "mattress", "nightstand", "dresser", "wardrobe", "pillow"],
    "living_room": ["sofa", "couch", "tv", "coffee table", "armchair", "remote control"],
    "kitchen": ["refrigerator", "microwave", "dining table", "plate", "bowl", "cup"],
    "bathroom": ["towel", "soap", "toothbrush", "toilet paper"],
    "office": ["desk", "computer", "laptop", "monitor", "chair", "bookshelf"],
    "dining_room": ["dining table", "chair", "plate", "bowl", "glass"]
}

# Load YOLOv8 model (pretrained coco)
model = YOLO("yolov8n.pt")  # lightweight version

def detect_objects(image_path: str) -> dict:
    """
    Detect objects in the image and return detailed analysis
    Returns: dict with detected_items, room_type, object_counts
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    results = model(image_path)[0]
    detected_items = []
    object_counts = Counter()

    for box in results.boxes:
        cls_id = int(box.cls)
        name = results.names[cls_id]
        confidence = float(box.conf)

        # Only include objects with reasonable confidence and are indoor-relevant
        if name in INDOOR_OBJECTS and confidence > 0.3:
            detected_items.append(name)
            object_counts[name] += 1

    # Determine most likely room type
    room_type = classify_room_type(detected_items)
    
    return {
        "detected_items": list(set(detected_items)),
        "object_counts": dict(object_counts),
        "room_type": room_type,
        "total_objects": len(detected_items)
    }

def classify_room_type(detected_items: list) -> str:
    """Classify the room type based on detected objects"""
    room_scores = {}
    
    for room_type, indicators in ROOM_INDICATORS.items():
        score = sum(1 for item in detected_items if item in indicators)
        if score > 0:
            room_scores[room_type] = score
    
    if room_scores:
        return max(room_scores, key=room_scores.get)
    return "general_room"

def generate_room_description(detection_result: dict) -> str:
    """Generate a comprehensive room description from detection results"""
    detected_items = detection_result["detected_items"]
    object_counts = detection_result["object_counts"]
    room_type = detection_result["room_type"]
    
    if not detected_items:
        return "A minimal or empty room with very few recognizable furniture items."

    # Create description with counts for multiple items
    item_descriptions = []
    for item, count in object_counts.items():
        if count > 1:
            item_descriptions.append(f"{count} {item}s")
        else:
            item_descriptions.append(f"a {item}")
    
    # Format the list nicely
    if len(item_descriptions) == 1:
        items_text = item_descriptions[0]
    elif len(item_descriptions) == 2:
        items_text = " and ".join(item_descriptions)
    else:
        items_text = ", ".join(item_descriptions[:-1]) + f", and {item_descriptions[-1]}"
    
    # Create room type specific description
    room_type_text = room_type.replace("_", " ").title()
    
    return f"This appears to be a {room_type_text} containing {items_text}. The space has {len(detected_items)} different types of furniture and objects."
