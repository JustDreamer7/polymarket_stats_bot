# Polymarket Betting Follow Bot

A Telegram bot for tracking Polymarket bettors. It lets you look up bettors by wallet address or username, view their stats and recent trades, subscribe to them, and receive real-time push notifications about new bets.

Data is pulled from the Polymarket **Data API** and **Gamma API**, stored in PostgreSQL, with background jobs run via APScheduler.


## Telegram Commands

| Command | Description |
|---|---|
| `/start` | Register the user in the system |
| `/help` | Show command help |
| `/search <wallet\|username>` | Show a bettor's stats (winrate, volume, winnings, ROI, positions) |
| `/show_trades <wallet\|username>` | Show the bettor's 10 latest trades |
| `/add <wallet\|username>` | Subscribe to a bettor (notifications on new trades) |
| `/remove <wallet\|username>` | Unsubscribe from a bettor |
| `/list` | Show your subscriptions (with pagination and inline buttons) |

`<wallet|username>` — a Polymarket wallet address (`0x...`) or Polymarket username.

## Project Structure

```
.
├── main.py                 # Entry point
├── app/
│   ├── app.py              # App factory, lifecycle, DB & scheduler init
│   ├── config.py           # App config
│   ├── clients/            # Async HTTP clients for the Polymarket API
│   │   ├── base_client.py          # Base client (zapros): retry, timeout, pagination
│   │   ├── polymarket_data_client.py   # Data API: positions, trades, leaderboard, accounting
│   │   └── polymarket_gamma_client.py  # Gamma API: public profile lookup
│   ├── common/             # Shared infrastructure
│   │   ├── database.py             # SQLAlchemy async/sync engine and sessions
│   │   ├── logger.py               # structlog JSON logger
│   │   ├── models.py               # DeclarativeBase for ORM models
│   │   └── common_repository.py    # Base repository: insert/upsert/delete, bulk upsert
│   ├── models/             # SQLAlchemy ORM entities
│   ├── repository/         # Data-access layer
│   ├── schemas/            # Dataclass DTOs for API responses
│   ├── tasks/              # Background jobs (APScheduler)
│   │   ├── trades_task.py          # TradesNotifier: notifications on new trades
│   │   └── bettor_stats_task.py    # BettorStatsUpdater: recomputes bettor stats
│   ├── tg_bot/
│   │   └── bot.py                  # TelegramBot: command and inline-button handlers
│   ├── use_cases/          # Controller layer (application logic)
│   └── utils/              # Small helpers
├── alembic/                
├── tests/                 
├── pyproject.toml          
├── Dockerfile              
├── docker-compose.yml      # postgres + migrate + bot
└── docker-compose-tests.yml # postgres for tests
```

## Configuration

Settings are read from environment variables (or a `.env` file).

**Required:**

| Variable | Purpose |
|---|---|
| `TELEGRAM_TOKEN` | Telegram bot API token |
| `POSTGRES_HOST` | DB host |
| `POSTGRES_PORT` | DB port |
| `POSTGRES_DB` | DB name |
| `POSTGRES_USER` | DB user |
| `POSTGRES_PASSWORD` | DB password |
| `POLYMARKET_API_KEY` | Polymarket API key |
| `POLYMARKET_API_SECRET` | Polymarket API secret |
| `POLYMARKET_API_PASSPHRASE` | Polymarket API passphrase |
| `POLYMARKET_ADDRESS` | Polymarket wallet address |

**Optional (with defaults):**

| Variable | Default | Purpose |
|---|---|---|
| `POSTGRES_SCHEMA` | `public` | Postgres schema / `search_path` |
| `RECENT_TRADES_LIMIT` | `30` | Number of recent trades fetched per bettor |
| `NOTIFY_INTERVAL_MINUTES` | `10` | How often the new-trades notifier runs |
| `STATS_INTERVAL_MINUTES` | `20` | How often bettor stats are recomputed |
| `ENV_FILE` | *(unset)* | Path to a `.env` file (via python-dotenv) |

## Running

### Locally (via uv)

```bash
uv sync
docker compose -f docker-compose.tests.yml up -d
alembic upgrade head
python main.py
```

### In Docker

```bash
cp tests/env/test.env .env   # fill in values
docker compose -f docker-compose.yml up -d --build
```

Services in `docker-compose.yml`:
- `postgres` — the database;
- `migrate` — a one-shot `alembic upgrade head`;
- `bot` — the application itself.
