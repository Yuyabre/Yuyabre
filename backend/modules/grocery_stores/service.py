"""
Grocery Store Service - Store discovery and inventory management.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2
from loguru import logger

from models.store import Store, StoreInventory, StoreProduct, StoreLocation
from models.household import Household
from config import settings


class GroceryStoreService:
    """
    Service for discovering nearby grocery stores and managing their inventory cache.
    
    This service:
    - Finds nearest stores based on household location
    - Fetches and caches store inventory
    - Provides product search within cached inventory
    """
    
    # Cache expiration: 24 hours
    INVENTORY_CACHE_HOURS = 24
    
    def __init__(self):
        """Initialize grocery store service."""
        logger.info("Grocery Store Service initialized")
    
    def _generate_locality_key(self, city: str, postal_code: Optional[str] = None) -> str:
        """
        Generate a unique locality key for caching.
        
        Args:
            city: City name
            postal_code: Optional postal code
            
        Returns:
            Locality key string (e.g., "delft_2611")
        """
        city_clean = city.lower().replace(" ", "_")
        if postal_code:
            # Use first part of postal code (e.g., "2611" from "2611 GP")
            postal_clean = postal_code.split()[0] if " " in postal_code else postal_code
            return f"{city_clean}_{postal_clean}"
        return city_clean
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on Earth (in kilometers).
        
        Args:
            lat1, lon1: Latitude and longitude of first point
            lat2, lon2: Latitude and longitude of second point
            
        Returns:
            Distance in kilometers
        """
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        # Earth radius in kilometers
        R = 6371.0
        return R * c
    
    async def find_nearest_stores(
        self,
        household_id: str,
        max_distance_km: float = 5.0,
        limit: int = 5
    ) -> List[Store]:
        """
        Find nearest grocery stores to a household.
        
        Args:
            household_id: Household ID to get location from
            max_distance_km: Maximum distance in kilometers (default: 5km)
            limit: Maximum number of stores to return
            
        Returns:
            List of Store objects sorted by distance (nearest first)
        """
        # Get household to find location
        household = await Household.find_one(Household.household_id == household_id)
        if not household:
            logger.warning(f"Household {household_id} not found")
            return []
        
        if not household.city:
            logger.warning(f"Household {household_id} has no city information")
            return []
        
        # For now, we'll search stores by city/postal code
        # In a real implementation, you'd use geocoding to get lat/lon from address
        # and then query stores by coordinates
        
        # First, try to find existing stores in the database
        query = {"is_active": True}
        if household.postal_code:
            # Try to find stores with matching postal code area
            postal_prefix = household.postal_code.split()[0] if " " in household.postal_code else household.postal_code
            query["location.postal_code"] = {"$regex": f"^{postal_prefix}"}
        else:
            query["location.city"] = household.city
        
        stores = await Store.find(query).limit(limit * 2).to_list()
        
        # If no stores found in DB, scrape Thuisbezorgd
        if not stores or len(stores) < limit:
            logger.info(f"Found {len(stores)} stores in DB, scraping Thuisbezorgd for more...")
            scraped_stores = await self._scrape_thuisbezorgd_stores(
                city=household.city,
                postal_code=household.postal_code
            )
            
            # Add scraped stores that aren't already in our list
            existing_names = {s.name for s in stores}
            for scraped in scraped_stores:
                if scraped.name not in existing_names:
                    stores.append(scraped)
                    existing_names.add(scraped.name)
        
        # If we have coordinates, sort by distance
        # Otherwise, just return stores in the area
        if stores and household.postal_code:
            # In a real implementation, you'd geocode the household address
            # For now, we'll just return stores in the area
            logger.info(f"Found {len(stores)} stores near household {household_id}")
            return stores[:limit]
        
        logger.info(f"Found {len(stores)} stores in {household.city}")
        return stores[:limit]
    
    async def _scrape_thuisbezorgd_stores(
        self,
        city: str,
        postal_code: Optional[str] = None
    ) -> List[Store]:
        """
        Scrape Thuisbezorgd to find stores in a given location.
        
        Args:
            city: City name
            postal_code: Optional postal code
            
        Returns:
            List of Store objects
        """
        import httpx
        from bs4 import BeautifulSoup
        import re
        
        logger.info(f"Scraping Thuisbezorgd for stores in {city} ({postal_code or 'no postal code'})")
        
        # Build URL - Thuisbezorgd format: /en/delivery/food/{city}-{postal_code}
        if postal_code:
            # Use first part of postal code (e.g., "2625" from "2625 AB")
            postal_clean = postal_code.split()[0] if " " in postal_code else postal_code
            location_slug = f"{city.lower()}-{postal_clean}"
        else:
            location_slug = city.lower()
        
        url = f"https://www.thuisbezorgd.nl/en/delivery/food/{location_slug}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                stores = []
                
                # Try to extract JSON data from script tags (common in modern SPAs)
                json_data = None
                script_tags = soup.find_all('script', type='application/json')
                for script in script_tags:
                    try:
                        import json
                        data = json.loads(script.string)
                        if isinstance(data, dict) and ('restaurants' in data or 'venues' in data):
                            json_data = data
                            break
                    except:
                        continue
                
                # Also try finding in window.__INITIAL_STATE__ or similar
                if not json_data:
                    state_scripts = soup.find_all('script', string=re.compile(r'__INITIAL_STATE__|window\.__data', re.I))
                    for script in state_scripts:
                        try:
                            # Extract JSON from JavaScript object
                            import json
                            script_text = script.string
                            # Try to find JSON object in script
                            json_match = re.search(r'\{.*"restaurants".*\}', script_text, re.DOTALL)
                            if json_match:
                                json_data = json.loads(json_match.group(0))
                                break
                        except:
                            continue
                
                # If we found JSON data, use it
                if json_data:
                    restaurants = json_data.get('restaurants', []) or json_data.get('venues', [])
                    logger.debug(f"Found {len(restaurants)} restaurants in JSON data")
                    
                    for rest_data in restaurants[:20]:
                        try:
                            store_name = rest_data.get('name') or rest_data.get('title', '')
                            if not store_name:
                                continue
                            
                            # Extract URL
                            store_url = rest_data.get('url') or rest_data.get('link', '')
                            if store_url and not store_url.startswith('http'):
                                store_url = f"https://www.thuisbezorgd.nl{store_url}"
                            
                            # Extract location if available
                            location_data = rest_data.get('location', {})
                            lat = location_data.get('latitude', 0.0) if isinstance(location_data, dict) else 0.0
                            lon = location_data.get('longitude', 0.0) if isinstance(location_data, dict) else 0.0
                            
                            location = StoreLocation(
                                latitude=lat,
                                longitude=lon,
                                city=city,
                                postal_code=postal_code,
                                country="Netherlands"
                            )
                            
                            # Check if store already exists
                            existing = await Store.find_one(Store.name == store_name)
                            if existing:
                                stores.append(existing)
                                continue
                            
                            # Create new store
                            store = Store(
                                name=store_name,
                                chain=rest_data.get('chain'),
                                location=location,
                                website=store_url,
                                api_endpoint=store_url,
                            )
                            await store.insert()
                            stores.append(store)
                            logger.info(f"Added new store from JSON: {store_name}")
                            
                        except Exception as e:
                            logger.debug(f"Error parsing restaurant from JSON: {e}")
                            continue
                
                # Fallback: HTML parsing
                if not stores:
                    # Thuisbezorgd structure: restaurants are in cards/links
                    # Look for restaurant cards or links
                    restaurant_cards = soup.find_all(['a', 'div'], class_=re.compile(r'restaurant|venue|card', re.I))
                    
                    # Also try finding by data attributes or specific selectors
                    if not restaurant_cards:
                        # Try alternative selectors
                        restaurant_cards = soup.find_all('a', href=re.compile(r'/restaurant/', re.I))
                    
                    logger.debug(f"Found {len(restaurant_cards)} potential restaurant elements in HTML")
                    
                    for card in restaurant_cards[:20]:  # Limit to first 20 to avoid too many requests
                        try:
                            # Extract store name
                            name_elem = card.find(['h2', 'h3', 'span', 'div'], class_=re.compile(r'name|title', re.I))
                            if not name_elem:
                                name_elem = card.find(string=re.compile(r'.+', re.DOTALL))
                            
                            if not name_elem:
                                continue
                            
                            store_name = name_elem.get_text(strip=True) if hasattr(name_elem, 'get_text') else str(name_elem).strip()
                            if not store_name or len(store_name) < 2:
                                continue
                            
                            # Extract link
                            link_elem = card if card.name == 'a' else card.find('a', href=True)
                            store_url = None
                            if link_elem and hasattr(link_elem, 'get'):
                                store_url = link_elem.get('href', '')
                                if store_url and not store_url.startswith('http'):
                                    store_url = f"https://www.thuisbezorgd.nl{store_url}"
                            
                            # Try to extract location info (might be in data attributes or nearby elements)
                            # For now, use the city/postal_code from household
                            location = StoreLocation(
                                latitude=0.0,  # Would need geocoding
                                longitude=0.0,
                                city=city,
                                postal_code=postal_code,
                                country="Netherlands"
                            )
                            
                            # Check if store already exists
                            existing = await Store.find_one(Store.name == store_name)
                            if existing:
                                stores.append(existing)
                                continue
                            
                            # Create new store
                            store = Store(
                                name=store_name,
                                chain=None,  # Could extract from name or URL
                                location=location,
                                website=store_url,
                                api_endpoint=store_url,  # Use URL as endpoint for scraping menu
                            )
                            await store.insert()
                            stores.append(store)
                            logger.info(f"Added new store: {store_name}")
                            
                        except Exception as e:
                            logger.debug(f"Error parsing restaurant card: {e}")
                            continue
                
                # If still no stores found, generate some mock stores
                if not stores:
                    logger.info("No stores found via scraping, generating mock stores")
                    stores = await self._generate_mock_stores(city, postal_code, count=5)
                
                logger.info(f"Scraped/found {len(stores)} stores from Thuisbezorgd")
                return stores
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error scraping Thuisbezorgd: {e}, generating mock stores")
            return await self._generate_mock_stores(city, postal_code, count=5)
        except Exception as e:
            logger.error(f"Error scraping Thuisbezorgd: {e}, generating mock stores", exc_info=True)
            return await self._generate_mock_stores(city, postal_code, count=5)
    
    async def _scrape_store_menu(
        self,
        store: Store
    ) -> List[StoreProduct]:
        """
        Scrape a store's menu/products from Thuisbezorgd.
        
        Args:
            store: Store object with website/api_endpoint
            
        Returns:
            List of StoreProduct objects
        """
        import httpx
        from bs4 import BeautifulSoup
        import re
        
        if not store.api_endpoint:
            logger.warning(f"Store {store.name} has no URL to scrape")
            return []
        
        logger.info(f"Scraping menu from {store.name} ({store.api_endpoint})")
        
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                response = await client.get(store.api_endpoint, headers=headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                products = []
                
                # Look for menu items - Thuisbezorgd menu structure
                # Menu items are typically in cards or lists with product info
                menu_items = soup.find_all(['div', 'li', 'article'], class_=re.compile(r'menu-item|product|dish|food', re.I))
                
                # Alternative: look for items with price information
                if not menu_items:
                    menu_items = soup.find_all(['div', 'span'], string=re.compile(r'€|EUR', re.I))
                    menu_items = [item.find_parent(['div', 'li', 'article']) for item in menu_items if item.find_parent()]
                    menu_items = [item for item in menu_items if item]
                
                logger.debug(f"Found {len(menu_items)} potential menu items")
                
                for item in menu_items[:50]:  # Limit to 50 items
                    try:
                        # Extract product name
                        name_elem = item.find(['h3', 'h4', 'span', 'div'], class_=re.compile(r'name|title|product', re.I))
                        if not name_elem:
                            # Try finding text that looks like a product name
                            name_elem = item.find(string=re.compile(r'^[A-Z][a-z]+', re.M))
                        
                        if not name_elem:
                            continue
                        
                        product_name = name_elem.get_text(strip=True) if hasattr(name_elem, 'get_text') else str(name_elem).strip()
                        if not product_name or len(product_name) < 2:
                            continue
                        
                        # Extract price
                        price_text = None
                        price_elem = item.find(string=re.compile(r'€\s*\d+[.,]\d+', re.I))
                        if price_elem:
                            price_text = price_elem if isinstance(price_elem, str) else price_elem.get_text(strip=True)
                        else:
                            # Try finding price in nearby elements
                            price_elem = item.find(['span', 'div'], class_=re.compile(r'price|cost', re.I))
                            if price_elem:
                                price_text = price_elem.get_text(strip=True)
                        
                        # Parse price
                        price = 0.0
                        if price_text:
                            # Extract number from price string (e.g., "€12.50" -> 12.50)
                            price_match = re.search(r'(\d+[.,]\d+)', price_text.replace(',', '.'))
                            if price_match:
                                price = float(price_match.group(1))
                        
                        if price == 0.0:
                            # Default price if not found
                            price = 5.99
                        
                        # Extract category (if available)
                        category = None
                        category_elem = item.find(['span', 'div'], class_=re.compile(r'category|type', re.I))
                        if category_elem:
                            category = category_elem.get_text(strip=True)
                        
                        # Extract image
                        image_url = None
                        img_elem = item.find('img', src=True)
                        if img_elem:
                            image_url = img_elem.get('src', '')
                            if image_url and not image_url.startswith('http'):
                                image_url = f"https://www.thuisbezorgd.nl{image_url}"
                        
                        # Generate product ID from name
                        product_id = f"TB_{re.sub(r'[^a-zA-Z0-9]', '_', product_name.upper())[:30]}"
                        
                        product = StoreProduct(
                            product_id=product_id,
                            name=product_name,
                            price=price,
                            unit="piece",  # Default unit
                            category=category,
                            available=True,
                            image_url=image_url,
                        )
                        
                        products.append(product)
                        
                    except Exception as e:
                        logger.debug(f"Error parsing menu item: {e}")
                        continue
                
                logger.info(f"Scraped {len(products)} products from {store.name}")
                return products
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error scraping store menu: {e}")
            return []
        except Exception as e:
            logger.error(f"Error scraping store menu: {e}", exc_info=True)
            return []
    
    async def _generate_mock_stores(
        self,
        city: str,
        postal_code: Optional[str] = None,
        count: int = 5
    ) -> List[Store]:
        """
        Generate mock store data when scraping fails.
        
        Args:
            city: City name
            postal_code: Optional postal code
            count: Number of stores to generate
            
        Returns:
            List of Store objects
        """
        common_chains = ["Albert Heijn", "Jumbo", "Lidl", "Aldi", "Plus", "Coop"]
        
        stores = []
        for i in range(count):
            chain = common_chains[i % len(common_chains)] if i < len(common_chains) else None
            store_name = f"{chain} {city}" if chain else f"Supermarket {i+1} {city}"
            
            # Check if already exists
            existing = await Store.find_one(Store.name == store_name)
            if existing:
                stores.append(existing)
                continue
            
            location = StoreLocation(
                latitude=0.0,
                longitude=0.0,
                city=city,
                postal_code=postal_code,
                country="Netherlands"
            )
            
            store = Store(
                name=store_name,
                chain=chain,
                location=location,
            )
            await store.insert()
            stores.append(store)
            logger.info(f"Generated mock store: {store_name}")
        
        return stores
    
    async def _generate_mock_products(
        self,
        store: Store,
        count: int = 20
    ) -> List[StoreProduct]:
        """
        Generate mock product data for a store (fallback when scraping fails).
        
        Args:
            store: Store object
            count: Number of products to generate
            
        Returns:
            List of StoreProduct objects
        """
        import random
        
        # Common grocery items with realistic prices
        common_items = [
            {"name": "Milk", "price": 1.29, "unit": "liter", "category": "Dairy"},
            {"name": "Bread", "price": 1.99, "unit": "loaf", "category": "Bakery"},
            {"name": "Eggs", "price": 2.49, "unit": "dozen", "category": "Dairy"},
            {"name": "Onions", "price": 0.99, "unit": "kg", "category": "Vegetables"},
            {"name": "Tomatoes", "price": 2.99, "unit": "kg", "category": "Vegetables"},
            {"name": "Potatoes", "price": 1.49, "unit": "kg", "category": "Vegetables"},
            {"name": "Chicken Breast", "price": 8.99, "unit": "kg", "category": "Meat"},
            {"name": "Pasta", "price": 1.19, "unit": "pack", "category": "Pantry"},
            {"name": "Rice", "price": 2.99, "unit": "kg", "category": "Pantry"},
            {"name": "Olive Oil", "price": 4.99, "unit": "bottle", "category": "Pantry"},
            {"name": "Bananas", "price": 1.99, "unit": "kg", "category": "Fruits"},
            {"name": "Apples", "price": 2.49, "unit": "kg", "category": "Fruits"},
            {"name": "Yogurt", "price": 1.79, "unit": "pack", "category": "Dairy"},
            {"name": "Cheese", "price": 3.99, "unit": "pack", "category": "Dairy"},
            {"name": "Butter", "price": 2.49, "unit": "pack", "category": "Dairy"},
        ]
        
        
        products = []
        selected_items = random.sample(common_items, min(count, len(common_items)))
        
        for item in selected_items:
            # Add some price variation
            price_variation = random.uniform(0.9, 1.1)
            price = round(item["price"] * price_variation, 2)
            
            product_id = f"TB_{store.store_id[:8]}_{item['name'].upper().replace(' ', '_')}"
            
            product = StoreProduct(
                product_id=product_id,
                name=item["name"],
                price=price,
                unit=item["unit"],
                category=item["category"],
                available=True,
            )
            products.append(product)
        
        return products
    
    async def _fetch_store_inventory_from_api(
        self,
        store: Store,
        locality_key: str
    ) -> List[StoreProduct]:
        """
        Fetch inventory from a store by scraping Thuisbezorgd, with mock fallback.
        
        Args:
            store: Store object
            locality_key: Locality key for caching
            
        Returns:
            List of StoreProduct objects
        """
        logger.info(f"Fetching inventory from {store.name} via web scraping")
        
        # Try scraping first
        products = []
        if store.api_endpoint:
            try:
                products = await self._scrape_store_menu(store)
            except Exception as e:
                logger.warning(f"Scraping failed for {store.name}: {e}, using mock data")
        
        # If scraping returned no products, use mock data
        if not products:
            logger.info(f"Generating mock products for {store.name}")
            products = await self._generate_mock_products(store, count=20)
        
        return products
    
    async def get_or_fetch_store_inventory(
        self,
        store_id: str,
        locality_key: str,
        force_refresh: bool = False
    ) -> Optional[StoreInventory]:
        """
        Get cached store inventory or fetch fresh if cache expired/missing.
        
        Args:
            store_id: Store ID
            locality_key: Locality key (e.g., "delft_2611")
            force_refresh: Force refresh even if cache is valid
            
        Returns:
            StoreInventory object or None if store not found
        """
        store = await Store.find_one(Store.store_id == store_id)
        if not store:
            logger.warning(f"Store {store_id} not found")
            return None
        
        # Check for existing cache
        if not force_refresh:
            cached = await StoreInventory.find_one(
                StoreInventory.store_id == store_id,
                StoreInventory.locality_key == locality_key
            )
            
            if cached:
                # Check if cache is still valid
                if cached.expires_at and cached.expires_at > datetime.utcnow():
                    logger.debug(f"Using cached inventory for store {store_id} in {locality_key}")
                    return cached
                else:
                    logger.info(f"Cache expired for store {store_id} in {locality_key}, refreshing...")
        
        # Fetch fresh inventory
        products = await self._fetch_store_inventory_from_api(store, locality_key)
        
        # Create or update inventory cache
        existing = await StoreInventory.find_one(
            StoreInventory.store_id == store_id,
            StoreInventory.locality_key == locality_key
        )
        
        expires_at = datetime.utcnow() + timedelta(hours=self.INVENTORY_CACHE_HOURS)
        
        if existing:
            existing.products = products
            existing.last_updated = datetime.utcnow()
            existing.expires_at = expires_at
            await existing.save()
            logger.info(f"Updated inventory cache for store {store_id} in {locality_key} ({len(products)} products)")
            return existing
        else:
            inventory = StoreInventory(
                store_id=store_id,
                locality_key=locality_key,
                products=products,
                expires_at=expires_at
            )
            await inventory.insert()
            logger.info(f"Created inventory cache for store {store_id} in {locality_key} ({len(products)} products)")
            return inventory
    
    async def search_products_in_stores(
        self,
        household_id: str,
        query: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for products in nearest stores' cached inventory.
        
        Args:
            household_id: Household ID to find nearest stores
            query: Product search query (e.g., "milk", "onion")
            max_results: Maximum number of results to return
            
        Returns:
            List of product dictionaries with store information
        """
        # Get household for locality
        household = await Household.find_one(Household.household_id == household_id)
        if not household or not household.city:
            logger.warning(f"Household {household_id} not found or missing location")
            return []
        
        locality_key = self._generate_locality_key(household.city, household.postal_code)
        
        # Find nearest stores
        stores = await self.find_nearest_stores(household_id, limit=3)
        if not stores:
            logger.info(f"No stores found near household {household_id}")
            return []
        
        query_lower = query.lower()
        results = []
        
        # Search in each store's cached inventory
        for store in stores:
            inventory = await self.get_or_fetch_store_inventory(store.store_id, locality_key)
            
            if not inventory or not inventory.products:
                continue
            
            # Search products
            for product in inventory.products:
                if query_lower in product.name.lower() or (product.brand and query_lower in product.brand.lower()):
                    results.append({
                        "product_id": product.product_id,
                        "name": product.name,
                        "brand": product.brand,
                        "price": product.price,
                        "unit": product.unit,
                        "category": product.category,
                        "available": product.available,
                        "store_id": store.store_id,
                        "store_name": store.name,
                        "store_chain": store.chain,
                        "image_url": product.image_url,
                        "description": product.description,
                    })
                    
                    if len(results) >= max_results:
                        break
            
            if len(results) >= max_results:
                break
        
        # Sort by price (cheapest first)
        results.sort(key=lambda x: x["price"])
        
        logger.info(f"Found {len(results)} products matching '{query}' in stores near household {household_id}")
        return results[:max_results]
    
    async def get_product_from_stores(
        self,
        household_id: str,
        product_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific product from nearest stores (returns cheapest option).
        
        Args:
            household_id: Household ID to find nearest stores
            product_name: Exact product name to find
            
        Returns:
            Product dictionary with store info, or None if not found
        """
        results = await self.search_products_in_stores(household_id, product_name, max_results=1)
        return results[0] if results else None

