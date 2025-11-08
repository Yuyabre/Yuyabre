# Shared Flat Grocery Management Agent

## Project Overview

An intelligent agent system designed to automate grocery management for shared flats and groups. The system handles inventory tracking, automatic ordering, expense splitting, and group communication.

## Core Objectives

- Automate grocery inventory management for shared living spaces
- Integrate ordering through Thuisbezorgd (Dutch grocery delivery)
- Automatically split costs via Splitwise
- Notify flatmates through WhatsApp
- Learn eating habits and ordering patterns over time

---

## Priority Tasks (1.5 Day Sprint)

**Sprint Goal:** Build a functional text-based agent that can autonomously order groceries, track inventory, and split expenses.

### Core Features (MUST HAVE)

1. **MongoDB Inventory System**

   - CRUD operations for inventory items
   - Track quantities, thresholds, and expiration dates
   - Real-time inventory updates when orders are placed

2. **Modular Splitwise Integration**

   - Separate, reusable Splitwise module
   - Create expenses automatically after orders
   - Equal split by default (configurable)
   - Handle expense creation, updates, and retrieval

3. **Autonomous Grocery Ordering**

   - Agent can place orders through Thuisbezorgd (API or scraping)
   - Order placement logic (triggered by low inventory or manual request)
   - Order confirmation and tracking

4. **Text-Based Agent Interface**
   - CLI or simple text interface for commands
   - Natural language processing for user commands
   - Agent can respond to queries about inventory, orders, expenses

### Deferred Features (OUT OF SCOPE for sprint)

- ❌ Voice input (Whisper API)
- ❌ Picture/OCR receipt scanning
- ❌ WhatsApp notifications (MAYBE)
- ❌ Calendar integration
- ❌ Learning/prediction algorithms
- ❌ Web UI (CLI/text only)
- ❌ Multi-household support

### Implementation Priority

**Day 1 (Morning):**

- [ ] Set up MongoDB database and schema
- [ ] Build inventory CRUD module
- [ ] Create basic text-based agent interface

**Day 1 (Afternoon):**

- [ ] Implement modular Splitwise integration
- [ ] Test Splitwise expense creation
- [ ] Connect inventory to Splitwise (when items are ordered)

**Day 2 (Morning):**

- [ ] Research/implement Thuisbezorgd integration
- [ ] Build order placement logic
- [ ] Connect ordering to inventory updates

**Day 2 (Afternoon):**

- [ ] End-to-end testing: Order → Inventory → Splitwise
- [ ] Error handling and edge cases
- [ ] Documentation and cleanup

---

## System Architecture

### Central Agent

The core AI agent that orchestrates all system components.

**Input Sources (Sprint Focus):**

- **Text** - Manual text input and commands (CLI or simple interface)
- ~~**Voice** - Voice commands for quick interactions~~ (Deferred)
- ~~**Pictures** - Image recognition for receipt scanning or inventory checks~~ (Deferred)

**External Data Sources:**

- **ChatGPT/LLM** - Natural language processing and decision making (for text commands)
- ~~**Calendar** - Schedule-based ordering and meal planning~~ (Deferred)

**Output:**

- Drives the Actions module
- Executes orders, updates inventory, creates Splitwise expenses
- ~~Generates insights from learned patterns~~ (Deferred)

---

## Key Components

### 1. Distributed Systems

**Ordering Patterns**

- Track frequency of specific items
- Identify recurring purchases
- Optimize order timing

**Eating Habits**

- Monitor consumption rates
- Learn dietary preferences per flatmate
- Predict future needs

**Splitwise Tracking**

- Automatic expense splitting
- Integration with Splitwise API
- Fair cost distribution based on consumption

**Inventory System**

- Real-time inventory tracking
- Low-stock alerts
- Expiration date monitoring

### 2. Actions Module

Core actions the agent can perform:

**Task Reminders**

- Remind flatmates about pending orders
- Alert about expiring items
- Notify about pending payments

**Order Groceries**

- Automated ordering through Thuisbezorgd
- Manual approval flow option
- Dietary restriction filtering

**API to Thuisbezorgd**

- Integration with delivery service
- Order placement and tracking
- Delivery time coordination

**Update Inventory**

- Add items from orders
- Remove consumed items
- Track quantity changes

**Send Message on WhatsApp**

- Group notifications
- Order confirmations
- Payment reminders
- Delivery updates

### 3. Data Storage & Logging

**Database (MongoDB - Sprint Focus)**

- Store all inventory items
- Historical order data
- Order status and tracking
- Splitwise expense references
- ~~User preferences~~ (Deferred)
- ~~Consumption patterns~~ (Deferred)

**Logging System**

- Basic console/file logging for development
- ~~Google Sheets integration~~ (Deferred)
- ~~Timeline of all events (MDT/timeline)~~ (Deferred)
- Audit trail for orders and expenses (basic)

---

## Technical Implementation Questions

### Thuisbezorgd Integration

**Questions to Address:**

- Does Thuisbezorgd have a public API?
  - If yes: Use official API
  - If no: Web scraping or alternative service
- Order approval workflow:
  - Fully automated?
  - Require manual confirmation?
  - Threshold-based (auto-order cheap items, confirm expensive ones)?

### Agent Intelligence

**Order Triggering Logic:**

- Inventory threshold reached (e.g., "only 2 eggs left")
- Scheduled times (e.g., "every Sunday at 10 AM")
- Manual requests from flatmates
- Predictive ordering based on consumption patterns

**Learning Mechanisms:**

- Frequency analysis of purchases
- Time-series forecasting for consumption
- Pattern recognition in eating habits
- Seasonal adjustment

**Voice Input:**

- Whisper API for speech-to-text?
- System voice recognition?
- Wake word detection?

### Splitwise Integration (Modular Implementation)

**Module Design:**

- Separate `splitwise/` module with clear interface
- Functions: `create_expense()`, `get_expense()`, `update_expense()`
- Configuration: API keys, group ID, default split method

**Cost Distribution (Sprint):**

- Equal split by default (simplest for MVP)
- ~~Usage-based split~~ (Deferred)
- ~~Opt-in/opt-out per order~~ (Deferred)
- ~~Custom split ratios per flatmate~~ (Deferred)

**Edge Cases (Future):**

- Flatmate temporarily away
- Guest visitors
- Personal vs. shared items

### WhatsApp Integration

**Integration Method:**

- WhatsApp Business API (official, requires approval)
- Unofficial libraries (e.g., whatsapp-web.js)
- Alternative: Telegram bot (easier API)

**Notification Types:**

- Order placed confirmation
- Delivery time update
- Bill split summary
- Low inventory alerts
- Payment reminders

---

## User Workflows

### Workflow 1: Text-Based Order (Sprint Focus)

```
User: "Order 2 liters of milk"
↓
Agent: Processes text command via LLM
↓
Agent: Checks Thuisbezorgd for milk options
↓
Agent: Sends text message on common whatsapp group and confirm if others need it (incase milk has been tagged as a shared item before or if multiple people have ordered it based on the inventory)
↓
Agent: Places order automatically (based on how many people asked for it)
↓
Agent: Send message to group chat (if implemented) about delivery
↓
Agent: Check delivery status. (Repeat until done)
↓
Agent: Updates MongoDB inventory (+X liters milk) (if success)
↓
Agent: Creates Splitwise expense (modular module)
↓
Agent: Responds: "Order placed! XL milk added to inventory. Splitwise expense created."
```

### Workflow 2: Manual Inventory Update (Sprint Focus)

```
User (CLI): "Add 5 eggs to inventory"
↓
Agent: Updates MongoDB inventory (+5 eggs)
↓
Agent: Responds: "Inventory updated: 5 eggs added"
```

### Workflow 3: Query Inventory (Sprint Focus)

```
User (CLI): "What's in the inventory?"
↓
Agent: Queries MongoDB
↓
Agent: Responds with formatted inventory list
```

### Workflow 4: Future - Automated Scheduled Order (Deferred)

```
Sunday 9 AM: Agent checks inventory
↓
Agent: Identifies low-stock items (learned patterns)
↓
Agent: Generates suggested order
↓
Agent: WhatsApp group: "Weekly order ready, review items?"
↓
Flatmates: Add/remove items via chat
↓
10 AM: Agent places order, splits costs, logs everything
```

---

## Data Models

### Inventory Item

```json
{
  "id": "uuid",
  "name": "Milk",
  "category": "Dairy",
  "quantity": 2,
  "unit": "liters",
  "threshold": 1,
  "last_updated": "2025-11-08T10:00:00Z",
  "expiration_date": "2025-11-15",
  "shared": true
}
```

### Order

```json
{
  "id": "uuid",
  "timestamp": "2025-11-08T10:00:00Z",
  "service": "Thuisbezorgd",
  "items": [
    {
      "product_id": "123",
      "name": "Milk",
      "quantity": 2,
      "price": 3.5,
      "requested_by": ["user1", "user2"]
    }
  ],
  "total": 3.5,
  "delivery_time": "2025-11-08T14:00:00Z",
  "status": "delivered",
  "splitwise_expense_id": "789"
}
```

### User Preference

```json
{
  "user_id": "user1",
  "dietary_restrictions": ["vegetarian"],
  "favorite_brands": ["Brand A", "Brand B"],
  "allergies": ["nuts"],
  "consumption_patterns": {
    "milk": {
      "weekly_average": 1.5,
      "preferred_type": "semi-skimmed"
    }
  }
}
```

---

## Technology Stack (Sprint Focus)

### Backend

- **Language:** Python (recommended for LLM integration) or Node.js
- **Framework:** FastAPI (Python) - minimal setup
- **Database:** **MongoDB** (primary database for inventory and orders)
- **LLM Integration:** OpenAI API (GPT-5) for text command processing
- ~~**Voice Processing:** Whisper API~~ (Deferred)

### Integrations (Sprint)

- **Splitwise:** Official API (modular implementation)
- **Thuisbezorgd:** Web scraping or API (if available)
- ~~**WhatsApp:** whatsapp-web.js or Business API~~ (Deferred)
- ~~**Calendar:** Google Calendar API~~ (Deferred)
- ~~**Image Processing:** OCR via Tesseract or Google Vision API~~ (Deferred)

### Infrastructure (Minimal for Sprint)

- **Hosting:** Local development (OVH VPS for deployment later)
- **Containerization:** Docker (optional, for consistency)
- ~~**Orchestration:** Docker Compose or Kubernetes~~ (Deferred)
- ~~**Monitoring:** Prometheus + Grafana~~ (Deferred)
- **Logging:** Basic file/console logging

---

## Development Phases

### Phase 1: Sprint (1.5 Days) - CURRENT FOCUS

**Core Deliverables:**

- [x] MongoDB database setup and schema design
- [ ] Inventory CRUD module (MongoDB)
- [ ] Modular Splitwise integration (separate module)
- [ ] Thuisbezorgd ordering integration (API or scraping)
- [ ] Text-based agent interface (CLI)
- [ ] End-to-end flow: Order → Inventory Update → Splitwise Expense

**Success Criteria:**

- Agent can receive text command: "Order 2 liters of milk"
- Agent places order via Thuisbezorgd
- Inventory automatically updated in MongoDB
- Splitwise expense created and split among flatmates
- Agent responds with confirmation

### Phase 2: Post-Sprint Enhancements

- [ ] Automatic low-stock detection and alerts
- [ ] Order history and basic analytics
- [ ] Error handling and retry logic
- [ ] Configuration file for API keys and settings
- [ ] Better CLI interface with commands help

### Phase 3: Communication & Intelligence (Future)

- [ ] WhatsApp notifications
- [ ] Voice input via Whisper API
- [ ] Picture-based receipt scanning (OCR)
- [ ] Pattern recognition in consumption
- [ ] Predictive ordering based on history

### Phase 4: Advanced Features (Future)

- [ ] Web interface for inventory management
- [ ] Calendar integration for scheduled orders
- [ ] Multi-household support
- [ ] Mobile app (Flutter)
- [ ] Advanced analytics dashboard
- [ ] Machine learning for habit prediction

---

## Challenges & Considerations

### Technical Challenges

- Thuisbezorgd may not have public API (scraping required)
- WhatsApp Business API requires business verification
- Voice recognition accuracy in multilingual households
- Real-time inventory tracking without IoT devices

### User Experience Challenges

- Balancing automation vs. control
- Handling conflicting preferences
- Privacy concerns with consumption tracking
- Ensuring fair cost splitting

### Scalability

- Multiple households using same system
- Handling peak times (everyone orders Sunday morning)
- Data storage growth over time
- API rate limits

---

## Success Metrics

- **Time Saved:** Reduce time spent on grocery management by 80%
- **Waste Reduction:** Decrease food waste by 30% through better tracking
- **Cost Fairness:** 100% accurate expense splitting
- **User Satisfaction:** >90% of orders placed without issues
- **Automation Rate:** 70% of orders triggered automatically

---

## Next Steps (Sprint Execution)

### Immediate Actions (Start Now)

1. **Set up MongoDB** - Install and configure MongoDB locally
2. **Design database schema** - Finalize Inventory and Order models
3. **Create project structure** - Set up modular architecture:
   - `inventory/` - MongoDB inventory module
   - `splitwise/` - Modular Splitwise integration
   - `ordering/` - Thuisbezorgd integration
   - `agent/` - Core agent logic
   - `cli/` - Text interface
4. **Research Thuisbezorgd API** - Check for official API or plan scraping approach
5. **Get Splitwise API credentials** - Register app and get OAuth tokens
6. **Set up LLM integration** - Configure OpenAI API for text processing

### Development Order

1. MongoDB + Inventory CRUD (Day 1 Morning)
2. Splitwise module (Day 1 Afternoon)
3. Thuisbezorgd integration (Day 2 Morning)
4. Agent orchestration + CLI (Day 2 Afternoon)

---

## Questions for Team Discussion

1. Which flatmates will be initial testers?
2. What's the budget for API costs (OpenAI, WhatsApp Business)?
3. Should we support multiple languages (NL/EN)?
4. Desktop app, web app, or mobile-first?
5. Privacy: how much consumption data should be tracked?
6. Backup plan if Thuisbezorgd integration fails?

---

## Resources & References

- [Splitwise API Documentation](https://dev.splitwise.com/)
- [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp)
- [Whisper API (OpenAI)](https://platform.openai.com/docs/guides/speech-to-text)
- [Thuisbezorgd/Takeaway.com](https://www.thuisbezorgd.nl/) - Research API availability
