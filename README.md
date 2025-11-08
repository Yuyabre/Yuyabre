# Yuyabre - Shared Flat Grocery Management Agent

An intelligent agent system designed to automate grocery management for shared flats and groups. The system handles inventory tracking, automatic ordering through Thuisbezorgd, expense splitting via Splitwise, and provides a text-based interface for natural language commands.

## 🎯 Current Sprint Goal (1.5 Days)

Build a functional text-based agent that can autonomously order groceries, track inventory in MongoDB, and automatically split expenses via Splitwise.

## ✨ Core Features

### ✅ In Development

- **MongoDB Inventory System** - Real-time inventory tracking with CRUD operations
- **Modular Splitwise Integration** - Automatic expense splitting after orders
- **Autonomous Grocery Ordering** - Order placement through Thuisbezorgd
- **Text-Based Agent Interface** - CLI with natural language processing

### 🔮 Future Features

- Voice input (Whisper API)
- Picture/OCR receipt scanning
- WhatsApp notifications
- Calendar integration
- Learning/prediction algorithms
- Web UI

## 🏗️ Project Structure

```
Yuyabre/
├── inventory/      # MongoDB inventory module
├── splitwise/      # Modular Splitwise integration
├── ordering/       # Thuisbezorgd integration
├── agent/          # Core agent logic
├── cli/            # Text interface
└── IDEA.md         # Detailed project documentation
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+ or Node.js 16+
- MongoDB (local or remote)
- Splitwise API credentials
- OpenAI API key (for LLM)
- Thuisbezorgd account (for ordering)

### Setup

1. Clone the repository
2. Install dependencies
3. Configure environment variables (see `.env.example`)
4. Set up MongoDB
5. Run the agent

```bash
# Example (Python)
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python cli/main.py
```

## 📋 Usage Examples

### Order Groceries

```
User: "Order 2 liters of milk"
Agent: Places order → Updates inventory → Creates Splitwise expense
```

### Update Inventory

```
User: "Add 5 eggs to inventory"
Agent: Updates MongoDB inventory
```

### Query Inventory

```
User: "What's in the inventory?"
Agent: Returns formatted inventory list
```

## 🛠️ Technology Stack

- **Backend:** Python (FastAPI) or Node.js (Express.js)
- **Database:** MongoDB
- **LLM:** OpenAI API (GPT-4/3.5)
- **Integrations:**
  - Splitwise API
  - Thuisbezorgd (API or web scraping)

## 📚 Documentation

- **[IDEA.md](./IDEA.md)** - Complete project documentation, architecture, and workflows
- **[GITHUB_ISSUES.md](./GITHUB_ISSUES.md)** - Detailed GitHub issues for kanban board

## 🎯 Development Status

**Current Phase:** Sprint (1.5 days)

- [x] Project structure design
- [ ] MongoDB setup and schema
- [ ] Inventory CRUD module
- [ ] Splitwise integration
- [ ] Thuisbezorgd integration
- [ ] Agent orchestration
- [ ] End-to-end testing

## 🤝 Contributing

This is a sprint project. See [IDEA.md](./IDEA.md) for detailed development phases and [GITHUB_ISSUES.md](./GITHUB_ISSUES.md) for task breakdown.

## 📝 License

[Add license information]

---

**Note:** This project is in active development. See [IDEA.md](./IDEA.md) for the complete project vision and roadmap.
