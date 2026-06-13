from fastapi import FastAPI
from app.data_loader import load_assets, load_portfolios, load_holdings, load_prices
from app.analytics import (calculate_portfolio_value, 
                           calculate_portfolio_risk, 
                           calculate_portfolio_returns,
                           calculate_portfolio_holdings,
                           calculate_sector_exposure,
                           calculate_risk_contribution,
                           run_custom_stress_test,
                           calculate_portfolio_value_duckdb,
                           compare_analytics_engines,
                           run_large_dataset_benchmark,
                           generate_ai_risk_summary)

from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.ai_chat import (
    generate_ai_risk_summary,
    answer_ai_risk_question,
)

app = FastAPI(title="Investment Risk Analytics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StressTestRequest(BaseModel):
    shocks: dict[str, float]

class ChatMessage(BaseModel):
    role: str
    text: str


class AiQuestionRequest(BaseModel):
    question: str
    chat_history: list[ChatMessage] = []

@app.get("/")
def root():
    return {"message": "Investment Risk Analytics API is running"}

@app.get("/api/assets")
def get_assets():
    assets = load_assets()
    return assets.to_dict(orient="records")

@app.get("/api/portfolios")
def get_portfolios():
    portfolios = load_portfolios()
    return portfolios.to_dict(orient="records")

@app.get("/api/holdings")
def get_holdings():
    holdings = load_holdings()
    return holdings.to_dict(orient="records")

@app.get("/api/prices")
def get_prices(limit: int = 20):
    prices = load_prices()
    return prices.head(limit).to_dict(orient="records")

@app.get("/api/portfolio/{portfolio_id}/value")
def get_portfolio_value(portfolio_id: int):
    return calculate_portfolio_value(portfolio_id)

@app.get("/api/portfolio/{portfolio_id}/risk")
def get_portfolio_risk(portfolio_id: int):
    return calculate_portfolio_risk(portfolio_id)

@app.get("/api/portfolio/{portfolio_id}/returns")
def get_portfolio_returns(portfolio_id: int):
    return calculate_portfolio_returns(portfolio_id)

@app.get("/api/portfolio/{portfolio_id}/holdings")
def get_portfolio_holdings(portfolio_id: int):
    return calculate_portfolio_holdings(portfolio_id)

@app.get("/api/portfolio/{portfolio_id}/sector-exposure")
def get_sector_exposure(portfolio_id: int):
    return calculate_sector_exposure(portfolio_id)

@app.get("/api/portfolio/{portfolio_id}/risk-contribution")
def get_risk_contribution(portfolio_id: int):
    return calculate_risk_contribution(portfolio_id)

@app.post("/api/portfolio/{portfolio_id}/stress-test")
def stress_test_portfolio(
    portfolio_id: int,
    request: StressTestRequest
):
    return run_custom_stress_test(
        portfolio_id,
        request.shocks
    )

@app.get("/api/portfolio/{portfolio_id}/value-fast")
def get_portfolio_value_fast(portfolio_id: int):
    return calculate_portfolio_value_duckdb(portfolio_id)

@app.get("/api/portfolio/{portfolio_id}/engine-comparison")
def get_engine_comparison(portfolio_id: int):
    return compare_analytics_engines(portfolio_id)

@app.get("/api/performance/large-benchmark")
def get_large_dataset_benchmark():
    return run_large_dataset_benchmark()

@app.post("/api/portfolio/{portfolio_id}/ai-risk-summary")
def get_ai_risk_summary(portfolio_id: int):
    return generate_ai_risk_summary(portfolio_id)

@app.post("/api/portfolio/{portfolio_id}/ai-risk-summary")
def get_ai_risk_summary(portfolio_id: int):
    return generate_ai_risk_summary(portfolio_id)


@app.post("/api/portfolio/{portfolio_id}/ask-ai")
def ask_ai_risk_analyst(
    portfolio_id: int,
    request: AiQuestionRequest
):
    return answer_ai_risk_question(
        portfolio_id,
        request.question,
        request.chat_history
    )