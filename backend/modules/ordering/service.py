"""
Ordering Service - Integration with Thuisbezorgd for grocery ordering.

NOTE: This is a skeleton implementation. The actual integration will depend on
whether Thuisbezorgd provides an API or requires web scraping.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger
import math

from models.order import Order, OrderItem, OrderStatus
from models.inventory import InventoryItem
from models.user import User
from models.household import Household
from models.store import Store
from modules.whatsapp import WhatsAppService
from modules.discord import DiscordService
from modules.user_inventory.service import UserInventoryService
from modules.splitwise import SplitwiseService
from modules.grocery_stores import GroceryStoreService
from beanie.operators import In
from config import settings
from utils.cache import get_order_cache, cached_query


class OrderingService:
    """
    Service class for managing grocery orders through Thuisbezorgd.
    
    This is a skeleton implementation that needs to be completed based on
    the available integration method (API or web scraping).
    """
    
    def __init__(self):
        """Initialize ordering service."""
        self.base_url = settings.thuisbezorgd_api_url
        self.email = settings.thuisbezorgd_email
        self.password = settings.thuisbezorgd_password
        self.cache = get_order_cache()
        self.whatsapp_service = WhatsAppService()
        try:
            from api.dependencies import discord_service as shared_discord_service
            self.discord_service = shared_discord_service
        except ImportError:
            logger.warning("OrderingService: Shared DiscordService not available, creating local instance")
            self.discord_service = DiscordService()
        self.user_inventory_service = UserInventoryService()
        self.splitwise_service = SplitwiseService()
        self.grocery_store_service = GroceryStoreService()
        self._preferred_store_cache: Dict[str, str] = {}
        logger.info("Ordering service initialized with cache")
    
    async def _invalidate_cache(self) -> None:
        """Invalidate all order cache entries."""
        await self.cache.invalidate("order")

    def _log_db_query(self, operation: str, **details: Any) -> None:
        """
        Log MongoDB queries executed through the ordering service.
        """
        logger.debug("[MongoDB] orders.{} | {}", operation, details)
    
    async def _create_splitwise_expense_for_order(self, order: Order) -> Optional[str]:
        """
        Create a Splitwise expense for an order if the household has a Splitwise group configured.
        
        Args:
            order: The order to create an expense for
            
        Returns:
            Splitwise expense ID if successful, None otherwise
        """
        # Check if order has a household
        if not order.household_id:
            logger.debug(f"Order {order.order_id} has no household_id, skipping Splitwise expense")
            return None
        
        # Get household to check for splitwise_group_id
        household = await Household.find_one(Household.household_id == order.household_id)
        if not household:
            logger.debug(f"Household {order.household_id} not found for order {order.order_id}")
            return None
        
        # Check if household has a Splitwise group configured
        if not household.splitwise_group_id:
            logger.debug(f"Household {order.household_id} has no splitwise_group_id, skipping Splitwise expense")
            return None
        
        # Get the user who created the order (they need OAuth tokens)
        if not order.created_by:
            logger.warning(f"Order {order.order_id} has no created_by user, cannot create Splitwise expense")
            return None
        
        creator = await User.find_one(User.user_id == order.created_by)
        if not creator:
            logger.warning(f"Creator user {order.created_by} not found for order {order.order_id}")
            return None
        
        # Check if creator has Splitwise OAuth tokens
        if not creator.splitwise_access_token or not creator.splitwise_access_token_secret:
            logger.debug(f"Creator {order.created_by} has no Splitwise OAuth tokens, skipping Splitwise expense")
            return None
        
        # Get current user's Splitwise user ID from API if not in DB
        current_user_splitwise_id = creator.splitwise_user_id
        if not current_user_splitwise_id:
            logger.info(f"Creator {order.created_by} has OAuth tokens but no splitwise_user_id in DB. Fetching from API...")
            current_user_splitwise_id = await self.splitwise_service.get_current_user_id(
                user_id=order.created_by,
                access_token=creator.splitwise_access_token,
                access_token_secret=creator.splitwise_access_token_secret,
            )
            if current_user_splitwise_id:
                # Update creator in DB with the fetched Splitwise user ID
                creator.splitwise_user_id = current_user_splitwise_id
                await creator.save()
                logger.info(f"Updated creator {order.created_by} with Splitwise user ID: {current_user_splitwise_id}")
        
        # Get group members from Splitwise API
        logger.info(f"Fetching group members from Splitwise group {household.splitwise_group_id}")
        group_members = await self.splitwise_service.get_group_members(
            user_id=order.created_by,
            access_token=creator.splitwise_access_token,
            access_token_secret=creator.splitwise_access_token_secret,
            group_id=household.splitwise_group_id,
        )
        
        if not group_members:
            logger.warning(f"Could not retrieve members from Splitwise group {household.splitwise_group_id} for order {order.order_id}")
            return None
        
        # Extract Splitwise user IDs from group members
        splitwise_user_ids = [member["id"] for member in group_members if member.get("id")]
        
        # Ensure creator is included
        if current_user_splitwise_id and current_user_splitwise_id not in splitwise_user_ids:
            splitwise_user_ids.append(current_user_splitwise_id)
        
        if not splitwise_user_ids:
            logger.debug(f"No members found in Splitwise group {household.splitwise_group_id} for order {order.order_id}")
            return None
        
        # Check if we have at least 2 users (required for splitting)
        if len(splitwise_user_ids) < 2:
            logger.warning(
                f"Splitwise group {household.splitwise_group_id} has only {len(splitwise_user_ids)} member(s). "
                f"At least 2 members are required to split an expense. Skipping expense creation for order {order.order_id}."
            )
            return None
        
        # Create expense description
        items_summary = ", ".join([item.name for item in order.items[:3]])
        if len(order.items) > 3:
            items_summary += f" and {len(order.items) - 3} more"
        description = f"Grocery Order #{order.order_id[:8]}: {items_summary}"
        
        # Create notes with order details
        notes = f"Order ID: {order.order_id}\n"
        notes += f"Service: {order.service}\n"
        if order.delivery_address:
            notes += f"Delivery: {order.delivery_address}\n"
        if order.notes:
            notes += f"Notes: {order.notes}"
        
        try:
            # Create expense using creator's OAuth tokens
            expense_id = await self.splitwise_service.create_user_expense(
                user_id=order.created_by,
                access_token=creator.splitwise_access_token,
                access_token_secret=creator.splitwise_access_token_secret,
                description=description,
                amount=order.total,
                splitwise_user_ids=splitwise_user_ids,
                group_id=household.splitwise_group_id,
                category="Groceries",
                date=order.timestamp,
                notes=notes,
                split_method="equal",
                paid_by_user_id=current_user_splitwise_id if current_user_splitwise_id else None,
            )
            
            if expense_id:
                logger.info(
                    f"Created Splitwise expense {expense_id} for order {order.order_id} "
                    f"(€{order.total:.2f}) in group {household.splitwise_group_id}"
                )
                return expense_id
            else:
                logger.warning(f"Failed to create Splitwise expense for order {order.order_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating Splitwise expense for order {order.order_id}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    async def search_products(
        self,
        query: str,
        household_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for products, checking nearest store inventory first, then fallback.
        
        Args:
            query: Search query (e.g., "milk", "eggs")
            household_id: Optional household ID to search in nearest stores
            
        Returns:
            List of product dictionaries with id, name, price, etc.
        """
        logger.info(f"Searching for products: {query}")
        
        # First, try to find products in nearest stores' cached inventory
        if household_id:
            try:
                preferred_store = await self._get_preferred_store(household_id)
                if preferred_store:
                    store_products = await self._search_products_in_store(
                        store=preferred_store,
                        query=query,
                        max_results=10,
                    )

                    if store_products:
                        logger.info(
                            f"Found {len(store_products)} products in preferred store "
                            f"{preferred_store.name} for '{query}'"
                        )
                        return store_products
            except Exception as e:
                logger.warning(f"Error searching store inventory: {e}, falling back to default search")
        
        # Fallback: Search in Flink mock menu
        logger.debug(f"Using Flink mock menu fallback for '{query}'")
        flink_products = await self._search_flink_mock_menu(query)
        
        if flink_products:
            logger.info(f"Found {len(flink_products)} products in Flink mock menu for '{query}'")
            return flink_products
        
        # Final fallback: return placeholder
        logger.warning(f"No products found in Flink mock menu for '{query}', using placeholder")
        return [
            {
                "product_id": "prod_123",
                "name": f"{query.capitalize()} - Sample Product",
                "description": "Sample product description",
                "price": 2.99,
                "unit": "piece",
                "available": True,
                "brand": "Sample Brand",
                "image_url": "https://example.com/image.jpg",
                "source": "fallback",
            }
        ]
    
    async def get_product_details(self, product_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific product.
        
        Args:
            product_id: Product ID (can be from Flink mock menu or other sources)
            
        Returns:
            Product details dictionary or None if not found
        """
        logger.info(f"Getting product details: {product_id}")
        
        # Try to find in Flink mock menu
        try:
            import json
            from pathlib import Path
            
            # Get the path to the flink_mock_menu.json file
            current_dir = Path(__file__).parent.parent
            flink_menu_path = current_dir / "grocery_stores" / "flink_mock_menu.json"
            
            if flink_menu_path.exists():
                # Load JSON file (cache it to avoid reloading every time)
                if not hasattr(self, '_flink_menu_cache'):
                    with open(flink_menu_path, 'r', encoding='utf-8') as f:
                        self._flink_menu_cache = json.load(f)
                
                items = self._flink_menu_cache.get('items', [])
                
                # Find product by ID
                for item in items:
                    if item.get('product_id') == product_id:
                        # Convert unit format
                        unit_obj = item.get('unit')
                        if unit_obj is None:
                            unit_str = "piece"
                        elif isinstance(unit_obj, dict):
                            unit_value = unit_obj.get('Value', 1.0)
                            unit_type = unit_obj.get('Unit', 'piece')
                            if unit_type:
                                unit_str = f"{unit_value} {unit_type}" if unit_value != 1.0 else unit_type
                            else:
                                unit_str = "piece"
                        else:
                            unit_str = str(unit_obj)
                        
                        return {
                            "product_id": item.get('product_id', ''),
                            "name": item.get('name', ''),
                            "description": f"{item.get('brand', '')} {item.get('name', '')}".strip(),
                            "price": item.get('price', 0.0),
                            "unit": unit_str,
                            "available": item.get('available', True),
                            "brand": item.get('brand'),
                            "category": item.get('category'),
                            "source": "flink_mock_menu",
                        }
        except Exception as e:
            logger.warning(f"Error looking up product in Flink mock menu: {e}")
        
        # Fallback: return placeholder
        logger.debug(f"Product {product_id} not found in Flink mock menu, using placeholder")
        return {
            "product_id": product_id,
            "name": "Sample Product",
            "description": "Sample description",
            "price": 2.99,
            "unit": "piece",
            "available": True,
            "brand": "Sample Brand",
            "source": "fallback",
        }
    
    async def create_order(
        self,
        items: List[Dict[str, any]],
        delivery_address: str,
        delivery_time: Optional[datetime] = None,
        notes: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> Optional[Order]:
        """
        Create and place an order on Thuisbezorgd.
        
        If any items are marked as shared, creates a group order and sends
        WhatsApp notifications to household members.
        
        Args:
            items: List of items to order, each with product_id, quantity, etc.
            delivery_address: Delivery address
            delivery_time: Preferred delivery time
            notes: Additional notes for the order
            created_by: User ID who created the order
            
        Returns:
            Created Order object if successful, None otherwise
        """
        logger.info(f"Creating order with {len(items)} items")
        
        try:
            # Get user and household info
            user = None
            household = None
            if created_by:
                try:
                    user = await User.find_one(User.user_id == created_by)
                    if user:
                        # Safely get household_id
                        user_household_id = getattr(user, 'household_id', None)
                        if user_household_id:
                            household = await Household.find_one(
                                Household.household_id == user_household_id
                            )
                except Exception as e:
                    logger.warning(f"Error fetching user/household: {e}")
                    user = None
                    household = None
            
            # Check if any items are shared (must check in household context)
            shared_items = []
            household_id_for_check = None
            if household and hasattr(household, 'household_id'):
                household_id_for_check = household.household_id
            
            # Import inventory service for flexible searching
            from modules.inventory import InventoryService
            inventory_service = InventoryService()
            
            for item_data in items:
                item_name = item_data.get("name", "")
                # Check if we have the inventory item name from the tool handler
                inventory_item_name = item_data.get("_inventory_item_name")
                
                # Normalize item name - remove common suffixes
                normalized_name = item_name.lower().strip()
                # Remove " - sample product" variations
                normalized_name = normalized_name.replace(" - sample product", "").strip()
                base_name = normalized_name.split(" - ")[0].strip()
                
                # Check if item exists in inventory and is shared (scoped to household)
                inventory_item = None
                
                # First, try using the inventory item name if provided
                if inventory_item_name and household_id_for_check:
                    # Use inventory service method which handles queries correctly
                    inventory_item = await inventory_service.get_item_by_name(
                        name=inventory_item_name,
                        household_id=household_id_for_check
                    )
                
                # If not found, try flexible matching
                if not inventory_item and household_id_for_check:
                    # Get all shared items in household for flexible matching
                    # Use inventory service which handles queries correctly
                    all_items = await inventory_service.get_all_items(household_id=household_id_for_check)
                    all_shared_items = [item for item in all_items if item.shared]
                    
                    # Try to find a match using flexible name comparison
                    for inv_item in all_shared_items:
                        inv_name_lower = inv_item.name.lower().strip()
                        inv_base = inv_name_lower.split(" - ")[0].strip()
                        
                        # Check if base names match (case-insensitive)
                        if base_name == inv_base or normalized_name == inv_name_lower:
                            inventory_item = inv_item
                            break
                        
                        # Also check if the base name is contained in either direction
                        if base_name in inv_name_lower or inv_base in normalized_name:
                            inventory_item = inv_item
                            break
                elif not inventory_item:
                    # Fallback: check globally (backward compatibility)
                    # Use search_items for more flexible matching
                    matches = await inventory_service.search_items(base_name)
                    if matches:
                        # Check if any match is shared
                        for match in matches:
                            if match.shared:
                                inventory_item = match
                                break
                
                if inventory_item and inventory_item.shared:
                    shared_items.append(item_data)
                    logger.info(f"Item '{item_name}' matched to shared inventory item '{inventory_item.name}'")
            
            # Determine if this is a group order
            is_group_order = len(shared_items) > 0 and household is not None
            
            logger.info(
                f"Order group status check: shared_items={len(shared_items)}, "
                f"household={'exists' if household else 'None'}, "
                f"is_group_order={is_group_order}"
            )
            
            # Get household_id safely
            household_id_value = None
            if household and hasattr(household, 'household_id'):
                household_id_value = household.household_id
            
            # Extract store information from items (if available)
            store_id = None
            store_name = None
            store_location = None
            for item_data in items:
                if item_data.get("store_id"):
                    store_id = item_data.get("store_id")
                    store_name = item_data.get("store_name")
                    # Try to get store location from grocery store service
                    if store_id:
                        try:
                            from models.store import Store
                            store = await Store.find_one(Store.store_id == store_id)
                            if store and store.location:
                                store_location = {
                                    "latitude": store.location.latitude,
                                    "longitude": store.location.longitude,
                                }
                        except Exception as e:
                            logger.debug(f"Could not fetch store location: {e}")
                    break
            
            # Calculate estimated delivery time and distance if we have store and household location
            estimated_delivery_time = None
            distance_km = None
            if store_location and household:
                try:
                    # Get household location (would need geocoding in real implementation)
                    # For now, use city/postal_code to estimate
                    household_location = await self._get_household_location(household)
                    if household_location:
                        distance_km = self._calculate_distance(
                            store_location["latitude"],
                            store_location["longitude"],
                            household_location["latitude"],
                            household_location["longitude"],
                        )
                        # Estimate delivery time: base 10 min + 2 min per km
                        estimated_minutes = 10 + (distance_km * 2)
                        estimated_delivery_time = datetime.utcnow() + timedelta(minutes=int(estimated_minutes))
                except Exception as e:
                    logger.debug(f"Could not calculate delivery time: {e}")
            
            # Create Order object
            order = Order(
                service="Thuisbezorgd",
                delivery_address=delivery_address,
                delivery_time=delivery_time,
                notes=notes,
                created_by=created_by,
                status=OrderStatus.PENDING,
                is_group_order=is_group_order,
                household_id=household_id_value,
                store_id=store_id,
                store_name=store_name,
                store_location=store_location,
                estimated_delivery_time=estimated_delivery_time,
                distance_km=distance_km,
            )
            
            # Add items to order
            for item_data in items:
                order_item = OrderItem(
                    product_id=item_data["product_id"],
                    name=item_data["name"],
                    quantity=item_data["quantity"],
                    unit=item_data.get("unit", "piece"),
                    price=item_data["price"],
                    total_price=item_data["price"] * item_data["quantity"],
                    requested_by=item_data.get("requested_by", [created_by] if created_by else []),
                )
                order.add_item(order_item)
            
            # If group order, set up pending responses
            if is_group_order and household and hasattr(household, 'member_ids'):
                # Set response deadline (e.g., 2 hours from now)
                order.response_deadline = datetime.utcnow() + timedelta(hours=2)
                
                # Get all household members except creator
                member_ids = getattr(household, 'member_ids', [])
                pending_users = [
                    uid for uid in member_ids
                    if uid != created_by
                ]
                
                # Mark which items need responses
                for item_data in shared_items:
                    item_name = item_data.get("name", "")
                    order.pending_responses[item_name] = pending_users.copy()
            
            # Calculate delivery fee (placeholder - should come from Thuisbezorgd)
            order.delivery_fee = 2.50
            order.calculate_total()
            
            # Save order to database
            self._log_db_query(
                "insert_one",
                payload={
                    "order_id": order.order_id,
                    "items": [
                        {"name": item["name"], "quantity": item["quantity"]}
                        for item in items
                    ],
                    "created_by": created_by,
                    "is_group_order": is_group_order,
                },
            )
            await order.insert()
            
            # Send notification if group order (try Discord first, fallback to WhatsApp)
            if is_group_order and household and hasattr(household, 'household_id'):
                # Build items for message with price information from order items
                items_for_message = []
                for shared_item in shared_items:
                    shared_item_name = shared_item.get("name", "")
                    # Find matching order item to get price
                    order_item = None
                    for oi in order.items:
                        # Match by name (normalize for comparison)
                        oi_name_normalized = oi.name.lower().replace(" - sample product", "").strip()
                        shared_name_normalized = shared_item_name.lower().replace(" - sample product", "").strip()
                        if oi_name_normalized == shared_name_normalized or oi.name == shared_item_name:
                            order_item = oi
                            break
                    
                    item_data = {
                        "name": shared_item.get("name", ""),
                        "quantity": shared_item.get("quantity", 0),
                        "unit": shared_item.get("unit", "piece")
                    }
                    
                    # Add price if available from order item
                    if order_item:
                        item_data["price"] = order_item.price
                    
                    items_for_message.append(item_data)
                
                # Get household_id safely
                hh_id = getattr(household, 'household_id', None)
                success = False
                message_sent_via = None
                
                # Try Discord first if configured
                if hh_id and household.discord_channel_id and self.discord_service.is_configured():
                    success = await self.discord_service.send_group_order_notification(
                        household_id=hh_id,
                        order_id=order.order_id,
                        items=items_for_message,
                        created_by_user=created_by or "",
                        response_deadline=order.response_deadline or datetime.utcnow(),
                    )
                    message_sent_via = "discord" if success else None
                
                # Fallback to WhatsApp if Discord failed or not configured
                if not success and hh_id and self.whatsapp_service.is_configured():
                    success = await self.whatsapp_service.send_group_order_notification(
                        household_id=hh_id,
                        order_id=order.order_id,
                        items=items_for_message,
                        created_by_user=created_by or "",
                        response_deadline=order.response_deadline or datetime.utcnow(),
                    )
                    message_sent_via = "whatsapp" if success else None
                
                if not success:
                    logger.warning(
                        f"Group order {order.order_id} created but no messaging service is configured. "
                        f"Order will be created as group order but no notification will be sent."
                    )
                
                order.whatsapp_message_sent = success  # Keep field name for backward compatibility
                await order.save()
                
                if success:
                    logger.info(f"Group order notification sent via {message_sent_via} for order {order.order_id}")
                else:
                    logger.warning(f"Failed to send group order notification for order {order.order_id}")
            
            # For group orders, keep status as PENDING until responses are collected
            # For regular orders, mark as confirmed and create Splitwise expense
            if not is_group_order:
                order.status = OrderStatus.CONFIRMED
                order.external_order_id = "TB_" + order.order_id[:8]
                await order.save()
                
                # Create Splitwise expense if household has splitwise_group_id
                expense_id = await self._create_splitwise_expense_for_order(order)
                if expense_id:
                    order.splitwise_expense_id = expense_id
                    await order.save()
            
            await self._invalidate_cache()
            
            logger.info(
                f"Order created successfully: {order.order_id} "
                f"(Total: €{order.total:.2f}, Group: {is_group_order})"
            )
            return order
            
        except Exception as e:
            import traceback
            logger.error(f"Failed to create order: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    @cached_query("order", get_order_cache)
    async def get_order_status(self, order_id: str) -> Optional[OrderStatus]:
        """
        Check the status of an order.
        
        Args:
            order_id: Internal order ID
            
        Returns:
            OrderStatus if found, None otherwise
            
        TODO: Implement actual status checking from Thuisbezorgd
        """
        self._log_db_query("find_one", filters={"order_id": order_id})
        order = await Order.find_one(Order.order_id == order_id)
        if not order:
            logger.warning(f"Order not found: {order_id}")
            return None
        
        # PLACEHOLDER: Check status with Thuisbezorgd
        # This should query the external service for real-time status
        
        return order.status
    
    async def update_order_status(
        self,
        order_id: str,
        new_status: OrderStatus
    ) -> Optional[Order]:
        """
        Update the status of an order.
        
        Args:
            order_id: Internal order ID
            new_status: New order status
            
        Returns:
            Updated Order object if successful, None otherwise
        """
        self._log_db_query("find_one", filters={"order_id": order_id})
        order = await Order.find_one(Order.order_id == order_id)
        if not order:
            logger.warning(f"Order not found: {order_id}")
            return None
        
        old_status = order.status
        order.status = new_status
        self._log_db_query(
            "update_one",
            filters={"order_id": order_id},
            updates={"status": new_status.value},
        )
        await order.save()
        await self._invalidate_cache()
        
        logger.info(f"Order {order_id} status updated: {old_status} -> {new_status}")
        return order
    
    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.
        
        Args:
            order_id: Internal order ID
            
        Returns:
            True if successful, False otherwise
            
        TODO: Implement actual order cancellation with Thuisbezorgd
        """
        self._log_db_query("find_one", filters={"order_id": order_id})
        order = await Order.find_one(Order.order_id == order_id)
        if not order:
            logger.warning(f"Order not found: {order_id}")
            return False
        
        if order.is_completed():
            logger.warning(f"Cannot cancel completed order: {order_id}")
            return False
        
        # PLACEHOLDER: Actually cancel order with Thuisbezorgd
        
        order.status = OrderStatus.CANCELLED
        self._log_db_query(
            "update_one",
            filters={"order_id": order_id},
            updates={"status": OrderStatus.CANCELLED.value},
        )
        await order.save()
        await self._invalidate_cache()
        
        logger.info(f"Order cancelled: {order_id}")
        return True
    
    async def process_group_order_response(
        self,
        order_id: str,
        user_id: str,
        responses: Dict[str, Any],
        response_event: Optional[Dict[str, Any]] = None,
    ) -> Optional[Order]:
        """
        Process a user's response to a group order.
        
        Args:
            order_id: Order ID
            user_id: User ID who responded
            responses: Response data with items user wants
            response_event: Optional event metadata to record for history
            
        Returns:
            Updated Order object if successful, None otherwise
        """
        order = await Order.find_one(Order.order_id == order_id)
        if not order:
            logger.warning(f"Order not found: {order_id}")
            return None
        
        if not order.is_group_order:
            logger.warning(f"Order {order_id} is not a group order")
            return order
        
        # Store user's response
        order.group_responses[user_id] = responses
        
        if response_event is not None:
            event_record = dict(response_event)
            event_record.setdefault("user_id", user_id)
            event_record.setdefault("timestamp", datetime.utcnow().isoformat())
            if "response" not in event_record:
                event_record["response"] = responses.get("confirmed")
            order.response_history.append(event_record)
        
        # Remove user from pending responses for items they responded to
        for item_name in list(order.pending_responses.keys()):
            if user_id in order.pending_responses[item_name]:
                order.pending_responses[item_name].remove(user_id)
        
        await order.save()
        await self._invalidate_cache()
        
        logger.info(f"Group order response processed for order {order_id} from user {user_id}")
        
        # Check if all responses are collected
        all_responses_collected = all(
            len(pending) == 0
            for pending in order.pending_responses.values()
        )
        
        # Also check if deadline has passed
        deadline_passed = (
            order.response_deadline is not None
            and datetime.utcnow() > order.response_deadline
        )
        
        if all_responses_collected or deadline_passed:
            # Update order with responses and finalize
            await self._finalize_group_order(order)
        
        return order

    async def get_group_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the latest status and response details for a group order.
        
        Args:
            order_id: Order identifier
        
        Returns:
            Dictionary summarizing order status and responses, or None if not found.
        """
        order = await Order.find_one(Order.order_id == order_id)
        if not order:
            logger.warning(f"Group order status requested for unknown order: {order_id}")
            return None
        
        return {
            "order_id": order.order_id,
            "status": order.status.value,
            "total": order.total,
            "created_at": order.timestamp.isoformat(),
            "created_by": order.created_by,
            "household_id": order.household_id,
            "is_group_order": order.is_group_order,
            "response_deadline": order.response_deadline.isoformat() if order.response_deadline else None,
            "pending_responses": order.pending_responses,
            "group_responses": order.group_responses,
            "response_history": order.response_history,
            "items": [
                {
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "price": item.price,
                    "requested_by": item.requested_by,
                }
                for item in order.items
            ],
        }
    
    async def _finalize_group_order(self, order: Order) -> None:
        """
        Finalize a group order by updating quantities based on responses.
        
        Args:
            order: Order to finalize
        """
        # Update item quantities based on responses
        for order_item in order.items:
            # Start with original quantity
            total_quantity = order_item.quantity
            
            # Add quantities from responses
            for user_id, response in order.group_responses.items():
                response_items = response.get("items", [])
                for resp_item in response_items:
                    if resp_item.get("name") == order_item.name:
                        total_quantity += resp_item.get("quantity", 0)
                        # Add user to requested_by list
                        if user_id not in order_item.requested_by:
                            order_item.requested_by.append(user_id)
            
            # Update order item quantity
            order_item.quantity = total_quantity
            order_item.total_price = order_item.price * total_quantity
        
        # Recalculate totals
        order.calculate_total()
        
        # Mark as confirmed
        order.status = OrderStatus.CONFIRMED
        order.external_order_id = "TB_" + order.order_id[:8]
        
        await order.save()
        await self._invalidate_cache()
        
        # Create Splitwise expense if household has splitwise_group_id
        expense_id = await self._create_splitwise_expense_for_order(order)
        if expense_id:
            order.splitwise_expense_id = expense_id
            await order.save()
        
        # Update user inventories for shared items
        for order_item in order.items:
            # Get all users who requested this item
            user_ids = order_item.requested_by
            if user_ids:
                await self.user_inventory_service.update_from_order(
                    order_item=order_item,
                    user_ids=user_ids,
                )
        
        # Send update to messaging service (Discord or WhatsApp)
        if order.household_id:
            update_message = (
                f"✅ Group order finalized!\n\n"
                f"Total: €{order.total:.2f}\n"
                f"Items updated based on responses.\n\n"
                f"Your individual inventories have been updated."
            )
            
            # Try Discord first
            household = await Household.find_one(Household.household_id == order.household_id)
            if household and household.discord_channel_id and self.discord_service.is_configured():
                await self.discord_service.send_order_update(
                    household_id=order.household_id,
                    order_id=order.order_id,
                    update_message=update_message,
                )
            elif self.whatsapp_service.is_configured():
                await self.whatsapp_service.send_order_update(
                    household_id=order.household_id,
                    order_id=order.order_id,
                    update_message=update_message,
                )
        
        logger.info(f"Group order {order.order_id} finalized")
    
    @cached_query("order", get_order_cache)
    async def get_order_history(self, limit: int = 20) -> List[Order]:
        """
        Get recent order history.
        
        Args:
            limit: Maximum number of orders to retrieve
            
        Returns:
            List of recent Orders
        """
        self._log_db_query(
            "find_all",
            filters={"sort": "-timestamp", "limit": limit},
        )
        orders = await Order.find_all().sort("-timestamp").limit(limit).to_list()
        return orders
    
    @cached_query("order", get_order_cache)
    async def get_orders_for_user(self, user_id: str, limit: int = 50) -> List[Order]:
        """
        Get all orders for a specific user.
        
        This includes:
        - Orders created by the user
        - Group orders from the user's household (if user is a member)
        
        Args:
            user_id: The user's unique identifier
            limit: Maximum number of orders to retrieve
            
        Returns:
            List of Orders relevant to the user
        """
        from models.user import User
        
        # Get user to find their household
        user = await User.find_one(User.user_id == user_id)
        if not user:
            logger.warning(f"User {user_id} not found when fetching orders")
            return []
        
        # Find orders where user created them
        created_orders = await Order.find(
            Order.created_by == user_id
        ).sort("-timestamp").limit(limit).to_list()
        
        # Also find group orders from user's household (if they have one)
        household_orders = []
        if user.household_id:
            household_orders = await Order.find(
                Order.household_id == user.household_id,
                Order.is_group_order == True
            ).sort("-timestamp").limit(limit).to_list()
        
        # Combine and deduplicate by order_id
        all_orders = {order.order_id: order for order in created_orders}
        for order in household_orders:
            if order.order_id not in all_orders:
                all_orders[order.order_id] = order
        
        # Sort by timestamp descending and limit
        sorted_orders = sorted(
            all_orders.values(),
            key=lambda o: o.timestamp,
            reverse=True
        )[:limit]
        
        self._log_db_query(
            "find_user_orders",
            filters={"user_id": user_id, "limit": limit, "count": len(sorted_orders)},
        )
        
        logger.info(f"Found {len(sorted_orders)} orders for user {user_id}")
        return sorted_orders
    
    async def _get_preferred_store(self, household_id: str) -> Optional[Store]:
        """
        Get (and cache) the preferred store for a household.
        
        Args:
            household_id: Household identifier
        
        Returns:
            Store object or None
        """
        cached_store_id = self._preferred_store_cache.get(household_id)
        if cached_store_id:
            store = await Store.find_one(Store.store_id == cached_store_id)
            if store:
                return store
            # Remove stale cache entry
            self._preferred_store_cache.pop(household_id, None)
        
        stores = await self.grocery_store_service.find_nearest_stores(
            household_id=household_id,
            limit=1,
        )
        if stores:
            store = stores[0]
            self._preferred_store_cache[household_id] = store.store_id
            return store
        return None
    
    async def _search_products_in_store(
        self,
        store: Store,
        query: str,
        max_results: int = 10,
    ) -> List[Dict]:
        """
        Search for products in a specific store's cached inventory.
        
        Args:
            store: Store object
            query: Search term
            max_results: Maximum number of results
        
        Returns:
            List of product dictionaries
        """
        if not store:
            return []
        
        try:
            if store.location and store.location.city and store.location.postal_code:
                postal_prefix = store.location.postal_code.split()[0] if store.location.postal_code and " " in store.location.postal_code else store.location.postal_code or ""
                locality_key = f"{store.location.city.lower()}_{postal_prefix.lower()}"
            else:
                locality_key = store.store_id  # Fallback locality key
            
            inventory = await self.grocery_store_service.get_or_fetch_store_inventory(
                store_id=store.store_id,
                locality_key=locality_key,
            )
            
            if not inventory or not inventory.products:
                return []
            
            query_lower = query.lower()
            matches: List[Dict[str, Any]] = []
            for product in inventory.products:
                name = product.name.lower()
                description = (product.description or "").lower()
                brand = (product.brand or "").lower()
                
                if query_lower in name or query_lower in description or query_lower in brand:
                    matches.append(
                        {
                            "product_id": product.product_id,
                            "name": product.name,
                            "description": product.description or "",
                            "price": product.price,
                            "unit": product.unit,
                            "available": product.available,
                            "brand": product.brand,
                            "image_url": product.image_url,
                            "store_id": store.store_id,
                            "store_name": store.name,
                            "store_chain": store.chain,
                            "source": "store_cache",
                            "last_updated_in_store_cache": inventory.last_updated.isoformat(),
                        }
                    )
                    
                    if len(matches) >= max_results:
                        break
            
            return matches
        except Exception as e:
            logger.warning(
                f"Failed to search products in store {store.store_id}: {e}",
                exc_info=True,
            )
            return []
    
    async def _search_flink_mock_menu(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search for products in the Flink mock menu JSON file.
        
        Args:
            query: Search query (e.g., "milk", "eggs")
            max_results: Maximum number of results to return
            
        Returns:
            List of product dictionaries
        """
        import json
        from pathlib import Path
        
        try:
            if not hasattr(self, "_flink_menu_cache"):
                current_dir = Path(__file__).parent.parent
                flink_menu_path = current_dir / "grocery_stores" / "flink_mock_menu.json"
                
                if not flink_menu_path.exists():
                    logger.warning(f"Flink mock menu file not found at {flink_menu_path}")
                    return []
                
                with open(flink_menu_path, "r", encoding="utf-8") as f:
                    self._flink_menu_cache = json.load(f)
                logger.debug(f"Loaded Flink mock menu with {len(self._flink_menu_cache.get('items', []))} items")
            
            items = self._flink_menu_cache.get("items", [])
            query_lower = query.lower()
            
            matches: List[Dict[str, Any]] = []
            for item in items:
                if not item.get("available", True):
                    continue
                
                name = item.get("name", "").lower()
                brand = (item.get("brand") or "").lower()
                category = (item.get("category") or "").lower()
                
                if query_lower in name or query_lower in brand or query_lower in category:
                    unit_obj = item.get("unit")
                    if unit_obj is None:
                        unit_str = "piece"
                    elif isinstance(unit_obj, dict):
                        unit_value = unit_obj.get("Value", 1.0)
                        unit_type = unit_obj.get("Unit", "piece")
                        if unit_type:
                            unit_str = f"{unit_value} {unit_type}" if unit_value != 1.0 else unit_type
                        else:
                            unit_str = "piece"
                    else:
                        unit_str = str(unit_obj)
                    
                    matches.append(
                        {
                            "product_id": item.get("product_id", ""),
                            "name": item.get("name", ""),
                            "description": f"{item.get('brand', '')} {item.get('name', '')}".strip(),
                            "price": item.get("price", 0.0),
                            "unit": unit_str,
                            "available": item.get("available", True),
                            "brand": item.get("brand"),
                            "category": item.get("category"),
                            "source": "flink_mock_menu",
                        }
                    )
                    
                    if len(matches) >= max_results:
                        break
            
            return matches
        except Exception as e:
            logger.error(f"Error searching Flink mock menu: {e}", exc_info=True)
            return []
    
    def _calculate_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """
        Calculate distance between two coordinates using Haversine formula.
        
        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
            
        Returns:
            Distance in kilometers
        """
        # Earth radius in kilometers
        R = 6371.0
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        # Haversine formula
        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1_rad)
            * math.cos(lat2_rad)
            * math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        
        return round(distance, 2)
    
    async def _get_household_location(self, household: Any) -> Optional[Dict[str, float]]:
        """
        Get household location coordinates.
        
        In a real implementation, this would geocode the address.
        For now, returns None if coordinates aren't available.
        
        Args:
            household: Household object
            
        Returns:
            Dict with latitude and longitude, or None
        """
        # TODO: Implement geocoding to convert address to coordinates
        # For now, return None - we'll need to add lat/lon to household model or geocode
        return None
    
    async def update_order_status_by_time(self, order: Order) -> Order:
        """
        Update order status based on elapsed time and distance.
        
        Status progression:
        - PENDING -> CONFIRMED (immediately after creation)
        - CONFIRMED -> PROCESSING (after 2 minutes)
        - PROCESSING -> OUT_FOR_DELIVERY (after 5 minutes or when estimated time approaches)
        - OUT_FOR_DELIVERY -> DELIVERED (when estimated time has passed)
        
        Args:
            order: Order object to update
            
        Returns:
            Updated Order object
        """
        if order.status == OrderStatus.DELIVERED or order.status == OrderStatus.CANCELLED:
            return order  # Don't update completed orders
        
        now = datetime.utcnow()
        elapsed = (now - order.timestamp).total_seconds() / 60  # minutes
        
        # Calculate estimated delivery time if not set
        if not order.estimated_delivery_time and order.distance_km:
            # Base 10 min + 2 min per km
            estimated_minutes = 10 + (order.distance_km * 2)
            order.estimated_delivery_time = order.timestamp + timedelta(minutes=int(estimated_minutes))
        
        # Status progression based on time
        if order.status == OrderStatus.PENDING:
            order.status = OrderStatus.CONFIRMED
        elif order.status == OrderStatus.CONFIRMED and elapsed >= 2:
            order.status = OrderStatus.PROCESSING
        elif order.status == OrderStatus.PROCESSING:
            # Move to out_for_delivery when we're close to estimated time or after 5 min
            if order.estimated_delivery_time:
                time_until_delivery = (order.estimated_delivery_time - now).total_seconds() / 60
                if time_until_delivery <= 15 or elapsed >= 5:  # 15 min before ETA or 5 min elapsed
                    order.status = OrderStatus.OUT_FOR_DELIVERY
            elif elapsed >= 5:
                order.status = OrderStatus.OUT_FOR_DELIVERY
        elif order.status == OrderStatus.OUT_FOR_DELIVERY:
            # Mark as delivered if estimated time has passed
            if order.estimated_delivery_time and now >= order.estimated_delivery_time:
                order.status = OrderStatus.DELIVERED
                if not order.delivery_time:
                    order.delivery_time = now
        
        await order.save()
        return order
    
    async def get_order_eta(
        self,
        order_id: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get estimated time of arrival (ETA) for an order.
        
        Args:
            order_id: Order ID
            user_id: Optional user ID for validation
            
        Returns:
            Dict with ETA information
        """
        order = await Order.find_one(Order.order_id == order_id)
        if not order:
            return {
                "found": False,
                "error": f"Order {order_id} not found",
            }
        
        # Validate user access if user_id provided
        if user_id:
            if order.created_by != user_id and order.household_id:
                # Check if user is in household
                household = await Household.find_one(Household.household_id == order.household_id)
                if not household or user_id not in household.member_ids:
                    return {
                        "found": False,
                        "error": "You don't have access to this order",
                    }
        
        # Update order status based on time
        order = await self.update_order_status_by_time(order)
        
        now = datetime.utcnow()
        
        # Calculate ETA
        if order.estimated_delivery_time:
            time_remaining = (order.estimated_delivery_time - now).total_seconds() / 60  # minutes
            if time_remaining <= 0:
                eta_minutes = 0
                eta_status = "delivered" if order.status == OrderStatus.DELIVERED else "arriving_soon"
            else:
                eta_minutes = int(time_remaining)
                eta_status = "in_transit" if order.status == OrderStatus.OUT_FOR_DELIVERY else "preparing"
        elif order.distance_km:
            # Calculate ETA based on distance
            estimated_minutes = 10 + (order.distance_km * 2)
            time_elapsed = (now - order.timestamp).total_seconds() / 60
            time_remaining = max(0, estimated_minutes - time_elapsed)
            eta_minutes = int(time_remaining)
            eta_status = "preparing" if order.status in [OrderStatus.CONFIRMED, OrderStatus.PROCESSING] else "in_transit"
        else:
            # No location data, estimate based on status
            if order.status == OrderStatus.PENDING or order.status == OrderStatus.CONFIRMED:
                eta_minutes = 30  # Default estimate
                eta_status = "preparing"
            elif order.status == OrderStatus.PROCESSING:
                eta_minutes = 20
                eta_status = "preparing"
            elif order.status == OrderStatus.OUT_FOR_DELIVERY:
                eta_minutes = 10
                eta_status = "in_transit"
            else:
                eta_minutes = 0
                eta_status = "delivered" if order.status == OrderStatus.DELIVERED else "unknown"
        
        return {
            "found": True,
            "order_id": order.order_id,
            "status": order.status.value,
            "eta_minutes": eta_minutes,
            "eta_status": eta_status,
            "estimated_delivery_time": order.estimated_delivery_time.isoformat() if order.estimated_delivery_time else None,
            "distance_km": order.distance_km,
            "store_name": order.store_name,
            "current_time": now.isoformat(),
            "order_placed_at": order.timestamp.isoformat(),
        }


class ThuisbezorgdScraper:
    """
    Web scraper for Thuisbezorgd if no API is available.
    
    This class would use Selenium or Playwright to automate browser interactions
    with Thuisbezorgd.nl for searching products and placing orders.
    
    TODO: Implement if API is not available
    """
    
    def __init__(self):
        """Initialize web scraper."""
        self.base_url = "https://www.thuisbezorgd.nl"
        logger.info("Thuisbezorgd scraper initialized (NOT IMPLEMENTED)")
    
    async def login(self, email: str, password: str) -> bool:
        """
        Login to Thuisbezorgd account.
        
        TODO: Implement login flow
        """
        logger.warning("Scraper login not implemented")
        return False
    
    async def _search_flink_mock_menu(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search for products in the Flink mock menu JSON file.
        
        Args:
            query: Search query (e.g., "milk", "eggs")
            max_results: Maximum number of results to return
            
        Returns:
            List of product dictionaries
        """
        import json
        import os
        from pathlib import Path
        
        try:
            # Get the path to the flink_mock_menu.json file
            current_dir = Path(__file__).parent.parent
            flink_menu_path = current_dir / "grocery_stores" / "flink_mock_menu.json"
            
            if not flink_menu_path.exists():
                logger.warning(f"Flink mock menu file not found at {flink_menu_path}")
                return []
            
            # Load JSON file (cache it to avoid reloading every time)
            if not hasattr(self, '_flink_menu_cache'):
                with open(flink_menu_path, 'r', encoding='utf-8') as f:
                    self._flink_menu_cache = json.load(f)
                logger.debug(f"Loaded Flink mock menu with {len(self._flink_menu_cache.get('items', []))} items")
            
            items = self._flink_menu_cache.get('items', [])
            query_lower = query.lower()
            
            # Search for matching products
            matches = []
            for item in items:
                if not item.get('available', True):
                    continue
                
                # Search in name, brand, and category
                name = item.get('name', '').lower()
                brand = (item.get('brand') or '').lower()
                category = (item.get('category') or '').lower()
                
                if query_lower in name or query_lower in brand or query_lower in category:
                    # Convert unit format
                    unit_obj = item.get('unit')
                    if unit_obj is None:
                        unit_str = "piece"
                    elif isinstance(unit_obj, dict):
                        # Format: {"Value": 1.0, "Unit": "l", "Quantity": 1}
                        unit_value = unit_obj.get('Value', 1.0)
                        unit_type = unit_obj.get('Unit', 'piece')
                        quantity = unit_obj.get('Quantity', 1)
                        if unit_type:
                            unit_str = f"{unit_value} {unit_type}" if unit_value != 1.0 else unit_type
                        else:
                            unit_str = "piece"
                    else:
                        unit_str = str(unit_obj)
                    
                    matches.append({
                        "product_id": item.get('product_id', ''),
                        "name": item.get('name', ''),
                        "description": f"{item.get('brand', '')} {item.get('name', '')}".strip(),
                        "price": item.get('price', 0.0),
                        "unit": unit_str,
                        "available": item.get('available', True),
                        "brand": item.get('brand'),
                        "category": item.get('category'),
                        "source": "flink_mock_menu",
                    })
                    
                    if len(matches) >= max_results:
                        break
            
            return matches
            
        except Exception as e:
            logger.error(f"Error searching Flink mock menu: {e}", exc_info=True)
            return []
    
    async def search_products(self, query: str) -> List[Dict]:
        """
        Search for products by scraping the website.
        
        TODO: Implement product search scraping
        """
        logger.warning("Scraper search not implemented, using Flink mock menu fallback")
        return await self._search_flink_mock_menu(query)
    
    async def place_order(self, items: List[Dict]) -> Optional[str]:
        """
        Place an order by automating the checkout process.
        
        TODO: Implement order placement scraping
        """
        logger.warning("Scraper order placement not implemented")
        return None

