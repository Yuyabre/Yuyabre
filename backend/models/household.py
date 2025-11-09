"""
Household Model - MongoDB schema for grouping users and managing WhatsApp groups.
"""
from datetime import datetime
from typing import List, Optional
from beanie import Document
from pydantic import Field
from uuid import uuid4
import secrets


class Household(Document):
    """
    Represents a household (flat) with multiple users.
    
    Attributes:
        household_id: Unique household identifier
        name: Name of the household (e.g., "Flat 3B")
        invite_code: Unique invite code for users to join this household (generated automatically)
        address: Physical address of the household
        city: City where the household is located
        postal_code: Postal/ZIP code
        country: Country where the household is located
        whatsapp_group_id: WhatsApp group ID or phone number for group messaging
        whatsapp_group_name: Name of the WhatsApp group
        member_ids: List of user IDs who are members of this household
        created_at: When the household was created
        is_active: Whether the household is currently active
        notes: Additional notes about the household
    """
    
    household_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., min_length=1, max_length=200)
    invite_code: str = Field(default_factory=lambda: secrets.token_urlsafe(16))  # Unique invite code
    address: Optional[str] = None  # Street address
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    whatsapp_group_id: Optional[str] = None  # Group ID or phone number
    whatsapp_group_name: Optional[str] = None
    member_ids: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    notes: Optional[str] = None
    
    class Settings:
        name = "households"
        indexes = [
            "household_id",
            "whatsapp_group_id",
            "invite_code",
        ]
    
    def add_member(self, user_id: str) -> None:
        """Add a member to the household."""
        if user_id not in self.member_ids:
            self.member_ids.append(user_id)
    
    def remove_member(self, user_id: str) -> None:
        """Remove a member from the household."""
        if user_id in self.member_ids:
            self.member_ids.remove(user_id)
    
    class Config:
        json_schema_extra = {
            "example": {
                "household_id": "550e8400-e29b4-a716-446655440000",
                "name": "Flat 3B",
                "whatsapp_group_id": "+31612345678",
                "whatsapp_group_name": "Flat 3B Groceries",
                "member_ids": ["user1", "user2", "user3"],
                "created_at": "2025-01-01T00:00:00Z",
                "is_active": True,
            }
        }

