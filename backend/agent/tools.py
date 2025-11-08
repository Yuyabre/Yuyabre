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
                "description": "Create a grocery order with the specified items.",
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
    ]

