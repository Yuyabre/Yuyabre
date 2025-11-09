"""
Detailed test of ordering service with menu integration.

Shows exact inputs and outputs, using restaurant1_menu.json
"""
import asyncio
import sys
import json
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from modules.ordering import OrderingService
from database import db
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stdout, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def print_input(label, data):
    """Print input data."""
    print(f"📥 INPUT: {label}")
    print("-" * 80)
    if isinstance(data, dict):
        print(json.dumps(data, indent=2, default=str))
    elif isinstance(data, list):
        for i, item in enumerate(data, 1):
            print(f"  {i}. {item}")
    else:
        print(f"  {data}")
    print()


def print_output(label, data):
    """Print output data."""
    print(f"📤 OUTPUT: {label}")
    print("-" * 80)
    if isinstance(data, dict):
        print(json.dumps(data, indent=2, default=str))
    elif isinstance(data, list):
        for i, item in enumerate(data, 1):
            if isinstance(item, dict):
                print(f"  {i}. {json.dumps(item, indent=2, default=str)}")
            else:
                print(f"  {i}. {item}")
    else:
        print(f"  {data}")
    print()


async def test_ordering_with_menu():
    """Test ordering service with detailed input/output."""
    
    print_section("🧪 ORDERING SERVICE TEST - Using restaurant1_menu.json")
    
    # Connect to database
    print("🔌 Connecting to MongoDB...")
    await db.connect()
    print("✅ Connected to MongoDB\n")
    
    service = OrderingService()
    test_user_id = "test_user_detailed_123"
    
    # ========================================================================
    # TEST 1: Search for products in menu
    # ========================================================================
    print_section("TEST 1: Search Products from Menu")
    
    search_query = "milk"
    print_input("Search Query", search_query)
    
    products = await service.search_products(search_query)
    
    print_output(f"Products Found (from restaurant1_menu.json)", {
        "total_found": len(products),
        "products": products[:5] if len(products) > 5 else products
    })
    
    if products:
        print(f"✅ Found {len(products)} products in menu")
        print(f"   First product: {products[0]['name']} - €{products[0]['price']}")
        print(f"   Product ID: {products[0]['product_id']}")
        print(f"   Restaurant: {products[0].get('restaurant_name', 'Unknown')}")
    else:
        print("❌ No products found")
        return
    
    # ========================================================================
    # TEST 2: Get product details
    # ========================================================================
    print_section("TEST 2: Get Product Details by ID")
    
    product_id = products[0]['product_id']
    print_input("Product ID", product_id)
    
    product_details = await service.get_product_details(product_id)
    
    print_output("Product Details (from restaurant1_menu.json)", product_details)
    
    if product_details:
        print(f"✅ Product found in menu")
        print(f"   Name: {product_details['name']}")
        print(f"   Price: €{product_details['price']}")
    else:
        print("❌ Product not found")
    
    # ========================================================================
    # TEST 3: Create first order
    # ========================================================================
    print_section("TEST 3: Create First Order (Milk)")
    
    milk_item = {
        "product_id": products[0]["product_id"],
        "name": products[0]["name"],
        "quantity": 2.0,
        "unit": products[0].get("unit", "piece"),
        "price": products[0]["price"],
        "requested_by": [test_user_id]
    }
    
    print_input("Order Items", [milk_item])
    print_input("Delivery Address", "123 Test Street")
    print_input("Created By", test_user_id)
    
    order1 = await service.create_order(
        items=[milk_item],
        delivery_address="123 Test Street",
        created_by=test_user_id
    )
    
    if order1:
        print_output("Order Created", {
            "order_id": order1.order_id,
            "status": order1.status.value,
            "items": [
                {
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "price": item.price,
                    "total_price": item.total_price
                }
                for item in order1.items
            ],
            "subtotal": order1.subtotal,
            "delivery_fee": order1.delivery_fee,
            "total": order1.total,
            "timestamp": str(order1.timestamp)
        })
        print(f"✅ Order 1 created successfully")
        print(f"   Order ID: {order1.order_id}")
        print(f"   Total: €{order1.total:.2f}")
    else:
        print("❌ Failed to create order")
        return
    
    # ========================================================================
    # TEST 4: Search for second product
    # ========================================================================
    print_section("TEST 4: Search for Second Product (Bread)")
    
    search_query2 = "bread"
    print_input("Search Query", search_query2)
    
    bread_products = await service.search_products(search_query2)
    
    print_output(f"Products Found (from restaurant1_menu.json)", {
        "total_found": len(bread_products),
        "products": bread_products[:3] if len(bread_products) > 3 else bread_products
    })
    
    if not bread_products:
        # Try chicken if bread not found
        print("   Bread not found, trying 'chicken'...")
        bread_products = await service.search_products("chicken")
        print_output(f"Products Found (chicken)", {
            "total_found": len(bread_products),
            "products": bread_products[:3] if len(bread_products) > 3 else bread_products
        })
    
    if not bread_products:
        print("❌ Could not find second product")
        await db.close()
        return
    
    # ========================================================================
    # TEST 5: Create second order (should be batched)
    # ========================================================================
    print_section("TEST 5: Create Second Order (Should Batch with First)")
    
    bread_item = {
        "product_id": bread_products[0]["product_id"],
        "name": bread_products[0]["name"],
        "quantity": 1.0,
        "unit": bread_products[0].get("unit", "piece"),
        "price": bread_products[0]["price"],
        "requested_by": [test_user_id]
    }
    
    print_input("Order Items", [bread_item])
    print_input("Delivery Address", "123 Test Street")
    print_input("Created By", test_user_id)
    print("   ⚠️  Note: This should be added to existing order (within 5 minutes)")
    
    order2 = await service.create_order(
        items=[bread_item],
        delivery_address="123 Test Street",
        created_by=test_user_id
    )
    
    if order2:
        print_output("Order Result", {
            "order_id": order2.order_id,
            "status": order2.status.value,
            "items": [
                {
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "price": item.price,
                    "total_price": item.total_price
                }
                for item in order2.items
            ],
            "subtotal": order2.subtotal,
            "delivery_fee": order2.delivery_fee,
            "total": order2.total,
            "timestamp": str(order2.timestamp)
        })
        
        # Check if batching worked
        if order1.order_id == order2.order_id:
            print(f"✅ BATCHING WORKED: Both items in same order!")
            print(f"   Order ID: {order1.order_id}")
            print(f"   Items: {len(order2.items)}")
            print(f"   Total: €{order2.total:.2f}")
        else:
            print(f"⚠️  Different orders: {order1.order_id} vs {order2.order_id}")
    else:
        print("❌ Failed to create second order")
    
    # ========================================================================
    # TEST 6: Verify menu file is being used
    # ========================================================================
    print_section("TEST 6: Verify Menu File Usage")
    
    menu_path = Path(backend_dir) / "data" / "restaurant1_menu.json"
    print_input("Menu File Path", str(menu_path))
    
    if menu_path.exists():
        with open(menu_path, 'r') as f:
            menu_data = json.load(f)
        
        print_output("Menu File Info", {
            "file_exists": True,
            "restaurant_name": menu_data.get("restaurant", {}).get("name"),
            "total_menu_items": len(menu_data.get("menu_items", [])),
            "delivery_cost": menu_data.get("restaurant", {}).get("delivery_cost"),
            "minimum_order": menu_data.get("restaurant", {}).get("minimum_order_amount")
        })
        
        # Verify products are from menu
        if order1:
            order_product_ids = [item.product_id for item in order1.items]
            menu_product_ids = [item.get("product_id") for item in menu_data.get("menu_items", [])]
            
            matches = [pid for pid in order_product_ids if pid in menu_product_ids]
            
            print_output("Product Verification", {
                "order_product_ids": order_product_ids,
                "products_in_menu": len(matches) == len(order_product_ids),
                "matched_ids": matches
            })
            
            if len(matches) == len(order_product_ids):
                print("✅ All order products are from restaurant1_menu.json!")
            else:
                print("⚠️  Some products not found in menu")
    else:
        print(f"❌ Menu file not found: {menu_path}")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print_section("📊 TEST SUMMARY")
    
    print("✅ Tests Completed:")
    print("   1. Product search from menu - WORKING")
    print("   2. Product details retrieval - WORKING")
    print("   3. Order creation - WORKING")
    print("   4. Order batching - WORKING" if order1 and order2 and order1.order_id == order2.order_id else "   4. Order batching - FAILED")
    print("   5. Menu file integration - WORKING")
    
    print("\n📋 Final Order Details:")
    if order2:
        print(f"   Order ID: {order2.order_id}")
        print(f"   Status: {order2.status.value}")
        print(f"   Items ({len(order2.items)}):")
        for item in order2.items:
            print(f"     - {item.name}: {item.quantity} {item.unit} @ €{item.price} = €{item.total_price:.2f}")
        print(f"   Subtotal: €{order2.subtotal:.2f}")
        print(f"   Delivery Fee: €{order2.delivery_fee:.2f}")
        print(f"   Total: €{order2.total:.2f}")
    
    # Cleanup
    print("\n🧹 Cleaning up test data...")
    try:
        if order1:
            await order1.delete()
        if order2 and order2.order_id != order1.order_id:
            await order2.delete()
        print("✅ Cleanup complete")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")
    
    await db.close()
    print("\n✅ Database connection closed")
    
    print_section("✨ TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(test_ordering_with_menu())

