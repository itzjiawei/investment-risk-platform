# Architecture Diagram

```text
                    ┌─────────────────────┐
                    │     React Frontend  │
                    │                     │
                    │ Dashboard           │
                    │ Analytics           │
                    │ AI Copilot          │
                    │ Comparison          │
                    │ Performance Lab     │
                    └──────────┬──────────┘
                               │
                               │ REST API
                               ▼

                    ┌─────────────────────┐
                    │      FastAPI        │
                    │                     │
                    │ Analytics Engine    │
                    │ AI Services         │
                    │ Benchmark Engine    │
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼

 ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
 │ PostgreSQL     │  │ DuckDB         │  │ Ollama         │
 │                │  │                │  │                │
 │ Portfolio Data │  │ Analytics      │  │ Llama 3.2      │
 │ Holdings       │  │ Benchmarking   │  │ AI Analysis    │
 └────────────────┘  └────────────────┘  └────────────────┘
```