from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/feedback", tags=["Feedback"])

@router.post("/")
def submit_feedback(data: dict):
    """
    Simple mock feedback route.
    Replace later with DB integration or email logic.
    """
    name = data.get("name", "Anonymous")
    message = data.get("message", "")
    print(f"📩 Feedback received from {name}: {message}")
    return JSONResponse(content={"status": "success", "message": "Feedback received!"})
