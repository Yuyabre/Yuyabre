"""
Comprehensive test script to verify ordering system with the real GroceryAgent.

This script tests:
1. Selective sharing (milk shared with B and C, eggs with only B, toilet paper personal)
2. Order batching (multiple orders within 5 minutes)
3. Missing product handling
4. Group order creation
5. Shared item tracking

This verifies that:
- Selective sharing works correctly (shared_with parameter)
- Order batching combines orders within 5 minutes
- Missing products are handled gracefully
- Shared items are correctly tracked
- Personal items are correctly tracked
"""
import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

# Set OpenAI API key and proxy URL (from staging branch)
os.environ["OPENAI_API_KEY"] = "sk-kaNQHHxHLdT-Ij30xYPeJw"
os.environ["OPENAI_PROXY_URL"] = "https://fj7qg3jbr3.execute-api.eu-west-1.amazonaws.com/v1"
print("✅ OpenAI API key set")
print("✅ OpenAI proxy URL set (from staging branch)")

from loguru import logger
from database import db
from agent.core import GroceryAgent
from models.user import User
from models.household import Household
from models.inventory import InventoryItem
from models.order import Order, OrderStatus

# Configure logger
logger.remove()
logger.add(lambda msg: print(msg, end=""), format="{message}")


async def setup_test_data():
    """Set up test users (Person A, B, C), household, and inventory items."""
    print("\n" + "="*80)
    print("SETTING UP TEST DATA")
    print("="*80)
    
    # Create Person A (main user who will place orders)
    person_a = await User.find_one(User.user_id == "person_a")
    if not person_a:
        person_a = User(
            user_id="person_a",
            name="Person A",
            email="persona@example.com"
        )
        await person_a.insert()
        print(f"✅ Created Person A: {person_a.user_id}")
    else:
        print(f"✅ Using existing Person A: {person_a.user_id}")
    
    # Create Person B
    person_b = await User.find_one(User.user_id == "person_b")
    if not person_b:
        person_b = User(
            user_id="person_b",
            name="Person B",
            email="personb@example.com"
        )
        await person_b.insert()
        print(f"✅ Created Person B: {person_b.user_id}")
    else:
        print(f"✅ Using existing Person B: {person_b.user_id}")
    
    # Create Person C
    person_c = await User.find_one(User.user_id == "person_c")
    if not person_c:
        person_c = User(
            user_id="person_c",
            name="Person C",
            email="personc@example.com"
        )
        await person_c.insert()
        print(f"✅ Created Person C: {person_c.user_id}")
    else:
        print(f"✅ Using existing Person C: {person_c.user_id}")
    
    # Create or get test household with all 3 people
    test_household = await Household.find_one(Household.household_id == "test_household_abc")
    if not test_household:
        test_household = Household(
            household_id="test_household_abc",
            name="Test Household ABC",
            member_ids=[person_a.user_id, person_b.user_id, person_c.user_id]  # All 3 members
        )
        await test_household.insert()
        print(f"✅ Created test household: {test_household.household_id}")
        print(f"   Members: {test_household.member_ids}")
    else:
        print(f"✅ Using existing test household: {test_household.household_id}")
        print(f"   Members: {test_household.member_ids}")
    
    # Link Person A to household
    if not person_a.household_id:
        person_a.household_id = test_household.household_id
        await person_a.save()
        print(f"✅ Linked Person A to household")
    
    # Add shared inventory items (shared with all household members)
    shared_items = [
        {"name": "Milk", "category": "Dairy", "quantity": 0, "unit": "liters"},
        {"name": "Diapers", "category": "Baby Care", "quantity": 0, "unit": "packages"},
    ]
    
    print("\n📦 Adding shared inventory items:")
    for item_data in shared_items:
        existing = await InventoryItem.find_one(
            InventoryItem.name == item_data["name"],
            InventoryItem.household_id == test_household.household_id
        )
        if not existing:
            item = InventoryItem(
                name=item_data["name"],
                category=item_data["category"],
                quantity=item_data["quantity"],
                unit=item_data["unit"],
                shared=True,
                household_id=test_household.household_id
            )
            await item.insert()
            print(f"   ✅ Added shared: {item.name}")
        else:
            print(f"   ℹ️  Already exists: {item_data['name']}")
    
    # Add personal inventory items (only for Person A)
    personal_items = [
        {"name": "Cheese", "category": "Dairy", "quantity": 0, "unit": "pieces"},
    ]
    
    print("\n📦 Adding personal inventory items:")
    for item_data in personal_items:
        existing = await InventoryItem.find_one(
            InventoryItem.name == item_data["name"],
            InventoryItem.user_id == person_a.user_id
        )
        if not existing:
            item = InventoryItem(
                name=item_data["name"],
                category=item_data["category"],
                quantity=item_data["quantity"],
                unit=item_data["unit"],
                shared=False,
                user_id=person_a.user_id
            )
            await item.insert()
            print(f"   ✅ Added personal: {item.name}")
        else:
            print(f"   ℹ️  Already exists: {item_data['name']}")
    
    return person_a, test_household


async def test_agent_command(agent: GroceryAgent, command: str, user_id: str):
    """Test a command with the agent and return the order if created."""
    print(f"\n💬 User command: '{command}'")
    print("🤖 Processing with agent...")
    
    try:
        response = await agent.process_command(
            command,
            user_id=user_id
        )
        print(f"\n✅ Agent response:")
        print(f"   {response}")
        
        # Check if order was created
        orders = await Order.find(
            Order.created_by == user_id
        ).sort("-timestamp").limit(1).to_list()
        
        if orders:
            return orders[0]
        else:
            print("\n⚠️  No order found after command")
            return None
            
    except Exception as e:
        print(f"\n❌ Error during agent processing: {e}")
        import traceback
        traceback.print_exc()
        return None


async def verify_order(order: Order, expected_shared_items: list = None):
    """Verify the order structure is correct."""
    if not order:
        print("\n❌ No order to verify")
        return False
    
    print(f"\n📋 Order Details:")
    print(f"   Order ID: {order.order_id}")
    print(f"   Status: {order.status.value}")
    print(f"   Total: €{order.total:.2f}")
    print(f"   Is Group Order: {order.is_group_order}")
    print(f"\n   Items ({len(order.items)}):")
    
    issues = []
    
    for i, item in enumerate(order.items, 1):
        print(f"\n   {i}. {item.name}")
        print(f"      Quantity: {item.quantity} {item.unit}")
        print(f"      Price: €{item.price:.2f} (Total: €{item.total_price:.2f})")
        print(f"      Shared: {item.shared}")
        print(f"      Shared By: {item.shared_by}")
        print(f"      Requested By: {item.requested_by}")
        
        # Check if shared field exists
        if not hasattr(item, 'shared'):
            issues.append(f"Item '{item.name}' missing 'shared' field")
            print(f"      ❌ Missing 'shared' field")
        else:
            print(f"      ✅ Has 'shared' field: {item.shared}")
        
        # Check if shared_by field exists
        if not hasattr(item, 'shared_by'):
            issues.append(f"Item '{item.name}' missing 'shared_by' field")
            print(f"      ❌ Missing 'shared_by' field")
        else:
            print(f"      ✅ Has 'shared_by' field: {item.shared_by}")
        
        # Verify logic: shared items should have multiple users
        if item.shared:
            print(f"      ✅ Correctly marked as SHARED")
            if len(item.shared_by) > 1:
                print(f"      ✅ Shared by {len(item.shared_by)} users: {item.shared_by}")
            else:
                issues.append(f"Item '{item.name}' is shared but shared_by has <= 1 user")
                print(f"      ⚠️  WARNING: Shared item but only {len(item.shared_by)} user(s) in shared_by")
        else:
            print(f"      ✅ Correctly marked as PERSONAL")
            if len(item.shared_by) == 1:
                print(f"      ✅ Only shared by creator: {item.shared_by}")
            else:
                issues.append(f"Item '{item.name}' is personal but shared_by has > 1 user")
                print(f"      ⚠️  WARNING: Personal item but {len(item.shared_by)} users in shared_by")
        
        # Check against expected shared items if provided
        if expected_shared_items:
            item_base_name = item.name.split(" - ")[0].strip().lower()
            should_be_shared = any(
                expected.lower() in item_base_name or item_base_name in expected.lower()
                for expected in expected_shared_items
            )
            if should_be_shared and not item.shared:
                issues.append(f"Item '{item.name}' should be shared but is marked as personal")
            elif not should_be_shared and item.shared:
                issues.append(f"Item '{item.name}' should be personal but is marked as shared")
    
    if issues:
        print(f"\n⚠️  Found {len(issues)} issue(s):")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("\n✅ All checks passed!")
        return True


async def test_order_batching(agent: GroceryAgent, user_id: str):
    """Test order batching - multiple orders within 5 minutes should be combined."""
    print("\n" + "="*80)
    print("📝 TEST: Order Batching")
    print("="*80)
    print("Testing if orders within 5 minutes are automatically combined...")
    print("Note: Only non-group orders can be batched")
    
    # First order - personal item (cheese) to avoid group order
    print("\n1️⃣  First order: 'Order 1 piece of cheese for myself'")
    order1 = await test_agent_command(agent, "Order 1 piece of cheese for myself", user_id)
    
    if not order1:
        print("❌ First order failed - cannot test batching")
        return False
    
    order1_id = order1.order_id
    order1_items_count = len(order1.items)
    print(f"   ✅ Order 1 created: {order1_id} ({order1_items_count} items)")
    print(f"   Is Group Order: {order1.is_group_order}")
    
    # Wait 1 second (still within 5 minute window)
    await asyncio.sleep(1)
    
    # Second order - also personal to avoid group order (batching only works for non-group orders)
    print("\n2️⃣  Second order (within 5 min): 'Order 1 more piece of cheese for myself'")
    order2 = await test_agent_command(agent, "Order 1 more piece of cheese for myself", user_id)
    
    if not order2:
        print("❌ Second order failed")
        return False
    
    # Check if orders were batched
    if order2.order_id == order1_id:
        print(f"   ✅ Orders batched correctly! Both items in order {order1_id}")
        print(f"   Items in order: {[item.name for item in order2.items]}")
        print(f"   Total items: {len(order2.items)} (was {order1_items_count})")
        if len(order2.items) > order1_items_count:
            return True
        else:
            print(f"   ⚠️  Items count didn't increase - may have updated quantity instead")
            return True  # Still counts as batching
    else:
        print(f"   ⚠️  Orders NOT batched - separate orders created")
        print(f"   Order 1: {order1_id} ({len(order1.items)} items, group: {order1.is_group_order})")
        print(f"   Order 2: {order2.order_id} ({len(order2.items)} items, group: {order2.is_group_order})")
        print(f"   Note: Group orders cannot be batched")
        return False


async def test_selective_sharing(agent: GroceryAgent, user_id: str, person_b_id: str, person_c_id: str):
    """Test selective sharing with multiple items."""
    print("\n" + "="*80)
    print("📝 TEST: Selective Sharing")
    print("="*80)
    print("Testing selective sharing:")
    print("  - Milk: shared with Person B and C (3 people)")
    print("  - Eggs: shared with only Person B (2 people)")
    print("  - Toilet paper: personal (1 person)")
    
    command = (
        "I want to order milk shared with person b and person c, "
        "eggs shared with only person b, "
        "and toilet paper for myself"
    )
    
    # First command - agent will ask for confirmation
    print(f"\n💬 User command: '{command}'")
    response1 = await agent.process_command(command, user_id=user_id)
    print(f"\n✅ Agent response:")
    print(f"   {response1}")
    
    # Confirm with quantities
    command2 = "Yes, order 2 liters of milk, 12 eggs, and 4 rolls of toilet paper"
    print(f"\n💬 User command: '{command2}'")
    response2 = await agent.process_command(command2, user_id=user_id)
    print(f"\n✅ Agent response:")
    print(f"   {response2}")
    
    # Get the created order
    orders = await Order.find(Order.created_by == user_id).sort("-timestamp").limit(1).to_list()
    if not orders:
        print("\n❌ No order created")
        return False
    
    order = orders[0]
    
    # Verify selective sharing
    print(f"\n📋 Verifying selective sharing in order {order.order_id}:")
    
    all_correct = True
    for item in order.items:
        item_name_lower = item.name.lower()
        print(f"\n   Item: {item.name}")
        print(f"      Shared: {item.shared}")
        print(f"      Shared By: {item.shared_by}")
        
        if "milk" in item_name_lower:
            expected = [user_id, person_b_id, person_c_id]
            if set(item.shared_by) == set(expected):
                print(f"      ✅ Milk correctly shared with 3 people")
            else:
                print(f"      ❌ Milk sharing incorrect. Expected: {expected}, Got: {item.shared_by}")
                all_correct = False
        elif "egg" in item_name_lower:
            expected = [user_id, person_b_id]
            if set(item.shared_by) == set(expected):
                print(f"      ✅ Eggs correctly shared with 2 people")
            else:
                print(f"      ❌ Eggs sharing incorrect. Expected: {expected}, Got: {item.shared_by}")
                all_correct = False
        elif "toilet" in item_name_lower:
            expected = [user_id]
            if not item.shared and set(item.shared_by) == set(expected):
                print(f"      ✅ Toilet paper correctly marked as personal")
            else:
                print(f"      ❌ Toilet paper incorrect. Expected personal: {expected}, Got: {item.shared_by}")
                all_correct = False
    
    return all_correct


async def test_missing_product(agent: GroceryAgent, user_id: str):
    """Test missing product handling."""
    print("\n" + "="*80)
    print("📝 TEST: Missing Product Handling")
    print("="*80)
    print("Testing order with product not in menu...")
    
    # Use a product that definitely doesn't exist
    command = "Order 5 packages of toilet paper for myself"
    
    # First command - agent will ask for confirmation
    response1 = await agent.process_command(command, user_id=user_id)
    print(f"\n✅ Agent response 1:")
    print(f"   {response1}")
    
    # Confirm to trigger actual order placement
    command2 = "Yes, order 5 packages of toilet paper"
    response2 = await agent.process_command(command2, user_id=user_id)
    print(f"\n✅ Agent response 2:")
    print(f"   {response2}")
    
    # Check if order was created with warnings
    orders = await Order.find(Order.created_by == user_id).sort("-timestamp").limit(1).to_list()
    
    # Check if agent mentioned missing product or if order has warnings
    response_lower = response2.lower()
    has_warning = (
        "not found" in response_lower or 
        "couldn't find" in response_lower or 
        "unavailable" in response_lower or
        "no matching" in response_lower or
        "wasn't included" in response_lower
    )
    
    if has_warning:
        print("\n   ✅ Agent handled missing product gracefully")
        if orders:
            print(f"   ℹ️  Order created: {orders[0].order_id}")
            print(f"   ℹ️  Items in order: {len(orders[0].items)}")
            if len(orders[0].items) == 0:
                print(f"   ✅ No items in order (correct - product not found)")
            else:
                print(f"   ℹ️  Some items found and added to order")
        return True
    else:
        print("\n   ⚠️  Agent response doesn't clearly indicate missing product handling")
        if orders:
            print(f"   ℹ️  Order was created: {orders[0].order_id}")
        return False


async def main():
    """Main test function."""
    print("\n" + "="*80)
    print("COMPREHENSIVE ORDERING SYSTEM TEST")
    print("="*80)
    
    try:
        # Connect to database
        print("\n🔌 Connecting to MongoDB...")
        await db.connect()
        print("✅ Connected to MongoDB")
        
        # Setup test data (Person A, B, C)
        person_a, test_household = await setup_test_data()
        
        # Get Person B and C IDs
        person_b = await User.find_one(User.user_id == "person_b")
        person_c = await User.find_one(User.user_id == "person_c")
        
        # Initialize agent
        print("\n" + "="*80)
        print("INITIALIZING GROCERY AGENT")
        print("="*80)
        print("\n🤖 Initializing GroceryAgent...")
        agent = GroceryAgent()
        print("✅ Agent initialized")
        
        # Test 1: Selective Sharing
        print("\n" + "="*80)
        print("TEST SUITE 1: SELECTIVE SHARING")
        print("="*80)
        test1_passed = await test_selective_sharing(
            agent,
            person_a.user_id,
            person_b.user_id if person_b else "person_b",
            person_c.user_id if person_c else "person_c"
        )
        
        await asyncio.sleep(2)
        
        # Test 2: Order Batching
        print("\n" + "="*80)
        print("TEST SUITE 2: ORDER BATCHING")
        print("="*80)
        test2_passed = await test_order_batching(agent, person_a.user_id)
        
        await asyncio.sleep(2)
        
        # Test 3: Missing Product Handling
        print("\n" + "="*80)
        print("TEST SUITE 3: MISSING PRODUCT HANDLING")
        print("="*80)
        test3_passed = await test_missing_product(agent, person_a.user_id)
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        tests = [
            ("Selective Sharing", test1_passed),
            ("Order Batching", test2_passed),
            ("Missing Product Handling", test3_passed),
        ]
        
        passed = sum(1 for _, result in tests if result)
        total = len(tests)
        
        for test_name, result in tests:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {status}: {test_name}")
        
        print(f"\n📊 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close database connection
        print("\n🔌 Closing database connection...")
        await db.close()
        print("✅ Disconnected from MongoDB")


if __name__ == "__main__":
    asyncio.run(main())

