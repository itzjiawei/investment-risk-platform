import { useEffect, useState } from "react";
import axios from "axios";

import { API_BASE_URL } from "../config";


type FailedTicker = {
  ticker: string;
  yfinance_ticker?: string;
  reason: string;
};

type JobSummary = {
  updated_tickers: string[];
  failed_tickers: FailedTicker[];
  rows_inserted: number;
  message: string;
  email_notifications?: {
    portfolio_id: number;
    recipient_email: string;
    status: string;
    message: string;
  }[];
};

type RegisteredJob = {
  id: string;
  name: string;
  next_run_time: string | null;
};

type JobsStatus = {
  scheduler_enabled: boolean;
  scheduler_running: boolean;
  schedule: {
    days: string;
    hour_utc: number;
    minute_utc: number;
  };
  registered_jobs: RegisteredJob[];
  last_run_status: string;
  last_run_summary: JobSummary | null;
  last_run_started_at: string | null;
  last_run_completed_at: string | null;
  last_run_error: string | null;
};

type Portfolio = {
  portfolio_id: number;
  portfolio_name: string;
};

function BackgroundJobsPage() {
  const [jobsStatus, setJobsStatus] = useState<JobsStatus | null>(null);
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolioId, setSelectedPortfolioId] = useState(1);
  const [recipientEmail, setRecipientEmail] = useState("");
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [sendingReport, setSendingReport] = useState(false);
  const [message, setMessage] = useState("");

  function loadJobsStatus() {
    setLoading(true);
    setMessage("");

    axios
      .get<JobsStatus>(`${API_BASE_URL}/api/jobs/status`)
      .then((res) => {
        setJobsStatus(res.data);
      })
      .catch(() => {
        setMessage("Unable to load background job status.");
      })
      .finally(() => {
        setLoading(false);
      });
  }

  function runScheduledRefreshNow() {
    setRunning(true);
    setMessage("");

    axios
      .post(`${API_BASE_URL}/api/jobs/market-refresh/run-now`)
      .then(() => {
        setMessage("Scheduled refresh completed.");
        loadJobsStatus();
      })
      .catch(() => {
        setMessage("Scheduled refresh failed.");
      })
      .finally(() => {
        setRunning(false);
      });
  }

  function sendTestReport() {
    if (!recipientEmail) {
      setMessage("Enter a recipient email first.");
      return;
    }

    setSendingReport(true);
    setMessage("");

    axios
      .post(`${API_BASE_URL}/api/notifications/send-report`, {
        portfolio_id: selectedPortfolioId,
        recipient_email: recipientEmail,
      })
      .then(() => {
        setMessage("Test risk report email sent.");
      })
      .catch((error) => {
        setMessage(
          error.response?.data?.detail ??
            "Unable to send test risk report email."
        );
      })
      .finally(() => {
        setSendingReport(false);
      });
  }

  useEffect(() => {
    loadJobsStatus();
    axios.get<Portfolio[]>(`${API_BASE_URL}/api/portfolios`).then((res) => {
      setPortfolios(res.data);

      if (res.data.length > 0) {
        setSelectedPortfolioId(res.data[0].portfolio_id);
      }
    });
  }, []);

  const nextRunTime = jobsStatus?.registered_jobs[0]?.next_run_time;
  const failedTickers = jobsStatus?.last_run_summary?.failed_tickers ?? [];
  const emailNotifications =
    jobsStatus?.last_run_summary?.email_notifications ?? [];

  return (
    <section className="table-card">
      <div className="chart-header">
        <div>
          <p className="eyebrow">Administration</p>
          <h2>Background Jobs</h2>
        </div>

        <button
          className="primary-button"
          type="button"
          onClick={runScheduledRefreshNow}
          disabled={running}
        >
          {running ? "Running..." : "Run Scheduled Refresh Now"}
        </button>
      </div>

      {loading && <p className="status-message">Loading job status...</p>}
      {message && <p className="status-message">{message}</p>}

      {jobsStatus && (
        <>
          <section className="metrics-grid">
            <div className="metric-card">
              <p>Scheduler</p>
              <h2>{jobsStatus.scheduler_enabled ? "Enabled" : "Disabled"}</h2>
            </div>
            <div className="metric-card">
              <p>Runtime</p>
              <h2>{jobsStatus.scheduler_running ? "Running" : "Stopped"}</h2>
            </div>
            <div className="metric-card">
              <p>Next Refresh</p>
              <h2>
                {nextRunTime ? new Date(nextRunTime).toLocaleString() : "None"}
              </h2>
            </div>
          </section>

          <div className="table-wrapper" style={{ marginTop: "20px" }}>
            <table>
              <tbody>
                <tr>
                  <th>Schedule</th>
                  <td>
                    {jobsStatus.schedule.days} at{" "}
                    {String(jobsStatus.schedule.hour_utc).padStart(2, "0")}:
                    {String(jobsStatus.schedule.minute_utc).padStart(2, "0")} UTC
                  </td>
                </tr>
                <tr>
                  <th>Last Run Status</th>
                  <td>{jobsStatus.last_run_status}</td>
                </tr>
                <tr>
                  <th>Last Run Completed</th>
                  <td>
                    {jobsStatus.last_run_completed_at
                      ? new Date(jobsStatus.last_run_completed_at).toLocaleString()
                      : "-"}
                  </td>
                </tr>
                <tr>
                  <th>Rows Inserted</th>
                  <td>{jobsStatus.last_run_summary?.rows_inserted ?? 0}</td>
                </tr>
                <tr>
                  <th>Updated Tickers</th>
                  <td>
                    {jobsStatus.last_run_summary?.updated_tickers.join(", ") ||
                      "-"}
                  </td>
                </tr>
                <tr>
                  <th>Failed Tickers</th>
                  <td>
                    {failedTickers.length > 0
                      ? failedTickers
                          .map((ticker) => `${ticker.ticker}: ${ticker.reason}`)
                          .join("; ")
                      : "-"}
                  </td>
                </tr>
                <tr>
                  <th>Last Error</th>
                  <td>{jobsStatus.last_run_error ?? "-"}</td>
                </tr>
                <tr>
                  <th>Email Notifications</th>
                  <td>
                    {emailNotifications.length > 0
                      ? emailNotifications
                          .map(
                            (email) =>
                              `Portfolio ${email.portfolio_id} to ${email.recipient_email}: ${email.status}`
                          )
                          .join("; ")
                      : "-"}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <section className="toolbar" style={{ marginTop: "20px" }}>
            <div className="toolbar-control">
              <label>Portfolio</label>
              <select
                value={selectedPortfolioId}
                onChange={(event) =>
                  setSelectedPortfolioId(Number(event.target.value))
                }
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

            <div className="toolbar-control">
              <label>Recipient</label>
              <input
                type="email"
                value={recipientEmail}
                onChange={(event) => setRecipientEmail(event.target.value)}
                placeholder="recipient@example.com"
              />
            </div>

            <button
              className="secondary-button"
              type="button"
              onClick={sendTestReport}
              disabled={sendingReport}
            >
              {sendingReport ? "Sending..." : "Send Test Report"}
            </button>
          </section>
        </>
      )}
    </section>
  );
}

export default BackgroundJobsPage;
