from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from openai import AzureOpenAI
import os, json

router = APIRouter(prefix="/recipes", tags=["Recipes"])

# ✅ Models
class Constraint(BaseModel):
    time_minutes: Optional[int] = None
    equipment: Optional[List[str]] = None
    cuisine: Optional[str] = None

class Ingredient(BaseModel):
    name: str
    confidence: Optional[float] = None
    qty: Optional[str] = None

class RecipeRequest(BaseModel):
    pantry: List[str]
    diet: Optional[str] = "normal"
    calorie_target: Optional[int] = None
    constraints: Optional[Constraint] = None
    mode: Optional[str] = "creative"

# ✅ Azure Setup
if os.getenv("RAILWAY_ENVIRONMENT") is None:
    from dotenv import load_dotenv
    load_dotenv()
    print("🧩 Loaded .env file (local)")
else:
    print("🚀 Using Railway system variables")

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version="2024-08-01-preview",
)

deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# ✅ Helper to parse model output safely
def safe_parse_json(content: str):
    try:
        start = content.find("{")
        end = content.rfind("}") + 1
        return json.loads(content[start:end])
    except Exception as e:
        print("⚠️ Failed to parse JSON from GPT:", e)
        print("🔍 Raw content:", content)
        return {
            "title": "Fallback Dish",
            "ingredients": [{"name": "rice", "qty": "1 cup"}],
            "instructions": ["Mix ingredients and serve."],
            "nutrition": {"calories": 200, "protein": 5, "carbs": 30, "fat": 3},
            "missing_items": [],
            "estimated_time_minutes": 15,
            "confidence": 0.6,
            "explanation": "Fallback response due to invalid GPT output.",
        }

# ✅ Recipe Generator Endpoint
@router.post("/generate")
def generate_recipe(request: RecipeRequest):
    try:
        print("🧠 Request received for recipe:", request.pantry)
        pantry_str = ", ".join(request.pantry)

        prompt = f"""
        You are an AI chef assistant.
        Given these pantry items: {pantry_str},
        generate a recipe strictly in valid JSON with keys:
        title, ingredients, instructions, nutrition, missing_items, estimated_time_minutes, confidence, explanation.
        Do NOT include markdown or text outside JSON.
        """

        response = client.chat.completions.create(
            model=deployment,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        content = response.choices[0].message.content.strip()
        print("🧾 Raw GPT output:", content[:500])  # Debug log

        recipe_data = safe_parse_json(content)
        print("✅ Returning parsed recipe to frontend.")
        return recipe_data

    except Exception as e:
        print("🔥 Error in /recipes/generate:", e)
        raise HTTPException(status_code=500, detail=str(e))
