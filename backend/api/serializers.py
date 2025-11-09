"""
Request and Response serializers (Pydantic models) for the API.
"""
from pydantic import BaseModel, EmailStr
from typing import List, Optional


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


class SignupRequest(BaseModel):
    """Request model for user signup."""
    name: str
    email: Optional[EmailStr] = None
    password: str
    phone: Optional[str] = None
    splitwise_user_id: Optional[str] = None
    preferences: Optional[UserPreferenceRequest] = None


class LoginRequest(BaseModel):
    """Request model for user login."""
    email: EmailStr
    password: str




class UserResponse(BaseModel):
    """Response model for user information."""
    user_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    household_id: Optional[str] = None
    is_active: bool
    joined_date: str


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
    member_ids: List[str] = []
    created_at: str
    is_active: bool
    notes: Optional[str] = None

