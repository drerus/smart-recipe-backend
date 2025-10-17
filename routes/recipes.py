from openai import AzureOpenAI
import os
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

# ---------------------------
# 🔧 Azure OpenAI Configuration
# ---------------------------

# Load .env only in local environment
if os.getenv("RAILWAY_ENVIRONMENT") is None:
    from dotenv import load_dotenv
    load_dotenv()
    print("🧩 Loaded .env file (local environment)")
else:
    print("🚀 Running in Railway environment — using system variables")

# Debug: Check environment variable availability
print("🔍 Checking Azure environment variables:")
print("  AZURE_OPENAI_KEY =", bool(os.getenv("AZURE_OPENAI_KEY")))
print("  AZURE_OPENAI_ENDPOINT =", bool(os.getenv("AZURE_OPENAI_ENDPOINT")))
print("  AZURE_OPENAI_DEPLOYMENT =", bool(os.getenv("AZURE_OPENAI_DEPLOYMENT")))

# Initialize Azure OpenAI Client
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version="2024-08-01-preview"  # ✅ Updated API version
)

deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")  # e.g., "gpt-4o" or "gpt-4o-mini"

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
# 🧠 Recipe Generator Logic (Azure GPT)
# ---------------------------
def generate_mock_recipe(data: RecipeRequest) -> RecipeResponse:
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
    """

    try:
        response = client.chat.completions.create(
            model=deployment,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        content = response.choices[0].message.content.strip()

        # ✅ Try to extract valid JSON
        try:
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            json_str = content[json_start:json_end]
            data_json = json.loads(json_str)
        except Exception as parse_err:
            print("⚠️ JSON parse error:", parse_err)
            print("🔍 Raw response content:", content)
            raise Exception("Invalid JSON format from Azure GPT")

        recipe = RecipeResponse(**data_json)
        return recipe

    except Exception as e:
        print("⚠️ Azure GPT error:", e)
        return RecipeResponse(
            title="Fallback Quick Dish",
            ingredients=[Ingredient(name=i, qty="1 cup") for i in data.pantry],
            instructions=["Mix ingredients and cook briefly."],
            nutrition=Nutrition(calories=400, protein=20, carbs=40, fat=10),
            missing_items=["salt", "oil"],
            estimated_time_minutes=15,
            confidence=0.6,
            explanation="Fallback recipe (Azure GPT unavailable)."
        )

# ---------------------------
# 🚀 API Endpoint
# ---------------------------
@router.post("/generate", response_model=RecipeResponse)
def generate_recipe(request: RecipeRequest):
    try:
        recipe = generate_mock_recipe(request)
        return recipe
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
