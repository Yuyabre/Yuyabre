# Ordering System - Step-by-Step Flow Explanation

## Complete Flow: From User Request to Order Creation

This document explains exactly what happens at each step when a user places an order.

---

## Scenario: User says "Order 2 liters of milk"

### STEP 1: User Input
**What happens:**
- User types or says: `"Order 2 liters of milk"`
- Frontend sends this to the backend API

**Input:**
```json
{
  "command": "Order 2 liters of milk",
  "user_id": "user123"
}
```

**What the system receives:**
- Natural language command
- User ID for identification

---

### STEP 2: Agent Processing (LLM)
**What happens:**
- `GroceryAgent.process_command()` receives the command
- LLM (OpenAI) analyzes the intent
- LLM decides to call the `place_order` tool

**Agent's decision:**
```
User wants to: ORDER
Items: milk (2 liters)
Action: Call place_order tool
```

**What the system does:**
- Parses natural language into structured intent
- Identifies items and quantities
- Selects appropriate tool to use

---

### STEP 3: Tool Handler - Parse Items
**What happens:**
- `ToolHandlers.place_order()` is called
- Extracts items from the command

**Input to tool handler:**
```json
{
  "items": [
    {
      "name": "milk",
      "quantity": 2.0,
      "unit": "liters"
    }
  ],
  "user_id": "user123"
}
```

**What the system does:**
- Extracts item name: "milk"
- Extracts quantity: 2.0
- Extracts unit: "liters"

---

### STEP 4: Product Search in Menu
**What happens:**
- For each item, calls `OrderingService.search_products("milk")`
- MenuLoader searches `restaurant1_menu.json`

**Detailed process:**

#### 4a. Load Menu File
```python
# MenuLoader.load_all_menus()
# Reads: backend/data/restaurant1_menu.json
# Loads: 558 menu items
```

**What the system does:**
- Opens `restaurant1_menu.json`
- Parses JSON file
- Caches menu data for performance

#### 4b. Search Menu Items
```python
# MenuLoader.search_all_menus("milk")
# Searches through all 558 items
```

**Search algorithm:**
1. Converts query to lowercase: `"milk"` → `"milk"`
2. Loops through all menu items
3. Checks if query matches:
   - Exact match: `item_name == "milk"`
   - Partial match: `"milk" in item_name`
   - Brand match: `item_brand == "milk"`
4. Filters out unavailable items

**What the system finds:**
- 22 products containing "milk"
- Examples:
  - "Whiskas Catmilk 200ml" - €1.59
  - "Melkan Semi-skimmed milk 1L" - €1.39
  - "Campina Semi-Skimmed Milk Can 2.4L" - €1.45

#### 4c. Format Results
**What the system does:**
- Formats each match with:
  - `product_id` (from menu)
  - `name` (from menu)
  - `price` (from menu)
  - `unit` (default: "piece")
  - `available` (from menu)
  - `brand` (from menu)
  - `restaurant_name` (from menu)
  - `image_url` (from menu)

**Output:**
```json
[
  {
    "product_id": "7eaf59a3c907582bbd39fb2ac8d870c8",
    "name": "Whiskas Catmilk 200ml",
    "price": 1.59,
    "unit": "piece",
    "available": true,
    "brand": "Whiskas",
    "restaurant_name": "Flink Amsterdam Buitenveldert"
  },
  ... (21 more products)
]
```

---

### STEP 5: Product Selection
**What happens:**
- Tool handler receives search results
- Selects first product (or LLM could select cheapest)

**Current behavior:**
```python
products = await ordering_service.search_products("milk")
product = products[0]  # Takes first result
```

**Selected product:**
```json
{
  "product_id": "7eaf59a3c907582bbd39fb2ac8d870c8",
  "name": "Whiskas Catmilk 200ml",
  "price": 1.59,
  "quantity": 2.0,
  "unit": "piece"
}
```

**What the system does:**
- Takes first search result
- Uses it for order creation
- (Future: LLM could select cheapest option)

---

### STEP 6: Check for Existing Order (Batching)
**What happens:**
- Before creating new order, checks for existing pending order
- `OrderingService.get_pending_order(user_id, within_minutes=5)`

**Query MongoDB:**
```python
# Finds orders where:
# - created_by == user_id
# - status == PENDING or CONFIRMED
# - is_group_order == False
# - timestamp >= (now - 5 minutes)
```

**What the system does:**
- Queries database for recent orders
- Checks if order exists within 5 minutes
- If found: will add items to existing order
- If not found: will create new order

**Result in this case:**
- No existing order found
- Proceeds to create new order

---

### STEP 7: Create Order Object
**What happens:**
- `OrderingService.create_order()` is called
- Creates new `Order` object

**Input:**
```json
{
  "items": [
    {
      "product_id": "7eaf59a3c907582bbd39fb2ac8d870c8",
      "name": "Whiskas Catmilk 200ml",
      "quantity": 2.0,
      "unit": "piece",
      "price": 1.59,
      "requested_by": ["user123"]
    }
  ],
  "delivery_address": "123 Test Street",
  "created_by": "user123"
}
```

**What the system does:**

#### 7a. Check for Shared Items
- Checks if items are marked as "shared" in inventory
- Determines if this should be a group order
- In this case: not shared → regular order

#### 7b. Get Delivery Fee from Menu
```python
# Loads menu to get delivery cost
menu_data = await menu_loader.load_menu("restaurant1")
delivery_cost_str = menu_data['restaurant']['delivery_cost']  # "€ 4,49"
delivery_fee = parse_price(delivery_cost_str)  # 4.49
```

**What the system does:**
- Loads menu file
- Extracts `delivery_cost`: "€ 4,49"
- Parses to float: 4.49
- Sets order delivery fee

#### 7c. Create Order Object
```python
order = Order(
    order_id="29586c67-4566-42d2-92e3-62ca49b4c7dc",  # Generated UUID
    timestamp=datetime.utcnow(),
    status=OrderStatus.PENDING,
    items=[OrderItem(...)],
    delivery_address="123 Test Street",
    created_by="user123",
    delivery_fee=4.49
)
```

**What the system does:**
- Generates unique order ID
- Sets timestamp to now
- Creates OrderItem objects
- Calculates subtotal: €3.18 (2 × €1.59)
- Sets delivery fee: €4.49 (from menu)
- Calculates total: €7.67

#### 7d. Save to MongoDB
```python
await order.insert()  # Saves to MongoDB collection "orders"
```

**What the system does:**
- Connects to MongoDB
- Inserts order document
- Stores all order data:
  - Order ID
  - Items
  - Prices
  - Status
  - Timestamp
  - User ID

---

### STEP 8: Return Response
**What happens:**
- Order creation completes
- Returns order details to tool handler
- Tool handler returns to agent
- Agent formats response for user

**Output from create_order():**
```json
{
  "order_id": "29586c67-4566-42d2-92e3-62ca49b4c7dc",
  "status": "confirmed",
  "items": [
    {
      "name": "Whiskas Catmilk 200ml",
      "quantity": 2.0,
      "price": 1.59,
      "total_price": 3.18
    }
  ],
  "total": 7.67
}
```

**Agent's response to user:**
```
"I've created your order for 2x Whiskas Catmilk 200ml. 
Total: €7.67 (including €4.49 delivery fee). 
Order ID: 29586c67-4566-42d2-92e3-62ca49b4c7dc"
```

---

## Scenario: User says "Order bread" (5 minutes later)

### STEP 1-4: Same as above
- User input: "Order bread"
- Agent processes
- Tool handler extracts: bread, 1 piece
- Searches menu: finds 2 bread products

### STEP 5: Product Selection
**Selected product:**
```json
{
  "product_id": "0201629e15496e8ffad56f7a6f04b249",
  "name": "The City Bakery Fruit Bread Half Sliced 440g",
  "price": 3.29
}
```

### STEP 6: Check for Existing Order (Batching)
**What happens:**
- Checks for existing order within 5 minutes
- **Finds existing order!** (from milk order)

**Query result:**
```python
pending_order = {
    "order_id": "29586c67-4566-42d2-92e3-62ca49b4c7dc",
    "status": "CONFIRMED",
    "timestamp": "2025-11-09 09:53:22",  # 2 minutes ago
    "items": [milk_item]
}
```

**What the system does:**
- Finds existing order
- Checks it's within 5 minutes: ✅ Yes
- Checks it's not a group order: ✅ Yes
- Decides to add to existing order

### STEP 7: Add Items to Existing Order
**What happens:**
- Calls `OrderingService.add_items_to_order()`
- Instead of creating new order

**Process:**

#### 7a. Load Existing Order
```python
order = await Order.find_one(Order.order_id == order_id)
```

#### 7b. Change Status if Needed
```python
if order.status == OrderStatus.CONFIRMED:
    order.status = OrderStatus.PENDING  # Allow modification
```

#### 7c. Add New Items
```python
new_item = OrderItem(
    product_id="0201629e15496e8ffad56f7a6f04b249",
    name="The City Bakery Fruit Bread Half Sliced 440g",
    quantity=1.0,
    price=3.29,
    total_price=3.29
)
order.add_item(new_item)
```

#### 7d. Recalculate Totals
```python
order.subtotal = 3.18 + 3.29 = 6.47
order.total = 6.47 + 4.49 = 10.96
```

#### 7e. Save Updated Order
```python
await order.save()  # Updates existing document in MongoDB
```

**What the system does:**
- Loads existing order from database
- Adds bread item to order
- Recalculates totals
- Updates order in MongoDB
- Returns updated order

**Result:**
- Same order ID
- Now contains: milk + bread
- Total: €10.96

### STEP 8: Return Response
**Agent's response:**
```
"I've added The City Bakery Fruit Bread Half Sliced 440g to your existing order.
Your order now contains:
- 2x Whiskas Catmilk 200ml
- 1x The City Bakery Fruit Bread Half Sliced 440g
Total: €10.96"
```

---

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: User Input                                         │
│ "Order 2 liters of milk"                                   │
└────────────────────┬──────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Agent Processing (LLM)                             │
│ - Parses intent                                             │
│ - Decides to call place_order tool                          │
└────────────────────┬──────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Tool Handler                                        │
│ - Extracts: milk, 2.0, liters                               │
└────────────────────┬──────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Product Search                                      │
│ - Loads restaurant1_menu.json (558 items)                   │
│ - Searches for "milk"                                       │
│ - Finds 22 matches                                          │
└────────────────────┬──────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Product Selection                                  │
│ - Selects first result: "Whiskas Catmilk 200ml"            │
└────────────────────┬──────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 6: Check for Existing Order                           │
│ - Queries MongoDB for orders within 5 minutes              │
│ - Result: None found → Create new order                     │
└────────────────────┬──────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 7: Create Order                                        │
│ - Gets delivery fee from menu: €4.49                        │
│ - Creates Order object                                      │
│ - Calculates: €3.18 + €4.49 = €7.67                        │
│ - Saves to MongoDB                                          │
└────────────────────┬──────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 8: Return Response                                     │
│ - Returns order details to agent                            │
│ - Agent formats user-friendly message                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Components and Their Roles

### 1. MenuLoader
**What it does:**
- Loads `restaurant1_menu.json`
- Searches products by name
- Returns formatted product data
- Parses prices from strings

**Files:**
- `modules/ordering/menu_loader.py`
- `backend/data/restaurant1_menu.json`

### 2. OrderingService
**What it does:**
- Searches products (uses MenuLoader)
- Creates orders
- Checks for existing orders (batching)
- Adds items to existing orders
- Gets delivery fees from menu

**Files:**
- `modules/ordering/service.py`

### 3. Tool Handlers
**What it does:**
- Receives LLM tool calls
- Calls OrderingService methods
- Formats data for orders
- Returns results to agent

**Files:**
- `agent/tool_handlers.py`

### 4. Agent (LLM)
**What it does:**
- Processes natural language
- Decides which tools to call
- Formats user-friendly responses

**Files:**
- `agent/core.py`
- `agent/conversation.py`

### 5. MongoDB
**What it does:**
- Stores orders
- Stores order history
- Enables order batching queries

**Database:**
- `grocery_agent.orders` collection

---

## Data Flow

### Product Search Flow
```
User: "milk"
  ↓
search_products("milk")
  ↓
MenuLoader.search_all_menus("milk")
  ↓
Load restaurant1_menu.json
  ↓
Search 558 items
  ↓
Find 22 matches
  ↓
Format results
  ↓
Return: [22 products]
```

### Order Creation Flow
```
Items: [milk]
  ↓
Check for existing order (within 5 min)
  ↓
None found → Create new
  ↓
Get delivery fee from menu (€4.49)
  ↓
Create Order object
  ↓
Calculate totals
  ↓
Save to MongoDB
  ↓
Return order
```

### Order Batching Flow
```
Items: [bread]
  ↓
Check for existing order (within 5 min)
  ↓
Found existing order!
  ↓
Load order from MongoDB
  ↓
Add bread item
  ↓
Recalculate totals
  ↓
Update in MongoDB
  ↓
Return updated order
```

---

## Important Details

### Menu File Location
- **Path**: `backend/data/restaurant1_menu.json`
- **Size**: 558 products
- **Restaurant**: Flink Amsterdam Buitenveldert
- **Delivery Cost**: €4.49

### Order Batching Rules
- **Time window**: 5 minutes
- **User**: Same user only
- **Type**: Non-group orders only
- **Status**: PENDING or CONFIRMED

### Price Calculation
```
Subtotal = sum(item.price × item.quantity)
Delivery Fee = from menu (€4.49)
Total = Subtotal + Delivery Fee
```

### Database Storage
- **Collection**: `orders`
- **Fields**: order_id, items, status, total, timestamp, etc.
- **Indexes**: order_id, timestamp, status, user_id

---

## Summary

**When user says "Order milk":**
1. ✅ Agent parses command
2. ✅ Searches menu for "milk" → finds 22 products
3. ✅ Selects first product
4. ✅ Checks for existing order → none found
5. ✅ Creates new order
6. ✅ Gets delivery fee from menu (€4.49)
7. ✅ Saves to MongoDB
8. ✅ Returns confirmation

**When user says "Order bread" (within 5 min):**
1. ✅ Agent parses command
2. ✅ Searches menu for "bread" → finds 2 products
3. ✅ Selects first product
4. ✅ Checks for existing order → **found!**
5. ✅ Adds bread to existing order
6. ✅ Recalculates totals
7. ✅ Updates MongoDB
8. ✅ Returns updated order confirmation

**Result**: One order with both items! 🎉

