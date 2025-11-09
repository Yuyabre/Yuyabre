# 🚀 Setup Guide - Yuyabre Grocery Management Agent

Complete guide for setting up the Yuyabre backend with all required credentials and configurations.

## 📋 Table of Contents

- [System Requirements](#system-requirements)
- [Installation Steps](#installation-steps)
- [Required Credentials](#required-credentials)
- [Environment Configuration](#environment-configuration)
- [Service Setup Instructions](#service-setup-instructions)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## 🖥️ System Requirements

### Software Requirements

- **Python**: 3.11 or higher
- **MongoDB**: 7.0 or higher (local or cloud instance)
- **Git**: For cloning the repository
- **pip**: Python package manager

### Optional but Recommended

- **Docker & Docker Compose**: For containerized deployment
- **ngrok** or similar: For webhook testing (Discord/WhatsApp)

## 📦 Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Yuyabre/backend
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up MongoDB

**Option A: Local MongoDB**

```bash
# Using Docker (recommended)
docker run -d -p 27017:27017 --name mongodb mongo:7.0

# Or install MongoDB locally
# macOS: brew install mongodb-community
# Ubuntu: sudo apt-get install mongodb
```

**Option B: MongoDB Atlas (Cloud)**

1. Go to https://www.mongodb.com/cloud/atlas
2. Create a free cluster
3. Get your connection string

### 5. Create Environment File

```bash
cp .env.example .env
# Edit .env with your credentials (see below)
```

### 6. Create Logs Directory

```bash
mkdir -p logs
```

## 🔑 Required Credentials

### Core Services (Required)

#### 1. OpenAI API Key

**Purpose**: Powers the AI agent's natural language understanding

**How to Get**:
1. Go to https://platform.openai.com/
2. Sign up or log in
3. Navigate to API Keys: https://platform.openai.com/api-keys
4. Click "Create new secret key"
5. Copy the key (you won't see it again!)

**Environment Variable**: `OPENAI_API_KEY`

**Example**:
```env
OPENAI_API_KEY=sk-proj-abc123xyz789...
```

**Cost**: Pay-as-you-go. GPT-4 is more expensive than GPT-3.5

---

#### 2. MongoDB Connection

**Purpose**: Stores all data (inventory, orders, users, households)

**Local MongoDB**:
```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=grocery_agent
```

**MongoDB Atlas (Cloud)**:
```env
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=grocery_agent
```

**How to Get MongoDB Atlas URI**:
1. Go to https://www.mongodb.com/cloud/atlas
2. Create account and free cluster
3. Click "Connect" → "Connect your application"
4. Copy the connection string
5. Replace `<password>` with your database password

---

### Optional Services

#### 3. Discord Bot (Recommended Alternative to WhatsApp)

**Purpose**: Send group order notifications and receive responses via Discord

**How to Set Up**:

1. **Create Discord Application**:
   - Go to https://discord.com/developers/applications
   - Click "New Application"
   - Give it a name (e.g., "Yuyabre Bot")
   - Click "Create"

2. **Create Bot**:
   - Go to "Bot" section in left sidebar
   - Click "Add Bot" → "Yes, do it!"
   - Under "Token", click "Reset Token" → "Yes, do it!"
   - Copy the token (this is your `DISCORD_BOT_TOKEN`)

3. **Set Bot Permissions**:
   - Go to "OAuth2" → "URL Generator"
   - Under "Scopes", check:
     - ✅ `bot`
   - Under "Bot Permissions", check:
     - ✅ `Send Messages`
     - ✅ `Read Message History`
     - ✅ `View Channels`
   - Copy the generated URL

4. **Invite Bot to Server**:
   - Paste the URL in your browser
   - Select your Discord server
   - Click "Authorize"
   - Complete the CAPTCHA

5. **Get Channel ID**:
   - In Discord, enable Developer Mode (User Settings → Advanced → Developer Mode)
   - Right-click on your channel → "Copy ID"
   - This is your `discord_channel_id` (set in household settings)

**Environment Variable**: `DISCORD_BOT_TOKEN`

**Example**:
```env
DISCORD_BOT_TOKEN=MTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzNA.GhIjKl.MnOpQrStUvWxYzAbCdEfGhIjKlMnOpQrStUvWx
```

**Note**: You'll also need to set `discord_channel_id` in your household record (via API or database)

---

#### 4. WhatsApp via Twilio (Alternative to Discord)

**Purpose**: Send group order notifications via WhatsApp

**How to Set Up**:

1. **Create Twilio Account**:
   - Go to https://www.twilio.com/
   - Sign up for free account
   - Verify your phone number

2. **Get WhatsApp Sandbox**:
   - Go to https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
   - Follow instructions to join the sandbox
   - Send the join code to the Twilio WhatsApp number

3. **Get Credentials**:
   - Go to https://console.twilio.com/
   - Find "Account SID" and "Auth Token" on dashboard
   - Copy both values

4. **Get WhatsApp Number**:
   - Go to Phone Numbers → Manage → Active numbers
   - Your WhatsApp number format: `whatsapp:+14155238886`

5. **Set Webhook URL** (for receiving messages):
   - Use ngrok: `ngrok http 8000`
   - Copy the HTTPS URL
   - Set webhook: `https://your-ngrok-url.ngrok.io/whatsapp/webhook`

**Environment Variables**:
```env
WHATSAPP_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
WHATSAPP_AUTH_TOKEN=your_auth_token_here
WHATSAPP_FROM_NUMBER=whatsapp:+14155238886
WHATSAPP_WEBHOOK_URL=https://your-domain.com/whatsapp/webhook
```

**Cost**: Free sandbox for testing, paid for production

---

#### 5. Splitwise API (Optional)

**Purpose**: Automatically split grocery expenses among housemates

**How to Set Up**:

1. **Create Splitwise App**:
   - Go to https://secure.splitwise.com/apps/new
   - Log in to Splitwise
   - Fill in application details:
     - Application Name: "Yuyabre Grocery Agent"
     - Description: "Automated grocery expense splitting"
     - Redirect URI: `http://localhost:8000/splitwise/callback`
   - Click "Create Application"

2. **Get Credentials**:
   - After creation, you'll see:
     - Consumer Key
     - Consumer Secret
   - Copy both values

3. **Get API Key**:
   - You'll need to complete OAuth flow to get API key
   - Or use personal API key from https://secure.splitwise.com/apps

4. **Get Group ID**:
   - Go to your Splitwise group
   - The URL will be: `https://secure.splitwise.com/#/groups/1234567`
   - The number `1234567` is your group ID

**Environment Variables**:
```env
SPLITWISE_API_KEY=your_api_key_here
SPLITWISE_CONSUMER_KEY=your_consumer_key_here
SPLITWISE_CONSUMER_SECRET=your_consumer_secret_here
SPLITWISE_GROUP_ID=1234567
```

**Note**: Splitwise integration is optional. The system works without it.

---

#### 6. Thuisbezorgd (Optional - For Actual Ordering)

**Purpose**: Place actual grocery orders (currently placeholder implementation)

**Environment Variables**:
```env
THUISBEZORGD_EMAIL=your_email@example.com
THUISBEZORGD_PASSWORD=your_password
THUISBEZORGD_API_URL=https://api.thuisbezorgd.nl
```

**Note**: This is currently a placeholder. Real integration depends on Thuisbezorgd API availability.

---

## ⚙️ Environment Configuration

Create a `.env` file in the `backend/` directory with all your credentials:

```env
# ============================================
# CORE CONFIGURATION (REQUIRED)
# ============================================

# MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=grocery_agent
# Optional if MongoDB requires auth:
# MONGODB_USERNAME=admin
# MONGODB_PASSWORD=password123

# OpenAI API
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_PROXY_URL=https://your-proxy-url.com/v1

# ============================================
# MESSAGING SERVICES (CHOOSE ONE OR BOTH)
# ============================================

# Discord Bot (Recommended)
DISCORD_BOT_TOKEN=your_discord_bot_token_here

# WhatsApp via Twilio (Alternative)
WHATSAPP_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
WHATSAPP_AUTH_TOKEN=your_twilio_auth_token
WHATSAPP_FROM_NUMBER=whatsapp:+14155238886
WHATSAPP_WEBHOOK_URL=https://your-domain.com/whatsapp/webhook

# ============================================
# OPTIONAL SERVICES
# ============================================

# Splitwise (Expense Splitting)
SPLITWISE_API_KEY=your_splitwise_api_key
SPLITWISE_CONSUMER_KEY=your_consumer_key
SPLITWISE_CONSUMER_SECRET=your_consumer_secret
SPLITWISE_GROUP_ID=1234567

# Thuisbezorgd (Grocery Ordering - Placeholder)
THUISBEZORGD_EMAIL=your_email@example.com
THUISBEZORGD_PASSWORD=your_password
THUISBEZORGD_API_URL=https://api.thuisbezorgd.nl

# ============================================
# APPLICATION SETTINGS
# ============================================

APP_ENV=development
APP_DEBUG=True
LOG_LEVEL=INFO
```

## 🔧 Service Setup Instructions

### Discord Setup (Step-by-Step)

1. **Create Bot**:
   ```
   https://discord.com/developers/applications
   → New Application → Name it → Create
   → Bot → Add Bot → Reset Token → Copy Token
   ```

2. **Set Permissions**:
   ```
   OAuth2 → URL Generator
   → Scopes: bot
   → Bot Permissions: Send Messages, Read Message History, View Channels
   → Copy URL → Open in browser → Authorize
   ```

3. **Get Channel ID**:
   ```
   Discord → Enable Developer Mode
   → Right-click channel → Copy ID
   ```

4. **Configure Household**:
   - Use API or database to set `discord_channel_id` in household record
   - Or set during household creation via CLI

### WhatsApp Setup (Step-by-Step)

1. **Twilio Account**:
   ```
   https://www.twilio.com → Sign Up
   → Verify phone → Get Account SID & Auth Token
   ```

2. **WhatsApp Sandbox**:
   ```
   Console → Messaging → Try it out → Send a WhatsApp message
   → Join sandbox by sending code to Twilio number
   ```

3. **Webhook Setup** (for receiving messages):
   ```bash
   # Install ngrok
   ngrok http 8000
   
   # Copy HTTPS URL (e.g., https://abc123.ngrok.io)
   # Set in Twilio Console → Messaging → Settings → WhatsApp Sandbox Settings
   # Webhook URL: https://abc123.ngrok.io/whatsapp/webhook
   ```

## ✅ Verification

### Test MongoDB Connection

```bash
python -c "from database import db; import asyncio; asyncio.run(db.connect()); print('✓ MongoDB connected')"
```

### Test OpenAI Connection

```bash
python -c "from config import settings; print(f'✓ OpenAI configured: {bool(settings.openai_api_key)}')"
```

### Test Discord Bot

1. Start the server: `python main.py`
2. Check logs for: `Discord bot logged in as YourBot#1234`
3. Send a message in your Discord channel
4. Check server logs for message forwarding

### Test WhatsApp

1. Start the server: `python main.py`
2. Send WhatsApp message to your Twilio number
3. Check server logs for webhook receipt

### Run Full System Test

```bash
# Start server
python main.py

# In another terminal, test CLI
python cli.py

# Try commands:
# - "Order 2 liters of milk"
# - "What's in the inventory?"
# - "Show low stock items"
```

## 🐛 Troubleshooting

### Discord Bot Not Starting

**Problem**: Bot doesn't appear online in Discord

**Solutions**:
- Check `DISCORD_BOT_TOKEN` is correct
- Verify bot has proper permissions
- Check server logs for errors
- Ensure bot is invited to server

### Discord Messages Not Received

**Problem**: Messages sent but not processed

**Solutions**:
- Verify `discord_channel_id` is set in household
- Check channel ID is correct (must be integer)
- Ensure bot has "Read Message History" permission
- Check webhook endpoint is accessible: `http://localhost:8000/discord/webhook`

### WhatsApp Not Working

**Problem**: Messages not sending/receiving

**Solutions**:
- Verify you've joined Twilio WhatsApp sandbox
- Check webhook URL is accessible (use ngrok for local testing)
- Verify phone number format: `whatsapp:+1234567890`
- Check Twilio console for error logs

### MongoDB Connection Failed

**Problem**: Cannot connect to database

**Solutions**:
- Verify MongoDB is running: `docker ps` or `mongod --version`
- Check connection string format
- For Atlas: Ensure IP is whitelisted
- Check firewall settings

### OpenAI API Errors

**Problem**: Agent not responding

**Solutions**:
- Verify API key is valid
- Check account has credits
- Verify proxy URL if using custom endpoint
- Check rate limits

## 📝 Quick Reference

### Minimum Required Credentials

For basic functionality (CLI only, no messaging):
- ✅ OpenAI API Key
- ✅ MongoDB Connection

For full functionality with messaging:
- ✅ OpenAI API Key
- ✅ MongoDB Connection
- ✅ Discord Bot Token **OR** WhatsApp (Twilio) credentials

### Environment File Template

```env
# Minimum setup
OPENAI_API_KEY=sk-...
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=grocery_agent

# Add messaging (choose one)
DISCORD_BOT_TOKEN=...
# OR
WHATSAPP_ACCOUNT_SID=...
WHATSAPP_AUTH_TOKEN=...
WHATSAPP_FROM_NUMBER=whatsapp:+...
```

## 🔒 Security Notes

- **Never commit `.env` file** to version control
- Add `.env` to `.gitignore`
- Use environment variables in production
- Rotate API keys regularly
- Use strong MongoDB passwords
- Keep Discord bot token secret

## 📞 Support

If you encounter issues:

1. Check server logs in `logs/` directory
2. Verify all credentials are correct
3. Test each service individually
4. Check service status pages:
   - OpenAI: https://status.openai.com/
   - Discord: https://discordstatus.com/
   - Twilio: https://status.twilio.com/

---

**Last Updated**: 2025-01-08
**Version**: 1.0.0

