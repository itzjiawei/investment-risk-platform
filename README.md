# Investment Risk Analytics Platform

A full-stack portfolio risk analytics platform built with React, FastAPI, PostgreSQL, Docker, Pandas, and DuckDB.

## Overview

This project provides portfolio managers and risk analysts with portfolio valuation, risk metrics, stress testing, and performance benchmarking capabilities.

The platform demonstrates both financial analytics and scalable data engineering concepts.

---

## Features

### Portfolio Analytics

- Portfolio valuation over time
- Daily and annualized returns
- Annualized volatility
- Sharpe Ratio
- Historical Value at Risk (VaR)
- Maximum Drawdown

### Portfolio Composition

- Holdings breakdown
- Sector exposure analysis
- Risk contribution by asset

### Scenario Analysis

- Custom stress testing
- Sector-specific shock simulations
- Portfolio impact estimation

### Performance Engineering

- Pandas analytics engine
- DuckDB analytics engine
- Large dataset benchmarking
- Performance comparison dashboard

---

## Tech Stack

### Frontend

- React
- TypeScript
- Axios
- Recharts

### Backend

- FastAPI
- Pandas
- DuckDB
- SQLAlchemy

### Database

- PostgreSQL
- Docker

---

## Architecture

```text
React Dashboard
       |
       v
FastAPI APIs
       |
       v
PostgreSQL
       |
       +---- Pandas Analytics
       |
       +---- DuckDB Analytics
```

---

## Example Analytics

### Risk Metrics

- Annualized Return
- Annualized Volatility
- Sharpe Ratio
- Historical VaR (95%)
- Maximum Drawdown

### Stress Testing

Example:

```text
Technology: -20%
Semiconductors: -30%
ETF: -15%
```

Portfolio impact is calculated and visualized.

---

## Performance Benchmark

Benchmarking was performed using a synthetic dataset containing approximately:

- 1,000 assets
- 300 holdings
- 1,000,000 historical price records

Example benchmark:

| Engine | Time |
|----------|----------|
| Pandas | 0.138s |
| DuckDB | 0.071s |

DuckDB achieved approximately 1.9x speedup for analytical workloads.

---

## Running Locally

### Backend

```bash
cd backend
python -m uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Database

```bash
docker compose up -d
```

---

## Future Enhancements

- AI Risk Analyst
- Portfolio Optimization
- Real Market Data Integration
- Authentication & User Accounts
- Cloud Deployment
- Multi-portfolio Management

---

## Author

Chen Jiawei