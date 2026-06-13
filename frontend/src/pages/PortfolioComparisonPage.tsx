import { useEffect, useState } from "react";
import axios from "axios";

type Portfolio = {
  portfolio_id: number;
  portfolio_name: string;
};

type PortfolioComparison = {
  portfolio_id: number;
  latest_value: number;
  annualized_return: number;
  annualized_volatility: number;
  sharpe_ratio: number;
  max_drawdown: number;
  historical_var_95: number;
};

type AiPortfolioComparison = {
  portfolio_ids: number[];
  summary: string;
};

const API_BASE_URL = "http://127.0.0.1:8000";

function formatCurrency(value: number) {
  return `$${value.toLocaleString(undefined, {
    maximumFractionDigits: 2,
  })}`;
}

function formatPercent(value: number) {
  return `${(value * 100).toFixed(2)}%`;
}

function PortfolioComparisonPage() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [comparisonPortfolioA, setComparisonPortfolioA] = useState(1);
  const [comparisonPortfolioB, setComparisonPortfolioB] = useState(2);
  const [comparisonResult, setComparisonResult] = useState<
    PortfolioComparison[]
  >([]);

  const [aiComparison, setAiComparison] =
    useState<AiPortfolioComparison | null>(null);

  const [aiComparisonLoading, setAiComparisonLoading] = useState(false);

  useEffect(() => {
    axios.get(`${API_BASE_URL}/api/portfolios`).then((res) => {
      setPortfolios(res.data);
    });
  }, []);

  function comparePortfolios() {
    axios
      .post(`${API_BASE_URL}/api/portfolio/compare`, {
        portfolio_ids: [comparisonPortfolioA, comparisonPortfolioB],
      })
      .then((res) => {
        setComparisonResult(res.data);
      });
  }

  function generateAiComparison() {
    setAiComparisonLoading(true);
    setAiComparison(null);

    axios
      .post(`${API_BASE_URL}/api/portfolio/compare-ai`, {
        portfolio_ids: [comparisonPortfolioA, comparisonPortfolioB],
      })
      .then((res) => {
        setAiComparison(res.data);
      })
      .finally(() => {
        setAiComparisonLoading(false);
      });
  }

  return (
    <section className="table-card">
      <div className="chart-header">
        <div>
          <p className="eyebrow">Portfolio Analysis</p>
          <h2>Portfolio Comparison</h2>
        </div>
      </div>

      <div className="comparison-controls">
        <select
          value={comparisonPortfolioA}
          onChange={(e) => setComparisonPortfolioA(Number(e.target.value))}
        >
          {portfolios.map((portfolio) => (
            <option key={portfolio.portfolio_id} value={portfolio.portfolio_id}>
              {portfolio.portfolio_name}
            </option>
          ))}
        </select>

        <select
          value={comparisonPortfolioB}
          onChange={(e) => setComparisonPortfolioB(Number(e.target.value))}
        >
          {portfolios.map((portfolio) => (
            <option key={portfolio.portfolio_id} value={portfolio.portfolio_id}>
              {portfolio.portfolio_name}
            </option>
          ))}
        </select>

        <div style={{ display: "flex", gap: "16px" }}>
          <button className="primary-button" onClick={comparePortfolios}>
            Compare
          </button>

          <button
            className="primary-button"
            onClick={generateAiComparison}
            disabled={aiComparisonLoading}
          >
            {aiComparisonLoading ? "Analyzing..." : "AI Compare"}
          </button>
        </div>
      </div>

      {comparisonResult.length > 0 && (
        <div className="table-wrapper" style={{ marginTop: "20px" }}>
          <table>
            <thead>
              <tr>
                <th>Metric</th>
                {comparisonResult.map((portfolio) => (
                  <th key={portfolio.portfolio_id}>
                    Portfolio {portfolio.portfolio_id}
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              <tr>
                <td>Latest Value</td>
                {comparisonResult.map((portfolio) => (
                  <td key={portfolio.portfolio_id}>
                    {formatCurrency(portfolio.latest_value)}
                  </td>
                ))}
              </tr>

              <tr>
                <td>Annualized Return</td>
                {comparisonResult.map((portfolio) => (
                  <td key={portfolio.portfolio_id}>
                    {formatPercent(portfolio.annualized_return)}
                  </td>
                ))}
              </tr>

              <tr>
                <td>Annualized Volatility</td>
                {comparisonResult.map((portfolio) => (
                  <td key={portfolio.portfolio_id}>
                    {formatPercent(portfolio.annualized_volatility)}
                  </td>
                ))}
              </tr>

              <tr>
                <td>Sharpe Ratio</td>
                {comparisonResult.map((portfolio) => (
                  <td key={portfolio.portfolio_id}>
                    {portfolio.sharpe_ratio}
                  </td>
                ))}
              </tr>

              <tr>
                <td>Max Drawdown</td>
                {comparisonResult.map((portfolio) => (
                  <td key={portfolio.portfolio_id}>
                    {formatPercent(portfolio.max_drawdown)}
                  </td>
                ))}
              </tr>

              <tr>
                <td>Historical VaR 95%</td>
                {comparisonResult.map((portfolio) => (
                  <td key={portfolio.portfolio_id}>
                    {formatPercent(portfolio.historical_var_95)}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      )}

      {aiComparison && (
        <div className="ai-summary-box">
          <h3>AI Portfolio Comparison</h3>
          <pre>{aiComparison.summary}</pre>
        </div>
      )}
    </section>
  );
}

export default PortfolioComparisonPage;