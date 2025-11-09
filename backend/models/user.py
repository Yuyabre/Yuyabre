"""
User Model - MongoDB schema for user preferences and profiles.
"""
from datetime import datetime
from typing import List, Dict, Optional
from beanie import Document
from pydantic import BaseModel, Field, EmailStr
from uuid import uuid4


class ConsumptionPattern(BaseModel):
    """
    Tracks consumption patterns for a specific item.
    
    Attributes:
        item_name: Name of the item
        weekly_average: Average weekly consumption
        preferred_type: Preferred variant/type (e.g., "semi-skimmed" for milk)
        preferred_brand: Preferred brand
        last_purchased: When this item was last purchased
    """
    
    item_name: str
    weekly_average: float = Field(default=0.0, ge=0)
    preferred_type: Optional[str] = None
    preferred_brand: Optional[str] = None
    last_purchased: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "item_name": "Milk",
                "weekly_average": 1.5,
                "preferred_type": "semi-skimmed",
                "preferred_brand": "Melkunie",
                "last_purchased": "2025-11-08T10:00:00Z"
            }
        }


class UserPreference(BaseModel):
    """
    User dietary preferences and restrictions.
    
    Attributes:
        dietary_restrictions: List of dietary restrictions (e.g., "vegetarian", "vegan")
        allergies: List of allergies (e.g., "nuts", "gluten")
        favorite_brands: List of preferred brands
        disliked_items: Items the user doesn't want
    """
    
    dietary_restrictions: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    favorite_brands: List[str] = Field(default_factory=list)
    disliked_items: List[str] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "dietary_restrictions": ["vegetarian"],
                "allergies": ["nuts"],
                "favorite_brands": ["Brand A", "Brand B"],
                "disliked_items": ["brussels sprouts"]
            }
        }


class User(Document):
    """
    Represents a flatmate/user in the system.
    
    Attributes:
        user_id: Unique user identifier
        name: User's full name
        email: User's email address
        phone: Phone number (for WhatsApp notifications)
        splitwise_user_id: User ID in Splitwise
        preferences: User dietary preferences
        consumption_patterns: Dictionary of consumption patterns per item
        is_active: Whether user is currently active in the flat
        joined_date: When the user joined the flat
        notes: Additional notes about the user
    """
    
    user_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    splitwise_user_id: Optional[str] = None
    # OAuth tokens for Splitwise
    splitwise_access_token: Optional[str] = None
    splitwise_access_token_secret: Optional[str] = None
    splitwise_oauth_token: Optional[str] = None  # Temporary token during OAuth flow
    splitwise_oauth_token_secret: Optional[str] = None  # Temporary secret during OAuth flow
    preferences: UserPreference = Field(default_factory=UserPreference)
    consumption_patterns: Dict[str, ConsumptionPattern] = Field(default_factory=dict)
    is_active: bool = Field(default=True)
    joined_date: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None
    
    class Settings:
        name = "users"
        indexes = [
            "user_id",
            "email",
            "splitwise_user_id",
        ]
    
    def add_consumption_pattern(self, pattern: ConsumptionPattern) -> None:
        """Add or update a consumption pattern for an item."""
        self.consumption_patterns[pattern.item_name] = pattern
    
    def has_allergy(self, item: str) -> bool:
        """Check if user is allergic to an item."""
        return item.lower() in [a.lower() for a in self.preferences.allergies]
    
    def has_dietary_restriction(self, restriction: str) -> bool:
        """Check if user has a specific dietary restriction."""
        return restriction.lower() in [r.lower() for r in self.preferences.dietary_restrictions]
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "+31612345678",
                "splitwise_user_id": "sw_123456",
                "preferences": {
                    "dietary_restrictions": ["vegetarian"],
                    "allergies": ["nuts"],
                    "favorite_brands": ["Brand A"],
                    "disliked_items": []
                },
                "consumption_patterns": {
                    "milk": {
                        "item_name": "Milk",
                        "weekly_average": 1.5,
                        "preferred_type": "semi-skimmed"
                    }
                },
                "is_active": True,
                "joined_date": "2025-01-01T00:00:00Z"
            }
        }

