# GitHub Issues for Grocery Management Agent

## Setup & Infrastructure

### Issue #1: Project Structure Setup
**Priority:** High  
**Labels:** `setup`, `infrastructure`  
**Assignee:** TBD  
**Milestone:** Day 1 Morning

**Description:**
Set up the project structure with modular architecture for the grocery management agent.

**Tasks:**
- [ ] Initialize project repository (Python/Node.js)
- [ ] Create directory structure:
  - `inventory/` - MongoDB inventory module
  - `splitwise/` - Modular Splitwise integration
  - `ordering/` - Thuisbezorgd integration
  - `agent/` - Core agent logic
  - `cli/` - Text interface
- [ ] Set up virtual environment and dependency management
- [ ] Create `.env.example` for configuration
- [ ] Add `.gitignore` file

**Acceptance Criteria:**
- Project structure is created and organized
- Dependencies can be installed
- Environment variables are documented

---

### Issue #2: MongoDB Setup and Schema Design
**Priority:** High  
**Labels:** `database`, `mongodb`, `setup`  
**Assignee:** TBD  
**Milestone:** Day 1 Morning

**Description:**
Set up MongoDB database and design schema for inventory and orders.

**Tasks:**
- [ ] Install and configure MongoDB locally
- [ ] Design Inventory collection schema:
  - id, name, category, quantity, unit, threshold, expiration_date, last_updated, shared
- [ ] Design Order collection schema:
  - id, timestamp, service, items[], total, delivery_time, status, splitwise_expense_id
- [ ] Create database connection module
- [ ] Write schema documentation

**Acceptance Criteria:**
- MongoDB is running locally
- Schema is documented in code
- Connection can be established
- Test data can be inserted

---

## Inventory Module

### Issue #3: Inventory CRUD Operations
**Priority:** High  
**Labels:** `inventory`, `mongodb`, `backend`  
**Assignee:** TBD  
**Milestone:** Day 1 Morning

**Description:**
Implement complete CRUD operations for inventory items in MongoDB.

**Tasks:**
- [ ] Create `inventory/` module structure
- [ ] Implement `create_item()` function
- [ ] Implement `get_item(id)` function
- [ ] Implement `get_all_items()` function
- [ ] Implement `update_item(id, data)` function
- [ ] Implement `delete_item(id)` function
- [ ] Implement `update_quantity(id, delta)` for adding/removing items
- [ ] Add input validation
- [ ] Write unit tests for each operation

**Acceptance Criteria:**
- All CRUD operations work correctly
- Items can be created, read, updated, and deleted
- Quantity updates work (add/subtract)
- Error handling for invalid inputs

---

### Issue #4: Inventory Query Functions
**Priority:** Medium  
**Labels:** `inventory`, `mongodb`, `backend`  
**Assignee:** TBD  
**Milestone:** Day 1 Morning

**Description:**
Implement query functions for inventory (low stock, expiring items, by category).

**Tasks:**
- [ ] Implement `get_low_stock_items()` - items below threshold
- [ ] Implement `get_expiring_items(days)` - items expiring soon
- [ ] Implement `get_items_by_category(category)`
- [ ] Implement `search_items(query)` - search by name
- [ ] Add helper function to format inventory for display

**Acceptance Criteria:**
- All query functions return correct results
- Low stock detection works
- Expiration date filtering works
- Search functionality is responsive

---

## Splitwise Integration

### Issue #5: Splitwise Module Structure
**Priority:** High  
**Labels:** `splitwise`, `integration`, `modular`  
**Assignee:** TBD  
**Milestone:** Day 1 Afternoon

**Description:**
Create modular Splitwise integration with clear interface and configuration.

**Tasks:**
- [ ] Create `splitwise/` module directory
- [ ] Set up Splitwise API client
- [ ] Create configuration module for API keys and group ID
- [ ] Design module interface (functions to expose)
- [ ] Add error handling structure
- [ ] Write module documentation

**Acceptance Criteria:**
- Module structure is clear and modular
- Configuration is externalized (env variables)
- Interface is well-defined
- Can authenticate with Splitwise API

---

### Issue #6: Splitwise Expense Creation
**Priority:** High  
**Labels:** `splitwise`, `integration`, `backend`  
**Assignee:** TBD  
**Milestone:** Day 1 Afternoon

**Description:**
Implement function to create expenses in Splitwise with equal split.

**Tasks:**
- [ ] Implement `create_expense(description, amount, group_id, users)` function
- [ ] Implement equal split logic (divide amount by number of users)
- [ ] Handle Splitwise API authentication
- [ ] Add error handling for API failures
- [ ] Return expense ID for tracking
- [ ] Write unit tests

**Acceptance Criteria:**
- Can create expenses in Splitwise
- Equal split works correctly
- Expense ID is returned and stored
- Errors are handled gracefully

---

### Issue #7: Splitwise Expense Retrieval and Updates
**Priority:** Medium  
**Labels:** `splitwise`, `integration`, `backend`  
**Assignee:** TBD  
**Milestone:** Day 1 Afternoon

**Description:**
Implement functions to retrieve and update Splitwise expenses.

**Tasks:**
- [ ] Implement `get_expense(expense_id)` function
- [ ] Implement `update_expense(expense_id, data)` function
- [ ] Add expense status checking
- [ ] Handle API rate limits
- [ ] Write unit tests

**Acceptance Criteria:**
- Can retrieve expense details
- Can update existing expenses
- Rate limiting is handled
- All functions have error handling

---

### Issue #8: Connect Inventory to Splitwise
**Priority:** High  
**Labels:** `integration`, `splitwise`, `inventory`  
**Assignee:** TBD  
**Milestone:** Day 1 Afternoon

**Description:**
Connect inventory updates to automatic Splitwise expense creation when orders are placed.

**Tasks:**
- [ ] Create integration function that triggers on order completion
- [ ] Map order items to Splitwise expense description
- [ ] Calculate total order amount
- [ ] Get list of flatmates from configuration
- [ ] Call Splitwise `create_expense()` with order details
- [ ] Store Splitwise expense ID in Order document
- [ ] Add error handling if Splitwise fails

**Acceptance Criteria:**
- When order is placed, Splitwise expense is created automatically
- Expense ID is stored in order document
- If Splitwise fails, order still completes (graceful degradation)

---

## Ordering Module

### Issue #9: Research Thuisbezorgd Integration
**Priority:** High  
**Labels:** `research`, `ordering`, `thuisbezorgd`  
**Assignee:** TBD  
**Milestone:** Day 2 Morning

**Description:**
Research and determine the best approach for Thuisbezorgd integration.

**Tasks:**
- [ ] Check if Thuisbezorgd has official API
- [ ] If no API, research web scraping approach
- [ ] Identify required endpoints/actions:
  - Search products
  - Add to cart
  - Place order
  - Check delivery status
- [ ] Document findings and approach
- [ ] Create proof-of-concept if API exists

**Acceptance Criteria:**
- Clear understanding of integration approach
- Documentation of API endpoints or scraping strategy
- Proof-of-concept works (at least authentication/search)

---

### Issue #10: Thuisbezorgd Order Placement
**Priority:** High  
**Labels:** `ordering`, `thuisbezorgd`, `backend`  
**Assignee:** TBD  
**Milestone:** Day 2 Morning

**Description:**
Implement order placement functionality through Thuisbezorgd.

**Tasks:**
- [ ] Create `ordering/` module directory
- [ ] Implement product search function
- [ ] Implement add to cart functionality
- [ ] Implement order placement function
- [ ] Handle authentication/session management
- [ ] Add error handling for failed orders
- [ ] Return order confirmation and tracking info

**Acceptance Criteria:**
- Can search for products
- Can add items to cart
- Can place order successfully
- Order confirmation is returned
- Errors are handled gracefully

---

### Issue #11: Order Status Tracking
**Priority:** Medium  
**Labels:** `ordering`, `thuisbezorgd`, `backend`  
**Assignee:** TBD  
**Milestone:** Day 2 Morning

**Description:**
Implement order status checking and delivery tracking.

**Tasks:**
- [ ] Implement `get_order_status(order_id)` function
- [ ] Implement polling mechanism for delivery status
- [ ] Update order status in MongoDB when delivery completes
- [ ] Handle different order states (pending, confirmed, preparing, delivering, delivered)
- [ ] Add timeout handling

**Acceptance Criteria:**
- Can check order status
- Order status updates in database
- Delivery completion is detected
- Timeout handling works

---

### Issue #12: Connect Ordering to Inventory Updates
**Priority:** High  
**Labels:** `integration`, `ordering`, `inventory`  
**Assignee:** TBD  
**Milestone:** Day 2 Morning

**Description:**
Automatically update inventory when orders are delivered.

**Tasks:**
- [ ] Create integration function that triggers on delivery completion
- [ ] Parse order items and quantities
- [ ] Update inventory for each item (add quantities)
- [ ] Handle new items (create inventory entries)
- [ ] Update order status in database
- [ ] Add error handling

**Acceptance Criteria:**
- When order is delivered, inventory is updated automatically
- New items are added to inventory
- Existing items have quantities increased
- Errors don't break the flow

---

## Agent Core

### Issue #13: LLM Integration for Text Processing
**Priority:** High  
**Labels:** `agent`, `llm`, `nlp`  
**Assignee:** TBD  
**Milestone:** Day 1 Morning

**Description:**
Set up LLM integration (OpenAI API) for processing natural language commands.

**Tasks:**
- [ ] Set up OpenAI API client
- [ ] Create prompt templates for different command types
- [ ] Implement text command parser
- [ ] Map commands to actions:
  - "Order X" → order action
  - "Add X to inventory" → inventory update
  - "What's in inventory?" → inventory query
- [ ] Add error handling for API failures
- [ ] Configure API key management

**Acceptance Criteria:**
- Can process natural language commands
- Commands are correctly mapped to actions
- API errors are handled
- Response format is consistent

---

### Issue #14: Agent Orchestration Logic
**Priority:** High  
**Labels:** `agent`, `core`, `orchestration`  
**Assignee:** TBD  
**Milestone:** Day 2 Afternoon

**Description:**
Create the core agent logic that orchestrates all modules together.

**Tasks:**
- [ ] Create `agent/` module with main orchestration logic
- [ ] Implement command routing (inventory, order, query)
- [ ] Implement order flow: parse → order → track → update inventory → Splitwise
- [ ] Implement inventory flow: parse → update → confirm
- [ ] Implement query flow: parse → query → format response
- [ ] Add logging for all actions
- [ ] Handle errors at each step

**Acceptance Criteria:**
- Agent can process "Order 2 liters of milk" end-to-end
- All modules are connected correctly
- Errors are handled gracefully
- Actions are logged

---

## CLI Interface

### Issue #15: Basic CLI Interface
**Priority:** High  
**Labels:** `cli`, `frontend`, `interface`  
**Assignee:** TBD  
**Milestone:** Day 1 Morning

**Description:**
Create a basic command-line interface for interacting with the agent.

**Tasks:**
- [ ] Create `cli/` module
- [ ] Implement main CLI loop (read input, process, display output)
- [ ] Add command parsing
- [ ] Format agent responses for display
- [ ] Add help command (`--help` or `help`)
- [ ] Add exit command
- [ ] Make it user-friendly with prompts

**Acceptance Criteria:**
- CLI starts and accepts input
- Commands are sent to agent
- Responses are displayed clearly
- Help command works
- Can exit cleanly

---

### Issue #16: CLI Command Help and Examples
**Priority:** Low  
**Labels:** `cli`, `documentation`, `ux`  
**Assignee:** TBD  
**Milestone:** Day 2 Afternoon

**Description:**
Add comprehensive help system and command examples to CLI.

**Tasks:**
- [ ] Add detailed help text for each command type
- [ ] Add example commands
- [ ] Add command suggestions for typos
- [ ] Format help nicely
- [ ] Add version info

**Acceptance Criteria:**
- Help command shows all available commands
- Examples are clear and helpful
- User can understand how to use the system

---

## Testing & Quality

### Issue #17: End-to-End Testing
**Priority:** High  
**Labels:** `testing`, `e2e`, `quality`  
**Assignee:** TBD  
**Milestone:** Day 2 Afternoon

**Description:**
Create end-to-end tests for the complete order flow.

**Tasks:**
- [ ] Test complete flow: "Order 2 liters of milk"
  - Command parsing
  - Order placement
  - Delivery tracking
  - Inventory update
  - Splitwise expense creation
- [ ] Test inventory update flow
- [ ] Test query flow
- [ ] Test error scenarios
- [ ] Document test results

**Acceptance Criteria:**
- Complete order flow works end-to-end
- All integration points are tested
- Error scenarios are handled
- Test results are documented

---

### Issue #18: Error Handling and Edge Cases
**Priority:** High  
**Labels:** `error-handling`, `quality`, `robustness`  
**Assignee:** TBD  
**Milestone:** Day 2 Afternoon

**Description:**
Implement comprehensive error handling and handle edge cases.

**Tasks:**
- [ ] Add error handling for MongoDB connection failures
- [ ] Add error handling for Splitwise API failures
- [ ] Add error handling for Thuisbezorgd failures
- [ ] Handle invalid commands gracefully
- [ ] Handle missing inventory items
- [ ] Handle network timeouts
- [ ] Add retry logic for transient failures
- [ ] Add user-friendly error messages

**Acceptance Criteria:**
- All error scenarios are handled
- User sees helpful error messages
- System doesn't crash on errors
- Retry logic works for transient failures

---

## Documentation

### Issue #19: API Documentation
**Priority:** Medium  
**Labels:** `documentation`, `api`  
**Assignee:** TBD  
**Milestone:** Day 2 Afternoon

**Description:**
Document all module interfaces and functions.

**Tasks:**
- [ ] Document inventory module API
- [ ] Document Splitwise module API
- [ ] Document ordering module API
- [ ] Document agent module API
- [ ] Add code comments/docstrings
- [ ] Create API reference document

**Acceptance Criteria:**
- All modules have clear documentation
- Functions have docstrings
- API reference is complete

---

### Issue #20: Setup and Configuration Guide
**Priority:** Medium  
**Labels:** `documentation`, `setup`  
**Assignee:** TBD  
**Milestone:** Day 2 Afternoon

**Description:**
Create comprehensive setup and configuration guide.

**Tasks:**
- [ ] Document MongoDB setup
- [ ] Document Splitwise API setup (OAuth, tokens)
- [ ] Document Thuisbezorgd setup
- [ ] Document environment variables
- [ ] Document installation steps
- [ ] Add troubleshooting section
- [ ] Create README with quick start

**Acceptance Criteria:**
- New developer can set up project from scratch
- All configuration is documented
- Troubleshooting guide is helpful

---

## Optional Enhancements

### Issue #21: WhatsApp Integration (Maybe)
**Priority:** Low  
**Labels:** `enhancement`, `whatsapp`, `optional`  
**Assignee:** TBD  
**Milestone:** Future

**Description:**
Add WhatsApp notifications for order confirmations and delivery updates.

**Tasks:**
- [ ] Research WhatsApp integration options
- [ ] Set up WhatsApp Business API or whatsapp-web.js
- [ ] Implement notification sending
- [ ] Add to order flow (notify on order placed, delivery)
- [ ] Add configuration for group chat ID

**Acceptance Criteria:**
- Can send WhatsApp messages
- Notifications are sent at appropriate times
- Configuration is easy

---

### Issue #22: Low Stock Alerts
**Priority:** Low  
**Labels:** `enhancement`, `inventory`, `optional`  
**Assignee:** TBD  
**Milestone:** Future

**Description:**
Implement automatic low stock detection and alerts.

**Tasks:**
- [ ] Create function to check all items for low stock
- [ ] Implement alert system (console/WhatsApp)
- [ ] Add scheduled check (cron job or scheduler)
- [ ] Format alert messages nicely

**Acceptance Criteria:**
- Low stock items are detected
- Alerts are sent when items are low
- Scheduled checks work

---

## Kanban Board Columns

Suggested columns:
- **Backlog** - All issues
- **To Do** - Ready to start
- **In Progress** - Currently working
- **Review/Test** - Needs testing or review
- **Done** - Completed

## Priority Order for Sprint

1. #1 - Project Structure Setup
2. #2 - MongoDB Setup and Schema Design
3. #3 - Inventory CRUD Operations
4. #13 - LLM Integration for Text Processing
5. #15 - Basic CLI Interface
6. #5 - Splitwise Module Structure
7. #6 - Splitwise Expense Creation
8. #8 - Connect Inventory to Splitwise
9. #9 - Research Thuisbezorgd Integration
10. #10 - Thuisbezorgd Order Placement
11. #12 - Connect Ordering to Inventory Updates
12. #14 - Agent Orchestration Logic
13. #17 - End-to-End Testing
14. #18 - Error Handling and Edge Cases

