from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import tempfile
import os
from typing import Optional
from app.pipeline import image_to_makeover

app = FastAPI(
    title="RoomMakeover.AI API",
    description="AI-powered room makeover suggestions using YOLOv8 and Gemini AI",
    version="1.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Welcome to RoomMakeover.AI API",
        "version": "1.0.0",
        "endpoints": {
            "/makeover": "POST - Upload room image and get makeover suggestions",
            "/styles": "GET - Get available interior design styles",
            "/docs": "GET - API documentation"
        }
    }

@app.get("/styles")
async def get_styles():
    """Get available interior design styles"""
    from app.llm_suggester import STYLE_GUIDES
    
    styles = {}
    for style_name, style_data in STYLE_GUIDES.items():
        styles[style_name] = {
            "name": style_name,
            "description": style_data["description"],
            "colors": style_data["colors"],
            "materials": style_data["materials"],
            "key_elements": style_data["key_elements"]
        }
    
    return {
        "styles": styles,
        "default_option": "Any"
    }

@app.post("/makeover")
async def create_makeover(
    image: UploadFile = File(...),
    budget: int = Form(...),
    style: str = Form("Any")
):
    """
    Generate room makeover suggestions
    
    - **image**: Room image file (JPG/JPEG)
    - **budget**: Budget in INR (500-50000)
    - **style**: Interior design style preference
    """
    
    # Validate inputs
    if budget < 500 or budget > 50000:
        raise HTTPException(status_code=400, detail="Budget must be between ₹500 and ₹50,000")
    
    if not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Save uploaded image temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            content = await image.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Process the image through the pipeline
        result = image_to_makeover(tmp_path, budget, style)

        # Clean up temp file
        os.remove(tmp_path)

        # Return structured response
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message", "Processing failed"))
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "room_description": result.get("room_description"),
                "detection_result": result.get("detection_result"),
                "makeover_plan": result.get("llm_response"),
                "parameters": {
                    "budget": budget,
                    "style": style,
                    "filename": image.filename
                }
            }
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "RoomMakeover.AI"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)