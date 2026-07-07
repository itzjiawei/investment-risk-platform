from pathlib import Path
from unittest.mock import Mock

import pytest

from app.services import performance_service


def _write_benchmark_csvs(data_dir: Path) -> None:
    data_dir.mkdir(exist_ok=True)
    (data_dir / "large_prices.csv").write_text(
        "\n".join(
            [
                "asset_id,date,close_price",
                "1,2026-07-01,100.0",
                "1,2026-07-02,101.0",
                "2,2026-07-01,50.0",
                "2,2026-07-02,52.0",
            ]
        ),
        encoding="utf-8",
    )
    (data_dir / "large_holdings.csv").write_text(
        "\n".join(
            [
                "portfolio_id,asset_id,quantity",
                "99,1,10",
                "99,2,20",
            ]
        ),
        encoding="utf-8",
    )


def test_large_dataset_benchmark_uses_configured_data_dir(tmp_path, monkeypatch):
    _write_benchmark_csvs(tmp_path)
    monkeypatch.setattr(performance_service, "DATA_DIR", tmp_path)

    result = performance_service.run_large_dataset_benchmark()

    assert result["dataset"] == "large synthetic portfolio dataset"
    assert result["price_rows"] == 4
    assert result["holding_rows"] == 2
    assert result["output_rows"] == 2
    assert result["pandas_time_seconds"] >= 0
    assert result["duckdb_time_seconds"] >= 0


def test_large_dataset_benchmark_reports_missing_files(tmp_path, monkeypatch):
    monkeypatch.setattr(performance_service, "DATA_DIR", tmp_path)

    with pytest.raises(FileNotFoundError, match="large_prices.csv"):
        performance_service.run_large_dataset_benchmark()


def test_large_dataset_benchmark_endpoint(client, monkeypatch):
    expected_response = {
        "dataset": "large synthetic portfolio dataset",
        "price_rows": 4,
        "holding_rows": 2,
        "output_rows": 2,
        "pandas_time_seconds": 0.01,
        "duckdb_time_seconds": 0.005,
        "duckdb_speedup": 2.0,
    }
    monkeypatch.setattr(
        "app.routers.performance.run_large_dataset_benchmark",
        Mock(return_value=expected_response),
    )

    response = client.get("/api/performance/large-benchmark")

    assert response.status_code == 200
    assert response.json() == expected_response


def test_large_dataset_benchmark_endpoint_returns_json_error(client, monkeypatch):
    monkeypatch.setattr(
        "app.routers.performance.run_large_dataset_benchmark",
        Mock(side_effect=FileNotFoundError("Large benchmark data files are missing")),
    )

    response = client.get("/api/performance/large-benchmark")

    assert response.status_code == 500
    assert response.json()["detail"] == "Large benchmark data files are missing"
