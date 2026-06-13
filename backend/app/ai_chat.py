from app.ai_service import ask_ollama
from app.analytics import (
    calculate_portfolio_risk,
    calculate_portfolio_holdings,
    calculate_sector_exposure,
    calculate_risk_contribution,
)


def generate_ai_risk_summary(portfolio_id: int):
    risk = calculate_portfolio_risk(portfolio_id)
    holdings = calculate_portfolio_holdings(portfolio_id)
    sector_exposure = calculate_sector_exposure(portfolio_id)
    risk_contribution = calculate_risk_contribution(portfolio_id)

    prompt = f"""
You are an investment risk analyst.

Analyze the following portfolio data and write a concise professional risk summary.

Rules:
- Do not give financial advice.
- Do not recommend buying or selling specific assets.
- Focus on risk, concentration, volatility, diversification, and stress sensitivity.
- Use clear bullet points.
- Keep it under 250 words.

Risk Metrics:
{risk}

Holdings:
{holdings}

Sector Exposure:
{sector_exposure}

Risk Contribution:
{risk_contribution}

Write the answer with these sections:
1. Key Risk Observations
2. Concentration Concerns
3. Risk Drivers
4. Suggested Monitoring Areas
"""

    summary = ask_ollama(prompt)

    return {
        "portfolio_id": portfolio_id,
        "summary": summary,
    }


def answer_ai_risk_question(portfolio_id: int, question: str):
    risk = calculate_portfolio_risk(portfolio_id)
    holdings = calculate_portfolio_holdings(portfolio_id)
    sector_exposure = calculate_sector_exposure(portfolio_id)
    risk_contribution = calculate_risk_contribution(portfolio_id)

    prompt = f"""
You are an AI risk analyst for an investment portfolio.

Answer the user's question using only the portfolio data provided below.

Rules:
- Do not make up data.
- Do not give buy/sell recommendations.
- Do not give personalized financial advice.
- If the question cannot be answered from the data, say what data is missing.
- Be concise, professional, and analytical.
- If the user asks whether to buy, sell, or increase a position, do not answer directly.
- Instead, explain the relevant risk factors from the provided data.
- Do not claim data is missing if the provided holdings, sector exposure, or risk contribution data contains relevant information.

User Question:
{question}

Portfolio Risk Metrics:
{risk}

Holdings:
{holdings}

Sector Exposure:
{sector_exposure}

Risk Contribution:
{risk_contribution}

Answer:
"""

    answer = ask_ollama(prompt)

    return {
        "portfolio_id": portfolio_id,
        "question": question,
        "answer": answer,
    }