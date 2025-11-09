"""
Request and Response serializers (Pydantic models) for the API.
"""
from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, EmailStr


class CommandRequest(BaseModel):
    """Request model for agent commands."""
    command: str
    user_id: Optional[str] = None


class CommandResponse(BaseModel):
    """Response model for agent commands."""
    success: bool
    message: str


class InventoryItemCreate(BaseModel):
    """Request model for creating inventory items."""
    name: str
    category: str
    quantity: float
    unit: str
    threshold: float = 1.0
    shared: bool = True
    brand: Optional[str] = None
    price: Optional[float] = None


class InventoryItemUpdate(BaseModel):
    """Request model for updating inventory items."""
    quantity: Optional[float] = None
    threshold: Optional[float] = None
    notes: Optional[str] = None


class MessageResponse(BaseModel):
    """Generic message response model."""
    message: str


# Authentication serializers
class UserPreferenceRequest(BaseModel):
    """Request model for user preferences."""
    dietary_restrictions: List[str] = []
    allergies: List[str] = []
    favorite_brands: List[str] = []
    disliked_items: List[str] = []


class UpdateUserPreferencesRequest(BaseModel):
    """Request model for updating user preferences (supports add/remove)."""
    dietary_restrictions: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    favorite_brands: Optional[List[str]] = None
    disliked_items: Optional[List[str]] = None
    remove_dietary_restrictions: Optional[List[str]] = None
    remove_allergies: Optional[List[str]] = None
    remove_favorite_brands: Optional[List[str]] = None
    remove_disliked_items: Optional[List[str]] = None


class SignupRequest(BaseModel):
    """Request model for user signup."""
    name: str
    email: Optional[EmailStr] = None
    password: str
    phone: Optional[str] = None
    splitwise_user_id: Optional[str] = None
    discord_user_id: Optional[str] = None  # Discord user ID for message matching
    preferences: Optional[UserPreferenceRequest] = None


class LoginRequest(BaseModel):
    """Request model for user login."""
    email: EmailStr
    password: str


class ConsumptionPatternRequest(BaseModel):
    """Request model for consumption pattern updates."""
    item_name: Optional[str] = None
    weekly_average: Optional[float] = None
    preferred_type: Optional[str] = None
    preferred_brand: Optional[str] = None
    last_purchased: Optional[datetime] = None


class UserUpdateRequest(BaseModel):
    """Generic request model for updating user fields."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    household_id: Optional[str] = None
    splitwise_user_id: Optional[str] = None
    splitwise_access_token: Optional[str] = None
    splitwise_access_token_secret: Optional[str] = None
    discord_user_id: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None
    preferences: Optional[UserPreferenceRequest] = None
    consumption_patterns: Optional[Dict[str, ConsumptionPatternRequest]] = None


class UserResponse(BaseModel):
    """Response model for user information."""
    user_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    discord_user_id: Optional[str] = None  # Discord user ID for message matching
    household_id: Optional[str] = None
    is_active: bool
    joined_date: str
    preferences: Optional[UserPreferenceRequest] = None


class UpdatePreferencesResponse(BaseModel):
    """Response model for updating user preferences."""
    success: bool
    message: str
    updated_fields: List[str] = []
    current_preferences: Optional[UserPreferenceRequest] = None


class JoinHouseholdRequest(BaseModel):
    """Request model for joining a household."""
    invite_code: str


class CreateHouseholdRequest(BaseModel):
    """Request model for creating a household."""
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    whatsapp_group_id: Optional[str] = None
    whatsapp_group_name: Optional[str] = None
    discord_channel_id: Optional[str] = None  # Discord channel ID for household notifications
    notes: Optional[str] = None


class HouseholdResponse(BaseModel):
    """Response model for household information."""
    household_id: str
    name: str
    invite_code: str
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    whatsapp_group_id: Optional[str] = None
    whatsapp_group_name: Optional[str] = None
    discord_channel_id: Optional[str] = None  # Discord channel ID for household notifications
    splitwise_group_id: Optional[str] = None  # Splitwise group ID for expense splitting
    member_ids: List[str] = []
    created_at: str
    is_active: bool
    notes: Optional[str] = None


class UpdateHouseholdRequest(BaseModel):
    """Request model for updating household information."""
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    whatsapp_group_id: Optional[str] = None
    whatsapp_group_name: Optional[str] = None
    discord_channel_id: Optional[str] = None
    splitwise_group_id: Optional[str] = None
    notes: Optional[str] = None


class SearchGroupsRequest(BaseModel):
    """Request model for searching Splitwise groups."""
    query: str  # Group name to search for


class CreateExpenseRequest(BaseModel):
    """Request model for creating a Splitwise expense."""
    description: str
    amount: float
    splitwise_user_ids: List[str]  # List of Splitwise user IDs to split among
    group_id: Optional[str] = None  # Splitwise group ID
    category: str = "Groceries"
    date: Optional[str] = None  # ISO format date string
    notes: Optional[str] = None
    split_method: str = "equal"  # How to split: "equal" or other methods
    paid_by_user_id: Optional[str] = None  # Splitwise user ID of person who paid

