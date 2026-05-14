# Yuyabre

**Yuyabre** is a prototype for an AI “roommate” for shared flats: it answers natural-language requests, tracks pantry inventory in MongoDB, helps coordinate grocery orders (including a Thuisbezorgd-style bridge, often mocked for demos), and can log expenses to Splitwise. It was built for the Prosus AI Hackathon 2025 and is structured as a small monorepo with a FastAPI backend and a React + Vite web client.

## Features

### AI agent

- **Natural-language commands** — Users describe what they want in plain text; the backend routes requests through an LLM-backed grocery agent (`backend/agent/`).
- **Synchronous API** — `POST /agent/command` returns a full assistant reply after tool use and reasoning.
- **Streaming WebSocket** — `WS /agent/command/stream` streams tokens and status events for the React chat UI.
- **Tool calling** — The model can invoke backend tools (see below) for inventory, orders, preferences, housemates, Splitwise, messaging, and delivery ETA.

**Agent tools** (exposed to the model; implemented in `backend/agent/tool_handlers.py`):

| Tool | What it does |
|------|----------------|
| `get_inventory_snapshot` | Read inventory, optionally filtered by dish or keyword. |
| `add_inventory_items` | Add items or increase quantities. |
| `update_inventory_item` | Update quantity, threshold, notes, or **shared vs personal** scope (household vs user inventory). |
| `check_low_stock` | List items below their restock threshold. |
| `place_order` | Create a grocery order; **shared items** can trigger a **group order** and notify housemates (Discord preferred, WhatsApp fallback). |
| `get_recent_orders` | Fetch recent order history. |
| `get_order_eta` | Delivery ETA and simulated status progression (pending → delivered). |
| `get_group_order_status` | See who responded on Discord/WhatsApp for a group order. |
| `update_user_preferences` | Add or remove dietary restrictions, allergies, favorite brands, disliked items. |
| `get_user_info` | Profile and preferences for “who am I” style questions. |
| `get_housemates` | List household members and optional contact info. |
| `send_discord_message` | Primary channel: post to the household Discord flow. |
| `check_discord_message_responses` | Poll yes/no style replies after a Discord prompt. |
| `send_whatsapp_message` | Fallback: Twilio WhatsApp to household or a specific number. |
| `create_splitwise_expense` | Log a shared expense (e.g. groceries) in Splitwise. |
| `get_splitwise_expenses` | List expenses visible to the user. |

### Users, households, and auth

- **Signup & login** — `POST /auth/signup`, `POST /auth/login` with password hashing for the web app.
- **User profile** — `GET` / `PATCH /auth/users/{user_id}` (name, email, phone, Splitwise and Discord linkage fields, notes).
- **Preferences** — `PATCH /auth/users/{user_id}/preferences` for dietary data used by the agent.
- **Households** — Create (`POST .../households`), fetch (`GET /auth/households/{id}`), join (`POST .../join-household`), update metadata (`PATCH .../households/{household_id}`).

### Inventory

- **Per-user and household inventory** — Items can be **shared** (household) or **personal** (owned by `user_id`); categories, units, thresholds, optional **expiration**, **brand**, **price**, and **notes**.
- **REST API** — `GET/POST /inventory/{user_id}`, `PATCH/DELETE /inventory/{item_id}`, `GET /inventory/low-stock`.
- **Caching** — Inventory and ordering paths use an async LRU cache with invalidation on writes (`backend/utils/cache.py`).

### Orders and grocery flow

- **Order listing & detail** — `GET /orders`, `GET /orders/{order_id}`, `GET /orders/users/{user_id}`.
- **Cancel** — `POST /orders/{order_id}/cancel`.
- **Ordering module** — Product search, store selection, cart-style order creation, optional **Splitwise expense** creation when an order completes, **group order** handling with housemate responses (`backend/modules/ordering/`).
- **Grocery / delivery bridge** — Thuisbezorgd-oriented configuration (`thuisbezorgd_*` in settings) plus mock-style catalog paths for demos (`backend/modules/grocery_stores/`).

### Splitwise

- **User OAuth** — `GET /auth/splitwise/authorize`, `GET /auth/splitwise/callback`, `POST /auth/splitwise`, `GET /auth/splitwise/status/{user_id}` (token storage on the user document).
- **Expenses API** — `GET/POST /splitwise/expenses`, `POST /splitwise/groups/search`.
- **Agent** — Create and list expenses via tools (see above).

### Discord and WhatsApp (optional)

- **Discord** — HTTP webhook endpoint `POST /discord/webhook`; optional **Discord bot** started with the API when `DISCORD_BOT_TOKEN` is set (`main.py` lifespan). Bot startup can fail on some Python versions if `discord.py` / voice deps are missing; the API still serves HTTP routes.
- **WhatsApp (Twilio)** — `POST /whatsapp/webhook` for inbound messages; outbound sends through the Twilio client when `twilio` is installed and env vars are set (`backend/modules/whatsapp/`).

### Web app (`app/`)

- **Authentication UI** — Email/password signup and login; session user persisted locally (`authStorage`).
- **Chat** — Markdown rendering, suggested quick actions, execution status indicators, WebSocket streaming from the agent.
- **Sidebar & header** — Navigation to inventory, orders, household, settings.
- **Inventory modal** — Browse and manage items for the signed-in user (TanStack Query + REST).
- **Orders modal** — Order history and detail cards.
- **Household modal** — View or edit household context.
- **Settings modal** — User-facing preferences and app settings.
- **Onboarding** — After login: optional **Splitwise OAuth** flow, then **household** create/join prompts when appropriate.
- **Theming** — Light / dark / system via `ThemeProvider`.
- **PWA** — `vite-plugin-pwa` (manifest, service worker, offline-oriented assets in production builds).

### CLI (`backend/cli.py`)

- **Interactive terminal UI** (Rich) — Connects to MongoDB, picks or creates a user/household, runs the same `GroceryAgent` as the API for demos without the browser.
- **Built-in help** — Examples for inventory, low stock, orders, and exit commands.

### Data stored in MongoDB (Beanie)

Documents initialized on API startup include **users** (preferences, consumption patterns, optional Splitwise/Discord fields), **households**, **inventory** items, **orders**, **user inventory** links, and **store** / **store inventory** models for the grocery bridge (`backend/database.py`, `backend/models/`).

### Platform and operations

- **Health** — `GET /health` reports API status and database connectivity.
- **OpenAPI** — Interactive docs at `/docs`, ReDoc at `/redoc`.
- **CORS** — Permissive defaults for local development (tighten for production).
- **Logging** — Loguru across services; optional rotating file logs when running `main` as a script.
- **Docker** — `backend/docker-compose.yml`: API + MongoDB + **Mongo Express** (DB UI on port 8081).
- **Tests** — `pytest` suite under `backend/tests/`; `make test` in `backend/`.

## Repository layout

| Path | Role |
|------|------|
| `backend/` | FastAPI app, agent, modules, tests, `docker-compose.yml`, `Makefile` |
| `app/` | React 19 + Vite SPA (chat, inventory, orders UI) |

Deeper backend notes: `backend/README.md`, `backend/QUICKSTART.md`, `backend/SETUP.md`, `backend/ARCHITECTURE.md`.

## Prerequisites

- **Python** 3.11+ (3.13 works for the API; optional `discord.py` may need extra care on very new Python versions).
- **Node.js** and **pnpm** (lockfile is `pnpm-lock.yaml`).
- **MongoDB** — local instance (e.g. `mongodb://localhost:27017`) or MongoDB Atlas.

## Quick start (local)

### 1. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env` and set at least:

- `OPENAI_API_KEY` — required for the agent.
- `MONGO_DB_URI` — e.g. `mongodb://localhost:27017` for local MongoDB.
- `MONGO_DB_DB_NAME` — defaults to `grocery_agent` if omitted in practice; align with your `.env`.

Start the API:

```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000  
- OpenAPI / Swagger: http://localhost:8000/docs  
- Health: http://localhost:8000/health  

Optional: seed or check the database (`backend/scripts/init_db.py`, or `make init-db` / `make check-db` from `backend/`).

### 2. Frontend

```bash
cd app
pnpm install
cp .env.example .env
```

For local development, point the SPA at the API (not the default `/api` proxy unless you configure one):

```env
VITE_API_BASE_URL=http://localhost:8000
```

```bash
pnpm dev
```

App: http://localhost:5173  

### 3. Smoke test

```bash
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/agent/command \
  -H "Content-Type: application/json" \
  -d '{"command": "What is in the inventory?"}'
```

## Environment variables (summary)

Values are loaded from `backend/.env` (see `backend/config.py` for aliases and defaults).

| Variable | Required | Purpose |
|----------|----------|---------|
| `OPENAI_API_KEY` | Yes | LLM calls for the agent |
| `OPENAI_MODEL` | No | Model id (default `gpt-5-mini`) |
| `MONGO_DB_URI` | Yes (for real data) | MongoDB connection string |
| `MONGO_DB_DB_NAME` | No | Database name (default `grocery_agent`) |
| `MONGO_DB_USERNAME`, `MONGO_DB_PASSWORD` | No | Credentials if your URI needs them |
| `OPENAI_PROXY_URL` | No | Custom OpenAI-compatible base URL |
| `SPLITWISE_API_KEY`, `SPLITWISE_CONSUMER_KEY`, `SPLITWISE_CONSUMER_SECRET`, `SPLITWISE_GROUP_ID` | No | Splitwise REST + OAuth + default group |
| `DISCORD_BOT_TOKEN`, `DISCORD_WEBHOOK_URL`, `DISCORD_PERMISSION_ID` | No | Discord bot + webhooks |
| `WHATSAPP_ACCOUNT_SID`, `WHATSAPP_AUTH_TOKEN`, `WHATSAPP_FROM_NUMBER`, `WHATSAPP_WEBHOOK_URL` | No | Twilio WhatsApp |
| `THUISBEZORGD_EMAIL`, `THUISBEZORGD_PASSWORD`, `THUISBEZORGD_API_URL` | No | Delivery / store bridge |
| `APP_ENV`, `APP_DEBUG`, `LOG_LEVEL` | No | Runtime behavior |
| `AUTO_ORDER_ENABLED`, `ORDER_APPROVAL_REQUIRED`, `LOW_STOCK_CHECK_INTERVAL` | No | Agent / ordering policy |

Frontend: `VITE_API_BASE_URL` in `app/.env` — backend origin for REST/WebSocket calls.

### HTTP API quick reference

| Area | Base path | Notes |
|------|-----------|--------|
| System | `GET /health` | |
| Agent | `/agent/command`, `WS /agent/command/stream` | |
| Auth & users | `/auth/...` | Signup, login, users, households, preferences |
| Inventory | `/inventory/...` | User-scoped and low-stock |
| Orders | `/orders/...` | List, detail, cancel, by user |
| Splitwise | `/splitwise/...`, `/auth/splitwise/...` | OAuth + expenses |
| Discord | `POST /discord/webhook` | |
| WhatsApp | `POST /whatsapp/webhook` | Twilio inbound |

Full schemas: http://localhost:8000/docs when the backend is running.

## Docker (backend + MongoDB)

From `backend/`:

```bash
cp .env.example .env   # ensure API keys and DB settings match how you run Mongo
docker compose up -d
```

Compose brings up the API, MongoDB, and optional Mongo Express. See `backend/docker-compose.yml` and `backend/Makefile` (`make docker-up`, `make docker-logs`, `make docker-down`).

## Tech stack

- **Backend:** FastAPI, Motor/Beanie, LangChain / LangGraph-style agent wiring, Loguru, Rich (CLI)  
- **Frontend:** React 19, Vite, TanStack Query, Zustand, Radix UI, Tailwind CSS, WebSocket client for agent streaming, `vite-plugin-pwa`  
- **Data:** MongoDB  
- **Integrations:** OpenAI, Splitwise, Thuisbezorgd-oriented ordering module, optional Twilio WhatsApp and Discord  

## Hackathon pitch (short)

Shared flats waste time on stock tracking, forgotten shops, and splitting bills. Yuyabre is a text-first agent that closes the loop: understand intent, update inventory, coordinate orders, and record costs—without rebuilding full expense or delivery products from scratch.

## License / contributing

This repository is a hackathon prototype. For forks or production use, review secrets, CORS, and connector terms for each third-party API before deployment.
