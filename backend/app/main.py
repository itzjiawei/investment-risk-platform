from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import BACKEND_CORS_ORIGINS
from app.routers import (
    ai,
    audit,
    auth,
    health,
    jobs,
    market_data,
    notifications,
    performance,
    portfolio,
)
from app.services.market_refresh_job_service import (
    start_market_refresh_scheduler,
    stop_market_refresh_scheduler,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    start_market_refresh_scheduler()
    try:
        yield
    finally:
        stop_market_refresh_scheduler()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Investment Risk Analytics API",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
    )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(audit.router)
    app.include_router(jobs.router)
    app.include_router(notifications.router)
    app.include_router(market_data.router)
    app.include_router(portfolio.router)
    app.include_router(performance.router)
    app.include_router(ai.router)

    return app


app = create_app()
