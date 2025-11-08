# Architecture Documentation

## System Overview

The Grocery Management Agent is built as a modular, scalable system with clear separation of concerns.

## Core Components

### 1. Agent Core (`agent/`)

The central AI orchestrator that:
- Processes natural language commands
- Parses user intent using OpenAI GPT
- Coordinates between different service modules
- Implements business logic for workflows

**Key Class**: `GroceryAgent`

### 2. Service Modules (`modules/`)

#### Inventory Service
- CRUD operations for inventory items
- Low-stock detection
- Expiration tracking
- Quantity management

#### Ordering Service
- Product search (Thuisbezorgd)
- Order placement
- Order status tracking
- Order history

#### Splitwise Service
- Expense creation
- Cost splitting among users
- Expense tracking
- Group expense retrieval

### 3. Data Models (`models/`)

#### InventoryItem
- Represents grocery items in inventory
- Tracks quantities, thresholds, expiration dates
- Methods for stock checking and updates

#### Order
- Represents a grocery order
- Contains order items, pricing, delivery info
- Tracks order status through lifecycle

#### User
- Represents a flatmate
- Stores preferences and dietary restrictions
- Tracks consumption patterns

### 4. Database Layer (`database.py`)

- MongoDB connection management
- Beanie ODM initialization
- Connection pooling and health checks

### 5. API Layer (`main.py`)

- FastAPI application
- REST endpoints for all operations
- Request/response validation
- Error handling

### 6. CLI Interface (`cli.py`)

- Interactive command-line interface
- Rich terminal UI
- User-friendly command processing

## Data Flow

### Example: Ordering Workflow

```
1. User Command (CLI/API)
   ↓
2. GroceryAgent.process_command()
   ↓
3. Intent Parsing (OpenAI GPT)
   ↓
4. OrderingService.create_order()
   ↓
5. Order saved to MongoDB
   ↓
6. InventoryService.update_quantity()
   ↓
7. SplitwiseService.create_expense()
   ↓
8. Response to User
```

## Design Patterns

### Service Layer Pattern
Each module has a service class that encapsulates business logic:
- `InventoryService`
- `OrderingService`
- `SplitwiseService`

### Repository Pattern
Beanie ODM provides repository-like access to MongoDB collections.

### Dependency Injection
Services are instantiated in the agent and can be easily swapped or mocked for testing.

## Scalability Considerations

### Current Architecture
- Single-instance deployment
- Direct MongoDB connection
- Synchronous Splitwise API calls

### Future Scaling Options
- **Horizontal Scaling**: Multiple API instances behind load balancer
- **Caching**: Redis for frequently accessed data
- **Message Queue**: RabbitMQ/Celery for async order processing
- **Microservices**: Split into separate services (inventory, ordering, expenses)

## Security

### Current Implementation
- Environment-based configuration
- API key management via .env
- Input validation with Pydantic

### Future Enhancements
- JWT authentication
- Rate limiting
- API key rotation
- Encryption at rest

## Testing Strategy

### Unit Tests
- Test individual service methods
- Mock external dependencies
- Focus on business logic

### Integration Tests
- Test API endpoints
- Use test database
- Verify data persistence

### End-to-End Tests
- Simulate full user workflows
- Test agent command processing
- Verify multi-service coordination

## Monitoring & Logging

### Current
- Loguru for structured logging
- File-based logs with rotation
- Console output for development

### Future
- Prometheus metrics
- Grafana dashboards
- Error tracking (Sentry)
- Performance monitoring

## Configuration Management

### Environment Variables
All configuration through `.env` file:
- Database connections
- API keys
- Feature flags
- Logging levels

### Settings Class
Type-safe configuration using Pydantic settings:
```python
from config import settings
settings.openai_api_key
settings.mongodb_uri
```

## API Design Principles

1. **RESTful**: Standard HTTP methods and status codes
2. **Versioned**: Future-proof with API versioning
3. **Documented**: Auto-generated OpenAPI docs
4. **Validated**: Request/response validation with Pydantic
5. **Consistent**: Standard error format across endpoints

## Extension Points

### Adding New Service Modules

1. Create module directory: `modules/new_service/`
2. Implement service class with async methods
3. Add to agent orchestration in `agent/core.py`
4. Create API endpoints in `main.py`
5. Write tests in `tests/test_new_service.py`

### Adding New Data Models

1. Create model file in `models/`
2. Define Beanie Document class
3. Add to database initialization in `database.py`
4. Import in `models/__init__.py`

### Adding New Agent Capabilities

1. Add intent parsing logic in `agent/core.py`
2. Implement handler method (e.g., `_handle_new_action`)
3. Update LLM system prompt with new action type
4. Add CLI/API endpoints as needed

## Performance Optimization

### Database
- Indexes on frequently queried fields
- Efficient query patterns with Beanie
- Connection pooling

### API
- Async operations throughout
- Efficient serialization with Pydantic
- Response caching (future)

### Agent
- Optimized LLM prompts for faster responses
- Caching of common queries (future)
- Batch processing of multiple items

## Deployment Architecture

### Development
```
Developer Machine
├── MongoDB (local)
├── API Server (uvicorn reload)
└── CLI (interactive)
```

### Production (Docker)
```
Docker Host
├── MongoDB Container
│   └── Persistent Volume
├── API Container(s)
│   └── Load Balanced
└── Reverse Proxy (nginx)
```

### Future Cloud Deployment
```
Cloud Provider
├── Managed MongoDB (Atlas)
├── Container Orchestration (K8s)
├── API Gateway
├── CDN (static assets)
└── Monitoring Stack
```

