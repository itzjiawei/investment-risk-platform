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
} from "recharts";

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

type SectorExposure = {
  sector: string;
  market_value: number;
  weight: number;
};

type DashboardPageProps = {
  portfolios: Portfolio[];
  selectedPortfolioId: number;
  setSelectedPortfolioId: (id: number) => void;
  risk: RiskMetrics | null;
  returns: ReturnPoint[];
  sectorExposure: SectorExposure[];
  formatCurrency: (value: number) => string;
  formatPercent: (value: number) => string;
  downloadRiskReport: () => void;
  refreshMarketData: () => void;
  canExportPdf: boolean;
  canRefreshMarketData: boolean;
  marketDataLoading: boolean;
  marketDataMessage: string;
  dashboardLoading: boolean;
  dashboardMessage: string;
};

const PIE_COLORS = [
  "#024f8b",
  "#009f93",
  "#c54031",
  "#d6a63a",
  "#677f9d",
  "#6d5a89",
];

function DashboardPage({
  portfolios,
  selectedPortfolioId,
  setSelectedPortfolioId,
  risk,
  returns,
  sectorExposure,
  formatCurrency,
  formatPercent,
  downloadRiskReport,
  refreshMarketData,
  canExportPdf,
  canRefreshMarketData,
  marketDataLoading,
  marketDataMessage,
  dashboardLoading,
  dashboardMessage,
}: DashboardPageProps) {
  const hasSectorExposure = sectorExposure.length > 0;

  return (
    <>
      <section className="hero">
        <div>
          <p className="eyebrow">Investment Risk Analytics</p>
          <h2>Portfolio Risk Dashboard</h2>
        </div>
        <p className="subtitle">
          A disciplined view of portfolio value, volatility, allocation and
          downside indicators for long-term capital stewardship.
        </p>
      </section>

      <section className="toolbar">
        <div className="toolbar-control">
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
        </div>

        <div className="toolbar-actions">
          <button
            className="secondary-button"
            type="button"
            onClick={refreshMarketData}
            disabled={marketDataLoading || !canRefreshMarketData}
            title={
              canRefreshMarketData
                ? undefined
                : "Your role cannot update portfolio prices."
            }
          >
            {marketDataLoading
              ? "Updating Prices..."
              : "Update Portfolio Prices"}
          </button>

          <button
            className="primary-button"
            type="button"
            onClick={downloadRiskReport}
            disabled={!canExportPdf}
            title={
              canExportPdf
                ? undefined
                : "Your role cannot export PDF risk reports."
            }
          >
            Download Risk Report
          </button>
        </div>
      </section>

      {marketDataMessage && (
        <p className="status-message">{marketDataMessage}</p>
      )}

      {dashboardLoading && (
        <p className="status-message">Loading portfolio dashboard...</p>
      )}

      {dashboardMessage && (
        <p className="status-message">{dashboardMessage}</p>
      )}

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
                tick={{ fill: "#67768d" }}
              />
              <YAxis
                tick={{ fill: "#67768d" }}
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
                stroke="#024f8b"
                strokeWidth={3}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="chart-card" style={{ marginTop: "24px" }}>
        <div className="chart-header">
          <div>
            <p className="eyebrow">Allocation</p>
            <h2>Sector Exposure</h2>
          </div>
        </div>

        {hasSectorExposure ? (
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
        ) : (
          <div className="empty-chart-state">
            <h3>No sector exposure data available</h3>
            <p>
              Try updating portfolio prices or check ticker mappings.
            </p>
          </div>
        )}
      </section>
    </>
  );
}

export default DashboardPage;
