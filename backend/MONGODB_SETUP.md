# MongoDB Setup Guide

## Quick Answer

**MongoDB is not running.** You need to start a MongoDB server. You don't need to add an API - just start MongoDB.

---

## Option 1: Docker (Easiest - Recommended) 🐳

### Start MongoDB with Docker

```bash
cd backend

# Start MongoDB in a container
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  mongo:7.0

# Check if it's running
docker ps | grep mongodb
```

### Or use Docker Compose (starts everything)

```bash
cd backend

# Start MongoDB + API + Mongo Express
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs mongodb
```

**This starts:**
- ✅ MongoDB on port 27017
- ✅ FastAPI on port 8000
- ✅ Mongo Express (DB admin) on port 8081

---

## Option 2: Install MongoDB Locally 💻

### macOS (using Homebrew)

```bash
# Install MongoDB
brew tap mongodb/brew
brew install mongodb-community

# Start MongoDB service
brew services start mongodb-community

# Check if running
brew services list | grep mongodb
```

### Linux (Ubuntu/Debian)

```bash
# Install MongoDB
sudo apt-get update
sudo apt-get install -y mongodb

# Start MongoDB service
sudo systemctl start mongod
sudo systemctl enable mongod  # Start on boot

# Check status
sudo systemctl status mongod
```

### Windows

1. Download MongoDB from: https://www.mongodb.com/try/download/community
2. Install MongoDB
3. Start MongoDB service from Services panel

---

## Verify MongoDB is Running ✅

### Test Connection

```bash
cd backend

# Test with Python
python3 -c "
import asyncio
from database import db

async def test():
    try:
        await db.connect()
        print('✅ MongoDB is running!')
        await db.close()
    except Exception as e:
        print(f'❌ MongoDB connection failed: {e}')

asyncio.run(test())
"
```

### Or use MongoDB shell

```bash
# If MongoDB is installed locally
mongosh

# Or if using Docker
docker exec -it mongodb mongosh
```

---

## Configuration

### Default Settings

Your app is configured to connect to:
- **Host**: `localhost:27017`
- **Database**: `grocery_agent`

These are set in `config.py` and can be overridden with environment variables.

### Environment Variables (Optional)

Create or edit `.env` file in `backend/`:

```env
# MongoDB Connection
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=grocery_agent

# If MongoDB has authentication:
# MONGODB_URI=mongodb://username:password@localhost:27017
```

---

## Troubleshooting

### Error: "Connection refused"

**Cause**: MongoDB is not running

**Solution**:
```bash
# Check if MongoDB is running
docker ps | grep mongodb  # If using Docker
brew services list | grep mongodb  # If using Homebrew
sudo systemctl status mongod  # If using systemd

# Start MongoDB
docker start mongodb  # Docker
brew services start mongodb-community  # Homebrew
sudo systemctl start mongod  # systemd
```

### Error: "Port 27017 already in use"

**Cause**: Another MongoDB instance is running

**Solution**:
```bash
# Find what's using the port
lsof -i :27017  # macOS/Linux
netstat -ano | findstr :27017  # Windows

# Stop the conflicting service or use a different port
```

### Error: "Authentication failed"

**Cause**: MongoDB requires authentication

**Solution**:
```env
# Add credentials to .env
MONGODB_URI=mongodb://username:password@localhost:27017
```

---

## Quick Start Commands

### Using Docker (Recommended)

```bash
cd backend

# Start MongoDB
docker run -d --name mongodb -p 27017:27017 mongo:7.0

# Test connection
python3 -c "import asyncio; from database import db; asyncio.run(db.connect()); print('✅ Connected!')"

# Stop MongoDB
docker stop mongodb

# Remove container (if needed)
docker rm mongodb
```

### Using Docker Compose

```bash
cd backend

# Start everything
docker-compose up -d

# Check logs
docker-compose logs -f mongodb

# Stop everything
docker-compose down

# Stop but keep data
docker-compose stop
```

---

## Database Management

### View Data (Mongo Express)

If using Docker Compose, Mongo Express is available at:
- **URL**: http://localhost:8081
- **Username**: admin
- **Password**: admin123

### Command Line

```bash
# Connect to MongoDB shell
docker exec -it mongodb mongosh

# Or if installed locally
mongosh

# List databases
show dbs

# Use your database
use grocery_agent

# List collections
show collections

# View orders
db.orders.find().pretty()
```

---

## Summary

**You don't need to add an API** - MongoDB is a database server, not an API.

**To fix the connection error:**
1. ✅ Start MongoDB (Docker is easiest)
2. ✅ Verify it's running
3. ✅ Test the connection
4. ✅ Run your application

**Recommended**: Use Docker - it's the simplest and most reliable option.

```bash
# One command to start MongoDB
docker run -d --name mongodb -p 27017:27017 mongo:7.0
```

That's it! Your app will now be able to connect to MongoDB. 🎉

