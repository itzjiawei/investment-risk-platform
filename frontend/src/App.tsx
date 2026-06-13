import { useEffect, useState } from "react";
import axios from "axios";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
  BarChart,
  Bar,
  CartesianGrid,
} from "recharts";
import "./App.css";
import PerformanceLab from "./pages/PerformanceLab";
import PortfolioComparisonPage from "./pages/PortfolioComparisonPage";
import AiCopilotPage from "./pages/AiCopilotPage";

type Portfolio = {
  portfolio_id: number;
  portfolio_name: string;
};

type RiskMetrics = {
  portfolio_id: number;
  latest_value: number;
  latest_daily_return: number;
  annualized_return: number;
  annualized_volatility: number;
  sharpe_ratio: number;
  max_drawdown: number;
  historical_var_95: number;
};

type ReturnPoint = {
  date: string;
  portfolio_value: number;
  daily_return: number;
};

type Holding = {
  ticker: string;
  name: string;
  sector: string;
  country: string;
  quantity: number;
  latest_price: number;
  market_value: number;
  weight: number;
};

type SectorExposure = {
  sector: string;
  market_value: number;
  weight: number;
};

type RiskContribution = {
  ticker: string;
  name: string;
  sector: string;
  weight: number;
  daily_volatility: number;
  risk_score: number;
  risk_contribution: number;
};

type StressTestResult = {
  portfolio_id: number;
  original_value: number;
  stressed_value: number;
  impact_value: number;
  impact_percent: number;
  breakdown: {
    ticker: string;
    name: string;
    sector: string;
    market_value: number;
    shock_percent: number;
    estimated_loss: number;
    stressed_value: number;
  }[];
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

const PIE_COLORS = [
  "#38bdf8",
  "#22c55e",
  "#f97316",
  "#eab308",
  "#a855f7",
  "#ef4444",
];

function App() {
  const [activePage, setActivePage] = useState<"dashboard" | "performance" | "comparison"| "AI">(
    "dashboard"
  );

  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolioId, setSelectedPortfolioId] = useState(1);
  const [risk, setRisk] = useState<RiskMetrics | null>(null);
  const [returns, setReturns] = useState<ReturnPoint[]>([]);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [sectorExposure, setSectorExposure] = useState<SectorExposure[]>([]);
  const [riskContribution, setRiskContribution] = useState<RiskContribution[]>(
    []
  );

  const [stressShocks, setStressShocks] = useState({
    Technology: -20,
    Semiconductors: -30,
    ETF: -15,
    Commodities: 5,
    Financials: -10,
  });

  const [stressResult, setStressResult] =
    useState<StressTestResult | null>(null);

  useEffect(() => {
    axios.get(`${API_BASE_URL}/api/portfolios`).then((res) => {
      setPortfolios(res.data);
    });
  }, []);

  useEffect(() => {
    axios
      .get(`${API_BASE_URL}/api/portfolio/${selectedPortfolioId}/risk`)
      .then((res) => {
        setRisk(res.data);
      });

    axios
      .get(`${API_BASE_URL}/api/portfolio/${selectedPortfolioId}/returns`)
      .then((res) => {
        const formattedReturns = res.data.map((point: ReturnPoint) => ({
          ...point,
          date: point.date.slice(0, 10),
        }));

        setReturns(formattedReturns);
      });

    axios
      .get(`${API_BASE_URL}/api/portfolio/${selectedPortfolioId}/holdings`)
      .then((res) => {
        setHoldings(res.data);
      });

    axios
      .get(
        `${API_BASE_URL}/api/portfolio/${selectedPortfolioId}/sector-exposure`
      )
      .then((res) => {
        setSectorExposure(res.data);
      });

    axios
      .get(
        `${API_BASE_URL}/api/portfolio/${selectedPortfolioId}/risk-contribution`
      )
      .then((res) => {
        setRiskContribution(res.data);
      });
  }, [selectedPortfolioId]);

  function runStressTest() {
    axios
      .post(`${API_BASE_URL}/api/portfolio/${selectedPortfolioId}/stress-test`, {
        shocks: stressShocks,
      })
      .then((res) => {
        setStressResult(res.data);
      });
  }

  return (
    <main className="page">
      <div className="nav-tabs">
        <button
          className={activePage === "dashboard" ? "active-tab" : ""}
          onClick={() => setActivePage("dashboard")}
        >
          Dashboard
        </button>

        <button
          className={activePage === "performance" ? "active-tab" : ""}
          onClick={() => setActivePage("performance")}
        >
          Performance Lab
        </button>

        <button
          className={activePage === "comparison" ? "active-tab" : ""}
          onClick={() => setActivePage("comparison")}
        >
          Comparison
        </button>

        <button
          className={activePage === "AI" ? "active-tab" : ""}
          onClick={() => setActivePage("AI")}
        >
          AI Copilot
        </button>
      </div>

      {activePage === "performance" && <PerformanceLab />}
      {activePage === "comparison" && <PortfolioComparisonPage />}
      {activePage === "AI" && <AiCopilotPage />}

      {activePage === "dashboard" && (
        <>
          <section className="hero">
            <p className="eyebrow">Investment Risk Analytics</p>
            <h1>Portfolio Risk Dashboard</h1>
            <p className="subtitle">
              Monitor portfolio value, returns, volatility and risk indicators
              from scalable analytics APIs.
            </p>
          </section>

          <section className="toolbar">
            <label>Portfolio</label>
            <select
              value={selectedPortfolioId}
              onChange={(e) => setSelectedPortfolioId(Number(e.target.value))}
            >
              {portfolios.map((portfolio) => (
                <option
                  key={portfolio.portfolio_id}
                  value={portfolio.portfolio_id}
                >
                  {portfolio.portfolio_name}
                </option>
              ))}
            </select>
          </section>

          {risk && (
            <section className="metrics-grid">
              <div className="metric-card">
                <p>Latest Value</p>
                <h2>{formatCurrency(risk.latest_value)}</h2>
              </div>

              <div className="metric-card">
                <p>Annualized Return</p>
                <h2>{formatPercent(risk.annualized_return)}</h2>
              </div>

              <div className="metric-card">
                <p>Annualized Volatility</p>
                <h2>{formatPercent(risk.annualized_volatility)}</h2>
              </div>

              <div className="metric-card">
                <p>Sharpe Ratio</p>
                <h2>{risk.sharpe_ratio}</h2>
              </div>

              <div className="metric-card">
                <p>Max Drawdown</p>
                <h2>{formatPercent(risk.max_drawdown)}</h2>
              </div>

              <div className="metric-card">
                <p>Historical VaR 95%</p>
                <h2>{formatPercent(risk.historical_var_95)}</h2>
              </div>
            </section>
          )}

          <section className="chart-card">
            <div className="chart-header">
              <div>
                <p className="eyebrow">Performance</p>
                <h2>Portfolio Value Over Time</h2>
              </div>
            </div>

            <div className="chart-wrapper">
              <ResponsiveContainer width="100%" height={380}>
                <LineChart data={returns}>
                  <XAxis
                    dataKey="date"
                    minTickGap={40}
                    tick={{ fill: "#94a3b8" }}
                  />
                  <YAxis
                    tick={{ fill: "#94a3b8" }}
                    tickFormatter={(value) => `$${Math.round(value / 1000)}k`}
                  />
                  <Tooltip
                    formatter={(value) => [
                      formatCurrency(Number(value)),
                      "Portfolio Value",
                    ]}
                  />
                  <Line
                    type="monotone"
                    dataKey="portfolio_value"
                    stroke="#38bdf8"
                    strokeWidth={3}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="table-card">
            <div className="chart-header">
              <div>
                <p className="eyebrow">Composition</p>
                <h2>Portfolio Holdings</h2>
              </div>
            </div>

            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Ticker</th>
                    <th>Name</th>
                    <th>Sector</th>
                    <th>Country</th>
                    <th>Quantity</th>
                    <th>Latest Price</th>
                    <th>Market Value</th>
                    <th>Weight</th>
                  </tr>
                </thead>

                <tbody>
                  {holdings.map((holding) => (
                    <tr key={holding.ticker}>
                      <td>{holding.ticker}</td>
                      <td>{holding.name}</td>
                      <td>{holding.sector}</td>
                      <td>{holding.country}</td>
                      <td>{holding.quantity.toLocaleString()}</td>
                      <td>{formatCurrency(holding.latest_price)}</td>
                      <td>{formatCurrency(holding.market_value)}</td>
                      <td>{formatPercent(holding.weight)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="chart-card" style={{ marginTop: "24px" }}>
            <div className="chart-header">
              <div>
                <p className="eyebrow">Allocation</p>
                <h2>Sector Exposure</h2>
              </div>
            </div>

            <div className="chart-wrapper">
              <ResponsiveContainer width="100%" height={400}>
                <PieChart>
                  <Pie
                    data={sectorExposure}
                    dataKey="market_value"
                    nameKey="sector"
                    outerRadius={140}
                    label={(props) =>
                      `${((props.percent ?? 0) * 100).toFixed(1)}%`
                    }
                  >
                    {sectorExposure.map((_, index) => (
                      <Cell
                        key={index}
                        fill={PIE_COLORS[index % PIE_COLORS.length]}
                      />
                    ))}
                  </Pie>

                  <Tooltip
                    formatter={(value) => [
                      formatCurrency(Number(value)),
                      "Market Value",
                    ]}
                  />

                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="chart-card" style={{ marginTop: "24px" }}>
            <div className="chart-header">
              <div>
                <p className="eyebrow">Risk Attribution</p>
                <h2>Risk Contribution by Asset</h2>
              </div>
            </div>

            <div className="chart-wrapper">
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={riskContribution} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />

                  <XAxis
                    type="number"
                    tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                  />

                  <YAxis dataKey="ticker" type="category" width={80} />

                  <Tooltip
                    formatter={(value) => [
                      `${(Number(value) * 100).toFixed(2)}%`,
                      "Risk Contribution",
                    ]}
                  />

                  <Bar dataKey="risk_contribution" fill="#38bdf8" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="table-card">
            <div className="chart-header">
              <div>
                <p className="eyebrow">Scenario Analysis</p>
                <h2>Custom Stress Test</h2>
              </div>
            </div>

            <div className="stress-grid">
              {Object.entries(stressShocks).map(([sector, value]) => (
                <div className="stress-input" key={sector}>
                  <label>{sector}</label>
                  <input
                    type="number"
                    value={value}
                    onChange={(e) =>
                      setStressShocks({
                        ...stressShocks,
                        [sector]: Number(e.target.value),
                      })
                    }
                  />
                  <span>%</span>
                </div>
              ))}
            </div>

            <button className="primary-button" onClick={runStressTest}>
              Run Stress Test
            </button>

            {stressResult && (
              <div className="stress-result">
                <div>
                  <p>Original Value</p>
                  <h3>{formatCurrency(stressResult.original_value)}</h3>
                </div>
                <div>
                  <p>Stressed Value</p>
                  <h3>{formatCurrency(stressResult.stressed_value)}</h3>
                </div>
                <div>
                  <p>Estimated Impact</p>
                  <h3>{formatCurrency(stressResult.impact_value)}</h3>
                </div>
                <div>
                  <p>Impact %</p>
                  <h3>{formatPercent(stressResult.impact_percent)}</h3>
                </div>
              </div>
            )}
          </section>
        </>
      )}
    </main>
  )};


export default App;
