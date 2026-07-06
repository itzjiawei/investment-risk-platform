import { useState } from "react";
import type { FormEvent } from "react";
import axios from "axios";
import { API_BASE_URL } from "../config";

type LoginPageProps = {
  onLogin: (
    token: string,
    user: {
      email: string;
      full_name: string;
      role: "admin" | "portfolio_manager" | "analyst" | "viewer";
    }
  ) => void;
};

function LoginPage({ onLogin }: LoginPageProps) {
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("admin123");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function submitLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");

    axios
      .post(`${API_BASE_URL}/api/auth/login`, {
        email,
        password,
      })
      .then((res) => {
        onLogin(res.data.access_token, {
          email: res.data.email,
          full_name: res.data.full_name,
          role: res.data.role,
        });
      })
      .catch(() => {
        setError("Invalid email or password.");
      })
      .finally(() => {
        setLoading(false);
      });
  }

  return (
    <main className="login-page">
      <section className="login-panel">
        <div>
          <p className="eyebrow">Secure Access</p>
          <h1>Investment Risk Platform</h1>
          <p className="subtitle">
            Sign in to view portfolio analytics, market data tools, AI analysis,
            and risk reports.
          </p>
        </div>

        <form className="login-form" onSubmit={submitLogin}>
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              autoComplete="email"
              required
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              required
            />
          </label>

          {error && <p className="login-error">{error}</p>}

          <button className="primary-button" type="submit" disabled={loading}>
            {loading ? "Signing In..." : "Sign In"}
          </button>
        </form>
      </section>
    </main>
  );
}

export default LoginPage;
