from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import BACKEND_CORS_ORIGINS
from app.routers import ai, health, market_data, performance, portfolio


def create_app() -> FastAPI:
    app = FastAPI(title="Investment Risk Analytics API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
    )

    app.include_router(health.router)
    app.include_router(market_data.router)
    app.include_router(portfolio.router)
    app.include_router(performance.router)
    app.include_router(ai.router)

    return app


app = create_app()
