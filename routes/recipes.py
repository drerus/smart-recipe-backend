from openai import AzureOpenAI
import os
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

# ---------------------------
# 🔧 Azure OpenAI Configuration
# ---------------------------

if os.getenv("RAILWAY_ENVIRONMENT") is None:
    from dotenv import load_dotenv
    load_dotenv()
    print("🧩 Loaded .env file (local environment)")
else:
    print("🚀 Running in Railway environment — using system variables")

print("🔍 Checking Azure environment variables:")
print("  AZURE_OPENAI_KEY =", bool(os.getenv("AZURE_OPENAI_KEY")))
print("  AZURE_OPENAI_ENDPOINT =", bool(os.getenv("AZURE_OPENAI_ENDPOINT")))
print("  AZURE_OPENAI_DEPLOYMENT =", bool(os.getenv("AZURE_OPENAI_DEPLOYMENT")))

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version="2024-08-01-preview"
)

deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# ---------------------------
# 📦 FastAPI Router and Schemas
# ---------------------------

router = APIRouter(prefix="/recipes", tags=["Recipes"])

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

class Nutrition(BaseModel):
    calories: float
    protein: float
    carbs: float
    fat: float

class RecipeResponse(BaseModel):
    title: str
    ingredients: List[Ingredient]
    instructions: List[str]
    nutrition: Nutrition
    missing_items: Optional[List[str]]
    estimated_time_minutes: Optional[int]
    confidence: float
    explanation: str


# ---------------------------
# 🧠 Recipe Generator Logic
# ---------------------------

def generate_mock_recipe(data: RecipeRequest) -> dict:
    pantry_str = ", ".join(data.pantry)
    diet = data.diet or "normal"
    calorie_target = data.calorie_target or "unspecified"

    prompt = f"""
    You are an AI chef assistant.
    Given the following pantry items: {pantry_str},
    diet: {diet},
    and calorie target: {calorie_target},
    generate ONE recipe in JSON format strictly following this schema:
    {{
      "title": "...",
      "ingredients": [{{"name":"...","qty":"..."}}],
      "instructions": ["...", "..."],
      "nutrition": {{"calories": ..., "protein": ..., "carbs": ..., "fat": ...}},
      "missing_items": ["..."],
      "estimated_time_minutes": ...,
      "confidence": 0.9,
      "explanation": "short reasoning"
    }}
    Do not include markdown or extra text. Return only pure JSON.
    """

    try:
        response = client.chat.completions.create(
            model=deployment,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        content = response.choices[0].message.content.strip()
        print("🧠 Raw GPT response:", content[:400])

        # ✅ Robust JSON extraction
        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        json_str = content[json_start:json_end].replace("```json", "").replace("```", "").strip()

        data_json = json.loads(json_str)
        print("✅ Parsed recipe:", data_json)

        return data_json  # return dict, not model (important!)

    except Exception as e:
        print("⚠️ Azure GPT error:", e)
        # Return fallback recipe directly as dict
        return {
            "title": "Fallback Quick Dish",
            "ingredients": [{"name": i, "qty": "1 cup"} for i in data.pantry],
            "instructions": ["Mix ingredients and cook briefly."],
            "nutrition": {"calories": 400, "protein": 20, "carbs": 40, "fat": 10},
            "missing_items": ["salt", "oil"],
            "estimated_time_minutes": 15,
            "confidence": 0.6,
            "explanation": "Fallback recipe (Azure GPT unavailable)."
        }

# ---------------------------
# 🚀 API Endpoint
# ---------------------------

@router.post("/generate")
def generate_recipe(request: RecipeRequest):
    try:
        recipe = generate_mock_recipe(request)
        return recipe  # ✅ directly returns JSON-safe dict
    except Exception as e:
        print("❌ Backend error:", e)
        raise HTTPException(status_code=500, detail=str(e))
