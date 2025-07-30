import os
import json
import requests
from dotenv import load_dotenv
import google.generativeai as genai
from langchain.prompts import PromptTemplate

load_dotenv()

# Load API key
GEMINI_API_KEY = "AIzaSyCi6SdU3Dtwxx_LYPL0OdAF6L0nlf_rWkY"

# Gemini setup
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Interior Design Style Definitions
STYLE_GUIDES = {
    "Modern": {
        "description": "Clean lines, minimalist approach, neutral colors, functional furniture",
        "colors": ["white", "black", "gray", "beige"],
        "materials": ["glass", "metal", "concrete", "leather"],
        "key_elements": ["geometric shapes", "open spaces", "minimal decor", "statement lighting"]
    },
    "Minimalist": {
        "description": "Less is more philosophy, clutter-free, functional simplicity",
        "colors": ["white", "cream", "light gray", "natural wood"],
        "materials": ["natural wood", "linen", "cotton", "bamboo"],
        "key_elements": ["hidden storage", "multi-functional furniture", "negative space", "natural light"]
    },
    "Scandinavian": {
        "description": "Cozy, functional, light woods, hygge-inspired comfort",
        "colors": ["white", "light blue", "soft gray", "natural wood tones"],
        "materials": ["light wood", "wool", "cotton", "linen"],
        "key_elements": ["natural textures", "cozy textiles", "functional design", "plants"]
    },
    "Bohemian": {
        "description": "Eclectic, colorful, artistic, layered textures and patterns",
        "colors": ["earth tones", "jewel tones", "warm oranges", "deep purples"],
        "materials": ["rattan", "macrame", "vintage fabrics", "natural fibers"],
        "key_elements": ["layered rugs", "hanging plants", "vintage furniture", "tapestries"]
    },
    "Industrial": {
        "description": "Raw materials, exposed elements, urban loft aesthetic",
        "colors": ["charcoal", "rust", "black", "deep brown"],
        "materials": ["exposed brick", "metal", "reclaimed wood", "concrete"],
        "key_elements": ["exposed pipes", "metal fixtures", "vintage machinery", "Edison bulbs"]
    },
    "Traditional": {
        "description": "Classic elegance, rich fabrics, warm colors, timeless furniture",
        "colors": ["burgundy", "navy", "forest green", "warm gold"],
        "materials": ["dark wood", "silk", "velvet", "brass"],
        "key_elements": ["antique furniture", "formal arrangements", "rich textures", "classic patterns"]
    },
    "Coastal": {
        "description": "Beach-inspired, light and airy, natural textures",
        "colors": ["ocean blue", "sandy beige", "coral", "seafoam green"],
        "materials": ["weathered wood", "rope", "seagrass", "linen"],
        "key_elements": ["nautical decor", "natural lighting", "woven textures", "shell accents"]
    }
}

# E-commerce search templates for Indian market
ECOMMERCE_PLATFORMS = {
    "amazon": "https://www.amazon.in/s?k={query}",
    "flipkart": "https://www.flipkart.com/search?q={query}",
    "pepperfry": "https://www.pepperfry.com/search?q={query}",
    "urban_ladder": "https://www.urbanladder.com/search?q={query}"
}

# Enhanced prompt template with style guidance and e-commerce integration
DECOR_PROMPT_TEMPLATE = """
You are an expert interior designer specializing in Indian home makeovers. 

ROOM ANALYSIS:
{room_description}

DETECTED OBJECTS: {detected_objects}
ROOM TYPE: {room_type}
EXISTING FURNITURE COUNT: {furniture_count}

STYLE PREFERENCE: {style}
{style_guide}

BUDGET: ₹{budget}

TASK: Create a comprehensive makeover plan that enhances this space while staying within budget.

REQUIREMENTS:
1. Suggest 3-5 specific items that would improve the room's aesthetics and functionality
2. Each item should include: name, description, estimated price in INR, and shopping category
3. Provide realistic pricing based on Indian e-commerce market (Amazon.in, Flipkart, Pepperfry)
4. Consider the existing furniture and suggest complementary pieces
5. Include both decorative and functional improvements
6. Ensure total cost stays within budget
7. Give preference to items that match the selected style

RESPONSE FORMAT (JSON only):
{{
    "room_analysis": "Brief analysis of current room state and potential",
    "style_direction": "How the chosen style will transform this space",
    "items": [
        {{
            "name": "Item name",
            "description": "Detailed description and why it fits",
            "price": "estimated price in INR",
            "category": "furniture/decor/lighting/textile/storage",
            "search_keywords": "keywords for finding on e-commerce sites",
            "style_impact": "how this item enhances the chosen style"
        }}
    ],
    "total_price": "total estimated cost",
    "makeover_summary": "A warm, inspiring 2-3 sentence description of the transformed space",
    "styling_tips": "2-3 practical tips for arranging and styling these items"
}}

Remember: Keep suggestions practical, achievable, and perfectly suited to Indian homes and market availability.
"""

def get_style_guide(style: str) -> str:
    """Get detailed style guide information"""
    if style == "Any" or style not in STYLE_GUIDES:
        return "Focus on creating a balanced, welcoming space that enhances functionality and aesthetics."
    
    guide = STYLE_GUIDES[style]
    return f"""
STYLE GUIDE - {style}:
- Description: {guide['description']}
- Preferred Colors: {', '.join(guide['colors'])}
- Materials: {', '.join(guide['materials'])}
- Key Elements: {', '.join(guide['key_elements'])}
"""

def generate_product_links(items: list) -> list:
    """Generate e-commerce links for suggested items"""
    enhanced_items = []
    
    for item in items:
        search_keywords = item.get('search_keywords', item['name'])
        
        # Generate shopping links
        shopping_links = {}
        for platform, url_template in ECOMMERCE_PLATFORMS.items():
            shopping_links[platform] = url_template.format(query=search_keywords.replace(' ', '+'))
        
        item['shopping_links'] = shopping_links
        enhanced_items.append(item)
    
    return enhanced_items

def get_makeover_plan(room_description: str, detection_result: dict, budget: int, style: str = "Any") -> dict:
    """Generate comprehensive makeover plan with e-commerce integration"""
    
    # Get style guide
    style_guide = get_style_guide(style)
    
    # Prepare prompt variables
    detected_objects = ", ".join(detection_result["detected_items"])
    room_type = detection_result["room_type"].replace("_", " ").title()
    furniture_count = detection_result["total_objects"]
    
    # Create and format prompt
    prompt = PromptTemplate.from_template(DECOR_PROMPT_TEMPLATE)
    final_prompt = prompt.format(
        room_description=room_description,
        detected_objects=detected_objects,
        room_type=room_type,
        furniture_count=furniture_count,
        style=style,
        style_guide=style_guide,
        budget=budget
    )

    try:
        response = model.generate_content(final_prompt)
        content = response.text
        
        # Clean and parse JSON response
        cleaned_content = content.strip()
        if cleaned_content.startswith("```json"):
            cleaned_content = cleaned_content[7:]
        if cleaned_content.endswith("```"):
            cleaned_content = cleaned_content[:-3]
        cleaned_content = cleaned_content.strip()
        
        # Parse JSON
        parsed_response = json.loads(cleaned_content)
        
        # Add shopping links to items
        if "items" in parsed_response:
            parsed_response["items"] = generate_product_links(parsed_response["items"])
        
        return {
            "status": "success",
            "raw_output": content,
            "parsed_response": parsed_response,
            "style_applied": style
        }
        
    except json.JSONDecodeError as e:
        return {
            "status": "json_error",
            "message": f"Failed to parse JSON response: {str(e)}",
            "raw_output": content
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
