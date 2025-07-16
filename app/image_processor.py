# app/image_processor.py

import os
import cv2
from ultralytics import YOLO

# Common indoor objects (can be expanded)
INDOOR_OBJECTS = {
    "bed", "chair", "sofa", "tv", "table", "lamp", "carpet", "bookshelf", "cabinet",
    "potted plant", "mirror", "painting", "desk", "window", "door", "cushion", "blanket"
}

# Load YOLOv8 model (pretrained coco)
model = YOLO("yolov8n.pt")  # lightweight version

def detect_objects(image_path: str) -> list:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    results = model(image_path)[0]
    detected_items = []

    for box in results.boxes:
        cls_id = int(box.cls)
        name = results.names[cls_id]

        if name in INDOOR_OBJECTS:
            detected_items.append(name)

    return list(set(detected_items))  # unique objects

def generate_room_description(detected_items: list) -> str:
    if not detected_items:
        return "A minimal or undecorated room with very few recognizable items."

    joined = ", ".join(detected_items[:-1]) + f", and {detected_items[-1]}" if len(detected_items) > 1 else detected_items[0]
    return f"A room containing {joined}."
