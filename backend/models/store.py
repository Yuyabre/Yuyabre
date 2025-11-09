"""
Store Model - MongoDB schema for grocery stores and their inventory.
"""
from datetime import datetime
from typing import List, Optional, Dict
from beanie import Document
from pydantic import BaseModel, Field
from uuid import uuid4


class StoreLocation(BaseModel):
    """
    Geographic location of a store.
    
    Attributes:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        address: Street address
        city: City name
        postal_code: Postal/ZIP code
        country: Country name
    """
    latitude: float
    longitude: float
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None


class Store(Document):
    """
    Represents a grocery store.
    
    Attributes:
        store_id: Unique store identifier
        name: Store name (e.g., "Albert Heijn", "Jumbo")
        chain: Store chain/brand name
        location: Geographic location of the store
        phone: Store phone number
        website: Store website URL
        api_endpoint: API endpoint for fetching inventory (if available)
        is_active: Whether the store is currently active
        last_inventory_update: When inventory was last fetched
        created_at: When the store was added to the system
    """
    
    store_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., min_length=1, max_length=200)
    chain: Optional[str] = None  # e.g., "Albert Heijn", "Jumbo", "Lidl"
    location: StoreLocation
    phone: Optional[str] = None
    website: Optional[str] = None
    api_endpoint: Optional[str] = None  # API endpoint for inventory
    is_active: bool = Field(default=True)
    last_inventory_update: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "stores"
        indexes = [
            "store_id",
            "chain",
            "location.latitude",
            "location.longitude",
            "is_active",
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "store_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Albert Heijn Delft Centrum",
                "chain": "Albert Heijn",
                "location": {
                    "latitude": 52.0116,
                    "longitude": 4.3571,
                    "address": "Markt 1",
                    "city": "Delft",
                    "postal_code": "2611 GP",
                    "country": "Netherlands"
                },
                "phone": "+31 15 212 3456",
                "website": "https://www.ah.nl",
                "is_active": True
            }
        }


class StoreProduct(BaseModel):
    """
    Represents a product available at a store.
    
    Attributes:
        product_id: Store-specific product ID
        name: Product name
        brand: Product brand
        price: Price per unit
        unit: Unit of measurement (e.g., "piece", "kg", "liter")
        category: Product category
        available: Whether product is currently in stock
        image_url: Product image URL
        description: Product description
    """
    product_id: str
    name: str
    brand: Optional[str] = None
    price: float = Field(ge=0)
    unit: str = Field(default="piece")
    category: Optional[str] = None
    available: bool = Field(default=True)
    image_url: Optional[str] = None
    description: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "AH_12345",
                "name": "Volle Melk",
                "brand": "AH Eigenmerk",
                "price": 1.29,
                "unit": "liter",
                "category": "Dairy",
                "available": True
            }
        }


class StoreInventory(Document):
    """
    Cached inventory for a store in a specific locality.
    
    Attributes:
        inventory_id: Unique inventory identifier
        store_id: Reference to the Store
        locality_key: Unique key for this locality (e.g., "delft_2611")
        products: List of products available at this store
        last_updated: When this inventory was last fetched/updated
        expires_at: When this inventory cache expires (for refresh)
        created_at: When this inventory was first cached
    """
    
    inventory_id: str = Field(default_factory=lambda: str(uuid4()))
    store_id: str  # Reference to Store.store_id
    locality_key: str  # e.g., "delft_2611" or "amsterdam_1012"
    products: List[StoreProduct] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None  # Cache expiration time
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "store_inventory"
        indexes = [
            "inventory_id",
            "store_id",
            "locality_key",
            "last_updated",
            "expires_at",
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "inventory_id": "550e8400-e29b-41d4-a716-446655440000",
                "store_id": "store_123",
                "locality_key": "delft_2611",
                "products": [
                    {
                        "product_id": "AH_12345",
                        "name": "Volle Melk",
                        "price": 1.29,
                        "unit": "liter"
                    }
                ],
                "last_updated": "2025-11-09T10:00:00Z"
            }
        }

