import {
  BarChart,
  Bar,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

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
};

type AnalyticsPageProps = {
  holdings: Holding[];
  riskContribution: RiskContribution[];
  stressShocks: {
  Technology: number;
  Semiconductors: number;
  ETF: number;
  Commodities: number;
  Financials: number;
};

stressResult: StressTestResult | null;

setStressShocks: React.Dispatch<
  React.SetStateAction<{
    Technology: number;
    Semiconductors: number;
    ETF: number;
    Commodities: number;
    Financials: number;
  }>
>;
  runStressTest: () => void;
  formatCurrency: (value: number) => string;
  formatPercent: (value: number) => string;
};

function AnalyticsPage({
  holdings,
  riskContribution,
  stressShocks,
  stressResult,
  setStressShocks,
  runStressTest,
  formatCurrency,
  formatPercent,
}: AnalyticsPageProps) {
  return (
    <>
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
                tickFormatter={(value) =>
                  `${(Number(value) * 100).toFixed(0)}%`
                }
              />

              <YAxis
                dataKey="ticker"
                type="category"
                width={80}
              />

              <Tooltip
                formatter={(value) => [
                  `${(Number(value) * 100).toFixed(2)}%`,
                  "Risk Contribution",
                ]}
              />

              <Bar
                dataKey="risk_contribution"
                fill="#38bdf8"
              />
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
  );
}

export default AnalyticsPage;