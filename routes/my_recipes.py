# routes/my_recipes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Column, Integer, String, Float, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from datetime import datetime

# =====================================================
# CONFIG
# =====================================================
SECRET_KEY = "your_secret_key_here"
ALGORITHM = "HS256"

router = APIRouter(prefix="/recipes", tags=["My Recipes"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

Base = declarative_base()
engine = create_engine("sqlite:///./users.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# =====================================================
# DATABASE MODEL
# =====================================================
class SavedRecipe(Base):
    __tablename__ = "saved_recipes"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    title = Column(String)
    recipe_data = Column(Text)
    rating = Column(Float)
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat())

Base.metadata.create_all(bind=engine)

# =====================================================
# HELPERS
# =====================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Token error")

# =====================================================
# SCHEMAS
# =====================================================
class RecipeSaveRequest(BaseModel):
    title: str
    recipe_data: str
    rating: float

class RecipeResponse(BaseModel):
    id: int
    title: str
    rating: float
    recipe_data: str
    created_at: str

    class Config:
        orm_mode = True

# =====================================================
# ROUTES
# =====================================================

# 💾 Save Recipe
@router.post("/save")
def save_recipe(
    request: RecipeSaveRequest,
    db: Session = Depends(get_db),
    username: str = Depends(get_current_user)
):
    new_recipe = SavedRecipe(
        username=username,
        title=request.title,
        recipe_data=request.recipe_data,
        rating=request.rating
    )
    db.add(new_recipe)
    db.commit()
    db.refresh(new_recipe)
    return {"message": "Recipe saved successfully!", "recipe_id": new_recipe.id}


# 📂 Fetch all recipes for current user
@router.get("/my", response_model=list[RecipeResponse])
def get_my_recipes(
    db: Session = Depends(get_db),
    username: str = Depends(get_current_user)
):
    recipes = db.query(SavedRecipe).filter(SavedRecipe.username == username).all()
    return recipes


# 🗑️ Delete a saved recipe
@router.delete("/delete/{recipe_id}")
def delete_recipe(
    recipe_id: int,
    db: Session = Depends(get_db),
    username: str = Depends(get_current_user)
):
    recipe = (
        db.query(SavedRecipe)
        .filter(SavedRecipe.id == recipe_id, SavedRecipe.username == username)
        .first()
    )
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    db.delete(recipe)
    db.commit()
    return {"message": "Recipe deleted successfully!"}
