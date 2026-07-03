from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.database.repository import load_portfolios
from app.services.ollama_service import ask_ollama
from app.services.portfolio_service import (
    calculate_portfolio_holdings,
    calculate_portfolio_risk,
    calculate_risk_contribution,
    calculate_sector_exposure,
    run_custom_stress_test,
)


DEFAULT_STRESS_SHOCKS = {
    "Technology": -20,
    "Semiconductors": -30,
    "ETF": -15,
    "Commodities": 5,
    "Financials": -10,
}


def generate_pdf_risk_report(portfolio_id: int) -> bytes:
    risk = calculate_portfolio_risk(portfolio_id)

    if "error" in risk:
        raise ValueError(risk["error"])

    holdings = calculate_portfolio_holdings(portfolio_id)
    sector_exposure = calculate_sector_exposure(portfolio_id)
    risk_contribution = calculate_risk_contribution(portfolio_id)
    stress_result = run_custom_stress_test(portfolio_id, DEFAULT_STRESS_SHOCKS)
    portfolio_name = _get_portfolio_name(portfolio_id)
    ai_summary = _try_generate_ai_summary(
        risk=risk,
        sector_exposure=sector_exposure,
        risk_contribution=risk_contribution,
    )

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
        title=f"Portfolio {portfolio_id} Risk Report",
    )

    styles = _build_styles()
    elements = [
        Paragraph("Investment Risk Analytics Platform", styles["eyebrow"]),
        Paragraph("Portfolio Risk Report", styles["title"]),
        Paragraph(
            f"Portfolio {portfolio_id}"
            + (f" - {portfolio_name}" if portfolio_name else ""),
            styles["subtitle"],
        ),
        Spacer(1, 0.22 * inch),
        Paragraph("Risk Metrics", styles["section_heading"]),
        _build_key_metrics_table(risk),
        Spacer(1, 0.18 * inch),
        Paragraph("Sector Exposure Summary", styles["section_heading"]),
        _build_sector_table(sector_exposure),
        Spacer(1, 0.18 * inch),
        Paragraph("Top Risk Contributors", styles["section_heading"]),
        _build_risk_contributors_table(risk_contribution),
        Spacer(1, 0.18 * inch),
        Paragraph("Stress Test Scenario", styles["section_heading"]),
        *_build_stress_section(stress_result, styles),
        Spacer(1, 0.18 * inch),
        Paragraph("AI Risk Summary", styles["section_heading"]),
        Paragraph(ai_summary, styles["body"]),
        Spacer(1, 0.12 * inch),
        Paragraph(
            "Generated locally from portfolio analytics data. This report is for risk monitoring and does not provide investment advice.",
            styles["footer"],
        ),
    ]

    document.build(elements)
    return buffer.getvalue()


def _build_styles():
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            textColor=colors.HexColor("#082047"),
            fontSize=24,
            leading=30,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportEyebrow",
            parent=styles["Normal"],
            alignment=TA_CENTER,
            textColor=colors.HexColor("#009f93"),
            fontSize=9,
            leading=11,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportSubtitle",
            parent=styles["Normal"],
            alignment=TA_CENTER,
            textColor=colors.HexColor("#667386"),
            fontSize=11,
            leading=14,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            textColor=colors.HexColor("#082047"),
            fontSize=14,
            leading=18,
            spaceBefore=6,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportBody",
            parent=styles["BodyText"],
            textColor=colors.HexColor("#24354c"),
            fontSize=9,
            leading=13,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportFooter",
            parent=styles["BodyText"],
            textColor=colors.HexColor("#667386"),
            fontSize=8,
            leading=11,
        )
    )

    return {
        "body": styles["ReportBody"],
        "eyebrow": styles["ReportEyebrow"],
        "footer": styles["ReportFooter"],
        "section_heading": styles["SectionHeading"],
        "subtitle": styles["ReportSubtitle"],
        "title": styles["ReportTitle"],
    }


def _build_key_metrics_table(risk: dict):
    rows = [
        ["Metric", "Value"],
        ["Latest Portfolio Value", _format_currency(risk["latest_value"])],
        ["Annualized Return", _format_percent(risk["annualized_return"])],
        ["Annualized Volatility", _format_percent(risk["annualized_volatility"])],
        ["Sharpe Ratio", f"{risk['sharpe_ratio']:.4g}"],
        ["Max Drawdown", _format_percent(risk["max_drawdown"])],
        ["Historical VaR 95%", _format_percent(risk["historical_var_95"])],
    ]

    return _styled_table(rows, [2.8 * inch, 2.8 * inch])


def _build_sector_table(sector_exposure: list[dict]):
    rows = [["Sector", "Market Value", "Weight"]]

    for sector in sector_exposure:
        rows.append(
            [
                sector["sector"],
                _format_currency(sector["market_value"]),
                _format_percent(sector["weight"]),
            ]
        )

    if len(rows) == 1:
        rows.append(["No sector exposure available", "-", "-"])

    return _styled_table(rows, [2.3 * inch, 1.8 * inch, 1.5 * inch])


def _build_risk_contributors_table(risk_contribution: list[dict]):
    rows = [["Ticker", "Name", "Sector", "Risk Contribution"]]

    top_contributors = risk_contribution[:5]

    for contributor in top_contributors:
        rows.append(
            [
                contributor["ticker"],
                contributor["name"],
                contributor["sector"],
                _format_percent(contributor["risk_contribution"]),
            ]
        )

    if len(rows) == 1:
        rows.append(["No contributors available", "-", "-", "-"])

    return _styled_table(rows, [0.9 * inch, 2.0 * inch, 1.5 * inch, 1.2 * inch])


def _build_stress_section(stress_result: dict, styles: dict):
    assumptions = ", ".join(
        f"{sector}: {shock}%"
        for sector, shock in DEFAULT_STRESS_SHOCKS.items()
    )

    elements = [
        Paragraph(f"Assumptions: {assumptions}", styles["body"]),
        Spacer(1, 0.08 * inch),
    ]

    if "error" in stress_result:
        elements.append(Paragraph(stress_result["error"], styles["body"]))
        return elements

    rows = [
        ["Original Value", "Stressed Value", "Impact Value", "Impact %"],
        [
            _format_currency(stress_result["original_value"]),
            _format_currency(stress_result["stressed_value"]),
            _format_currency(stress_result["impact_value"]),
            _format_percent(stress_result["impact_percent"]),
        ],
    ]

    elements.append(_styled_table(rows, [1.4 * inch] * 4))
    return elements


def _styled_table(rows: list[list[str]], column_widths: list[float]):
    table = Table(rows, colWidths=column_widths, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#082047")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("LEADING", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#ddd5c7")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#fffdf8")),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#24354c")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _try_generate_ai_summary(
    risk: dict,
    sector_exposure: list[dict],
    risk_contribution: list[dict],
) -> str:
    prompt = f"""
You are an investment risk analyst.

Write a concise risk summary for this PDF report using only the data below.
Do not provide financial advice or buy/sell recommendations.

Risk Metrics:
{risk}

Sector Exposure:
{sector_exposure}

Risk Contribution:
{risk_contribution[:5]}
"""

    try:
        summary = ask_ollama(prompt, timeout=2).strip()
    except Exception:
        return (
            "AI-generated risk summary unavailable. Ollama may not be running locally. "
            "The rest of this report was generated from calculated portfolio analytics."
        )

    return summary or (
        "AI-generated risk summary unavailable. Ollama returned an empty response."
    )


def _get_portfolio_name(portfolio_id: int) -> str | None:
    try:
        portfolios = load_portfolios()
    except Exception:
        return None

    match = portfolios[portfolios["portfolio_id"] == portfolio_id]

    if match.empty:
        return None

    return str(match.iloc[0]["portfolio_name"])


def _format_currency(value: float) -> str:
    return f"${value:,.2f}"


def _format_percent(value: float) -> str:
    return f"{value * 100:.2f}%"
