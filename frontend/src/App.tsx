import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";
import PerformanceLab from "./pages/PerformanceLab";
import PortfolioComparisonPage from "./pages/PortfolioComparisonPage";
import AiCopilotPage from "./pages/AiCopilotPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import DashboardPage from "./pages/DashboardPage";
import { API_BASE_URL } from "./config";

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

type MarketDataRefreshResult = {
  updated_tickers: string[];
  failed_tickers: {
    ticker: string;
    yfinance_ticker?: string;
    reason: string;
  }[];
  rows_inserted: number;
  message: string;
};

function formatCurrency(value: number) {
  return `$${value.toLocaleString(undefined, {
    maximumFractionDigits: 2,
  })}`;
}

function formatPercent(value: number) {
  return `${(value * 100).toFixed(2)}%`;
}

function App() {
  const [activePage, setActivePage] = useState<
    "dashboard" | "performance" | "comparison" | "AI" | "analytics"
  >(
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
  const [marketDataLoading, setMarketDataLoading] = useState(false);
  const [marketDataMessage, setMarketDataMessage] = useState("");

  useEffect(() => {
    axios.get(`${API_BASE_URL}/api/portfolios`).then((res) => {
      setPortfolios(res.data);
    });
  }, []);

  function loadDashboardData(portfolioId: number) {
    axios
      .get(`${API_BASE_URL}/api/portfolio/${portfolioId}/risk`)
      .then((res) => {
        setRisk(res.data);
      });

    axios
      .get(`${API_BASE_URL}/api/portfolio/${portfolioId}/returns`)
      .then((res) => {
        const formattedReturns = res.data.map((point: ReturnPoint) => ({
          ...point,
          date: point.date.slice(0, 10),
        }));

        setReturns(formattedReturns);
      });

    axios
      .get(`${API_BASE_URL}/api/portfolio/${portfolioId}/holdings`)
      .then((res) => {
        setHoldings(res.data);
      });

    axios
      .get(`${API_BASE_URL}/api/portfolio/${portfolioId}/sector-exposure`)
      .then((res) => {
        setSectorExposure(res.data);
      });

    axios
      .get(`${API_BASE_URL}/api/portfolio/${portfolioId}/risk-contribution`)
      .then((res) => {
        setRiskContribution(res.data);
      });
  }

  useEffect(() => {
    loadDashboardData(selectedPortfolioId);
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

  function refreshMarketData() {
    setMarketDataLoading(true);
    setMarketDataMessage("");

    axios
      .post<MarketDataRefreshResult>(
        `${API_BASE_URL}/api/portfolio/${selectedPortfolioId}/market-data/refresh`
      )
      .then((res) => {
        const failedTickers = res.data.failed_tickers
          .map((failedTicker) => {
            const yfinanceLabel =
              failedTicker.yfinance_ticker &&
              failedTicker.yfinance_ticker !== failedTicker.ticker
                ? ` (${failedTicker.yfinance_ticker})`
                : "";

            return `${failedTicker.ticker}${yfinanceLabel}: ${failedTicker.reason}`;
          })
          .join("; ");
        const failedMessage = failedTickers
          ? ` Failed tickers: ${failedTickers}.`
          : "";

        setMarketDataMessage(
          `${res.data.message}. Inserted ${res.data.rows_inserted} new price rows.${failedMessage}`
        );
        loadDashboardData(selectedPortfolioId);
      })
      .catch(() => {
        setMarketDataMessage("Market data refresh failed. Please try again.");
      })
      .finally(() => {
        setMarketDataLoading(false);
      });
  }

  function downloadRiskReport() {
    axios
      .get(
        `${API_BASE_URL}/api/portfolio/${selectedPortfolioId}/risk-report/pdf`,
        {
          responseType: "blob",
        }
      )
      .then((res) => {
        const contentDisposition = res.headers["content-disposition"];
        const filenameMatch = contentDisposition?.match(/filename="(.+)"/);
        const filename =
          filenameMatch?.[1] ??
          `portfolio-${selectedPortfolioId}-risk-report.pdf`;
        const url = window.URL.createObjectURL(
          new Blob([res.data], { type: "application/pdf" })
        );
        const link = document.createElement("a");

        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      });
  }

  return (
    <main className="page">
      <header className="app-header">
        <div className="brand-lockup">
          <div className="brand-mark" aria-hidden="true">
            IR
          </div>
          <div>
            <p className="brand-kicker">Sovereign Risk Console</p>
            <h1>Investment Risk Platform</h1>
          </div>
        </div>

        <div className="header-status">
          <span className="status-dot" aria-hidden="true" />
          Live analytics
        </div>
      </header>

      <nav className="nav-tabs" aria-label="Primary sections">
        {[
          ["dashboard", "Dashboard"],
          ["analytics", "Analytics"],
          ["comparison", "Comparison"],
          ["AI", "AI Copilot"],
          ["performance", "Performance Lab"],
        ].map(([page, label]) => (
          <button
            key={page}
            className={activePage === page ? "active-tab" : ""}
            onClick={() =>
              setActivePage(
                page as "dashboard" | "performance" | "comparison" | "AI" | "analytics"
              )
            }
          >
            {label}
          </button>
        ))}
      </nav>

      <div className="workspace">
        {activePage === "performance" && <PerformanceLab />}
        {activePage === "comparison" && <PortfolioComparisonPage />}
        {activePage === "AI" && <AiCopilotPage />}
        {activePage === "analytics" && (
          <AnalyticsPage
            holdings={holdings}
            riskContribution={riskContribution}
            stressShocks={stressShocks}
            stressResult={stressResult}
            setStressShocks={setStressShocks}
            runStressTest={runStressTest}
            formatCurrency={formatCurrency}
            formatPercent={formatPercent}
          />
        )}

        {activePage === "dashboard" && (
          <DashboardPage
            portfolios={portfolios}
            selectedPortfolioId={selectedPortfolioId}
            setSelectedPortfolioId={setSelectedPortfolioId}
            risk={risk}
            returns={returns}
            sectorExposure={sectorExposure}
            formatCurrency={formatCurrency}
            formatPercent={formatPercent}
            downloadRiskReport={downloadRiskReport}
            refreshMarketData={refreshMarketData}
            marketDataLoading={marketDataLoading}
            marketDataMessage={marketDataMessage}
          />
        )}
      </div>
    </main>
  )};


export default App;
