from fastapi import APIRouter, Depends

from app.services.auth_service import get_current_user
from app.services.performance_service import run_large_dataset_benchmark


router = APIRouter(prefix="/api", dependencies=[Depends(get_current_user)])


@router.get("/performance/large-benchmark")
def get_large_dataset_benchmark():
    return run_large_dataset_benchmark()
