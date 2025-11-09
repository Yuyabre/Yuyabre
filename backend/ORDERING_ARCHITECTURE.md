# Ordering System Architecture

## 📋 Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Component Design](#component-design)
4. [Data Models](#data-models)
5. [Data Flow](#data-flow)
6. [Key Features](#key-features)
7. [Integration Points](#integration-points)
8. [API Design](#api-design)
9. [Error Handling](#error-handling)
10. [Future Enhancements](#future-enhancements)

---

## Overview

The Ordering System is a comprehensive solution for managing grocery orders through delivery services. It integrates with restaurant menus, supports group orders, selective sharing, automatic batching, and prepares for Splitwise expense creation upon delivery.

### Key Capabilities

- ✅ **Product Search**: Search across restaurant menus from JSON files
- ✅ **Order Creation**: Create orders with automatic batching
- ✅ **Selective Sharing**: Per-item sharing with specific users
- ✅ **Group Orders**: Automatic group orders with WhatsApp integration
- ✅ **Status Management**: Track order status through lifecycle
- ✅ **Missing Product Handling**: Graceful degradation for unavailable items

---

## System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Layer                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │   CLI    │  │   API    │  │ WhatsApp │  │ Frontend │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
└───────┼─────────────┼─────────────┼─────────────┼──────────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Agent Layer (LLM)                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              GroceryAgent                                │   │
│  │  - Natural language processing                           │   │
│  │  - Intent parsing                                        │   │
│  │  - Tool orchestration                                    │   │
│  └───────────────────────┬────────────────────────────────┘   │
└───────────────────────────┼────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Tool Handler Layer                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              ToolHandlers.place_order()                   │   │
│  │  - Validates items                                       │   │
│  │  - Searches products                                     │   │
│  │  - Handles missing products                              │   │
│  │  - Calls OrderingService                                 │   │
│  └───────────────────────┬────────────────────────────────┘   │
└───────────────────────────┼────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Service Layer                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              OrderingService                              │   │
│  │  - Product search                                        │   │
│  │  - Order creation & batching                             │   │
│  │  - Group order management                                │   │
│  │  - Status management                                     │   │
│  └───────────────────────┬────────────────────────────────┘   │
│                          │                                      │
│        ┌─────────────────┴─────────────────┐                  │
│        ▼                                   ▼                   │
│  ┌──────────────┐                  ┌──────────────┐           │
│  │ MenuLoader   │                  │ WhatsApp     │           │
│  │ - Load menus │                  │ Service      │           │
│  │ - Search     │                  │ - Notify     │           │
│  └──────────────┘                  └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   MongoDB    │  │  JSON Menu   │  │  Inventory   │         │
│  │  - Orders    │  │  Files       │  │  Service     │         │
│  │  - History   │  │  - restaurant1│  │  - Shared    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
User Request
    │
    ▼
Agent (LLM) ──→ Parse Intent ──→ Call place_order tool
    │
    ▼
Tool Handler ──→ Validate Items ──→ Search Products ──→ Create Order
    │                │                    │                │
    │                │                    │                │
    │                ▼                    ▼                ▼
    │         Missing? Skip      MenuLoader      OrderingService
    │         Add to warnings    Search menus    Create/Update order
    │                │                    │                │
    │                │                    │                │
    └────────────────┴────────────────────┴────────────────┘
                                    │
                                    ▼
                            Check for Batching
                                    │
                                    ▼
                            Group Order? ──→ Yes ──→ WhatsApp Notification
                                    │
                                    No
                                    │
                                    ▼
                            Save to MongoDB
                                    │
                                    ▼
                            Return Response
```

---

## Component Design

### 1. OrderingService

**Location**: `modules/ordering/service.py` (925 lines)

**Responsibility**: Core business logic for all ordering operations.

**Key Methods**:

#### Product Operations
```python
async def search_products(query: str) -> List[Dict]
async def get_product_details(product_id: str) -> Optional[Dict]
```
- Searches across all restaurant menus
- Returns formatted product results
- Handles search failures gracefully

#### Order Operations
```python
async def create_order(
    items: List[Dict],
    delivery_address: str,
    created_by: Optional[str] = None
) -> Optional[Order]

async def get_pending_order(
    user_id: str,
    within_minutes: int = 5
) -> Optional[Order]

async def add_items_to_order(
    order_id: str,
    items: List[Dict],
    created_by: str
) -> Optional[Order]
```
- Creates new orders or adds to existing (batching)
- Handles shared items and group orders
- Supports selective sharing via `shared_with` parameter

#### Group Order Management
```python
async def process_group_order_response(
    order_id: str,
    user_id: str,
    responses: Dict
) -> Optional[Order]

async def _finalize_group_order(order: Order) -> None
```
- Processes housemate responses
- Updates quantities and `shared_by` based on responses
- Finalizes order when all respond or deadline passes

#### Status Management
```python
async def get_order_status(order_id: str) -> Optional[OrderStatus]
async def update_order_status(
    order_id: str,
    new_status: OrderStatus
) -> Optional[Order]
async def cancel_order(order_id: str) -> bool
```

**Dependencies**:
- `MenuLoader`: For product search
- `WhatsAppService`: For group order notifications
- `UserInventoryService`: For inventory updates
- `MongoDB`: For order persistence

**Caching**: Uses LRU cache for performance optimization

---

### 2. MenuLoader

**Location**: `modules/ordering/menu_loader.py` (250 lines)

**Responsibility**: Loads and searches restaurant menus from JSON files.

**Key Methods**:

```python
async def load_menu(restaurant_id: str = "restaurant1") -> Optional[Dict]
async def load_all_menus() -> List[Dict]
async def search_all_menus(query: str) -> List[Dict]
async def get_product_by_id_all_menus(product_id: str) -> Optional[Dict]
```

**Features**:
- Loads JSON menu files from `backend/data/`
- Caches loaded menus for performance
- Supports multiple restaurants
- Flexible search (exact, partial, brand matching)

**Menu File Structure**:
```json
{
  "restaurant": {
    "name": "Flink Amsterdam Buitenveldert",
    "delivery_cost": "€ 4,49",
    "minimum_order_amount": "€ 31,00"
  },
  "menu_items": [
    {
      "product_id": "unique_id",
      "name": "Product Name",
      "price": 1.59,
      "available": true,
      "brand": "Brand Name",
      "image_url": "https://..."
    }
  ]
}
```

**Search Algorithm**:
1. Exact name match
2. Partial name match (query in name)
3. Brand match
4. Case-insensitive

---

### 3. Tool Handlers

**Location**: `agent/tool_handlers.py`

**Responsibility**: Bridge between LLM and OrderingService.

**Key Method**:

```python
async def place_order(
    items: List[Dict],
    delivery_address: Optional[str] = None,
    notes: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]
```

**Process**:
1. Validates items (name, quantity)
2. Searches for products in menu
3. Handles missing products (adds to warnings)
4. Calls `OrderingService.create_order()`
5. Updates inventory after order
6. Returns formatted response with warnings

**Selective Sharing Support**:
- Extracts `shared_with` from LLM tool calls
- Passes to OrderingService
- Handles missing products with `partial_warnings`

---

### 4. Agent Integration

**Location**: `agent/core.py`, `agent/tools.py`, `agent/context.py`

**Tool Schema** (`tools.py`):
```python
{
    "name": "place_order",
    "description": "Create a grocery order...",
    "parameters": {
        "items": [{
            "name": "string",
            "quantity": "number",
            "unit": "string",
            "shared_with": ["user_id1", "user_id2"]  # Optional
        }]
    }
}
```

**Context Enhancement** (`context.py`):
- Includes household member information in system prompt
- Provides user IDs for selective sharing
- Format: `"Household Members: Person A (ID: person_a), Person B (ID: person_b)"`

---

## Data Models

### OrderStatus Enum

```python
class OrderStatus(str, Enum):
    PENDING = "pending"              # Order created, awaiting confirmation
    CONFIRMED = "confirmed"           # Order confirmed, being prepared
    PROCESSING = "processing"         # Order being processed
    OUT_FOR_DELIVERY = "out_for_delivery"  # Order on the way
    DELIVERED = "delivered"           # Order delivered
    CANCELLED = "cancelled"          # Order cancelled
    FAILED = "failed"                # Order failed
```

### OrderItem Model

```python
class OrderItem(BaseModel):
    product_id: str                  # External product ID
    name: str                        # Product name
    quantity: float                  # Quantity ordered
    unit: str                        # Unit of measurement
    price: float                     # Price per unit
    total_price: float               # Total price (quantity × price)
    requested_by: List[str]          # User IDs who requested
    shared: bool                     # Whether item is shared
    shared_by: List[str]             # User IDs who share the cost
```

**Purpose**: Represents a single item within an order, with sharing information for cost splitting.

### Order Document

```python
class Order(Document):
    # Identity
    order_id: str                    # UUID
    timestamp: datetime              # Creation time
    service: str                     # "Thuisbezorgd"
    external_order_id: Optional[str] # External service order ID
    
    # Items & Pricing
    items: List[OrderItem]           # Ordered items
    subtotal: float                  # Sum of item prices
    delivery_fee: float              # Delivery fee from menu
    total: float                     # Total amount
    
    # Status & Delivery
    status: OrderStatus              # Current status
    delivery_time: Optional[datetime]  # Estimated/actual delivery
    delivery_address: Optional[str]  # Delivery address
    
    # User & Household
    created_by: Optional[str]        # User ID who created
    household_id: Optional[str]      # Household for group orders
    is_group_order: bool             # Whether group order
    
    # Group Order Management
    pending_responses: Dict[str, List[str]]  # item_name -> [user_ids]
    response_deadline: Optional[datetime]    # Deadline for responses
    group_responses: Dict[str, Dict]         # user_id -> response data
    whatsapp_message_sent: bool              # Whether WhatsApp sent
    
    # Integration
    splitwise_expense_ids: Dict[str, str]    # item_name -> expense_id
    notes: Optional[str]                     # Additional notes
```

**MongoDB Collection**: `orders`

**Indexes**:
- `order_id` (unique)
- `timestamp` (for batching queries)
- `status` (for filtering)
- `created_by` (for user orders)
- `household_id` (for group orders)
- `is_group_order` (for filtering)

---

## Data Flow

### Complete Order Creation Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: User Request                                        │
│ "Order milk shared with person b and person c"             │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Agent Processing (LLM)                              │
│ - Parses intent                                             │
│ - Identifies: order, items, sharing                         │
│ - Calls place_order tool                                    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Tool Handler                                        │
│ - Validates items                                           │
│ - Extracts shared_with: ["person_b", "person_c"]          │
│ - Searches products: search_products("milk")               │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 4: MenuLoader                                          │
│ - Loads restaurant1_menu.json                              │
│ - Searches 558 items for "milk"                            │
│ - Returns: [22 matches]                                    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 5: Product Selection                                   │
│ - Takes first result: "Whiskas Catmilk 200ml" (€1.59)     │
│ - Future: LLM selects cheapest/best                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 6: Order Batching Check                                │
│ - get_pending_order(user_id, within_minutes=5)             │
│ - No existing order found                                   │
│ - Proceed to create new                                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 7: Shared Item Detection                               │
│ - Check inventory: Is "Milk" shared?                       │
│ - Yes: is_item_shared = True                               │
│ - household_id found                                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 8: Selective Sharing Application                       │
│ - shared_with = ["person_b", "person_c"]                   │
│ - shared_by = [creator] + shared_with                       │
│ - shared_by = ["person_a", "person_b", "person_c"]         │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 9: Group Order Setup                                   │
│ - is_group_order = True                                     │
│ - pending_responses["Whiskas Catmilk"] = ["person_b", "person_c"]
│ - response_deadline = now + 2 hours                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 10: Delivery Fee Calculation                           │
│ - Load menu: delivery_cost = "€ 4,49"                      │
│ - Parse: delivery_fee = 4.49                                │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 11: Order Creation                                     │
│ - Create Order object                                       │
│ - Add OrderItem with shared_by                              │
│ - Calculate totals                                          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 12: WhatsApp Notification                              │
│ - notify_user_ids = ["person_b", "person_c"]               │
│ - Send message to person_b and person_c only                │
│ - Message: "New group order: Milk (2L)"                    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 13: MongoDB Persistence                                │
│ - Save Order to MongoDB                                     │
│ - Collection: orders                                        │
│ - Status: PENDING                                           │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 14: Response                                           │
│ - Return order details                                      │
│ - Include group_order info                                  │
│ - Agent informs user                                        │
└─────────────────────────────────────────────────────────────┘
```

### Order Batching Flow

```
Order 1: "Order milk" (10:00:00)
    │
    ▼
Create order_123 (PENDING)
    │
    │
Order 2: "Order eggs" (10:02:00) ──┐
    │                              │
    ▼                              │
get_pending_order() ───────────────┘
    │
    ▼
Found order_123 (within 5 min)
    │
    ▼
add_items_to_order(order_123, [eggs])
    │
    ▼
Update order_123: items = [milk, eggs]
    │
    │
Order 3: "Order bread" (10:06:00) ──┐
    │                              │
    ▼                              │
get_pending_order() ───────────────┘
    │
    ▼
No order found (6 min > 5 min)
    │
    ▼
Create new order_456 (PENDING)
```

### Group Order Finalization Flow

```
Group Order Created
    │
    ▼
WhatsApp sent to person_b, person_c
    │
    ├──────────────────┐
    │                  │
    ▼                  ▼
person_b responds    person_c responds
"Yes, +1L"          "No, skip"
    │                  │
    ├──────────────────┘
    │
    ▼
process_group_order_response()
    │
    ▼
Update group_responses
    │
    ▼
All responses collected?
    │
    ▼ Yes
_finalize_group_order()
    │
    ├── Update quantities: 2L + 1L = 3L
    ├── Update shared_by: ["person_a", "person_b"] (person_c removed)
    ├── Mark as CONFIRMED
    └── Update inventory for person_a and person_b
```

---

## Key Features

### 1. Order Batching

**Purpose**: Automatically combine multiple order requests into a single order.

**Rules**:
- Time window: 5 minutes
- Same user only
- Non-group orders only
- Status: PENDING or CONFIRMED

**Implementation**:
```python
# In create_order()
pending_order = await self.get_pending_order(created_by, within_minutes=5)
if pending_order:
    return await self.add_items_to_order(pending_order.order_id, items, created_by)
```

**Benefits**:
- Reduces delivery fees
- Better user experience
- Automatic (no user action needed)

---

### 2. Selective Sharing

**Purpose**: Allow per-item sharing with specific users instead of all household members.

**How it works**:
- LLM can specify `shared_with` per item
- Only specified users + creator are included
- WhatsApp notifications only sent to specified users
- `shared_by` field set correctly for cost splitting

**Example**:
```python
# LLM tool call
{
    "items": [{
        "name": "milk",
        "quantity": 2,
        "shared_with": ["person_b", "person_c"]  # Only B and C
    }]
}

# Result
order_item.shared_by = ["person_a", "person_b", "person_c"]  # Creator + specified
```

**Implementation**:
- Tool schema includes `shared_with` parameter
- `create_order()` checks for `shared_with` in item_data
- Sets `shared_by` and `pending_responses` accordingly
- WhatsApp service only notifies specified users

---

### 3. Group Orders

**Purpose**: Automatically create group orders for shared items and collect housemate responses.

**Flow**:
1. Order created with shared items
2. `is_group_order = True`
3. `pending_responses` set for each shared item
4. WhatsApp notification sent
5. Users respond via WhatsApp
6. `process_group_order_response()` updates order
7. `_finalize_group_order()` when all respond or deadline passes

**Finalization**:
- Updates quantities based on responses
- Updates `shared_by` to only include users who want items
- Marks order as CONFIRMED
- Updates inventory for all users

---

### 4. Missing Product Handling

**Purpose**: Gracefully handle products not found in menu.

**How it works**:
- If product not found, item is skipped
- Added to `missing_products` list
- Order created with available items only
- Warnings returned in response

**Response Format**:
```python
{
    "order_id": "...",
    "items": [...],  # Only found items
    "partial_warnings": [
        {
            "name": "Toilet Paper",
            "reason": "No matching products found"
        }
    ]
}
```

**Agent Behavior**:
- Informs user about missing items
- Suggests alternatives or separate order
- Order still created with available items

---

## Integration Points

### 1. Agent Integration

**Files**:
- `agent/core.py`: GroceryAgent orchestrator
- `agent/tool_handlers.py`: place_order() handler
- `agent/tools.py`: Tool schema
- `agent/context.py`: Household member context

**Flow**:
```
Agent → Tool Handler → OrderingService → MenuLoader → MongoDB
```

### 2. Inventory Integration

**Purpose**: Determines if items are shared.

**How**:
- Checks inventory for item with `shared=True`
- Matches order items to inventory items
- Sets `is_group_order` if shared items found

**Files**:
- `modules/inventory/service.py`
- `models/inventory.py`

### 3. WhatsApp Integration

**Purpose**: Notify housemates about group orders.

**Files**:
- `modules/whatsapp/service.py`
- `api/controllers/whatsapp_controller.py`

**Flow**:
```
Order created → WhatsApp notification → User responses → Order updated
```

**Selective Notification**:
- Only notifies users in `pending_responses`
- Supports `notify_user_ids` parameter
- Sends individual messages or household broadcast

### 4. Splitwise Integration (Planned)

**Purpose**: Create expenses for shared items after delivery.

**Files**:
- `modules/splitwise/service.py`

**Planned Flow**:
```
Order DELIVERED → Check shared items → Create Splitwise expenses
```

**Implementation** (To be added):
- Triggered when order status changes to DELIVERED
- Creates expense for each shared item
- Splits cost among `shared_by` users
- Stores expense IDs in `splitwise_expense_ids`

### 5. API Integration

**Files**:
- `api/routers/orders.py`: FastAPI routes
- `api/controllers/orders_controller.py`: Controllers

**Endpoints**:
- `POST /api/orders`: Create order
- `GET /api/orders/{order_id}`: Get order
- `GET /api/orders`: List orders
- `PUT /api/orders/{order_id}/status`: Update status

---

## API Design

### Order Creation

**Endpoint**: `POST /api/orders`

**Request**:
```json
{
    "items": [
        {
            "name": "milk",
            "quantity": 2,
            "unit": "liters",
            "shared_with": ["user_b", "user_c"]
        }
    ],
    "delivery_address": "123 Main St",
    "notes": "Please leave at door"
}
```

**Response**:
```json
{
    "order_id": "uuid",
    "status": "pending",
    "total": 7.67,
    "items": [...],
    "is_group_order": true,
    "group_order": {
        "whatsapp_sent": true,
        "response_deadline": "2025-11-09T16:00:00Z",
        "shared_items": [...]
    },
    "partial_warnings": []
}
```

### Status Update

**Endpoint**: `PUT /api/orders/{order_id}/status`

**Request**:
```json
{
    "status": "delivered"
}
```

**Response**:
```json
{
    "order_id": "uuid",
    "status": "delivered",
    "updated_at": "2025-11-09T14:00:00Z"
}
```

---

## Error Handling

### Product Search Failures

**Scenario**: Product not found in menu

**Handling**:
- Item skipped
- Added to `missing_products` list
- Order created with available items
- Warning returned in response

### Order Creation Failures

**Scenario**: Database error, validation error

**Handling**:
- Log error with traceback
- Return `None` from `create_order()`
- Tool handler returns error response
- Agent informs user of failure

### Group Order Response Failures

**Scenario**: Invalid response format, user not in pending_responses

**Handling**:
- Log warning
- Return existing order unchanged
- User can retry with correct format

### Missing Dependencies

**Scenario**: WhatsApp service not configured

**Handling**:
- Order still created
- `whatsapp_message_sent = False`
- Warning logged
- User informed that notification not sent

---

## Future Enhancements

### 1. Automatic Status Progression

**Current**: Manual status updates only

**Planned**: Mock automatic progression
- PENDING → CONFIRMED (after 1 min)
- CONFIRMED → PROCESSING (after 2 min)
- PROCESSING → OUT_FOR_DELIVERY (after 5 min)
- OUT_FOR_DELIVERY → DELIVERED (after 10 min)

**Implementation**:
- Background task or scheduled job
- Updates status automatically
- Triggers Splitwise expense creation on DELIVERED

### 2. LLM Product Selection

**Current**: Takes first search result

**Planned**: LLM selects best option
- Considers price, brand preferences
- User dietary restrictions
- Availability

### 3. Real API Integration

**Current**: JSON menu files

**Planned**: Real delivery service API
- Replace MenuLoader with API client
- Real-time product availability
- Real order placement
- Real status updates

### 4. Splitwise Expense Creation

**Current**: Not implemented

**Planned**: Automatic expense creation
- Triggered when status → DELIVERED
- Creates expense for each shared item
- Splits cost among `shared_by` users
- Stores expense IDs in order

### 5. Delivery Time Estimation

**Current**: Not calculated

**Planned**: Estimate delivery time
- Calculate from menu data
- Show estimated delivery to user
- Update as order progresses

### 6. Product Recommendations

**Current**: No recommendations

**Planned**: Suggest alternatives
- For missing products
- Based on brand preferences
- Similar products

---

## Configuration

### Environment Variables

```python
# config.py
ordering_menu_path: Optional[str]  # Path to menu directory (default: backend/data/)
```

### Menu File Location

**Default**: `backend/data/restaurant1_menu.json`

**Structure**:
- Restaurant info (name, delivery cost)
- Menu items (product_id, name, price, available, brand)

**Current Menu**:
- 558 items
- Restaurant: Flink Amsterdam Buitenveldert
- Delivery cost: €4.49

---

## Summary

The Ordering System architecture provides:

- ✅ **Modular Design**: Clear separation of concerns
- ✅ **Scalable**: Supports multiple restaurants and menus
- ✅ **Flexible**: Selective sharing, batching, group orders
- ✅ **Robust**: Error handling, missing product support
- ✅ **Integrated**: Works with Agent, Inventory, WhatsApp
- ✅ **Extensible**: Ready for Splitwise, real API integration

**Total Code**: ~2,124 lines across core ordering module

**Key Files**:
- `service.py`: 925 lines (main service)
- `menu_loader.py`: 250 lines (menu management)
- `tool_handlers.py`: ~100 lines (agent integration)
- `order.py`: ~170 lines (data models)

