# Yuyabre Backend

FastAPI service that powers our autonomous roommate: it listens to natural language requests, plans multi-step grocery workflows, and keeps shared-flat finances tidy for the hackathon demo.

## What Happens Under the Hood

- **Agent brain**: `agent/core.py` routes every command through GPT-5, builds a plan, and dispatches modular actions.
- **Inventory engine**: MongoDB + Beanie track items, thresholds, and expirations the moment orders complete.
- **Ordering bridge**: pluggable Thuisbezorgd client (mock + live modes) so we can switch between sandbox data and real carts.
- **Expense autopilot**: Splitwise module posts the bill and assigns shares without manual data entry.
- **Realtime UX**: WebSocket streaming endpoint (`/agent/command/stream`) sends token-by-token updates to the React front end.

## Hackathon-Ready Setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add OpenAI, MongoDB, Splitwise credentials
uvicorn main:app --reload
```

## Key Endpoints for the Demo

- `POST /agent/command` — primary entry point; send `{ "command": "Order oat milk", "user_id": "demo" }`.
- `GET /agent/command/stream` (WebSocket) — stream reasoning tokens and status events.
- `GET /inventory/low-stock` — surfaces why the agent is taking action.
- `POST /orders` — direct order API if you want to bypass LLM planning in stretch demos.

Swagger docs live at `http://localhost:8000/docs` for judges who want to peek under the hood after the pitch.

## Observability in Two Minutes

- Structured logs land in `logs/agent.log`; tail them during judging for narrated traces.
- Toggle verbose planning by setting `AGENT_DEBUG=true` in `.env` — the front end will surface the same steps.
- Mongo Express (port 8081 via Docker compose) is handy if someone asks to see raw inventory data.

## Stretch Goals (Post-Judging)

- Properly implement Thuisbezorgd with partners APIs
- Add Whisper-powered voice commands for a richer booth experience.
- Add receipt scanning for easy expenses addition based on which ingredients are shared between flatmates
- Layer in auto-scheduling so the agent preps shopping lists for recurring events.
- Allow for item sharing between specific flatmates, not just all-or-nothing.
