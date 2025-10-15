from fastapi import FastAPI
from routes import recipes, ingredients, feedback, auth, my_recipes  # 👈 added my_recipes
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app
app = FastAPI(title="Snap2Cook API", version="1.0")

# ✅ Enable CORS for frontend (React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict later like ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include routes
app.include_router(recipes.router)
app.include_router(ingredients.router)
app.include_router(feedback.router)
app.include_router(auth.router)
app.include_router(my_recipes.router)  # 👈 added this line

# ✅ Root route
@app.get("/")
def home():
    return {"message": "Snap2Cook Backend Running 🚀"}
