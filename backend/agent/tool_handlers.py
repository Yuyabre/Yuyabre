"""
Tool Handlers - Implementation of all agent tools.
"""
from typing import Any, Dict, List, Optional, Callable, Awaitable
from datetime import datetime
from loguru import logger

from modules.inventory import InventoryService
from modules.ordering import OrderingService
from modules.splitwise import SplitwiseService
from modules.whatsapp import WhatsAppService
from modules.discord import DiscordService
from models.user import User
from models.household import Household
from beanie.operators import In


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
        discord_service: Optional[DiscordService] = None,
        update_system_prompt_callback: Optional[Callable[[str], Awaitable[None]]] = None,
    ):
        """
        Initialize tool handlers.
        
        Args:
            inventory_service: Inventory service instance
            ordering_service: Ordering service instance
            splitwise_service: Splitwise service instance
            whatsapp_service: WhatsApp service instance
            discord_service: Discord service instance (optional)
            update_system_prompt_callback: Optional callback to update system prompt when preferences change
        """
        self.inventory_service = inventory_service
        self.ordering_service = ordering_service
        self.splitwise_service = splitwise_service
        self.whatsapp_service = whatsapp_service
        self.discord_service = discord_service or DiscordService()
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
            # Get household_id if user has one
            household_id = None
            if user and user.household_id:
                household_id = user.household_id
            
            products = await self.ordering_service.search_products(search_name, household_id=household_id)
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
    
    async def get_group_order_status(
        self,
        *,
        order_id: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return the latest status and responses for a group order."""
        if not order_id:
            return {"error": "order_id is required."}
        
        summary = await self.ordering_service.get_group_order_status(order_id)
        if not summary:
            return {"error": f"Order {order_id} not found."}
        
        return summary
    
    async def get_order_eta(
        self,
        *,
        order_id: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get the estimated time of arrival (ETA) for a delivery order.
        
        Args:
            order_id: Order ID
            user_id: User ID (automatically provided)
            
        Returns:
            Dict with ETA information
        """
        if not order_id:
            return {"error": "order_id is required."}
        
        result = await self.ordering_service.get_order_eta(
            order_id=order_id,
            user_id=user_id,
        )
        
        return result
    
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
                # Preserve the original user_id to track who originally owned/created the item
                # Only set user_id if the item doesn't have one (edge case - shouldn't happen for personal items)
                if not item.user_id:
                    update_fields["user_id"] = user_id
                # If item already has a user_id, we don't include it in update_fields
                # so it remains unchanged (preserving the original owner)
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
    
    async def get_housemates(
        self,
        *,
        user_id: Optional[str] = None,
        include_contact_info: bool = True,
    ) -> Dict[str, Any]:
        """
        Get a list of all housemates in the user's household.
        
        Args:
            user_id: ID of the user (required)
            include_contact_info: Whether to include phone numbers and email addresses
            
        Returns:
            Dict with list of housemates and their information
        """
        if not user_id:
            return {
                "error": "User ID is required to get housemates",
            }
        
        # Get user to find household
        user = await User.find_one(User.user_id == user_id)
        if not user:
            return {
                "error": f"User not found: {user_id}",
            }
        
        if not user.household_id:
            return {
                "housemates": [],
                "household": None,
                "message": "User is not part of a household",
            }
        
        # Get household
        household = await Household.find_one(Household.household_id == user.household_id)
        if not household:
            return {
                "housemates": [],
                "household": None,
                "message": "Household not found",
            }
        
        # Get all household members
        if not household.member_ids:
            return {
                "housemates": [],
                "household": {
                    "name": household.name,
                    "household_id": household.household_id,
                },
                "message": "No housemates found",
            }
        
        # Fetch all user details
        users = await User.find(
            In(User.user_id, household.member_ids),
            User.is_active == True
        ).to_list()
        
        housemates = []
        for housemate in users:
            housemate_info = {
                "user_id": housemate.user_id,
                "name": housemate.name,
                "is_current_user": housemate.user_id == user_id,
            }
            
            if include_contact_info:
                if housemate.phone:
                    housemate_info["phone"] = housemate.phone
                if housemate.email:
                    housemate_info["email"] = housemate.email
            
            housemates.append(housemate_info)
        
        return {
            "housemates": housemates,
            "household": {
                "name": household.name,
                "household_id": household.household_id,
                "total_members": len(housemates),
            },
            "count": len(housemates),
        }
    
    async def send_discord_message(
        self,
        message: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a Discord message to the household's Discord channel.
        
        Args:
            message: The message content to send
            user_id: ID of the user (required)
            
        Returns:
            Dict with success status and details
        """
        if not self.discord_service.is_configured():
            return {
                "success": False,
                "error": "Discord service is not configured. Please configure Discord bot token.",
            }
        
        if not user_id:
            return {
                "success": False,
                "error": "user_id is required when sending Discord message",
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
        
        # Get household
        household = await Household.find_one(Household.household_id == user.household_id)
        if not household:
            return {
                "success": False,
                "error": f"Household not found for user {user_id}",
            }
        
        if not household.discord_channel_id:
            return {
                "success": False,
                "error": "Household does not have a Discord channel configured. Please configure discord_channel_id in the household settings.",
            }
        
        # Send to Discord channel
        logger.info(f"Sending Discord message to household {household.household_id}, channel {household.discord_channel_id}")
        logger.debug(f"Message: {message}")
        
        results = await self.discord_service.send_to_household(
            household_id=household.household_id,
            message=message,
            initiated_by_user_id=user.user_id,
            metadata={
                "source": "manual_discord_message",
                "initiated_at": datetime.utcnow().isoformat(),
            },
        )
        
        message_id = next((mid for mid in results.values() if mid is not None and mid != "webhook"), None)
        context_id = results.get("context_id")
        
        if message_id or context_id:
            logger.info(f"Discord message sent successfully. Message ID: {message_id}, Context ID: {context_id}")
            return {
                "success": True,
                "message": f"Discord message sent to household channel",
                "message_id": message_id,
                "context_id": context_id,  # Return context_id so agent can check responses
            }
        else:
            logger.error(f"Failed to send Discord message to channel {household.discord_channel_id}")
            logger.error("Check logs above for detailed error information")
            return {
                "success": False,
                "error": "Failed to send Discord message. Check server logs for details. Possible causes: bot not ready, invalid channel ID, or missing permissions.",
            }
    
    async def check_discord_message_responses(
        self,
        context_id: Optional[str] = None,
        message_id: Optional[int] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Check responses to a Discord message sent in the current session.
        
        Args:
            context_id: The context ID returned from send_discord_message
            message_id: The Discord message ID (alternative to context_id)
            user_id: ID of the user (required to filter by user)
            
        Returns:
            Dict with response information
        """
        if not self.discord_service.is_configured():
            return {
                "found": False,
                "error": "Discord service is not configured.",
            }
        
        if not user_id:
            return {
                "found": False,
                "error": "user_id is required to check Discord message responses",
            }
        
        if not context_id and not message_id:
            return {
                "found": False,
                "error": "Either context_id or message_id must be provided",
            }
        
        # Get responses from Discord service
        result = await self.discord_service.get_message_responses(
            context_id=context_id,
            message_id=message_id,
            user_id=user_id,
        )
        
        return result
    
    async def create_splitwise_expense(
        self,
        description: str,
        amount: float,
        notes: Optional[str] = None,
        category: str = "Groceries",
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new expense in Splitwise to split costs with household members.
        
        Args:
            description: Description of the expense
            amount: Total amount of the expense
            notes: Optional additional notes
            category: Expense category (default: "Groceries")
            user_id: ID of the user creating the expense
            
        Returns:
            Dict with success status and expense details
        """
        if not user_id:
            return {
                "success": False,
                "error": "User ID is required to create Splitwise expense",
            }
        
        # Get user to check authorization and get household
        user = await User.find_one(User.user_id == user_id)
        if not user:
            return {
                "success": False,
                "error": f"User {user_id} not found",
            }
        
        # Check if user has Splitwise OAuth tokens
        if not user.splitwise_access_token or not user.splitwise_access_token_secret:
            return {
                "success": False,
                "error": "User is not authorized with Splitwise. Please connect your Splitwise account first.",
            }
        
        # Check if user has a household
        if not user.household_id:
            return {
                "success": False,
                "error": "User is not part of a household. Cannot create shared expense.",
            }
        
        # Get household to check for splitwise_group_id
        household = await Household.find_one(Household.household_id == user.household_id)
        if not household:
            return {
                "success": False,
                "error": f"Household {user.household_id} not found",
            }
        
        # Check if household has a Splitwise group configured
        if not household.splitwise_group_id:
            return {
                "success": False,
                "error": "Household does not have a Splitwise group configured. Please configure splitwise_group_id in household settings.",
            }
        
        # Get current user's Splitwise user ID from API if not in DB
        current_user_splitwise_id = user.splitwise_user_id
        if not current_user_splitwise_id:
            logger.info(f"User {user_id} has OAuth tokens but no splitwise_user_id in DB. Fetching from API...")
            current_user_splitwise_id = await self.splitwise_service.get_current_user_id(
                user_id=user_id,
                access_token=user.splitwise_access_token,
                access_token_secret=user.splitwise_access_token_secret,
            )
            if current_user_splitwise_id:
                # Update user in DB with the fetched Splitwise user ID
                user.splitwise_user_id = current_user_splitwise_id
                await user.save()
                logger.info(f"Updated user {user_id} with Splitwise user ID: {current_user_splitwise_id}")
        
        # Get group members from Splitwise API
        logger.info(f"Fetching group members from Splitwise group {household.splitwise_group_id}")
        group_members = await self.splitwise_service.get_group_members(
            user_id=user_id,
            access_token=user.splitwise_access_token,
            access_token_secret=user.splitwise_access_token_secret,
            group_id=household.splitwise_group_id,
        )
        
        if not group_members:
            return {
                "success": False,
                "error": f"Could not retrieve members from Splitwise group {household.splitwise_group_id}. The group may not exist or you may not have access.",
            }
        
        # Extract Splitwise user IDs from group members
        splitwise_user_ids = [member["id"] for member in group_members if member.get("id")]
        
        # Ensure current user is included
        if current_user_splitwise_id and current_user_splitwise_id not in splitwise_user_ids:
            splitwise_user_ids.append(current_user_splitwise_id)
        
        if not splitwise_user_ids:
            return {
                "success": False,
                "error": "No members found in Splitwise group.",
            }
        
        # Check if we have at least 2 users (required for splitting)
        if len(splitwise_user_ids) < 2:
            return {
                "success": False,
                "error": f"Splitwise group has only {len(splitwise_user_ids)} member(s). At least 2 members are required to split an expense. Please add more members to your Splitwise group.",
            }
        
        if amount <= 0:
            return {
                "success": False,
                "error": "Expense amount must be greater than zero",
            }
        
        try:
            # Create expense using user's OAuth tokens
            expense_id = await self.splitwise_service.create_user_expense(
                user_id=user_id,
                access_token=user.splitwise_access_token,
                access_token_secret=user.splitwise_access_token_secret,
                description=description,
                amount=amount,
                splitwise_user_ids=splitwise_user_ids,
                group_id=household.splitwise_group_id,
                category=category,
                date=None,  # Use current date
                notes=notes,
                split_method="equal",
                paid_by_user_id=current_user_splitwise_id if current_user_splitwise_id else None,
            )
            
            if expense_id:
                logger.info(
                    f"Created Splitwise expense {expense_id} for user {user_id}: "
                    f"{description} (€{amount:.2f}) in group {household.splitwise_group_id}"
                )
                return {
                    "success": True,
                    "expense_id": expense_id,
                    "description": description,
                    "amount": amount,
                    "split_among": len(splitwise_user_ids),
                    "group_id": household.splitwise_group_id,
                    "message": f"Expense '{description}' (€{amount:.2f}) created successfully and split equally among {len(splitwise_user_ids)} household member(s).",
                }
            else:
                logger.warning(f"Failed to create Splitwise expense for user {user_id}")
                return {
                    "success": False,
                    "error": "Failed to create expense in Splitwise. Check server logs for details.",
                }
                
        except Exception as e:
            logger.error(f"Error creating Splitwise expense for user {user_id}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return {
                "success": False,
                "error": f"Error creating Splitwise expense: {str(e)}",
            }
    
    async def get_splitwise_expenses(
        self,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get all expenses from Splitwise for the current user.
        
        Args:
            user_id: ID of the user requesting the expenses
            
        Returns:
            Dict with list of expenses or error message
        """
        if not user_id:
            return {
                "success": False,
                "error": "User ID is required to get Splitwise expenses",
            }
        
        # Get user to check authorization
        user = await User.find_one(User.user_id == user_id)
        if not user:
            return {
                "success": False,
                "error": f"User {user_id} not found",
            }
        
        # Check if user has Splitwise OAuth tokens
        if not user.splitwise_access_token or not user.splitwise_access_token_secret:
            return {
                "success": False,
                "error": "User is not authorized with Splitwise. Please connect your Splitwise account first.",
            }
        
        try:
            # Get all expenses using Splitwise service
            expenses_data = await self.splitwise_service.get_user_expenses(
                user_id=user_id,
                access_token=user.splitwise_access_token,
                access_token_secret=user.splitwise_access_token_secret,
            )
            
            logger.info(f"Successfully retrieved {len(expenses_data)} Splitwise expenses for user {user_id}")
            return {
                "success": True,
                "expenses": expenses_data,
                "count": len(expenses_data),
            }
                
        except Exception as e:
            logger.error(f"Error getting Splitwise expenses for user {user_id}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return {
                "success": False,
                "error": f"Error retrieving Splitwise expenses: {str(e)}",
            }

