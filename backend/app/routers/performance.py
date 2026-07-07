from fastapi import APIRouter, Depends, HTTPException

from app.services.auth_service import get_current_user
from app.services.performance_service import run_large_dataset_benchmark


router = APIRouter(prefix="/api", dependencies=[Depends(get_current_user)])


@router.get("/performance/large-benchmark")
def get_large_dataset_benchmark():
    try:
        return run_large_dataset_benchmark()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
