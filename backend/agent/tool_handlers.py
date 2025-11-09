"""
Tool Handlers - Implementation of all agent tools.
"""
from typing import Any, Dict, List, Optional, Callable, Awaitable
from loguru import logger

from modules.inventory import InventoryService
from modules.ordering import OrderingService
from modules.splitwise import SplitwiseService
from modules.whatsapp import WhatsAppService
from models.user import User
from models.household import Household


class ToolHandlers:
    """
    Handles all tool execution for the agent.
    """
    
    def __init__(
        self,
        inventory_service: InventoryService,
        ordering_service: OrderingService,
        splitwise_service: SplitwiseService,
        whatsapp_service: WhatsAppService,
        update_system_prompt_callback: Optional[Callable[[str], Awaitable[None]]] = None,
    ):
        """
        Initialize tool handlers.
        
        Args:
            inventory_service: Inventory service instance
            ordering_service: Ordering service instance
            splitwise_service: Splitwise service instance
            whatsapp_service: WhatsApp service instance
            update_system_prompt_callback: Optional callback to update system prompt when preferences change
        """
        self.inventory_service = inventory_service
        self.ordering_service = ordering_service
        self.splitwise_service = splitwise_service
        self.whatsapp_service = whatsapp_service
        self.update_system_prompt_callback = update_system_prompt_callback
    
    def normalize_allergy(self, allergy: str) -> str:
        """
        Normalize allergy names to common forms.
        
        Examples:
        - "lactose intolerant" -> "lactose"
        - "dairy intolerant" -> "dairy"
        - "gluten free" -> "gluten"
        """
        allergy_lower = allergy.lower().strip()
        
        # Common mappings
        mappings = {
            "lactose intolerant": "lactose",
            "lactose intolerance": "lactose",
            "dairy intolerant": "dairy",
            "dairy free": "dairy",
            "gluten free": "gluten",
            "gluten intolerant": "gluten",
            "celiac": "gluten",
            "peanut allergy": "peanuts",
            "nut allergy": "nuts",
            "tree nut allergy": "tree nuts",
            "shellfish allergy": "shellfish",
            "seafood allergy": "shellfish",
        }
        
        # Check for exact matches first
        if allergy_lower in mappings:
            return mappings[allergy_lower]
        
        # Check if any mapping key is contained in the allergy string
        for key, value in mappings.items():
            if key in allergy_lower:
                return value
        
        # Return original if no mapping found
        return allergy.strip()
    
    async def get_inventory_snapshot(
        self,
        user_id: Optional[str] = None,
        dish: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return a snapshot of current inventory, optionally filtered."""
        items = await self.inventory_service.get_all_items(user_id=user_id)

        def matches_query(item) -> bool:
            if search and search.lower() not in item.name.lower():
                return False
            return True

        filtered = [item for item in items if matches_query(item)]

        return {
            "dish": dish,
            "count": len(filtered),
            "items": [
                {
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "category": item.category,
                    "threshold": item.threshold,
                    "shared": item.shared,
                }
                for item in filtered
            ],
        }

    async def add_inventory_items(
        self,
        *,
        items: List[Dict[str, Any]],
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add or increment items in the inventory."""
        if not items:
            return {"error": "No items provided to add."}

        # Get user's household_id if available
        household_id = None
        if user_id:
            user = await User.find_one(User.user_id == user_id)
            if user:
                household_id = getattr(user, 'household_id', None)

        results = []
        for item in items:
            name = item.get("name")
            quantity = item.get("quantity")
            if not name or quantity is None:
                results.append(
                    {
                        "name": name or "unknown",
                        "status": "skipped",
                        "reason": "Missing name or quantity.",
                    }
                )
                continue

            # Determine if item should be shared (default to shared if in household)
            shared = item.get("shared")
            if shared is None:
                shared = household_id is not None  # Default to shared if in household

            existing_item = await self.inventory_service.get_item_by_name(
                name, 
                user_id=user_id if not shared else None,
                household_id=household_id if shared else None
            )
            updated = await self.inventory_service.add_or_increment_item(
                name=name,
                quantity=quantity,
                unit=item.get("unit"),
                category=item.get("category"),
                user_id=user_id if not shared else None,
                household_id=household_id if shared else None,
                shared=shared,
            )
            results.append(
                {
                    "name": updated.name,
                    "quantity": updated.quantity,
                    "unit": updated.unit,
                    "status": "updated" if existing_item else "created",
                    "shared": updated.shared,
                }
            )

        return {"items": results}

    async def place_order(
        self,
        *,
        items: List[Dict[str, Any]],
        delivery_address: Optional[str] = None,
        notes: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Place an order for the given items."""
        if not items:
            return {"error": "No items provided to order."}

        # Get user's household_id if available
        household_id = None
        if user_id:
            user = await User.find_one(User.user_id == user_id)
            if user:
                household_id = getattr(user, 'household_id', None)

        order_items = []
        missing_products = []

        for item in items:
            name = item.get("name")
            quantity = float(item.get("quantity", 0))
            if not name or quantity <= 0:
                missing_products.append(
                    {"name": name, "reason": "Invalid name or quantity"}
                )
                continue

            # Check inventory first to see if item is shared
            # This helps with matching later
            inventory_item = None
            base_name = name.split(" - ")[0].strip().lower()
            
            if household_id:
                # Try to find in household shared inventory
                all_shared = await self.inventory_service.get_all_items(household_id=household_id)
                for inv_item in all_shared:
                    if inv_item.shared:
                        inv_base = inv_item.name.split(" - ")[0].strip().lower()
                        if base_name == inv_base or base_name in inv_item.name.lower():
                            inventory_item = inv_item
                            break
            
            # Search for products using the original name or inventory item name
            search_name = inventory_item.name if inventory_item else name
            products = await self.ordering_service.search_products(search_name)
            if not products:
                missing_products.append(
                    {"name": name, "reason": "No matching products found"}
                )
                continue

            product = products[0]
            order_items.append(
                {
                    "product_id": product["product_id"],
                    "name": product["name"],
                    "quantity": quantity,
                    "unit": item.get("unit") or product.get("unit") or "unit",
                    "price": product["price"],
                    "requested_by": [user_id] if user_id else [],
                    # Store original inventory item name for better matching
                    "_inventory_item_name": inventory_item.name if inventory_item else None,
                }
            )

        if not order_items:
            return {
                "error": "No products could be matched for ordering.",
                "missing": missing_products,
            }

        order = await self.ordering_service.create_order(
            items=order_items,
            delivery_address=delivery_address or "Default Address",
            notes=notes,
            created_by=user_id,
        )

        if not order:
            return {"error": "Failed to create the order with the delivery service."}

        # Update inventory with ordered items (only for non-group orders or after group order is finalized)
        # For group orders, inventory will be updated after responses are collected
        if not order.is_group_order:
            # Get user's household_id if available
            household_id = None
            if user_id:
                user = await User.find_one(User.user_id == user_id)
                if user:
                    household_id = getattr(user, 'household_id', None)
            
            for item in order.items:
                # Determine if item should be shared (check if it exists as shared in household)
                is_shared = False
                if household_id:
                    existing_shared = await self.inventory_service.get_item_by_name(
                        item.name, household_id=household_id
                    )
                    if existing_shared and existing_shared.shared:
                        is_shared = True
                
                await self.inventory_service.add_or_increment_item(
                    name=item.name,
                    quantity=item.quantity,
                    unit=item.unit,
                    category="Ordered",
                    user_id=user_id if not is_shared else None,
                    household_id=household_id if is_shared else None,
                    shared=is_shared,
                )

        summary = {
            "order_id": order.order_id,
            "status": order.status.value,
            "total": order.total,
            "items": [
                {
                    "name": it.name,
                    "quantity": it.quantity,
                    "unit": it.unit,
                    "price": it.price,
                }
                for it in order.items
            ],
            "is_group_order": order.is_group_order,
        }

        # Add group order information
        if order.is_group_order:
            summary["group_order"] = {
                "whatsapp_sent": order.whatsapp_message_sent,
                "response_deadline": order.response_deadline.isoformat() if order.response_deadline else None,
                "shared_items": [
                    {
                        "name": item.name,
                        "quantity": item.quantity,
                        "unit": item.unit,
                    }
                    for item in order.items
                    if any(
                        # Check if this item is in the shared items list
                        item.name == shared_item.get("name") or
                        item.name.split(" - ")[0] == shared_item.get("name", "").split(" - ")[0]
                        for shared_item in order_items
                    )
                ],
            }

        if missing_products:
            summary["partial_warnings"] = missing_products

        return summary

    async def check_low_stock(
        self,
        *,
        limit: Optional[int] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List low-stock items."""
        items = await self.inventory_service.get_low_stock_items(user_id=user_id)
        if limit:
            items = items[:limit]

        return {
            "count": len(items),
            "items": [
                {
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "threshold": item.threshold,
                }
                for item in items
            ],
        }

    async def get_recent_orders(
        self,
        *,
        limit: Optional[int] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Retrieve recent orders."""
        orders = await self.ordering_service.get_order_history(limit=limit or 5)
        return {
            "count": len(orders),
            "orders": [
                {
                    "order_id": order.order_id,
                    "status": order.status.value,
                    "total": order.total,
                    "created_at": order.timestamp.isoformat(),
                    "items": [
                        {
                            "name": item.name,
                            "quantity": item.quantity,
                            "unit": item.unit,
                        }
                        for item in order.items
                    ],
                }
                for order in orders
            ],
        }
    
    async def update_user_preferences(
        self,
        *,
        dietary_restrictions: Optional[List[str]] = None,
        allergies: Optional[List[str]] = None,
        favorite_brands: Optional[List[str]] = None,
        disliked_items: Optional[List[str]] = None,
        remove_dietary_restrictions: Optional[List[str]] = None,
        remove_allergies: Optional[List[str]] = None,
        remove_favorite_brands: Optional[List[str]] = None,
        remove_disliked_items: Optional[List[str]] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update user preferences (dietary restrictions, allergies, brands, disliked items).
        
        This tool allows the agent to update user preferences on the fly when users
        mention them in conversation.
        """
        if not user_id:
            return {
                "success": False,
                "error": "User ID is required to update preferences",
            }
        
        # Fetch user
        user = await User.find_one(User.user_id == user_id)
        if not user:
            return {
                "success": False,
                "error": f"User not found: {user_id}",
            }
        
        updated_fields = []
        
        # Add dietary restrictions
        if dietary_restrictions:
            for restriction in dietary_restrictions:
                restriction_clean = restriction.strip()
                restriction_lower = restriction_clean.lower()
                if restriction_lower and restriction_lower not in [
                    r.lower() for r in user.preferences.dietary_restrictions
                ]:
                    user.preferences.dietary_restrictions.append(restriction_clean)
                    updated_fields.append(f"Added dietary restriction: {restriction_clean}")
        
        # Remove dietary restrictions
        if remove_dietary_restrictions:
            for restriction in remove_dietary_restrictions:
                restriction_lower = restriction.lower().strip()
                user.preferences.dietary_restrictions = [
                    r for r in user.preferences.dietary_restrictions
                    if r.lower() != restriction_lower
                ]
                updated_fields.append(f"Removed dietary restriction: {restriction}")
        
        # Add allergies (with normalization)
        if allergies:
            for allergy in allergies:
                normalized_allergy = self.normalize_allergy(allergy)
                allergy_lower = normalized_allergy.lower()
                if allergy_lower and allergy_lower not in [
                    a.lower() for a in user.preferences.allergies
                ]:
                    user.preferences.allergies.append(normalized_allergy)
                    updated_fields.append(f"Added allergy: {normalized_allergy}")
        
        # Remove allergies (with normalization)
        if remove_allergies:
            for allergy in remove_allergies:
                normalized_allergy = self.normalize_allergy(allergy)
                allergy_lower = normalized_allergy.lower()
                user.preferences.allergies = [
                    a for a in user.preferences.allergies
                    if a.lower() != allergy_lower
                ]
                updated_fields.append(f"Removed allergy: {normalized_allergy}")
        
        # Add favorite brands
        if favorite_brands:
            for brand in favorite_brands:
                brand_clean = brand.strip()
                brand_lower = brand_clean.lower()
                if brand_lower and brand_lower not in [
                    b.lower() for b in user.preferences.favorite_brands
                ]:
                    user.preferences.favorite_brands.append(brand_clean)
                    updated_fields.append(f"Added favorite brand: {brand_clean}")
        
        # Remove favorite brands
        if remove_favorite_brands:
            for brand in remove_favorite_brands:
                brand_lower = brand.lower().strip()
                user.preferences.favorite_brands = [
                    b for b in user.preferences.favorite_brands
                    if b.lower() != brand_lower
                ]
                updated_fields.append(f"Removed favorite brand: {brand}")
        
        # Add disliked items
        if disliked_items:
            for item in disliked_items:
                item_clean = item.strip()
                item_lower = item_clean.lower()
                if item_lower and item_lower not in [
                    d.lower() for d in user.preferences.disliked_items
                ]:
                    user.preferences.disliked_items.append(item_clean)
                    updated_fields.append(f"Added disliked item: {item_clean}")
        
        # Remove disliked items
        if remove_disliked_items:
            for item in remove_disliked_items:
                item_lower = item.lower().strip()
                user.preferences.disliked_items = [
                    d for d in user.preferences.disliked_items
                    if d.lower() != item_lower
                ]
                updated_fields.append(f"Removed disliked item: {item}")
        
        # Save user if any changes were made
        if updated_fields:
            await user.save()
            logger.info(f"Updated preferences for user {user_id}: {updated_fields}")
            
            # Update the conversation's system prompt to reflect new preferences
            # This ensures the agent immediately knows about the updated preferences
            if self.update_system_prompt_callback:
                await self.update_system_prompt_callback(user_id)
            
            return {
                "success": True,
                "message": f"Preferences updated: {', '.join(updated_fields)}",
                "updated_fields": updated_fields,
                "current_preferences": {
                    "dietary_restrictions": user.preferences.dietary_restrictions,
                    "allergies": user.preferences.allergies,
                    "favorite_brands": user.preferences.favorite_brands,
                    "disliked_items": user.preferences.disliked_items,
                },
            }
        else:
            return {
                "success": True,
                "message": "No changes made to preferences",
            }
    
    async def get_user_info(
        self,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get information about the current user."""
        if not user_id:
            return {
                "error": "User ID is required to get user information",
            }
        
        # Fetch user
        user = await User.find_one(User.user_id == user_id)
        if not user:
            return {
                "error": f"User not found: {user_id}",
            }
        
        # Build user info response
        user_info = {
            "user_id": user.user_id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "household_id": user.household_id,
            "is_active": user.is_active,
            "joined_date": user.joined_date.isoformat() if user.joined_date else None,
        }
        
        # Add preferences
        prefs = user.preferences
        user_info["preferences"] = {
            "dietary_restrictions": prefs.dietary_restrictions,
            "allergies": prefs.allergies,
            "favorite_brands": prefs.favorite_brands,
            "disliked_items": prefs.disliked_items,
        }
        
        return user_info
    
    async def update_inventory_item(
        self,
        *,
        item_name: str,
        shared: Optional[bool] = None,
        quantity: Optional[float] = None,
        threshold: Optional[float] = None,
        notes: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update properties of an existing inventory item."""
        if not user_id:
            return {
                "error": "User ID is required to update inventory items",
            }
        
        # Get user's household_id if available
        user = await User.find_one(User.user_id == user_id)
        if not user:
            return {
                "error": f"User not found: {user_id}",
            }
        
        household_id = getattr(user, 'household_id', None)
        
        # Try to find the item - first try as personal, then as shared
        item = None
        if household_id:
            # Try shared item first
            item = await self.inventory_service.get_item_by_name(
                item_name, household_id=household_id
            )
        
        # If not found as shared, try personal
        if not item:
            item = await self.inventory_service.get_item_by_name(
                item_name, user_id=user_id
            )
        
        # If still not found, try a broader search
        if not item:
            matches = await self.inventory_service.search_items(item_name, user_id=user_id)
            if matches:
                item = matches[0]
        
        if not item:
            return {
                "error": f"Item '{item_name}' not found in inventory",
            }
        
        # Prepare update fields
        update_fields = {}
        
        # Handle shared status change
        if shared is not None:
            if shared:
                # Making it shared - move to household
                if not household_id:
                    return {
                        "error": "User is not part of a household. Cannot make item shared.",
                    }
                update_fields["shared"] = True
                update_fields["household_id"] = household_id
                update_fields["user_id"] = None
            else:
                # Making it personal - move to user
                update_fields["shared"] = False
                update_fields["user_id"] = user_id
                update_fields["household_id"] = None
        
        # Handle other optional updates
        if quantity is not None:
            update_fields["quantity"] = max(0, float(quantity))
        
        if threshold is not None:
            update_fields["threshold"] = max(0, float(threshold))
        
        if notes is not None:
            update_fields["notes"] = notes
        
        if not update_fields:
            return {
                "error": "No fields to update. Please specify at least one field to update.",
            }
        
        # Update the item
        updated_item = await self.inventory_service.update_item(
            item.item_id,
            **update_fields
        )
        
        if not updated_item:
            return {
                "error": f"Failed to update item '{item_name}'",
            }
        
        result = {
            "success": True,
            "item_name": updated_item.name,
            "updated_fields": list(update_fields.keys()),
        }
        
        # Include updated values
        if "shared" in update_fields:
            result["shared"] = updated_item.shared
        if "quantity" in update_fields:
            result["quantity"] = updated_item.quantity
        if "threshold" in update_fields:
            result["threshold"] = updated_item.threshold
        if "notes" in update_fields:
            result["notes"] = updated_item.notes
        
        logger.info(f"Updated inventory item '{item_name}': {update_fields}")
        return result
    
    async def send_whatsapp_message(
        self,
        message: str,
        user_id: Optional[str] = None,
        to_household: bool = True,
        phone_number: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a WhatsApp message to household members or a specific user.
        
        Args:
            message: The message content to send
            user_id: ID of the user (required if to_household is True)
            to_household: If True, send to all household members. If False, send to specific phone number.
            phone_number: Phone number in international format (required if to_household is False)
            
        Returns:
            Dict with success status and details
        """
        if not self.whatsapp_service.is_configured():
            return {
                "success": False,
                "error": "WhatsApp service is not configured. Please configure Twilio credentials.",
            }
        
        if to_household:
            if not user_id:
                return {
                    "success": False,
                    "error": "user_id is required when sending to household",
                }
            
            # Get user to find household
            user = await User.find_one(User.user_id == user_id)
            if not user:
                return {
                    "success": False,
                    "error": f"User {user_id} not found",
                }
            
            if not user.household_id:
                return {
                    "success": False,
                    "error": "User is not part of a household",
                }
            
            # Send to all household members
            results = await self.whatsapp_service.send_to_household(
                household_id=user.household_id,
                message=message,
            )
            
            # Count successful sends
            successful = sum(1 for sid in results.values() if sid is not None)
            total = len(results)
            
            return {
                "success": successful > 0,
                "message": f"Sent WhatsApp message to {successful}/{total} household members",
                "sent_to": successful,
                "total_members": total,
            }
        else:
            if not phone_number:
                return {
                    "success": False,
                    "error": "phone_number is required when to_household is False",
                }
            
            # Send to specific phone number
            message_sid = await self.whatsapp_service.send_message(
                to=phone_number,
                message=message,
            )
            
            if message_sid:
                return {
                    "success": True,
                    "message": f"WhatsApp message sent to {phone_number}",
                    "message_sid": message_sid,
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to send WhatsApp message to {phone_number}",
                }

