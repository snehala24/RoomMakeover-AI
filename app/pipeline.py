# app/pipeline.py

from app.image_processor import detect_objects, generate_room_description
from app.llm_suggester import get_makeover_plan

def image_to_makeover(image_path: str, budget: int, style: str = "Any") -> dict:
    try:
        # Step 1: Detect objects and analyze room
        detection_result = detect_objects(image_path)
        room_description = generate_room_description(detection_result)

        # Step 2: Get makeover suggestion with enhanced context
        response = get_makeover_plan(room_description, detection_result, budget, style)

        # Combine result with additional metadata
        return {
            "room_description": room_description,
            "detection_result": detection_result,
            "llm_response": response
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
