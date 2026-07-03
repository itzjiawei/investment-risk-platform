from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import ai, health, market_data, performance, portfolio


def create_app() -> FastAPI:
    app = FastAPI(title="Investment Risk Analytics API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
        ],
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
