import os
from dotenv import load_dotenv
import google.generativeai as genai
from langchain.prompts import PromptTemplate

from dotenv import load_dotenv
import os

load_dotenv()

# Load API key
load_dotenv()
GEMINI_API_KEY = "AIzaSyCi6SdU3Dtwxx_LYPL0OdAF6L0nlf_rWkY"


# Gemini setup
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Prompt template
DECOR_PROMPT_TEMPLATE = """
You are an interior designer assistant.

Analyze the following room context and suggest a makeover plan.
Your plan should include:
1. A list of decor items that can enhance the space
2. The estimated price for each item
3. Total cost should not exceed ₹{budget}
4. Return a JSON with keys: "items", "total_price", and "notes"

Room Description:
{room_description}

Preferred Style: {style}
"""

def get_makeover_plan(room_description: str, budget: int, style: str = "Any") -> dict:
    prompt = PromptTemplate.from_template(DECOR_PROMPT_TEMPLATE)
    final_prompt = prompt.format(room_description=room_description, budget=budget, style=style)

    try:
        response = model.generate_content(final_prompt)
        content = response.text

        # Optional: Evaluate if it's JSON or plain text
        return {
            "status": "success",
            "raw_output": content
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
