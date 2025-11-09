"""
Simple JSON-based storage for development/testing without MongoDB.

This allows the app to work with JSON files instead of MongoDB.
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from loguru import logger
from datetime import datetime


class JSONStorage:
    """Simple JSON-based storage for User objects."""
    
    def __init__(self, file_path: str = "data/users.json"):
        """Initialize JSON storage."""
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Create file if it doesn't exist."""
        if not self.file_path.exists():
            self.file_path.write_text(json.dumps([], indent=2))
            logger.info(f"Created storage file: {self.file_path}")
    
    def _load(self) -> List[Dict[str, Any]]:
        """Load all data from JSON file."""
        try:
            if not self.file_path.exists():
                return []
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"Error loading JSON storage: {e}")
            return []
    
    def _save(self, data: List[Dict[str, Any]]):
        """Save data to JSON file."""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving JSON storage: {e}")
            raise
    
    def find_one(self, **filters) -> Optional[Dict[str, Any]]:
        """Find one user matching filters."""
        users = self._load()
        
        for user in users:
            match = True
            for key, value in filters.items():
                # Handle nested filters like User.splitwise_access_token != None
                if key.startswith('_not_'):
                    actual_key = key[5:]  # Remove '_not_' prefix
                    if user.get(actual_key) is not None:
                        match = False
                        break
                elif user.get(key) != value:
                    match = False
                    break
            
            if match:
                return user
        
        return None
    
    def find_all(self, **filters) -> List[Dict[str, Any]]:
        """Find all users matching filters."""
        users = self._load()
        
        if not filters:
            return users
        
        results = []
        for user in users:
            match = True
            for key, value in filters.items():
                # Handle != None filters
                if key.startswith('_not_'):
                    actual_key = key[5:]
                    if user.get(actual_key) is None:
                        match = False
                        break
                elif user.get(key) != value:
                    match = False
                    break
            
            if match:
                results.append(user)
        
        return results
    
    def insert(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new user."""
        users = self._load()
        
        # Add timestamp if not present
        if 'joined_date' not in user_data:
            user_data['joined_date'] = datetime.utcnow().isoformat()
        
        users.append(user_data)
        self._save(users)
        logger.info(f"Inserted user: {user_data.get('name', 'Unknown')}")
        return user_data
    
    def update(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a user by user_id."""
        users = self._load()
        
        for i, user in enumerate(users):
            if user.get('user_id') == user_id:
                users[i].update(updates)
                self._save(users)
                logger.info(f"Updated user: {user_id}")
                return users[i]
        
        return None
    
    def save(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save/update a user (upsert)."""
        users = self._load()
        user_id = user_data.get('user_id')
        
        if not user_id:
            # Insert new user
            return self.insert(user_data)
        
        # Update existing user
        for i, user in enumerate(users):
            if user.get('user_id') == user_id:
                users[i].update(user_data)
                self._save(users)
                logger.info(f"Saved user: {user_id}")
                return users[i]
        
        # User not found, insert new
        return self.insert(user_data)


# Global storage instance
json_storage = JSONStorage()

