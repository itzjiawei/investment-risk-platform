import { useEffect, useRef, useState } from "react";
import axios from "axios";
import "./App.css";
import PerformanceLab from "./pages/PerformanceLab";
import PortfolioComparisonPage from "./pages/PortfolioComparisonPage";
import AiCopilotPage from "./pages/AiCopilotPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import AuditLogsPage from "./pages/AuditLogsPage";
import BackgroundJobsPage from "./pages/BackgroundJobsPage";
import { API_BASE_URL } from "./config";

type Portfolio = {
  portfolio_id: number;
  portfolio_name: string;
};

type AuthUser = {
  email: string;
  full_name: string;
  role: "admin" | "portfolio_manager" | "analyst" | "viewer";
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

type DashboardData = {
  risk: RiskMetrics;
  returns: ReturnPoint[];
  holdings: Holding[];
  sector_exposure: SectorExposure[];
  risk_contribution: RiskContribution[];
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
    category?: string;
    period?: string;
    interval?: string;
    source?: string;
  }[];
  rows_inserted: number;
  message: string;
};

const AUTH_TOKEN_STORAGE_KEY = "investment-risk-auth-token";
const AUTH_USER_STORAGE_KEY = "investment-risk-auth-user";

function formatCurrency(value: number) {
  return `$${value.toLocaleString(undefined, {
    maximumFractionDigits: 2,
  })}`;
}

function formatPercent(value: number) {
  return `${(value * 100).toFixed(2)}%`;
}

function App() {
  const [authToken, setAuthToken] = useState(() =>
    localStorage.getItem(AUTH_TOKEN_STORAGE_KEY)
  );
  const [authUser, setAuthUser] = useState<AuthUser | null>(() => {
    const storedUser = localStorage.getItem(AUTH_USER_STORAGE_KEY);

    if (!storedUser) return null;

    try {
      return JSON.parse(storedUser) as AuthUser;
    } catch {
      localStorage.removeItem(AUTH_USER_STORAGE_KEY);
      return null;
    }
  });
  const [activePage, setActivePage] = useState<
    | "dashboard"
    | "performance"
    | "comparison"
    | "AI"
    | "analytics"
    | "audit"
    | "jobs"
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
  const [dashboardLoading, setDashboardLoading] = useState(false);
  const [dashboardMessage, setDashboardMessage] = useState("");
  const dashboardRequestIdRef = useRef(0);
  const canRefreshMarketData =
    authUser?.role === "admin" || authUser?.role === "portfolio_manager";
  const canExportPdf =
    authUser?.role === "admin" ||
    authUser?.role === "portfolio_manager" ||
    authUser?.role === "analyst";
  const canUseAi = canExportPdf;
  const canViewAuditLogs = authUser?.role === "admin";

  useEffect(() => {
    if (!authToken) {
      delete axios.defaults.headers.common.Authorization;
      return;
    }

    axios.defaults.headers.common.Authorization = `Bearer ${authToken}`;
  }, [authToken]);

  useEffect(() => {
    if (!authToken) return;

    const interceptorId = axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          handleLogout();
        }

        return Promise.reject(error);
      }
    );

    return () => {
      axios.interceptors.response.eject(interceptorId);
    };
  }, [authToken]);

  useEffect(() => {
    if (!authToken) return;

    axios.get(`${API_BASE_URL}/api/portfolios`).then((res) => {
      setPortfolios(res.data);
    });
  }, [authToken]);

  function loadDashboardData(portfolioId: number) {
    if (!authToken) return;

    const requestId = dashboardRequestIdRef.current + 1;
    dashboardRequestIdRef.current = requestId;
    setDashboardLoading(true);
    setDashboardMessage("");

    axios
      .get<DashboardData>(`${API_BASE_URL}/api/portfolio/${portfolioId}/dashboard`)
      .then((res) => {
        if (requestId !== dashboardRequestIdRef.current) return;

        const formattedReturns = res.data.returns.map((point: ReturnPoint) => ({
          ...point,
          date: point.date.slice(0, 10),
        }));

        setRisk(res.data.risk);
        setReturns(formattedReturns);
        setHoldings(res.data.holdings);
        setSectorExposure(res.data.sector_exposure);
        setRiskContribution(res.data.risk_contribution);
      })
      .catch(() => {
        if (requestId !== dashboardRequestIdRef.current) return;

        setDashboardMessage(
          "Unable to load portfolio dashboard. Existing data is still shown if available."
        );
      })
      .finally(() => {
        if (requestId === dashboardRequestIdRef.current) {
          setDashboardLoading(false);
        }
      });
  }

  useEffect(() => {
    if (!authToken) return;

    loadDashboardData(selectedPortfolioId);
  }, [authToken, selectedPortfolioId]);

  function handleLogin(token: string, user: AuthUser) {
    localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, token);
    localStorage.setItem(AUTH_USER_STORAGE_KEY, JSON.stringify(user));
    setAuthToken(token);
    setAuthUser(user);
  }

  function handleLogout() {
    localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
    localStorage.removeItem(AUTH_USER_STORAGE_KEY);
    delete axios.defaults.headers.common.Authorization;
    setAuthToken(null);
    setAuthUser(null);
    setPortfolios([]);
    setRisk(null);
    setReturns([]);
    setHoldings([]);
    setSectorExposure([]);
    setRiskContribution([]);
    setStressResult(null);
    setMarketDataMessage("");
    setDashboardMessage("");
  }

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
    if (!canRefreshMarketData) {
      setMarketDataMessage(
        "You do not have permission to update portfolio prices."
      );
      return;
    }

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
            const diagnosticParts = [
              failedTicker.category,
              failedTicker.source,
            ].filter(Boolean);
            const diagnosticLabel = diagnosticParts.length
              ? ` [${diagnosticParts.join(", ")}]`
              : "";

            return `${failedTicker.ticker}${yfinanceLabel}: ${failedTicker.reason}${diagnosticLabel}`;
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
    if (!canExportPdf) {
      setMarketDataMessage(
        "You do not have permission to download risk reports."
      );
      return;
    }

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

  const navItems = [
    { page: "dashboard", label: "Dashboard", disabled: false },
    { page: "analytics", label: "Analytics", disabled: false },
    { page: "comparison", label: "Comparison", disabled: false },
    { page: "AI", label: "AI Copilot", disabled: !canUseAi },
    { page: "performance", label: "Performance Lab", disabled: false },
    { page: "jobs", label: "Background Jobs", disabled: !canViewAuditLogs },
    { page: "audit", label: "Audit Logs", disabled: !canViewAuditLogs },
  ] as const;

  if (!authToken) {
    return <LoginPage onLogin={handleLogin} />;
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

        <div className="header-actions">
          <div className="header-status">
            <span className="status-dot" aria-hidden="true" />
            {authUser?.role ?? "Authenticated"}
          </div>

          <button className="logout-button" type="button" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </header>

      <nav className="nav-tabs" aria-label="Primary sections">
        {navItems.map(({ page, label, disabled }) => (
          <button
            key={page}
            className={activePage === page ? "active-tab" : ""}
            disabled={disabled}
            title={
              disabled
                ? "Your role does not include access to this feature."
                : undefined
            }
            onClick={() =>
              setActivePage(
                page as "dashboard" | "performance" | "comparison" | "AI" | "analytics"
                | "audit"
                | "jobs"
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
        {activePage === "AI" &&
          (canUseAi ? (
            <AiCopilotPage />
          ) : (
            <section className="chart-card">
              <h2>Access restricted</h2>
              <p className="subtitle">
                Your role does not include access to AI Copilot.
              </p>
            </section>
          ))}
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

        {activePage === "audit" &&
          (canViewAuditLogs ? (
            <AuditLogsPage />
          ) : (
            <section className="chart-card">
              <h2>Access restricted</h2>
              <p className="subtitle">
                Your role does not include access to audit logs.
              </p>
            </section>
          ))}

        {activePage === "jobs" &&
          (canViewAuditLogs ? (
            <BackgroundJobsPage />
          ) : (
            <section className="chart-card">
              <h2>Access restricted</h2>
              <p className="subtitle">
                Your role does not include access to background jobs.
              </p>
            </section>
          ))}

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
            canExportPdf={canExportPdf}
            canRefreshMarketData={canRefreshMarketData}
            marketDataLoading={marketDataLoading}
            marketDataMessage={marketDataMessage}
            dashboardLoading={dashboardLoading}
            dashboardMessage={dashboardMessage}
          />
        )}
      </div>
    </main>
  )};


export default App;
