"""
Order Model - MongoDB schema for tracking grocery orders.
"""
from datetime import datetime
from typing import List, Optional, Dict
from enum import Enum
from beanie import Document
from pydantic import BaseModel, Field
from uuid import uuid4


class OrderStatus(str, Enum):
    """Order status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    FAILED = "failed"


class OrderItem(BaseModel):
    """
    Represents a single item within an order.
    
    Attributes:
        product_id: External product ID from Thuisbezorgd
        name: Name of the product
        quantity: Quantity ordered
        unit: Unit of measurement
        price: Price per unit
        total_price: Total price for this item (quantity * price)
        requested_by: List of user IDs who requested this item
        shared: Whether this item is shared among housemates
        shared_by: List of user IDs who share this item (for cost splitting)
    """
    
    product_id: str
    name: str
    quantity: float = Field(gt=0)
    unit: str
    price: float = Field(ge=0)
    total_price: float = Field(ge=0)
    requested_by: List[str] = Field(default_factory=list)
    shared: bool = Field(default=False, description="Whether this item is shared among housemates")
    shared_by: List[str] = Field(default_factory=list, description="List of user IDs who share this item for cost splitting")
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "prod_123",
                "name": "Milk",
                "quantity": 2.0,
                "unit": "liters",
                "price": 1.75,
                "total_price": 3.50,
                "requested_by": ["user1", "user2"],
                "shared": True,
                "shared_by": ["user1", "user2", "user3"]
            }
        }


class Order(Document):
    """
    Represents a grocery order placed through Thuisbezorgd.
    
    Attributes:
        order_id: Unique order identifier
        timestamp: When the order was created
        service: Delivery service used (default: "Thuisbezorgd")
        items: List of ordered items
        subtotal: Subtotal before fees
        delivery_fee: Delivery fee charged
        total: Total amount including all fees
        delivery_time: Estimated or actual delivery time
        delivery_address: Delivery address
        status: Current order status
        external_order_id: Order ID from Thuisbezorgd
        splitwise_expense_id: Associated Splitwise expense ID
        notes: Additional notes about the order
        created_by: User who created the order
        is_group_order: Whether this is a group order requiring housemate responses
        household_id: ID of the household for group orders
        pending_responses: Dict mapping item names to list of user IDs who need to respond
        response_deadline: Deadline for housemates to respond
        group_responses: Dict mapping user_id to their response data
        whatsapp_message_sent: Whether WhatsApp notification was sent
    """
    
    order_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    service: str = Field(default="Thuisbezorgd")
    items: List[OrderItem] = Field(default_factory=list)
    subtotal: float = Field(default=0.0, ge=0)
    delivery_fee: float = Field(default=0.0, ge=0)
    total: float = Field(default=0.0, ge=0)
    delivery_time: Optional[datetime] = None
    delivery_address: Optional[str] = None
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    external_order_id: Optional[str] = None
    splitwise_expense_id: Optional[str] = None
    notes: Optional[str] = None
    created_by: Optional[str] = None
    is_group_order: bool = Field(default=False)
    household_id: Optional[str] = None
    pending_responses: Dict[str, List[str]] = Field(default_factory=dict)  # item_name -> [user_ids]
    response_deadline: Optional[datetime] = None
    group_responses: Dict[str, Dict] = Field(default_factory=dict)  # user_id -> response data
    whatsapp_message_sent: bool = Field(default=False)
    
    class Settings:
        name = "orders"
        indexes = [
            "order_id",
            "timestamp",
            "status",
            "external_order_id",
            "splitwise_expense_id",
            "household_id",
            "is_group_order",
        ]
    
    def calculate_total(self) -> float:
        """Calculate the total order amount."""
        self.subtotal = sum(item.total_price for item in self.items)
        self.total = self.subtotal + self.delivery_fee
        return self.total
    
    def add_item(self, item: OrderItem) -> None:
        """Add an item to the order and recalculate total."""
        self.items.append(item)
        self.calculate_total()
    
    def is_completed(self) -> bool:
        """Check if order is completed (delivered or cancelled)."""
        return self.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]
    
    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2025-11-08T10:00:00Z",
                "service": "Thuisbezorgd",
                "items": [
                    {
                        "product_id": "123",
                        "name": "Milk",
                        "quantity": 2,
                        "unit": "liters",
                        "price": 1.75,
                        "total_price": 3.50,
                        "requested_by": ["user1", "user2"]
                    }
                ],
                "subtotal": 3.50,
                "delivery_fee": 2.50,
                "total": 6.00,
                "delivery_time": "2025-11-08T14:00:00Z",
                "status": "delivered",
                "splitwise_expense_id": "789"
            }
        }

