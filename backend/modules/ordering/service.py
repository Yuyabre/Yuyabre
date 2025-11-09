"""
Ordering Service - Integration with Thuisbezorgd for grocery ordering.

NOTE: This is a skeleton implementation. The actual integration will depend on
whether Thuisbezorgd provides an API or requires web scraping.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger

from models.order import Order, OrderItem, OrderStatus
from models.inventory import InventoryItem
from models.user import User
from models.household import Household
from modules.whatsapp import WhatsAppService
from modules.discord import DiscordService
from modules.user_inventory.service import UserInventoryService
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
        self.discord_service = DiscordService()
        self.user_inventory_service = UserInventoryService()
        logger.info("Ordering service initialized with cache")
    
    async def _invalidate_cache(self) -> None:
        """Invalidate all order cache entries."""
        await self.cache.invalidate("order")

    def _log_db_query(self, operation: str, **details: Any) -> None:
        """
        Log MongoDB queries executed through the ordering service.
        """
        logger.debug("[MongoDB] orders.{} | {}", operation, details)
    
    async def search_products(self, query: str) -> List[Dict]:
        """
        Search for products on Thuisbezorgd.
        
        Args:
            query: Search query (e.g., "milk", "eggs")
            
        Returns:
            List of product dictionaries with id, name, price, etc.
            
        TODO: Implement actual search logic based on available API/scraping method
        """
        logger.info(f"Searching for products: {query}")
        
        # PLACEHOLDER IMPLEMENTATION
        # This should be replaced with actual API calls or web scraping
        
        # Example return structure:
        return [
            {
                "product_id": "prod_123",
                "name": f"{query.capitalize()} - Sample Product",
                "description": "Sample product description",
                "price": 2.99,
                "unit": "piece",
                "available": True,
                "brand": "Sample Brand",
                "image_url": "https://example.com/image.jpg"
            }
        ]
    
    async def get_product_details(self, product_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific product.
        
        Args:
            product_id: Thuisbezorgd product ID
            
        Returns:
            Product details dictionary or None if not found
            
        TODO: Implement actual product details retrieval
        """
        logger.info(f"Getting product details: {product_id}")
        
        # PLACEHOLDER IMPLEMENTATION
        return {
            "product_id": product_id,
            "name": "Sample Product",
            "description": "Sample description",
            "price": 2.99,
            "unit": "piece",
            "available": True,
            "brand": "Sample Brand",
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
                items_for_message = [
                    {
                        "name": item.get("name", ""),
                        "quantity": item.get("quantity", 0),
                        "unit": item.get("unit", "piece")
                    }
                    for item in shared_items
                ]
                
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
            # For regular orders, mark as confirmed
            if not is_group_order:
                order.status = OrderStatus.CONFIRMED
                order.external_order_id = "TB_" + order.order_id[:8]
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
    ) -> Optional[Order]:
        """
        Process a user's response to a group order.
        
        Args:
            order_id: Order ID
            user_id: User ID who responded
            responses: Response data with items user wants
            
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
    
    async def search_products(self, query: str) -> List[Dict]:
        """
        Search for products by scraping the website.
        
        TODO: Implement product search scraping
        """
        logger.warning("Scraper search not implemented")
        return []
    
    async def place_order(self, items: List[Dict]) -> Optional[str]:
        """
        Place an order by automating the checkout process.
        
        TODO: Implement order placement scraping
        """
        logger.warning("Scraper order placement not implemented")
        return None

