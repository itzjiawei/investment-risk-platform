from unittest.mock import Mock
import logging

import pandas as pd
import pytest

from app.services.notification_service import (
    EmailAttachment,
    EmailMessage,
    NotificationError,
    NotificationResult,
    NotificationService,
    ConsoleNotificationProvider,
)


class FakeEmailProvider:
    def __init__(self, result=None, error: Exception | None = None):
        self.result = result or NotificationResult(
            success=True,
            message="Email sent",
            provider_message_id="message-123",
        )
        self.error = error
        self.messages = []

    def send_email(self, message: EmailMessage):
        self.messages.append(message)

        if self.error:
            raise self.error

        return self.result


def test_console_provider_logs_notification(caplog):
    caplog.set_level(logging.INFO)
    provider = ConsoleNotificationProvider()
    result = provider.send_email(
        EmailMessage(
            recipient_email="admin@example.com",
            subject="Risk Report",
            text_content="Plain report",
            html_content="<p>Report</p>",
            attachments=[
                EmailAttachment(
                    filename="report.pdf",
                    content=b"PDF bytes",
                    mime_type="application/pdf",
                )
            ],
        )
    )

    assert result.success is True
    assert result.message == "Notification logged to console"
    assert "Notification would have been sent to admin@example.com" in caplog.text


def test_notification_service_sends_pdf_report(monkeypatch):
    fake_provider = FakeEmailProvider()
    mocked_audit = Mock()
    monkeypatch.setattr(
        "app.services.notification_service.calculate_portfolio_risk",
        Mock(
            return_value={
                "portfolio_id": 1,
                "latest_value": 100000,
                "annualized_return": 0.1,
                "annualized_volatility": 0.2,
                "sharpe_ratio": 0.4,
                "max_drawdown": -0.1,
                "historical_var_95": -0.02,
            }
        ),
    )
    monkeypatch.setattr(
        "app.services.notification_service.generate_pdf_risk_report",
        Mock(return_value=b"%PDF-1.4 test"),
    )
    monkeypatch.setattr(
        "app.services.notification_service.load_portfolios",
        Mock(
            return_value=pd.DataFrame(
                [{"portfolio_id": 1, "portfolio_name": "Global Growth Portfolio"}]
            )
        ),
    )
    monkeypatch.setattr(
        "app.services.notification_service.create_audit_log",
        mocked_audit,
    )

    result = NotificationService(fake_provider).send_portfolio_risk_report(
        portfolio_id=1,
        recipient_email="admin@example.com",
        triggered_by="manual_admin",
    )

    assert result.success is True
    assert fake_provider.messages[0].recipient_email == "admin@example.com"
    assert fake_provider.messages[0].attachments[0].filename == (
        "portfolio-1-risk-report.pdf"
    )
    assert mocked_audit.call_args.kwargs["status"] == "success"
    assert mocked_audit.call_args.kwargs["metadata"]["recipient_email"] == (
        "admin@example.com"
    )


def test_notification_service_audits_send_failure(monkeypatch):
    mocked_audit = Mock()
    monkeypatch.setattr(
        "app.services.notification_service.calculate_portfolio_risk",
        Mock(
            return_value={
                "portfolio_id": 1,
                "latest_value": 100000,
                "annualized_return": 0.1,
                "annualized_volatility": 0.2,
                "sharpe_ratio": 0.4,
                "max_drawdown": -0.1,
                "historical_var_95": -0.02,
            }
        ),
    )
    monkeypatch.setattr(
        "app.services.notification_service.generate_pdf_risk_report",
        Mock(return_value=b"%PDF-1.4 test"),
    )
    monkeypatch.setattr(
        "app.services.notification_service.load_portfolios",
        Mock(return_value=pd.DataFrame([])),
    )
    monkeypatch.setattr(
        "app.services.notification_service.create_audit_log",
        mocked_audit,
    )

    with pytest.raises(NotificationError):
        NotificationService(
            FakeEmailProvider(error=NotificationError("Notification failed"))
        ).send_portfolio_risk_report(
            portfolio_id=1,
            recipient_email="admin@example.com",
            triggered_by="manual_admin",
        )

    assert mocked_audit.call_args.kwargs["status"] == "failed"
    assert mocked_audit.call_args.kwargs["metadata"]["error"] is not None
