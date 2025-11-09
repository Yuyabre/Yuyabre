# 🚀 Quick Start Guide

Get your Grocery Management Agent up and running in 5 minutes!

## Prerequisites Check

```bash
# Check Python version (need 3.11+)
python --version

# Check if MongoDB is installed
mongod --version

# Or use Docker
docker --version
```

## Option 1: Quick Start with Docker (Recommended)

### Step 1: Configure Environment

```bash
cd backend

# Copy environment template
cp .env.example .env

# Edit .env and add your API keys (minimum required: OPENAI_API_KEY)
nano .env  # or use your favorite editor
```

### Step 2: Start Everything

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Step 3: Initialize Database

```bash
# Add sample data
docker-compose exec api python scripts/init_db.py init
```

### Step 4: Try It Out!

**API (Swagger UI)**: http://localhost:8000/docs

**Test command**:
```bash
curl -X POST "http://localhost:8000/agent/command" \
  -H "Content-Type: application/json" \
  -d '{"command": "What is in the inventory?"}'
```

**CLI Interface**:
```bash
docker-compose exec api python cli.py
```

## Option 2: Local Development Setup

### Step 1: Install Dependencies

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### Step 2: Start MongoDB

```bash
# Option A: System MongoDB
brew services start mongodb-community  # macOS
sudo systemctl start mongod           # Linux

# Option B: Docker MongoDB only
docker run -d -p 27017:27017 --name mongodb mongo:7.0
```

### Step 3: Configure

```bash
# Copy and edit .env
cp .env.example .env

# Required: Add your OpenAI API key
# Optional: Add Splitwise credentials
nano .env
```

### Step 4: Initialize Database

```bash
# Check connection
python scripts/init_db.py check

# Add sample data
python scripts/init_db.py init
```

### Step 5: Run the Application

**Start API Server**:
```bash
# Development mode (auto-reload)
uvicorn main:app --reload

# Or use make
make run-api
```

**Access**:
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Start CLI Interface**:
```bash
# In a separate terminal
python cli.py

# Or use make
make run-cli
```

## Quick Test Commands

### CLI Commands

Once in the CLI, try:

```
You: What's in the inventory?
You: Show low stock items
You: Add 3 apples to inventory
You: Order 2 liters of milk
You: Show recent orders
You: help
```

### API Requests

```bash
# Health check
curl http://localhost:8000/health

# Get inventory
curl http://localhost:8000/inventory

# Get low stock items
curl http://localhost:8000/inventory/low-stock

# Process agent command
curl -X POST "http://localhost:8000/agent/command" \
  -H "Content-Type: application/json" \
  -d '{"command": "Show inventory"}'

# Create inventory item
curl -X POST "http://localhost:8000/inventory" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bananas",
    "category": "Fruits",
    "quantity": 6,
    "unit": "pieces",
    "threshold": 3
  }'
```

## Using Make Commands

The project includes a Makefile for convenience:

```bash
# Install dependencies
make install

# Run tests
make test

# Start API server
make run-api

# Start CLI
make run-cli

# Docker operations
make docker-up
make docker-down
make docker-logs

# Database operations
make init-db
make check-db

# Code quality
make format
make lint
make clean
```

## Troubleshooting

### MongoDB Connection Issues

```bash
# Check if MongoDB is running
# Docker:
docker ps | grep mongodb

# System:
ps aux | grep mongod

# Test connection
python scripts/init_db.py check
```

### OpenAI API Issues

```bash
# Verify API key is set
grep OPENAI_API_KEY .env

# Test with a simple command
python -c "from openai import OpenAI; client = OpenAI(); print('✓ API key valid')"
```

### Import Errors

```bash
# Make sure you're in the virtual environment
which python  # should show venv path

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Port Already in Use

```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn main:app --port 8001
```

## Next Steps

1. **Configure Splitwise** (optional but recommended):
   - Get API credentials from https://secure.splitwise.com/apps/new
   - Add to `.env` file
   - Test with: `curl http://localhost:8000/splitwise/expenses`

2. **Explore the API**:
   - Open http://localhost:8000/docs
   - Try different endpoints
   - Check the schemas and examples

3. **Read the Docs**:
   - `README.md` - Full documentation
   - `ARCHITECTURE.md` - System design details
   - API Docs - http://localhost:8000/docs

4. **Start Development**:
   - Check out the code structure
   - Run tests: `pytest -v`
   - Make changes and see them auto-reload

## Common Use Cases

### Use Case 1: Check What's Low

```bash
# CLI
You: Show low stock items

# API
curl http://localhost:8000/inventory/low-stock
```

### Use Case 2: Add Items After Shopping

```bash
# CLI
You: Add 2 liters of milk and 12 eggs to inventory

# API
curl -X POST http://localhost:8000/inventory \
  -H "Content-Type: application/json" \
  -d '{"name":"Milk","category":"Dairy","quantity":2,"unit":"liters"}'
```

### Use Case 3: Order Groceries

```bash
# CLI
You: Order 1kg of cheese and 500g of tomatoes

# API
curl -X POST http://localhost:8000/agent/command \
  -H "Content-Type: application/json" \
  -d '{"command":"Order 1kg cheese"}'
```

### Use Case 4: Check Order History

```bash
# CLI
You: Show recent orders

# API
curl http://localhost:8000/orders?limit=10
```

## Development Workflow

```bash
# 1. Start services
docker-compose up -d  # or make docker-up

# 2. Make changes to code
# (files auto-reload in development mode)

# 3. Test changes
pytest tests/test_inventory.py -v

# 4. Check logs
docker-compose logs -f api

# 5. Stop services when done
docker-compose down
```

## Getting Help

- **API Documentation**: http://localhost:8000/docs
- **Project README**: `README.md`
- **Architecture Guide**: `ARCHITECTURE.md`
- **CLI Help**: Type `help` in the CLI

---

**You're all set! 🎉**

Start with the CLI to see the agent in action, or explore the API docs to integrate with other applications.

