"""
Tool definitions for the Grocery Agent.

This module contains the tool schemas that are available to the LLM.
"""
from typing import Any, Dict, List


def build_tool_specs() -> List[Dict[str, Any]]:
    """Define tool schemas available to the LLM."""
    return [
        {
            "type": "function",
            "function": {
                "name": "get_inventory_snapshot",
                "description": "Fetch the current inventory items. "
                "Optionally focus on ingredients for a specific dish or search query.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dish": {
                            "type": "string",
                            "description": "Dish or recipe the user is interested in.",
                        },
                        "search": {
                            "type": "string",
                            "description": "Keyword filter for inventory items.",
                        },
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "add_inventory_items",
                "description": "Add new items to the inventory or increase quantities for existing items.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "items": {
                            "type": "array",
                            "description": "Items to add or increment.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {
                                        "type": "string",
                                        "description": "Item name.",
                                    },
                                    "quantity": {
                                        "type": "number",
                                        "description": "Quantity to add.",
                                    },
                                    "unit": {
                                        "type": "string",
                                        "description": "Unit of measurement.",
                                    },
                                    "category": {
                                        "type": "string",
                                        "description": "Optional category.",
                                    },
                                },
                                "required": ["name", "quantity"],
                            },
                        }
                    },
                    "required": ["items"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "place_order",
                "description": "Create a grocery order with the specified items. "
                "If any items are marked as 'shared' in the inventory, the system will automatically "
                "create a group order and send a Discord message (or WhatsApp if Discord not configured) to household members asking if they need those items too. "
                "The order will be updated based on housemates' responses. "
                "The tool will return `is_group_order: true` and `whatsapp_sent: true` (field name used for both Discord and WhatsApp) if this happens.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "items": {
                            "type": "array",
                            "description": "Items that need to be ordered.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "quantity": {"type": "number"},
                                    "unit": {
                                        "type": "string",
                                        "description": "Measurement unit (piece, grams, ml, etc).",
                                    },
                                },
                                "required": ["name", "quantity"],
                            },
                            "minItems": 1,
                        },
                        "delivery_address": {
                            "type": "string",
                            "description": "Optional delivery address override.",
                        },
                        "notes": {
                            "type": "string",
                            "description": "Additional notes for the order.",
                        },
                    },
                    "required": ["items"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "check_low_stock",
                "description": "List items that are below their stock threshold.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of low-stock items to return. Defaults to 20.",
                        }
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_recent_orders",
                "description": "Retrieve recently placed grocery orders.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "How many recent orders to fetch (default 5).",
                        }
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "update_user_preferences",
                "description": "Update the user's dietary preferences, allergies, favorite brands, or disliked items. "
                "Use this when the user mentions dietary restrictions, allergies, brand preferences, or items they dislike. "
                "Examples: 'I am lactose intolerant', 'I'm vegetarian', 'I'm allergic to nuts', 'I prefer Melkunie brand', 'I hate cilantro'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dietary_restrictions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of dietary restrictions to add (e.g., 'vegetarian', 'vegan', 'pescatarian', 'halal', 'kosher'). "
                            "This will ADD to existing restrictions, not replace them.",
                        },
                        "allergies": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of allergies to add (e.g., 'nuts', 'gluten', 'dairy', 'lactose', 'eggs', 'shellfish'). "
                            "This will ADD to existing allergies, not replace them.",
                        },
                        "favorite_brands": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of favorite brands to add (e.g., 'Melkunie', 'Albert Heijn'). "
                            "This will ADD to existing brands, not replace them.",
                        },
                        "disliked_items": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of items the user dislikes to add (e.g., 'cilantro', 'brussels sprouts'). "
                            "This will ADD to existing disliked items, not replace them.",
                        },
                        "remove_dietary_restrictions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of dietary restrictions to remove.",
                        },
                        "remove_allergies": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of allergies to remove.",
                        },
                        "remove_favorite_brands": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of favorite brands to remove.",
                        },
                        "remove_disliked_items": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of disliked items to remove.",
                        },
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_user_info",
                "description": "Get information about the current user, including their name, email, preferences, and other profile details. "
                "Use this when the user asks questions like 'who am I', 'what user am I', 'what's my name', or 'tell me about myself'. "
                "You already have access to user context in the system prompt, but this tool can be used to provide detailed information to the user.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "update_inventory_item",
                "description": "Update properties of an existing inventory item, such as marking it as shared or personal, updating quantity, threshold, or other attributes. "
                "Use this when the user wants to change whether an item is shared with housemates, update quantities, or modify item properties. "
                "When marking an item as shared, it will be moved to the household inventory. When marking as personal, it will be moved to the user's personal inventory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "item_name": {
                            "type": "string",
                            "description": "Name of the inventory item to update.",
                        },
                        "shared": {
                            "type": "boolean",
                            "description": "Whether the item should be shared with housemates. If true, the item becomes a household item. If false, it becomes a personal item.",
                        },
                        "quantity": {
                            "type": "number",
                            "description": "New quantity for the item (optional).",
                        },
                        "threshold": {
                            "type": "number",
                            "description": "New low-stock threshold for the item (optional).",
                        },
                        "notes": {
                            "type": "string",
                            "description": "Additional notes about the item (optional).",
                        },
                    },
                    "required": ["item_name"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "send_whatsapp_message",
                "description": "Send a WhatsApp message to household members or a specific user. "
                "This is a FALLBACK option. Always prefer `send_discord_message` first. "
                "Only use WhatsApp if Discord is not configured for the household or if the user explicitly requests WhatsApp. "
                "You can send to the entire household or to a specific user by phone number.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The message content to send via WhatsApp.",
                        },
                        "to_household": {
                            "type": "boolean",
                            "description": "If true, send to all household members. If false, send to specific phone number.",
                            "default": True,
                        },
                        "phone_number": {
                            "type": "string",
                            "description": "Phone number in international format (e.g., '+31612345678'). Required if to_household is false.",
                        },
                    },
                    "required": ["message"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_housemates",
                "description": "Get a list of all housemates in the user's household, including their contact information (name, phone, email). "
                "Use this when the user asks about housemates, flatmates, or wants to know who lives in the household. "
                "This helps you identify who to contact or send messages to.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "include_contact_info": {
                            "type": "boolean",
                            "description": "Whether to include phone numbers and email addresses. Defaults to true.",
                            "default": True,
                        },
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "send_discord_message",
                "description": "Send a Discord message to the household's Discord channel. "
                "This is the PRIMARY and PREFERRED method for sending messages to housemates. "
                "Use this when the user asks to send a message to housemates, notify the household, or communicate with flatmates. "
                "Always prefer Discord over WhatsApp. Only use WhatsApp if Discord is not configured for the household.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The message content to send via Discord.",
                        },
                    },
                    "required": ["message"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "create_splitwise_expense",
                "description": "Create a new expense in Splitwise to split costs with household members. "
                "Use this when the user wants to add an expense to Splitwise, split a cost, or record a shared expense. "
                "The expense will be automatically split equally among all household members who have Splitwise accounts. "
                "If the household has a Splitwise group configured, the expense will be added to that group.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "Description of the expense (e.g., 'Grocery shopping', 'Dinner at restaurant').",
                        },
                        "amount": {
                            "type": "number",
                            "description": "Total amount of the expense in the currency used by the Splitwise group (e.g., 25.50 for €25.50).",
                        },
                        "notes": {
                            "type": "string",
                            "description": "Optional additional notes or details about the expense.",
                        },
                        "category": {
                            "type": "string",
                            "description": "Optional expense category (e.g., 'Groceries', 'Restaurants', 'Transportation'). Defaults to 'Groceries'.",
                            "default": "Groceries",
                        },
                    },
                    "required": ["description", "amount"],
                },
            },
        },
    ]

