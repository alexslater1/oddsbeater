# oddsbeater

Private football betting analysis. 

The laptop does the heavy work (polite
scraping, a point-in-time pipeline, ML) and later publishes small static
artifacts to AWS.

## Layout

| Path        | Purpose                                    |
| ----------- | ------------------------------------------ |
| `pipeline/` | Python (uv): scrapers, parsers, loaders    |
| `data/`     | git-ignored local data lake (raw payloads) |
| `planning/` | git-ignored local planning docs            |

## Planned Layout

Each folder is added when its phase starts.

| Path                  | Stack                     | Purpose                                                                         |
| --------------------- | ------------------------- | ------------------------------------------------------------------------------- |
| `infra/`              | Terraform                 | AWS resources: hosting, auth, API, scheduled jobs, monitoring                   |
| `db/`, `compose.yaml` | Postgres, dbmate, Docker  | Analytics database: the single source of truth, with full history               |
| `services/`           | Go                        | Publisher for the static data; API for bets and sessions; odds and lineup jobs  |
| `contracts/`          | JSON Schema               | Shared data shapes and generated types for every language boundary              |
| `web/`                | TypeScript, React, Vite   | Owner-facing web app                                                            |
| `ml/`, `backtests/`   | Python, YAML              | Model training, predictions and scenarios; backtest definitions                 |
| `sim/`                | Rust                      | Joint probabilities for same-match combinations                                 |

## Requirements

[uv](https://docs.astral.sh/uv/) — it installs the pinned Python 3.14 for you.

## Run

Nothing to run yet. This sets up the environment and checks it works:

```
uv sync --directory pipeline
uv run --directory pipeline python -c "import pipeline; print('ok')"
```
