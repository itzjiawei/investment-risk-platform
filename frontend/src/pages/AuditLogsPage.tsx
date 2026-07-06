import { useEffect, useState } from "react";
import axios from "axios";

import { API_BASE_URL } from "../config";


type AuditLog = {
  id: number;
  user_email: string | null;
  user_role: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  status: string;
  created_at: string;
};

function AuditLogsPage() {
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  useEffect(() => {
    setLoading(true);
    setMessage("");

    axios
      .get<AuditLog[]>(`${API_BASE_URL}/api/audit-logs?limit=100`)
      .then((res) => {
        setAuditLogs(res.data);
      })
      .catch(() => {
        setMessage("Unable to load audit logs.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  return (
    <section className="table-card">
      <div className="chart-header">
        <div>
          <p className="eyebrow">Administration</p>
          <h2>Audit Logs</h2>
        </div>
      </div>

      {loading && <p className="status-message">Loading audit logs...</p>}
      {message && <p className="status-message">{message}</p>}

      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>User</th>
              <th>Role</th>
              <th>Action</th>
              <th>Resource</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {auditLogs.map((log) => (
              <tr key={log.id}>
                <td>{new Date(log.created_at).toLocaleString()}</td>
                <td>{log.user_email ?? "System"}</td>
                <td>{log.user_role ?? "-"}</td>
                <td>{log.action}</td>
                <td>
                  {[log.resource_type, log.resource_id].filter(Boolean).join(": ") ||
                    "-"}
                </td>
                <td>{log.status}</td>
              </tr>
            ))}

            {!loading && auditLogs.length === 0 && (
              <tr>
                <td colSpan={6}>No audit logs available.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default AuditLogsPage;
