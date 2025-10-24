from fastapi import FastAPI
from routes import recipes, ingredients, feedback, auth, my_recipes
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="Snap2Cook API", version="1.0")

# ✅ Frontend URLs (Vercel + Local)
ALLOWED_ORIGINS = [
    "https://snap2cook-frontend-sbgg.vercel.app",  # your live Vercel domain
    "http://localhost:5173",  # local testing
]

# ✅ Enable CORS — Required for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include API routers
app.include_router(recipes.router)
app.include_router(ingredients.router)
app.include_router(feedback.router)
app.include_router(auth.router)
app.include_router(my_recipes.router)

@app.get("/")
def home():
    return {"message": "Snap2Cook Backend Running 🚀"}
