import { useState } from "react";
import axios from "axios";
import { API_BASE_URL } from "../config";

type BenchmarkResult = {
  dataset: string;
  price_rows: number;
  holding_rows: number;
  output_rows: number;
  pandas_time_seconds: number;
  duckdb_time_seconds: number;
  duckdb_speedup: number;
};

function PerformanceLab() {
  const [result, setResult] = useState<BenchmarkResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  function runBenchmark() {
    setLoading(true);
    setErrorMessage("");
    setResult(null);

    axios
      .get(`${API_BASE_URL}/api/performance/large-benchmark`)
      .then((res) => {
        setResult(res.data);
      })
      .catch((error) => {
        const detail = error.response?.data?.detail;
        setErrorMessage(
          detail || "Unable to run the benchmark. Please try again later."
        );
      })
      .finally(() => {
        setLoading(false);
      });
  }

  return (
    <section className="table-card">
      <div className="chart-header">
        <div>
          <p className="eyebrow">Performance Engineering</p>
          <h2>DuckDB vs Pandas Benchmark</h2>
        </div>
      </div>

      <p className="subtitle">
        Benchmark portfolio valuation on a large synthetic dataset to compare
        Pandas dataframe processing against DuckDB analytical SQL execution.
      </p>

      <button className="primary-button" onClick={runBenchmark} disabled={loading}>
        {loading ? "Running Benchmark..." : "Run Large Dataset Benchmark"}
      </button>

      {errorMessage && (
        <p className="status-message">{errorMessage}</p>
      )}

      {result && (
        <div className="stress-result">
          <div>
            <p>Price Rows</p>
            <h3>{result.price_rows.toLocaleString()}</h3>
          </div>

          <div>
            <p>Pandas Time</p>
            <h3>{result.pandas_time_seconds}s</h3>
          </div>

          <div>
            <p>DuckDB Time</p>
            <h3>{result.duckdb_time_seconds}s</h3>
          </div>

          <div>
            <p>DuckDB Speedup</p>
            <h3>{result.duckdb_speedup}x</h3>
          </div>
        </div>
      )}
    </section>
  );
}

export default PerformanceLab;
