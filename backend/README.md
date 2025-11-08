# 🛒 Grocery Management Agent - Backend

An intelligent AI agent system for automating grocery management in shared living spaces. This backend provides the core functionality for inventory tracking, automatic ordering through Thuisbezorgd, expense splitting via Splitwise, and natural language command processing.

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)

## ✨ Features

### Core Features (MVP)

- **MongoDB Inventory System**: Full CRUD operations with quantity tracking, thresholds, and expiration dates
- **Modular Splitwise Integration**: Automatic expense creation and cost splitting
- **Autonomous Grocery Ordering**: Integration with Thuisbezorgd for automated ordering
- **Text-Based Agent Interface**: CLI and REST API for natural language commands
- **LLM-Powered Processing**: Uses OpenAI GPT for command understanding

### Key Capabilities

- ✅ Natural language command processing
- ✅ Inventory management with low-stock alerts
- ✅ Automatic order placement
- ✅ Cost splitting among flatmates
- ✅ Order tracking and history
- ✅ RESTful API for integrations

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (Future)                  │
│              React/Flutter Mobile App                │
└────────────────┬────────────────────────────────────┘
                 │
                 │ HTTP/REST
                 ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI Backend (This Repo)            │
├─────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────┐   │
│  │          GroceryAgent (Core AI)              │   │
│  │     - Command Processing                     │   │
│  │     - Intent Parsing (OpenAI)                │   │
│  │     - Workflow Orchestration                 │   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │Inventory │  │ Ordering │  │Splitwise │           │
│  │ Service  │  │ Service  │  │ Service  │           │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘           │
│       │             │              │                │
└───────┼─────────────┼──────────────┼───────────────-┘
        │             │              │
        ▼             ▼              ▼
   ┌────────┐   ┌──────────┐   ┌──────────┐
   │MongoDB │   │Thuisbez. │   │Splitwise │
   │Database│   │   API    │   │   API    │
   └────────┘   └──────────┘   └──────────┘
```

## 🛠️ Tech Stack

- **Framework**: FastAPI (Python)
- **Database**: MongoDB with Beanie ODM
- **AI/LLM**: OpenAI GPT-4
- **API Integrations**:
  - Splitwise API (expense management)
  - Thuisbezorgd (grocery ordering - to be implemented)
- **CLI**: Rich library for enhanced terminal UI
- **Testing**: Pytest with async support
- **Containerization**: Docker & Docker Compose

## 📁 Project Structure

```
backend/
├── agent/                    # Core AI agent
│   ├── __init__.py
│   └── core.py              # GroceryAgent orchestrator
│
├── models/                   # Database models
│   ├── __init__.py
│   ├── inventory.py         # InventoryItem model
│   ├── order.py             # Order & OrderItem models
│   └── user.py              # User & preferences models
│
├── modules/                  # Service modules
│   ├── inventory/           # Inventory management
│   │   ├── __init__.py
│   │   └── service.py       # InventoryService
│   ├── ordering/            # Order placement
│   │   ├── __init__.py
│   │   └── service.py       # OrderingService
│   └── splitwise/           # Expense splitting
│       ├── __init__.py
│       └── service.py       # SplitwiseService
│
├── tests/                    # Test suite
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures
│   ├── test_inventory.py
│   └── test_api.py
│
├── utils/                    # Utilities
│   ├── __init__.py
│   └── logger.py            # Logging configuration
│
├── main.py                   # FastAPI application
├── cli.py                    # Command-line interface
├── database.py               # Database connection
├── config.py                 # Configuration management
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker image
├── docker-compose.yml        # Docker orchestration
└── README.md                 # This file
```

## 🚀 Setup & Installation

### Prerequisites

- Python 3.11+
- MongoDB 7.0+
- OpenAI API key
- (Optional) Docker & Docker Compose

### Local Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd backend
```

2. **Create virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up MongoDB**

```bash
# Install MongoDB locally or use Docker:
docker run -d -p 27017:27017 --name mongodb mongo:7.0
```

5. **Configure environment variables**

```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

6. **Create logs directory**

```bash
mkdir logs
```

### Docker Installation (Recommended)

1. **Using Docker Compose**

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

This starts:
- MongoDB on port 27017
- FastAPI on port 8000
- Mongo Express (DB admin) on port 8081

## ⚙️ Configuration

Create a `.env` file in the backend directory:

```env
# MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=grocery_agent

# OpenAI API
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-5-nano
OPENAI_PROXY_URL=https://fj7qg3jbr3.execute-api.eu-west-1.amazonaws.com/v1

# Splitwise API
SPLITWISE_API_KEY=your_splitwise_api_key
SPLITWISE_CONSUMER_KEY=your_consumer_key
SPLITWISE_CONSUMER_SECRET=your_consumer_secret
SPLITWISE_GROUP_ID=your_group_id

# Thuisbezorgd
THUISBEZORGD_EMAIL=your_email
THUISBEZORGD_PASSWORD=your_password

# Application
APP_ENV=development
APP_DEBUG=True
LOG_LEVEL=INFO
```

### Getting API Keys

- **OpenAI**: https://platform.openai.com/api-keys
- **Splitwise**: https://secure.splitwise.com/apps/new
- **Thuisbezorgd**: Use your account credentials

## 💻 Usage

### CLI Interface

Start the interactive command-line interface:

```bash
python cli.py
```

**Example Commands:**

```
You: Order 2 liters of milk
Agent: ✓ Order placed successfully!

You: What's in the inventory?
Agent: Current inventory:
- Milk: 2.0 liters
- Eggs: 12.0 pieces

You: Show low stock items
Agent: Low stock items:
- Bread: 0.5 pieces (threshold: 1.0)
```

### REST API

Start the FastAPI server:

```bash
# Development mode (auto-reload)
uvicorn main:app --reload

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

Access the API:
- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📚 API Documentation

### Core Endpoints

#### Agent Commands

```http
POST /agent/command
Content-Type: application/json

{
  "command": "Order 2 liters of milk",
  "user_id": "user_123"
}
```

#### Inventory Management

```http
# Get all inventory items
GET /inventory

# Get specific item
GET /inventory/{item_id}

# Create new item
POST /inventory
{
  "name": "Milk",
  "category": "Dairy",
  "quantity": 2.0,
  "unit": "liters"
}

# Update item
PATCH /inventory/{item_id}
{
  "quantity": 3.0
}

# Delete item
DELETE /inventory/{item_id}

# Get low stock items
GET /inventory/low-stock
```

#### Orders

```http
# Get order history
GET /orders?limit=20

# Get specific order
GET /orders/{order_id}

# Cancel order
POST /orders/{order_id}/cancel
```

#### Splitwise

```http
# Get expenses
GET /splitwise/expenses?limit=20
```

## 🔧 Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_inventory.py -v
```

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

### Adding New Features

1. **Create a new module** in `modules/`
2. **Define models** in `models/` if needed
3. **Add service logic** in the module's `service.py`
4. **Integrate with agent** in `agent/core.py`
5. **Add API endpoints** in `main.py`
6. **Write tests** in `tests/`

## 🧪 Testing

The project includes comprehensive tests:

- **Unit Tests**: Test individual components
- **Integration Tests**: Test API endpoints
- **Database Tests**: Test MongoDB operations

Run tests with:

```bash
pytest -v
```

## 🚢 Deployment

### Using Docker

1. **Build the image**

```bash
docker build -t grocery-agent-backend .
```

2. **Run with Docker Compose**

```bash
docker-compose up -d
```

### Manual Deployment

1. **Set up production environment**

```bash
export APP_ENV=production
export APP_DEBUG=False
```

2. **Run with Gunicorn**

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 📝 TODO & Future Enhancements

### High Priority

- [ ] Complete Thuisbezorgd integration (API or web scraping)
- [ ] Implement actual order placement logic
- [ ] Add WhatsApp notifications module
- [ ] User authentication and authorization
- [ ] Better error handling and retry logic

### Medium Priority

- [ ] Voice input via Whisper API
- [ ] Receipt scanning with OCR
- [ ] Calendar integration for scheduled orders
- [ ] Pattern recognition and predictive ordering
- [ ] Web dashboard UI

### Low Priority

- [ ] Multi-household support
- [ ] Mobile app (Flutter)
- [ ] Advanced analytics dashboard
- [ ] Machine learning for habit prediction

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Submit a pull request

## 📄 License

[Your License Here]

## 👥 Team

- [Your Name] - Initial work

## 🙏 Acknowledgments

- OpenAI for GPT API
- Splitwise for expense management API
- FastAPI and Beanie ODM teams

---

**Built with ❤️ for shared living spaces**

