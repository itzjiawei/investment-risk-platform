from dataclasses import dataclass
import logging
from typing import Any, Protocol

from fastapi import Request

from app.config import (
    NOTIFICATION_REPORT_RECIPIENTS,
)
from app.database.repository import load_portfolios
from app.services.audit_service import create_audit_log
from app.services.pdf_report_service import generate_pdf_risk_report
from app.services.portfolio_service import calculate_portfolio_risk


logger = logging.getLogger(__name__)


class NotificationError(Exception):
    pass


@dataclass
class EmailAttachment:
    filename: str
    content: bytes
    mime_type: str


@dataclass
class EmailMessage:
    recipient_email: str
    subject: str
    text_content: str
    html_content: str
    attachments: list[EmailAttachment]


@dataclass
class NotificationResult:
    success: bool
    message: str
    provider_message_id: str | None = None


class EmailProvider(Protocol):
    def send_email(self, message: EmailMessage) -> NotificationResult:
        ...


class ConsoleNotificationProvider:
    def send_email(self, message: EmailMessage) -> NotificationResult:
        attachment_names = [
            attachment.filename
            for attachment in message.attachments
        ]
        logger.info(
            "Notification would have been sent to %s with subject %s and attachments %s",
            message.recipient_email,
            message.subject,
            attachment_names,
        )
        return NotificationResult(
            success=True,
            message="Notification logged to console",
        )


class NotificationService:
    def __init__(self, email_provider: EmailProvider | None = None):
        self.email_provider = email_provider or ConsoleNotificationProvider()

    def send_portfolio_risk_report(
        self,
        portfolio_id: int,
        recipient_email: str,
        triggered_by: str,
        user: dict | None = None,
        request: Request | None = None,
    ) -> NotificationResult:
        try:
            risk = calculate_portfolio_risk(portfolio_id)

            if "error" in risk:
                raise NotificationError(risk["error"])

            pdf_bytes = generate_pdf_risk_report(portfolio_id)
            portfolio_name = _get_portfolio_name(portfolio_id)
            message = _build_risk_report_email(
                portfolio_id=portfolio_id,
                portfolio_name=portfolio_name,
                recipient_email=recipient_email,
                risk=risk,
                pdf_bytes=pdf_bytes,
            )
            result = self.email_provider.send_email(message)
            _audit_email(
                status="success",
                portfolio_id=portfolio_id,
                recipient_email=recipient_email,
                triggered_by=triggered_by,
                provider_message_id=result.provider_message_id,
                user=user,
                request=request,
            )
            return result
        except Exception as exc:
            logger.exception("Failed to send portfolio risk report email")
            _audit_email(
                status="failed",
                portfolio_id=portfolio_id,
                recipient_email=recipient_email,
                triggered_by=triggered_by,
                error=str(exc),
                user=user,
                request=request,
            )
            raise NotificationError(str(exc)) from exc


def send_scheduled_daily_risk_reports(
    refresh_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    if not NOTIFICATION_REPORT_RECIPIENTS:
        logger.info("No scheduled report recipients configured")
        return []

    service = NotificationService()
    results = []

    for portfolio_id in _get_all_portfolio_ids():
        for recipient_email in NOTIFICATION_REPORT_RECIPIENTS:
            try:
                result = service.send_portfolio_risk_report(
                    portfolio_id=portfolio_id,
                    recipient_email=recipient_email,
                    triggered_by="scheduled_market_refresh",
                )
                results.append(
                    {
                        "portfolio_id": portfolio_id,
                        "recipient_email": recipient_email,
                        "status": "success",
                        "message": result.message,
                    }
                )
            except NotificationError as exc:
                results.append(
                    {
                        "portfolio_id": portfolio_id,
                        "recipient_email": recipient_email,
                        "status": "failed",
                        "message": str(exc),
                    }
                )

    logger.info(
        "Scheduled risk report email flow completed after market refresh: %s",
        refresh_summary,
    )
    return results


def _build_risk_report_email(
    portfolio_id: int,
    portfolio_name: str | None,
    recipient_email: str,
    risk: dict[str, Any],
    pdf_bytes: bytes,
) -> EmailMessage:
    title = f"Portfolio {portfolio_id}"
    if portfolio_name:
        title += f" - {portfolio_name}"

    text_content = (
        f"Daily Risk Report for {title}\n\n"
        f"Latest value: {_format_currency(risk['latest_value'])}\n"
        f"Annualized return: {_format_percent(risk['annualized_return'])}\n"
        f"Annualized volatility: {_format_percent(risk['annualized_volatility'])}\n"
        f"Sharpe ratio: {risk['sharpe_ratio']}\n"
        f"Max drawdown: {_format_percent(risk['max_drawdown'])}\n"
        f"Historical VaR 95%: {_format_percent(risk['historical_var_95'])}\n"
    )
    html_content = f"""
    <h2>Daily Risk Report</h2>
    <p><strong>{title}</strong></p>
    <ul>
      <li>Latest value: {_format_currency(risk['latest_value'])}</li>
      <li>Annualized return: {_format_percent(risk['annualized_return'])}</li>
      <li>Annualized volatility: {_format_percent(risk['annualized_volatility'])}</li>
      <li>Sharpe ratio: {risk['sharpe_ratio']}</li>
      <li>Max drawdown: {_format_percent(risk['max_drawdown'])}</li>
      <li>Historical VaR 95%: {_format_percent(risk['historical_var_95'])}</li>
    </ul>
    <p>The updated PDF risk report is attached.</p>
    """

    return EmailMessage(
        recipient_email=recipient_email,
        subject=f"Daily Risk Report - {title}",
        text_content=text_content,
        html_content=html_content,
        attachments=[
            EmailAttachment(
                filename=f"portfolio-{portfolio_id}-risk-report.pdf",
                content=pdf_bytes,
                mime_type="application/pdf",
            )
        ],
    )


def _audit_email(
    status: str,
    portfolio_id: int,
    recipient_email: str,
    triggered_by: str,
    user: dict | None = None,
    request: Request | None = None,
    provider_message_id: str | None = None,
    error: str | None = None,
) -> None:
    create_audit_log(
        action="risk_report_email",
        status=status,
        user=user,
        request=request,
        resource_type="portfolio",
        resource_id=portfolio_id,
        metadata={
            "recipient_email": recipient_email,
            "triggered_by": triggered_by,
            "provider": "console",
            "provider_message_id": provider_message_id,
            "error": error,
        },
    )


def _get_all_portfolio_ids() -> list[int]:
    portfolios = load_portfolios()
    if portfolios.empty:
        return []

    return [
        int(portfolio_id)
        for portfolio_id in portfolios["portfolio_id"].dropna().tolist()
    ]


def _get_portfolio_name(portfolio_id: int) -> str | None:
    portfolios = load_portfolios()
    match = portfolios[portfolios["portfolio_id"] == portfolio_id]

    if match.empty:
        return None

    return str(match.iloc[0]["portfolio_name"])


def _format_currency(value: float) -> str:
    return f"${value:,.2f}"


def _format_percent(value: float) -> str:
    return f"{value * 100:.2f}%"
