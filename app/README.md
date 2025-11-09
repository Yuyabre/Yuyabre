# Yuyabre Web Client

This React/Vite single-page app is the face of our autonomous flatmate agent. It lets users chat with the agent, watch live planning traces, and see inventory and expenses update in real time.

## Demo Storyboard

- **Chat-first flow**: type `“We’re out of oat milk, can you restock?”` and the UI streams the agent’s reasoning while it calls the backend.
- **Inventory spotlight**: low-stock badges and expiring items animate so judges instantly see why the agent acts.
- **Suggested actions**: one-click prompts (e.g., “Clear fridge before Sunday brunch”) highlight scripted scenarios during the 5‑minute pitch.

## Tech Notes

- React 19 + Vite with Radix UI primitives for a fast, accessible hackathon demo.
- TanStack Query hydrates inventory/orders via REST while WebSockets stream agent output.
- Zustand keeps chat state in sync across sidebar, transcript, and suggested actions.
- Tailored for projector mode: responsive layout, dark theme, large typography.

## Run the Frontend

```bash
cd app
pnpm install
cp .env.example .env   # set VITE_API_BASE_URL to backend origin
pnpm dev               # http://localhost:5173 for local demo
```

## Ship the Build

```bash
pnpm build
pnpm preview           # smoke-test the static bundle before deploying
```
