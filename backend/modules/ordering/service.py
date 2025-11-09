"""
Ordering Service - Integration with Thuisbezorgd for grocery ordering.

Uses menu loader to search products from pre-scraped restaurant menus.
This mocks API/scraping functionality until real API is available.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger

from models.order import Order, OrderItem, OrderStatus
from models.inventory import InventoryItem
from models.user import User
from models.household import Household
from modules.whatsapp import WhatsAppService
from modules.user_inventory.service import UserInventoryService
from modules.ordering.menu_loader import MenuLoader
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
        self.user_inventory_service = UserInventoryService()
        self.menu_loader = MenuLoader()  # Loads menus from JSON (mocks API/scraping)
        logger.info("Ordering service initialized with cache and menu loader")
    
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
        Search for products in restaurant menus (mocks API/scraping).
        
        Searches across all available restaurant menus for matching products.
        
        Args:
            query: Search query (e.g., "milk", "eggs", "bread")
            
        Returns:
            List of product dictionaries with product_id, name, price, etc.
            Format matches what tool handlers expect.
        """
        logger.info(f"Searching for products: {query}")
        
        try:
            # Search across all menus (mocks API call to multiple restaurants)
            matches = await self.menu_loader.search_all_menus(query)
            
            if not matches:
                logger.warning(f"No products found for query: {query}")
                return []
            
            # Format results to match expected structure
            formatted_results = []
            for match in matches:
                formatted_result = {
                    "product_id": match.get("product_id", ""),
                    "name": match.get("name", ""),
                    "price": float(match.get("price", 0.0)),
                    "unit": "piece",  # Default unit (menu doesn't specify)
                    "available": match.get("available", True),
                    "brand": match.get("brand"),
                    "image_url": match.get("image_url"),
                    "restaurant_name": match.get("restaurant_name"),
                    "restaurant_id": match.get("restaurant_id"),
                }
                formatted_results.append(formatted_result)
            
            logger.info(f"Found {len(formatted_results)} product(s) for '{query}'")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            # Return empty list on error (graceful degradation)
            return []
    
    async def get_product_details(self, product_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific product from menu (mocks API call).
        
        Args:
            product_id: Product ID to look up
            
        Returns:
            Product details dictionary or None if not found
        """
        logger.info(f"Getting product details: {product_id}")
        
        try:
            # Search across all menus for this product ID
            product = await self.menu_loader.get_product_by_id_all_menus(product_id)
            
            if not product:
                logger.warning(f"Product not found: {product_id}")
                return None
            
            # Format to match expected structure
            return {
                "product_id": product.get("product_id", product_id),
                "name": product.get("name", ""),
                "price": float(product.get("price", 0.0)),
                "unit": "piece",  # Default unit
                "available": product.get("available", True),
                "brand": product.get("brand"),
                "image_url": product.get("image_url"),
                "restaurant_name": product.get("restaurant_name"),
                "restaurant_id": product.get("restaurant_id"),
            }
            
        except Exception as e:
            logger.error(f"Error getting product details: {e}")
            return None
    
    async def get_pending_order(self, user_id: Optional[str] = None, within_minutes: int = 5) -> Optional[Order]:
        """
        Get the most recent order for a user that can still be modified (pending or recently confirmed).
        
        Args:
            user_id: User ID to check for orders
            within_minutes: Only consider orders created within this time window (default: 5)
            
        Returns:
            Most recent modifiable order if found, None otherwise
        """
        if not user_id:
            return None
        
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=within_minutes)
            
            # Find orders for this user created within the time window
            # Check both PENDING and CONFIRMED (recently confirmed orders can still be modified)
            # Exclude group orders (they have their own flow)
            # Exclude orders that are already processing/delivered/cancelled
            # Use OR condition for status (Beanie doesn't have .in_(), so we check both)
            pending_orders = await Order.find(
                Order.created_by == user_id,
                Order.is_group_order == False,
                Order.timestamp >= cutoff_time,
                Order.status == OrderStatus.PENDING
            ).sort("-timestamp").limit(1).to_list()
            
            confirmed_orders = await Order.find(
                Order.created_by == user_id,
                Order.is_group_order == False,
                Order.timestamp >= cutoff_time,
                Order.status == OrderStatus.CONFIRMED
            ).sort("-timestamp").limit(1).to_list()
            
            # Combine and get the most recent
            all_orders = pending_orders + confirmed_orders
            
            if all_orders:
                # Sort by timestamp descending and get the most recent
                all_orders.sort(key=lambda o: o.timestamp, reverse=True)
                order = all_orders[0]
                logger.info(f"Found modifiable order {order.order_id} (status: {order.status}) for user {user_id}")
                return order
            
            return None
        except Exception as e:
            logger.warning(f"Error checking for pending orders: {e}")
            return None
    
    async def add_items_to_order(
        self,
        order_id: str,
        items: List[Dict[str, any]],
        created_by: Optional[str] = None,
    ) -> Optional[Order]:
        """
        Add items to an existing pending order.
        
        Args:
            order_id: Order ID to add items to
            items: List of items to add
            created_by: User ID adding the items
            
        Returns:
            Updated Order object if successful, None otherwise
        """
        logger.info(f"Adding {len(items)} items to order {order_id}")
        
        try:
            order = await Order.find_one(Order.order_id == order_id)
            if not order:
                logger.warning(f"Order not found: {order_id}")
                return None
            
            # Allow adding to PENDING or recently CONFIRMED orders
            if order.status not in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
                logger.warning(f"Cannot add items to order {order_id} with status {order.status}")
                return None
            
            # If order is CONFIRMED, change it back to PENDING so it can be modified
            if order.status == OrderStatus.CONFIRMED:
                order.status = OrderStatus.PENDING
                logger.info(f"Changed order {order_id} status from CONFIRMED to PENDING for modification")
            
            # Add new items to the order
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
            
            # Recalculate totals
            order.calculate_total()
            
            # Save updated order
            await order.save()
            await self._invalidate_cache()
            
            logger.info(f"Added {len(items)} items to order {order_id}. New total: €{order.total:.2f}")
            return order
            
        except Exception as e:
            logger.error(f"Error adding items to order: {e}")
            return None

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
        
        If there's a recent pending order for the user, items will be added to it instead
        of creating a new order (unless it's a group order).
        
        Args:
            items: List of items to order, each with product_id, quantity, etc.
            delivery_address: Delivery address
            delivery_time: Preferred delivery time
            notes: Additional notes for the order
            created_by: User ID who created the order
            
        Returns:
            Created or updated Order object if successful, None otherwise
        """
        logger.info(f"Creating order with {len(items)} items")
        
        # Check if there's a recent order we can add to (within 5 minutes)
        if created_by:
            pending_order = await self.get_pending_order(created_by, within_minutes=5)
            if pending_order:
                logger.info(f"Adding items to existing pending order {pending_order.order_id}")
                # Add items to existing order
                updated_order = await self.add_items_to_order(
                    order_id=pending_order.order_id,
                    items=items,
                    created_by=created_by
                )
                if updated_order:
                    return updated_order
                # If adding failed, continue to create new order
        
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
            
            # Calculate delivery fee from restaurant menu (mocks API call)
            # Try to get delivery fee from menu data
            delivery_fee = 2.50  # Default fallback
            try:
                # Load menu to get delivery cost
                menu_data = await self.menu_loader.load_menu("restaurant1")
                if menu_data and menu_data.get('restaurant'):
                    delivery_cost_str = menu_data['restaurant'].get('delivery_cost', '€ 2,50')
                    delivery_fee = self.menu_loader._parse_price(delivery_cost_str)
            except Exception as e:
                logger.warning(f"Could not get delivery fee from menu, using default: {e}")
            
            order.delivery_fee = delivery_fee
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
            
            # Send WhatsApp notification if group order
            if is_group_order and household and hasattr(household, 'household_id'):
                if not self.whatsapp_service.is_configured():
                    logger.warning(
                        f"Group order {order.order_id} created but WhatsApp service is not configured. "
                        f"Order will be created as group order but no WhatsApp message will be sent."
                    )
                    order.whatsapp_message_sent = False
                    await order.save()
                else:
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
                    if hh_id:
                        success = await self.whatsapp_service.send_group_order_notification(
                            household_id=hh_id,
                            order_id=order.order_id,
                            items=items_for_message,
                            created_by_user=created_by or "",
                            response_deadline=order.response_deadline or datetime.utcnow(),
                        )
                    else:
                        success = False
                        logger.warning(f"Could not get household_id from household object")
                    
                    order.whatsapp_message_sent = success
                    await order.save()
                    
                    if success:
                        logger.info(f"WhatsApp notification sent for group order {order.order_id}")
                    else:
                        logger.warning(f"Failed to send WhatsApp notification for order {order.order_id}")
            
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
        Check the status of an order (mocks API status check).
        
        Currently returns status from database. In the future, this will
        query the actual delivery service API for real-time status.
        
        Args:
            order_id: Internal order ID
            
        Returns:
            OrderStatus if found, None otherwise
        """
        self._log_db_query("find_one", filters={"order_id": order_id})
        order = await Order.find_one(Order.order_id == order_id)
        if not order:
            logger.warning(f"Order not found: {order_id}")
            return None
        
        # TODO: In the future, query external API for real-time status
        # For now, return status from database (mocks API response)
        # Mock status progression could be implemented here if needed
        
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
        
        # Send update to WhatsApp group
        if order.household_id and self.whatsapp_service.is_configured():
            update_message = (
                f"✅ Group order finalized!\n\n"
                f"Total: €{order.total:.2f}\n"
                f"Items updated based on responses.\n\n"
                f"Your individual inventories have been updated."
            )
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

