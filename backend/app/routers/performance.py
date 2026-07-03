from fastapi import APIRouter

from app.services.performance_service import run_large_dataset_benchmark


router = APIRouter(prefix="/api")


@router.get("/performance/large-benchmark")
def get_large_dataset_benchmark():
    return run_large_dataset_benchmark()
