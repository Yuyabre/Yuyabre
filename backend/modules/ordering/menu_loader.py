"""
Menu Loader - Loads restaurant menus from JSON files.

This module mocks API/scraping functionality by loading pre-scraped menu data.
In the future, this can be replaced with actual API calls or web scraping.
"""
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger
import json

from config import settings


class MenuLoader:
    """
    Loads restaurant menus from JSON files.
    
    This mocks the behavior of API calls or web scraping by loading
    pre-scraped menu data from JSON files.
    """
    
    def __init__(self, menu_path: Optional[str] = None):
        """
        Initialize menu loader.
        
        Args:
            menu_path: Path to menu directory (default: backend/data/)
        """
        if menu_path:
            self.menu_dir = Path(menu_path)
        else:
            # Default to backend/data/
            backend_dir = Path(__file__).resolve().parent.parent.parent
            self.menu_dir = backend_dir / "data"
        
        self._menu_cache: Dict[str, Dict] = {}
        logger.info(f"MenuLoader initialized with path: {self.menu_dir}")
    
    def _load_menu_file(self, filename: str) -> Optional[Dict]:
        """
        Load a menu from a JSON file.
        
        Args:
            filename: Name of the menu file (e.g., "restaurant1_menu.json")
            
        Returns:
            Menu data dictionary or None if file not found
        """
        # Check cache first
        if filename in self._menu_cache:
            return self._menu_cache[filename]
        
        menu_path = self.menu_dir / filename
        
        if not menu_path.exists():
            logger.warning(f"Menu file not found: {menu_path}")
            return None
        
        try:
            with open(menu_path, 'r', encoding='utf-8') as f:
                menu_data = json.load(f)
            
            # Cache the menu
            self._menu_cache[filename] = menu_data
            logger.debug(f"Loaded menu from {filename}: {len(menu_data.get('menu_items', []))} items")
            return menu_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse menu file {filename}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading menu file {filename}: {e}")
            return None
    
    async def load_menu(self, restaurant_id: str = "restaurant1") -> Optional[Dict]:
        """
        Load a restaurant menu (mocks API/scraping call).
        
        Args:
            restaurant_id: Restaurant identifier (default: "restaurant1")
            
        Returns:
            Menu data dictionary or None if not found
        """
        filename = f"{restaurant_id}_menu.json"
        menu_data = self._load_menu_file(filename)
        
        if menu_data:
            logger.info(f"Loaded menu for {restaurant_id}: {menu_data.get('restaurant', {}).get('name', 'Unknown')}")
        
        return menu_data
    
    async def load_all_menus(self) -> List[Dict]:
        """
        Load all available menus (mocks multiple API calls).
        
        Returns:
            List of menu data dictionaries
        """
        menus = []
        
        # Look for all menu files in data directory
        if not self.menu_dir.exists():
            logger.warning(f"Menu directory does not exist: {self.menu_dir}")
            return menus
        
        menu_files = list(self.menu_dir.glob("*_menu.json"))
        
        for menu_file in menu_files:
            menu_data = self._load_menu_file(menu_file.name)
            if menu_data:
                menus.append(menu_data)
        
        logger.info(f"Loaded {len(menus)} menu(s) from {self.menu_dir}")
        return menus
    
    def search_in_menu(self, menu_data: Dict, query: str) -> List[Dict]:
        """
        Search for products in a menu.
        
        Args:
            menu_data: Menu data dictionary
            query: Search query (product name)
            
        Returns:
            List of matching products
        """
        if not menu_data or 'menu_items' not in menu_data:
            return []
        
        query_lower = query.lower().strip()
        matches = []
        
        for item in menu_data['menu_items']:
            if not item.get('available', True):
                continue
            
            item_name = item.get('name', '').lower()
            
            # Exact match
            if query_lower == item_name:
                matches.append(item)
            # Partial match (query in name)
            elif query_lower in item_name:
                matches.append(item)
            # Brand match
            elif item.get('brand', '').lower() == query_lower:
                matches.append(item)
        
        return matches
    
    async def search_all_menus(self, query: str) -> List[Dict]:
        """
        Search for products across all available menus.
        
        Args:
            query: Search query (product name)
            
        Returns:
            List of matching products with restaurant info
        """
        menus = await self.load_all_menus()
        all_matches = []
        
        for menu_data in menus:
            restaurant_info = menu_data.get('restaurant', {})
            restaurant_name = restaurant_info.get('name', 'Unknown')
            
            matches = self.search_in_menu(menu_data, query)
            
            # Add restaurant context to each match
            for match in matches:
                match_with_context = {
                    **match,
                    'restaurant_id': restaurant_info.get('name', '').lower().replace(' ', '_'),
                    'restaurant_name': restaurant_name,
                    'delivery_cost': self._parse_price(restaurant_info.get('delivery_cost', '€ 0,00')),
                    'minimum_order_amount': self._parse_price(restaurant_info.get('minimum_order_amount', '€ 0,00')),
                    'free_delivery_threshold': self._parse_price(restaurant_info.get('free_delivery_threshold', '€ 0,00')),
                }
                all_matches.append(match_with_context)
        
        logger.info(f"Found {len(all_matches)} matches for '{query}' across {len(menus)} menu(s)")
        return all_matches
    
    def _parse_price(self, price_str: str) -> float:
        """
        Parse price string (e.g., "€ 4,49") to float.
        
        Args:
            price_str: Price string
            
        Returns:
            Price as float
        """
        try:
            # Remove currency symbols and spaces
            cleaned = price_str.replace('€', '').replace('$', '').strip()
            # Replace comma with dot for decimal
            cleaned = cleaned.replace(',', '.')
            return float(cleaned)
        except (ValueError, AttributeError):
            return 0.0
    
    def get_product_by_id(self, menu_data: Dict, product_id: str) -> Optional[Dict]:
        """
        Get a specific product by ID from a menu.
        
        Args:
            menu_data: Menu data dictionary
            product_id: Product ID to find
            
        Returns:
            Product dictionary or None if not found
        """
        if not menu_data or 'menu_items' not in menu_data:
            return None
        
        for item in menu_data['menu_items']:
            if item.get('product_id') == product_id:
                return item
        
        return None
    
    async def get_product_by_id_all_menus(self, product_id: str) -> Optional[Dict]:
        """
        Get a product by ID across all menus.
        
        Args:
            product_id: Product ID to find
            
        Returns:
            Product dictionary with restaurant context or None if not found
        """
        menus = await self.load_all_menus()
        
        for menu_data in menus:
            product = self.get_product_by_id(menu_data, product_id)
            if product:
                restaurant_info = menu_data.get('restaurant', {})
                return {
                    **product,
                    'restaurant_id': restaurant_info.get('name', '').lower().replace(' ', '_'),
                    'restaurant_name': restaurant_info.get('name', 'Unknown'),
                }
        
        return None

