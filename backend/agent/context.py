"""
Context Management - Building system prompts with user context.
"""
from typing import Optional
from loguru import logger
from beanie.operators import In

from agent.prompts import SYSTEM_PROMPT
from models.user import User


async def build_system_prompt_with_context(user_id: Optional[str] = None) -> str:
    """
    Build system prompt with user context and preferences.
    
    Args:
        user_id: User ID to fetch context for
        
    Returns:
        Enhanced system prompt with user context
    """
    base_prompt = SYSTEM_PROMPT
    
    if not user_id:
        return base_prompt
    
    # Fetch user information
    user = await User.find_one(User.user_id == user_id)
    if not user:
        return base_prompt
    
    # Build user context string - always include user name
    context_parts = [f"Current User: {user.name} (ID: {user.user_id})"]
    
    # Add email if available
    if user.email:
        context_parts.append(f"Email: {user.email}")
    
    # Add household members if available (for selective sharing)
    if user.household_id:
        from models.household import Household
        household = await Household.find_one(Household.household_id == user.household_id)
        if household and household.member_ids:
            # Get all household members
            household_users = await User.find(
                In(User.user_id, household.member_ids)
            ).to_list()
            if household_users:
                member_info = []
                for member in household_users:
                    member_info.append(f"{member.name} (ID: {member.user_id})")
                context_parts.append(f"Household Members: {', '.join(member_info)}")
    
    # Add preferences if they exist
    prefs = user.preferences
    if prefs.dietary_restrictions:
        context_parts.append(f"Dietary restrictions: {', '.join(prefs.dietary_restrictions)}")
    if prefs.allergies:
        context_parts.append(f"Allergies: {', '.join(prefs.allergies)}")
    if prefs.favorite_brands:
        context_parts.append(f"Preferred brands: {', '.join(prefs.favorite_brands)}")
    if prefs.disliked_items:
        context_parts.append(f"Disliked items: {', '.join(prefs.disliked_items)}")
    
    # Always include user context, even if just the name
    user_context = "\n".join(context_parts)
    enhanced_prompt = (
        f"{base_prompt}\n\n"
        f"IMPORTANT: You are currently talking to {user.name}. "
        f"You always know which user you are talking to based on the context below. "
        f"User Context:\n{user_context}\n\n"
    )
    
    # Add preference guidance if preferences exist
    if prefs.dietary_restrictions or prefs.allergies or prefs.favorite_brands or prefs.disliked_items:
        enhanced_prompt += (
            f"When making recommendations or placing orders, always respect the user's dietary restrictions, "
            f"allergies, and preferences. Never suggest items the user is allergic to or has marked as disliked. "
            f"Prefer brands the user likes when available.\n"
        )
    
    return enhanced_prompt

