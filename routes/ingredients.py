from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Optional
from openai import AzureOpenAI
from dotenv import load_dotenv
import os, base64, json, traceback

# Load environment variables
load_dotenv()

router = APIRouter(prefix="/ingredients", tags=["Ingredients"])

# Initialize Azure GPT-4o client
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version="2024-05-01-preview"
)
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")  # e.g., "gpt-4o"

@router.post("/recognize")
async def recognize_image(
    ingredients: Optional[List[str]] = Form(None),
    image: Optional[UploadFile] = File(None)
):
    """
    Recognize ingredients from either:
    1. Manual text list, or
    2. Uploaded image analyzed via Azure GPT-4o Vision.
    """

    try:
        # 🥗 Manual ingredient input
        if ingredients:
            results = [{"name": i.lower(), "confidence": 0.98} for i in ingredients]
            print("✅ Manual ingredients:", results)
            return JSONResponse(content={"ingredients": results})

        # 📸 Image input
        if image:
            print(f"📷 Image received: {image.filename}")
            img_bytes = await image.read()
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")

            prompt = """
            You are an AI kitchen assistant.
            Analyze the given image and identify all visible food ingredients.
            Return ONLY a JSON array like this:
            [{"name": "ingredient_name", "confidence": 0.95}]
            Do not include any other text or explanation.
            """

            print("🧠 Sending image to GPT-4o (correct image_url object format)...")

            response = client.chat.completions.create(
                model=deployment,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
                            },
                        ],
                    }
                ],
                temperature=0.2,
            )

            content = response.choices[0].message.content.strip()
            print("🧩 Raw GPT-4o response:", content)

            # Try parsing JSON
            try:
                json_start = content.find("[")
                json_end = content.rfind("]") + 1
                json_str = content[json_start:json_end]
                data_json = json.loads(json_str)
                print("✅ Parsed ingredients:", data_json)
            except Exception as parse_err:
                print("⚠️ JSON parse error:", parse_err)
                print("🪵 Raw content:", content)
                raise HTTPException(status_code=500, detail="Invalid JSON format from GPT-4o")

            return JSONResponse(content={"ingredients": data_json})

        # 🚫 No input
        print("⚠️ No input provided to /ingredients/recognize")
        return JSONResponse(
            content={"error": "No input provided. Please upload an image or send ingredients."},
            status_code=400,
        )

    except Exception as e:
        print("❌ GPT-4o Vision Error:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"GPT-4o Vision Error: {str(e)}")
