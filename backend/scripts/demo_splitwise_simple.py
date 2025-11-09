"""
Simple Demo: Create a Splitwise Expense

Creates a €10 expense split equally among 3 people (Alice, Bob, Charlie).
Alice pays the full amount.

Usage:
    python scripts/demo_splitwise_simple.py
    (Run from backend/ directory)
"""

import sys
from pathlib import Path

# Add parent directory to path so imports work
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import asyncio
from loguru import logger
from utils.json_storage import json_storage
from modules.splitwise import SplitwiseService
import requests
from requests_oauthlib import OAuth1


async def create_expense_direct(
    splitwise_service,
    user_data,
    description,
    amount,
    splitwise_user_ids,
    payer_index=0
):
    """Create expense using direct API calls."""
    try:
        # Create OAuth session
        session = requests.Session()
        session.auth = OAuth1(
            splitwise_service.consumer_key,
            client_secret=splitwise_service.consumer_secret,
            resource_owner_key=user_data['splitwise_access_token'],
            resource_owner_secret=user_data['splitwise_access_token_secret']
        )
        
        # Calculate equal split with proper rounding
        num_people = len(splitwise_user_ids)
        split_amount = amount / num_people
        
        # Calculate owed shares - use floor for all but last, then adjust last to make total exact
        owed_shares = []
        total_so_far = 0.0
        
        for i in range(num_people):
            if i == num_people - 1:
                # Last person gets the remainder to make total exact
                owed_share = round(amount - total_so_far, 2)
            else:
                owed_share = round(split_amount, 2)
                total_so_far += owed_share
            owed_shares.append(owed_share)
        
        # Verify total is exact
        total_owed = sum(owed_shares)
        if abs(total_owed - amount) > 0.01:
            # If still off, adjust the payer's share
            diff = amount - total_owed
            owed_shares[payer_index] = round(owed_shares[payer_index] + diff, 2)
        
        # Build expense data
        expense_data = {
            "cost": str(round(amount, 2)),
            "description": description,
            "currency_code": "EUR",
        }
        
        # Add users
        for idx, sw_user_id in enumerate(splitwise_user_ids):
            expense_data[f"users[{idx}][user_id]"] = str(int(sw_user_id))
            expense_data[f"users[{idx}][paid_share]"] = str(round(amount, 2)) if idx == payer_index else "0.00"
            expense_data[f"users[{idx}][owed_share]"] = str(round(owed_shares[idx], 2))
        
        # Make API call
        response = session.post(
            'https://secure.splitwise.com/api/v3.0/create_expense',
            data=expense_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        if response.status_code != 200:
            raise Exception(f"API call failed: {response.status_code} - {response.text}")
        
        result = response.json()
        
        if 'errors' in result and result['errors']:
            raise Exception(f"Splitwise API error: {result['errors']}")
        
        if 'expenses' in result and len(result['expenses']) > 0:
            expense_id = str(result['expenses'][0]['id'])
            logger.info(f"✓ Created expense: {description} (€{amount:.2f}) - ID: {expense_id}")
            return expense_id
        else:
            raise Exception(f"No expense created. Response: {result}")
        
    except Exception as e:
        logger.error(f"Failed to create expense {description}: {e}")
        return None


async def demo():
    """Demo: Create a €10 expense split among 3 people."""
    
    logger.info("=" * 60)
    logger.info("💰 Splitwise Expense Demo")
    logger.info("=" * 60)
    
    # Initialize service
    splitwise_service = SplitwiseService()
    
    if not splitwise_service.is_configured():
        logger.error("❌ Splitwise not configured!")
        return
    
    # Load users from JSON storage
    users = json_storage.find_all()
    
    if len(users) < 3:
        logger.error("❌ Need at least 3 users for this demo")
        return
    
    # Find users
    alice = None
    bob = None
    charlie = None
    
    for user in users:
        if user['name'].lower() == 'alice':
            alice = user
        elif user['name'].lower() == 'bob':
            bob = user
        elif user['name'].lower() == 'charlie':
            charlie = user
    
    if not alice or not bob or not charlie:
        logger.error("❌ Could not find Alice, Bob, and Charlie in users")
        return
    
    # Check authorization
    for user in [alice, bob, charlie]:
        if not user.get('splitwise_access_token') or not user.get('splitwise_access_token_secret'):
            logger.error(f"❌ {user['name']} is not authorized with Splitwise")
            logger.error(f"   Please authorize at: http://localhost:8000/api/auth/splitwise/authorize?user_id={user['user_id']}")
            return
    
    # Get Splitwise user IDs
    alice_sw_id = alice.get('splitwise_user_id')
    bob_sw_id = bob.get('splitwise_user_id')
    charlie_sw_id = charlie.get('splitwise_user_id')
    
    if not all([alice_sw_id, bob_sw_id, charlie_sw_id]):
        logger.error("❌ Missing Splitwise user IDs")
        return
    
    logger.info(f"\n👥 Users:")
    logger.info(f"   Alice (Splitwise ID: {alice_sw_id})")
    logger.info(f"   Bob (Splitwise ID: {bob_sw_id})")
    logger.info(f"   Charlie (Splitwise ID: {charlie_sw_id})")
    
    # Create expense: €10 split equally, Alice pays
    amount = 10.00
    splitwise_user_ids = [alice_sw_id, bob_sw_id, charlie_sw_id]
    
    logger.info(f"\n💶 Expense Details:")
    logger.info(f"   Total: €{amount:.2f}")
    logger.info(f"   Split equally among 3 people: €{amount/3:.2f} each")
    logger.info(f"   Alice pays: €{amount:.2f}")
    
    logger.info(f"\n📝 Creating expense...")
    
    expense_id = await create_expense_direct(
        splitwise_service=splitwise_service,
        user_data=alice,
        description="Demo Expense - €10 Split",
        amount=amount,
        splitwise_user_ids=splitwise_user_ids,
        payer_index=0  # Alice pays
    )
    
    if expense_id:
        logger.info(f"\n✅ SUCCESS! Expense created!")
        logger.info(f"   Expense ID: {expense_id}")
        logger.info(f"   View it in Splitwise: https://secure.splitwise.com/expenses/{expense_id}")
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 Demo Complete!")
        logger.info("\nSummary:")
        logger.info(f"  • Total expense: €{amount:.2f}")
        logger.info(f"  • Alice paid €{amount:.2f}, owes €{amount/3:.2f}")
        logger.info(f"  • Bob owes €{amount/3:.2f}")
        logger.info(f"  • Charlie owes €{amount/3:.2f}")
        logger.info("\nCheck your Splitwise account to see the expense!")
    else:
        logger.error("❌ Failed to create expense!")


if __name__ == "__main__":
    asyncio.run(demo())

