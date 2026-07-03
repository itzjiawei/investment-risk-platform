from fastapi import APIRouter


router = APIRouter()


@router.get("/")
def root():
    return {"message": "Investment Risk Analytics API is running"}
