# Yuyabre - Prosus AI Hackathon 2025

Yuyabre is our hackathon prototype for an AI roommate that keeps the shared pantry balanced without nagging anyone. The agent watches inventory, negotiates grocery orders, and settles the bill instantly, all through natural language instructions.

## Why It Matters

- **Hackathon challenge**: build a lifestyle agent that delivers real-world automation in under 1.5 days.
- **Problem**: shared apartments lose time and money to poor inventory tracking, forgotten orders, and messy expense splitting.
- **Solution**: a text-first agent that automates the full loop, while monitoring stock, deciding what to buy, ordering it, updating the inventory database, and logging the cost.

## How the Agent Works

- **Conversation first**: users type simple requests (`"We’re out of oats, restock please"`); the agent plans actions via LLM reasoning.
- **Contextual memory**: MongoDB keeps real-time inventory plus household preferences.
- **Order automation**: fulfilment happens through a Thuisbezorgd integration with configurable vendor profiles (mocked due to time and physical constraints (i.e. partners-only APIs))
- **Fair cost sharing**: every order pushes an expense to Splitwise with the right participants and notes.

## Tech Snapshot

- FastAPI backend orchestrating actions and calling external services
- React + Vite chat interface tailored for fast demo flows
- MongoDB Atlas, Splitwise API, Thuisbezorgd ordering bridge
- OpenAI GPT-5 powering intent parsing and decision logic

## Try It in the Demo Booth

1. Clone the repo: `git clone https://github.com/brewcoua/Yuyabre`
2. In backend, copy `.env.example` to `.env` and drop in OpenAI, Splitwise, and Mongo credentials
3. Similarly, in app, copy `.env.example` to `.env` and edit the api url if needed
4. Launch both the app and the backend

## Pitch Highlights

- End-to-end automation of a real group task, ready for hackathon judges
- Modular connectors let us swap vendors or finance platforms in future sprints
- Focus on agentic features, not re-inventing the wheel (e.g. expenses management)

Let us know if you’d like to run the live demo or peek at the decision traces!
