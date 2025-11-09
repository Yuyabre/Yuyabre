"""
Fetch Splitwise User IDs for authorized users.

This script fetches and updates the Splitwise user ID for all authorized users
by making a direct API call to get_current_user endpoint.

Usage:
    python scripts/fetch_splitwise_ids.py
    (Run from backend/ directory)
"""

import sys
from pathlib import Path

# Add parent directory to path so imports work
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import asyncio
from loguru import logger
import requests
from requests_oauthlib import OAuth1
from utils.json_storage import json_storage
from modules.splitwise import SplitwiseService


async def fetch_splitwise_ids():
    """Fetch Splitwise user IDs for all authorized users."""
    logger.info("🔍 Fetching Splitwise User IDs...")
    
    splitwise_service = SplitwiseService()
    
    if not splitwise_service.is_configured():
        logger.error("❌ Splitwise not configured!")
        return
    
    # Get all users
    users = json_storage.find_all()
    
    updated_count = 0
    
    for user in users:
        if user.get('splitwise_access_token') and user.get('splitwise_access_token_secret'):
            if not user.get('splitwise_user_id'):
                try:
                    # Use direct API call with OAuth 1.0
                    session = requests.Session()
                    session.auth = OAuth1(
                        splitwise_service.consumer_key,
                        client_secret=splitwise_service.consumer_secret,
                        resource_owner_key=user['splitwise_access_token'],
                        resource_owner_secret=user['splitwise_access_token_secret']
                    )
                    
                    response = session.get('https://secure.splitwise.com/api/v3.0/get_current_user')
                    
                    if response.status_code == 200:
                        user_data = response.json()
                        splitwise_user_id = str(user_data['user']['id'])
                        
                        # Update user with Splitwise ID
                        json_storage.update(user['user_id'], {
                            'splitwise_user_id': splitwise_user_id
                        })
                        logger.info(f"✓ {user['name']}: {splitwise_user_id}")
                        updated_count += 1
                    else:
                        logger.error(f"❌ API call failed for {user['name']}: {response.status_code} - {response.text}")
                        
                except Exception as e:
                    logger.error(f"❌ Error fetching ID for {user['name']}: {e}")
            else:
                logger.info(f"✓ {user['name']}: Already has ID {user['splitwise_user_id']}")
    
    logger.info(f"\n✅ Updated {updated_count} users with Splitwise IDs")


if __name__ == "__main__":
    asyncio.run(fetch_splitwise_ids())

