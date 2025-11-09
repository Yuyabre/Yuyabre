# Splitwise Integration Architecture

## How Each File Contributes to Splitwise

### 1. **`modules/splitwise/service.py`** - Core Service Layer

**Purpose:** Main service class that handles all Splitwise operations

**Key Methods:**
- **OAuth Flow (MongoDB):**
  - `get_authorize_url(user_id)` - Gets authorization URL, stores temp tokens in MongoDB User
  - `handle_oauth_callback()` - Exchanges tokens, stores access tokens in MongoDB User
  - `is_user_authorized(user_id)` - Checks if MongoDB User has tokens

- **OAuth Flow (JSON):**
  - `get_authorize_url_json(user_id, user_data)` - Gets authorization URL, stores temp tokens in JSON
  - `handle_oauth_callback_json()` - Exchanges tokens, stores access tokens in JSON
  - Uses `_exchange_tokens_manual()` - Shared helper for token exchange

- **Expense Operations:**
  - `get_group_expenses_json(user_data)` - Fetches expenses using direct API calls
  - **Note:** Expense creation uses direct API calls (in `agent/core.py`)

**What it stores:**
- OAuth tokens (access_token, access_token_secret) - Required for API calls
- Temporary tokens (oauth_token, oauth_token_secret) - During OAuth flow only
- Splitwise user ID - Used to identify users in expenses

**Unused code removed:**
- ✅ Removed SDK `getAuthorizeURL()` attempt (always used manual)
- ✅ Removed unused SDK client creation in callback
- ✅ Replaced SDK `getCurrentUser()` with direct API calls (2 places)
- ✅ Replaced SDK `getExpenses()` with direct API calls
- ✅ Removed `splitwise` SDK import entirely

**SDK completely removed:**
- ✅ All SDK usage replaced with direct API calls
- ✅ No dependency on `splitwise` Python SDK
- ✅ All operations use `requests-oauthlib` for OAuth 1.0

---

### 2. **`main.py`** - MongoDB API Server

**Purpose:** FastAPI server using MongoDB for production

**Splitwise Endpoints:**
- `GET /api/auth/splitwise/authorize?user_id=xxx` 
  - Calls `splitwise_service.get_authorize_url(user_id)`
  - Queries MongoDB User model
  - Returns authorization URL

- `GET /api/auth/splitwise/callback?oauth_token=xxx&oauth_verifier=yyy`
  - Calls `splitwise_service.handle_oauth_callback()`
  - Stores tokens in MongoDB User document
  - Can find user by `oauth_token` if `user_id` not provided

- `GET /api/auth/splitwise/status/{user_id}`
  - Calls `splitwise_service.is_user_authorized(user_id)`
  - Checks MongoDB User for tokens

- `GET /splitwise/expenses?user_id=xxx`
  - Gets MongoDB User, converts to dict
  - Calls `get_group_expenses_json()` (works with both storage types)

**Data Flow:**
```
Request → main.py → SplitwiseService → MongoDB User model → Save tokens
```

---

### 3. **`main_json.py`** - JSON API Server

**Purpose:** FastAPI server using JSON file storage for development/testing

**Splitwise Endpoints:** (Same URLs as `main.py`)
- `GET /api/auth/splitwise/authorize?user_id=xxx`
  - Gets user from `json_storage.find_one()`
  - Calls `splitwise_service.get_authorize_url_json(user_id, user)`
  - Stores temp tokens in JSON file

- `GET /api/auth/splitwise/callback?oauth_token=xxx&oauth_verifier=yyy`
  - Gets user from `json_storage.find_one()`
  - Calls `splitwise_service.handle_oauth_callback_json()`
  - Updates JSON file with tokens

- `GET /api/auth/splitwise/status/{user_id}`
  - Gets user from JSON, manually checks for tokens
  - Returns authorization status

- `GET /splitwise/expenses?user_id=xxx`
  - Gets user from JSON, passes dict directly
  - Calls `get_group_expenses_json()`

**Data Flow:**
```
Request → main_json.py → SplitwiseService → JSON file → Save tokens
```

---

### 4. **`agent/core.py`** - Expense Creation

**Purpose:** Creates Splitwise expenses when orders are placed

**What it does:**
- After order is created, checks if user is authorized
- Uses **direct API calls** (not service methods) to create expense
- Stores `splitwise_expense_id` in Order model

**Code location:** Lines 179-224
- Creates OAuth session with `requests-oauthlib`
- Builds expense data (form-encoded format)
- Makes POST to `https://secure.splitwise.com/api/v3.0/create_expense`
- Saves expense ID to Order

**Why direct API calls:**
- Service methods for expense creation were removed (SDK issues)
- Direct calls work reliably with OAuth 1.0

---

### 5. **`config.py`** - Configuration

**Purpose:** Stores Splitwise credentials and settings

**Splitwise Settings:**
- `splitwise_consumer_key` - OAuth consumer key (from Splitwise app)
- `splitwise_consumer_secret` - OAuth consumer secret
- `splitwise_callback_url` - Where Splitwise redirects after auth (default: `http://localhost:8000/api/auth/splitwise/callback`)
- `splitwise_group_id` - Optional group ID for expenses

**Used by:**
- `SplitwiseService.__init__()` - Loads credentials
- OAuth flow - Uses callback URL

---

### 6. **`models/user.py`** - User Data Model

**Purpose:** Defines User schema with Splitwise OAuth fields

**Splitwise Fields:**
- `splitwise_access_token` - Permanent access token (stored after OAuth)
- `splitwise_access_token_secret` - Permanent access token secret
- `splitwise_oauth_token` - Temporary token (during OAuth flow only)
- `splitwise_oauth_token_secret` - Temporary secret (during OAuth flow only)
- `splitwise_user_id` - Splitwise account ID (fetched after authorization)

**Storage:**
- MongoDB: Stored in User document
- JSON: Stored in `data/users.json` as dict fields

---

### 7. **`utils/json_storage.py`** - JSON File Storage

**Purpose:** File-based storage for development (replaces MongoDB)

**Methods used by Splitwise:**
- `find_one(user_id=xxx)` - Get user by ID
- `find_one(splitwise_oauth_token=xxx)` - Find user by OAuth token
- `update(user_id, {...})` - Update user with new tokens
- `find_all()` - Get all users (for demos)

**Data location:** `data/users.json`

---

### 8. **`scripts/fetch_splitwise_ids.py`** - Helper Script

**Purpose:** Fetches Splitwise user IDs for authorized users

**What it does:**
- Reads all users from JSON storage
- For each authorized user, calls Splitwise API to get their user ID
- Updates `splitwise_user_id` field in JSON

**Uses:** Direct API calls with `requests-oauthlib`

---

### 9. **`data/users.json`** - User Data (JSON Storage)

**Purpose:** Stores user data including Splitwise OAuth tokens

**Contains:**
- User info (name, email, user_id)
- Splitwise OAuth tokens (access_token, access_token_secret)
- Splitwise user ID

**Note:** Only used when running `main_json.py`, not `main.py`

---

## Data Flow Summary

### OAuth Authorization Flow:
```
1. User → GET /api/auth/splitwise/authorize?user_id=xxx
2. main.py/main_json.py → SplitwiseService.get_authorize_url()
3. Service → Gets request token from Splitwise
4. Service → Stores temp tokens (MongoDB User or JSON file)
5. Service → Returns authorization URL
6. User → Clicks URL, authorizes on Splitwise
7. Splitwise → Redirects to /api/auth/splitwise/callback
8. main.py/main_json.py → SplitwiseService.handle_oauth_callback()
9. Service → Exchanges tokens, gets access tokens
10. Service → Stores access tokens (MongoDB User or JSON file)
11. Service → Fetches Splitwise user ID, stores it
```

### Expense Creation Flow:
```
1. Order placed → agent/core.py
2. Check if user authorized → SplitwiseService.is_user_authorized()
3. Get user tokens → MongoDB User or JSON
4. Create OAuth session → requests-oauthlib
5. Build expense data → Form-encoded format
6. POST to Splitwise API → Direct API call
7. Save expense ID → Order.splitwise_expense_id
```

### Expense Retrieval Flow:
```
1. User → GET /splitwise/expenses?user_id=xxx
2. main.py/main_json.py → Get user (MongoDB or JSON)
3. Service → get_group_expenses_json(user_data)
4. Service → Direct API call to get_expenses endpoint
5. Service → Parses JSON response
6. Returns expense list
```

---

## Unused Code Removed

### From `service.py`:
1. ✅ Removed SDK `getAuthorizeURL()` attempt (always used manual anyway)
2. ✅ Removed unused SDK client creation in `handle_oauth_callback()`
3. ✅ Replaced SDK `getCurrentUser()` with direct API calls (2 places)
4. ✅ Replaced SDK `getExpenses()` with direct API calls
5. ✅ Removed `splitwise` SDK import entirely

---

## Migration to MongoDB for Production

### Current State:
- **Development:** `main_json.py` uses JSON file storage
- **Production Ready:** `main.py` uses MongoDB (code is ready)

### Steps to Migrate:

**1. Start MongoDB:**
```bash
# Option A: Docker
docker run -d -p 27017:27017 --name mongodb mongo:7.0

# Option B: Docker Compose
docker-compose up -d mongodb

# Option C: Local installation
brew install mongodb-community  # macOS
brew services start mongodb-community
```

**2. Migrate User Data (Optional):**
```python
# Create migration script: migrate_json_to_mongodb.py
from utils.json_storage import json_storage
from models.user import User
from database import db
import asyncio

async def migrate():
    await db.connect()
    
    json_users = json_storage.find_all()
    for json_user in json_users:
        user = User(
            user_id=json_user['user_id'],
            name=json_user['name'],
            email=json_user.get('email'),
            splitwise_access_token=json_user.get('splitwise_access_token'),
            splitwise_access_token_secret=json_user.get('splitwise_access_token_secret'),
            splitwise_user_id=json_user.get('splitwise_user_id'),
            # ... other fields
        )
        await user.insert()
    
    await db.close()

asyncio.run(migrate())
```

**3. Switch to MongoDB:**
- Use `main.py` instead of `main_json.py`
- All endpoints work the same way
- Data stored in MongoDB instead of JSON file

**4. Run Production Server:**
```bash
# Using main.py (MongoDB)
uvicorn main:app --host 0.0.0.0 --port 8000

# Or with Docker Compose
docker-compose up
```

### What Changes:
- ✅ Same API endpoints
- ✅ Same OAuth flow
- ✅ Same functionality
- ✅ Data stored in MongoDB (more reliable, scalable)
- ✅ Can handle multiple users, concurrent requests
- ✅ Better for production deployment

### What Stays the Same:
- ✅ OAuth flow logic
- ✅ Expense creation (direct API calls)
- ✅ Expense retrieval
- ✅ All service methods work identically

---

## Summary

**All files work together:**
1. **config.py** → Provides credentials
2. **service.py** → Handles OAuth and API calls
3. **main.py/main_json.py** → Expose API endpoints
4. **models/user.py** → Defines data structure
5. **agent/core.py** → Creates expenses on orders
6. **json_storage.py** → Development storage (optional)
7. **scripts/fetch_splitwise_ids.py** → Helper utility

**Data storage:**
- Development: JSON file (`data/users.json`)
- Production: MongoDB (User collection)

**Code is production-ready** - just needs MongoDB running!

