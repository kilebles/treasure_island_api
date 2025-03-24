from fastapi import APIRouter

router = APIRouter()


@router.get("/", tags=["health"])
async def health():
    return {"message": "API is running"}