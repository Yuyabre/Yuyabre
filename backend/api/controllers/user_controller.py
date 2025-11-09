"""
Controller for user-related operations and authentication.
"""
from fastapi import HTTPException, status

from api.dependencies import user_service
from api.serializers import (
    SignupRequest,
    LoginRequest,
    UserResponse,
    JoinHouseholdRequest,
    CreateHouseholdRequest,
    HouseholdResponse,
    UpdateUserPreferencesRequest,
    UpdatePreferencesResponse,
    UserPreferenceRequest,
)
from models import UserPreference
from models.user import User
from loguru import logger


class UserController:
    """Controller for handling user operations and authentication."""
    
    @staticmethod
    async def signup(request: SignupRequest) -> UserResponse:
        """
        Create a new user account.
        
        Args:
            request: Signup request with user details
            
        Returns:
            UserResponse with user info
            
        Raises:
            HTTPException: If email already exists or validation fails
        """
        try:
            # Convert preferences if provided
            user_preferences = None
            if request.preferences:
                user_preferences = UserPreference(
                    dietary_restrictions=request.preferences.dietary_restrictions,
                    allergies=request.preferences.allergies,
                    favorite_brands=request.preferences.favorite_brands,
                    disliked_items=request.preferences.disliked_items,
                )
            
            user = await user_service.signup(
                name=request.name,
                email=request.email,
                password=request.password,
                phone=request.phone,
                splitwise_user_id=request.splitwise_user_id,
                discord_user_id=request.discord_user_id,
                preferences=user_preferences,
            )
            
            return UserResponse(
                user_id=user.user_id,
                name=user.name,
                email=user.email,
                phone=user.phone,
                discord_user_id=user.discord_user_id,
                household_id=user.household_id,
                is_active=user.is_active,
                joined_date=user.joined_date.isoformat() if user.joined_date else "",
                preferences=UserPreferenceRequest(
                    dietary_restrictions=user.preferences.dietary_restrictions,
                    allergies=user.preferences.allergies,
                    favorite_brands=user.preferences.favorite_brands,
                    disliked_items=user.preferences.disliked_items,
                ) if user.preferences else None,
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    @staticmethod
    async def login(request: LoginRequest) -> UserResponse:
        """
        Authenticate a user with email and password.
        
        Args:
            request: Login request with email and password
            
        Returns:
            UserResponse with user info
            
        Raises:
            HTTPException: If credentials are invalid
        """
        try:
            user = await user_service.login(
                email=request.email,
                password=request.password,
            )
            
            return UserResponse(
                user_id=user.user_id,
                name=user.name,
                email=user.email,
                phone=user.phone,
                discord_user_id=user.discord_user_id,
                household_id=user.household_id,
                is_active=user.is_active,
                joined_date=user.joined_date.isoformat() if user.joined_date else "",
                preferences=UserPreferenceRequest(
                    dietary_restrictions=user.preferences.dietary_restrictions,
                    allergies=user.preferences.allergies,
                    favorite_brands=user.preferences.favorite_brands,
                    disliked_items=user.preferences.disliked_items,
                ) if user.preferences else None,
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )
    
    @staticmethod
    async def create_household(
        user_id: str,
        request: CreateHouseholdRequest,
    ) -> HouseholdResponse:
        """
        Create a new household for a user.
        
        Args:
            user_id: The user's unique identifier
            request: Create household request with household details
            
        Returns:
            HouseholdResponse with household info including invite_code
            
        Raises:
            HTTPException: If user not found or user is already in a household
        """
        try:
            household = await user_service.create_household(
                user_id=user_id,
                name=request.name,
                address=request.address,
                city=request.city,
                postal_code=request.postal_code,
                country=request.country,
                whatsapp_group_id=request.whatsapp_group_id,
                whatsapp_group_name=request.whatsapp_group_name,
                discord_channel_id=request.discord_channel_id,
                notes=request.notes,
            )
            
            return HouseholdResponse(
                household_id=household.household_id,
                name=household.name,
                invite_code=household.invite_code,
                address=household.address,
                city=household.city,
                postal_code=household.postal_code,
                country=household.country,
                whatsapp_group_id=household.whatsapp_group_id,
                whatsapp_group_name=household.whatsapp_group_name,
                discord_channel_id=household.discord_channel_id,
                member_ids=household.member_ids,
                created_at=household.created_at.isoformat() if household.created_at else "",
                is_active=household.is_active,
                notes=household.notes,
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    @staticmethod
    async def get_household_by_id(household_id: str) -> HouseholdResponse:
        """
        Get household information by household_id.
        
        Args:
            household_id: The household's unique identifier
            
        Returns:
            HouseholdResponse with household info including invite_code
            
        Raises:
            HTTPException: If household not found
        """
        household = await user_service.get_household_by_id(household_id)
        if not household:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Household not found"
            )
        
        return HouseholdResponse(
            household_id=household.household_id,
            name=household.name,
            invite_code=household.invite_code,
            address=household.address,
            city=household.city,
            postal_code=household.postal_code,
            country=household.country,
            whatsapp_group_id=household.whatsapp_group_id,
            whatsapp_group_name=household.whatsapp_group_name,
            member_ids=household.member_ids,
            created_at=household.created_at.isoformat() if household.created_at else "",
            is_active=household.is_active,
            notes=household.notes,
        )
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> UserResponse:
        """
        Get a user's information by user_id.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            UserResponse with user information
            
        Raises:
            HTTPException: If user not found
        """
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            user_id=user.user_id,
            name=user.name,
            email=user.email,
            phone=user.phone,
            household_id=user.household_id,
            is_active=user.is_active,
            joined_date=user.joined_date.isoformat() if user.joined_date else "",
            preferences=UserPreferenceRequest(
                dietary_restrictions=user.preferences.dietary_restrictions,
                allergies=user.preferences.allergies,
                favorite_brands=user.preferences.favorite_brands,
                disliked_items=user.preferences.disliked_items,
            ) if user.preferences else None,
        )
    
    @staticmethod
    async def join_household(
        user_id: str,
        request: JoinHouseholdRequest,
    ) -> dict:
        """
        Add a user to a household using an invite code.
        
        Args:
            user_id: The user's unique identifier
            request: Join household request with invite code
            
        Returns:
            Dictionary with success message and household info
            
        Raises:
            HTTPException: If invite code is invalid or user is already in a household
        """
        try:
            household = await user_service.join_household(
                user_id=user_id,
                invite_code=request.invite_code,
            )
            
            return {
                "message": f"Successfully joined household: {household.name}",
                "household_id": household.household_id,
                "household_name": household.name,
            }
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    @staticmethod
    def normalize_allergy(allergy: str) -> str:
        """
        Normalize allergy names to common forms.
        
        Args:
            allergy: Allergy name to normalize
            
        Returns:
            Normalized allergy name
        """
        allergy_lower = allergy.lower().strip()
        
        # Common normalizations
        normalizations = {
            "peanuts": "peanuts",
            "peanut": "peanuts",
            "tree nuts": "tree nuts",
            "tree nut": "tree nuts",
            "nuts": "tree nuts",
            "walnuts": "tree nuts",
            "almonds": "tree nuts",
            "cashews": "tree nuts",
            "gluten": "gluten",
            "wheat": "gluten",
            "dairy": "dairy",
            "milk": "dairy",
            "lactose": "dairy",
            "eggs": "eggs",
            "egg": "eggs",
            "soy": "soy",
            "soya": "soy",
            "fish": "fish",
            "shellfish": "shellfish",
            "seafood": "shellfish",
        }
        
        return normalizations.get(allergy_lower, allergy.strip())
    
    @staticmethod
    async def update_user_preferences(
        user_id: str,
        request: UpdateUserPreferencesRequest,
    ) -> UpdatePreferencesResponse:
        """
        Update user preferences (dietary restrictions, allergies, brands, disliked items).
        
        Args:
            user_id: The user's unique identifier
            request: Update preferences request with fields to add/remove
            
        Returns:
            UpdatePreferencesResponse with success status and updated fields
            
        Raises:
            HTTPException: If user not found
        """
        # Fetch user
        user = await User.find_one(User.user_id == user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}"
            )
        
        updated_fields = []
        
        # Add dietary restrictions
        if request.dietary_restrictions:
            for restriction in request.dietary_restrictions:
                restriction_clean = restriction.strip()
                restriction_lower = restriction_clean.lower()
                if restriction_lower and restriction_lower not in [
                    r.lower() for r in user.preferences.dietary_restrictions
                ]:
                    user.preferences.dietary_restrictions.append(restriction_clean)
                    updated_fields.append(f"Added dietary restriction: {restriction_clean}")
        
        # Remove dietary restrictions
        if request.remove_dietary_restrictions:
            for restriction in request.remove_dietary_restrictions:
                restriction_lower = restriction.lower().strip()
                user.preferences.dietary_restrictions = [
                    r for r in user.preferences.dietary_restrictions
                    if r.lower() != restriction_lower
                ]
                updated_fields.append(f"Removed dietary restriction: {restriction}")
        
        # Add allergies (with normalization)
        if request.allergies:
            for allergy in request.allergies:
                normalized_allergy = UserController.normalize_allergy(allergy)
                allergy_lower = normalized_allergy.lower()
                if allergy_lower and allergy_lower not in [
                    a.lower() for a in user.preferences.allergies
                ]:
                    user.preferences.allergies.append(normalized_allergy)
                    updated_fields.append(f"Added allergy: {normalized_allergy}")
        
        # Remove allergies (with normalization)
        if request.remove_allergies:
            for allergy in request.remove_allergies:
                normalized_allergy = UserController.normalize_allergy(allergy)
                allergy_lower = normalized_allergy.lower()
                user.preferences.allergies = [
                    a for a in user.preferences.allergies
                    if a.lower() != allergy_lower
                ]
                updated_fields.append(f"Removed allergy: {normalized_allergy}")
        
        # Add favorite brands
        if request.favorite_brands:
            for brand in request.favorite_brands:
                brand_clean = brand.strip()
                brand_lower = brand_clean.lower()
                if brand_lower and brand_lower not in [
                    b.lower() for b in user.preferences.favorite_brands
                ]:
                    user.preferences.favorite_brands.append(brand_clean)
                    updated_fields.append(f"Added favorite brand: {brand_clean}")
        
        # Remove favorite brands
        if request.remove_favorite_brands:
            for brand in request.remove_favorite_brands:
                brand_lower = brand.lower().strip()
                user.preferences.favorite_brands = [
                    b for b in user.preferences.favorite_brands
                    if b.lower() != brand_lower
                ]
                updated_fields.append(f"Removed favorite brand: {brand}")
        
        # Add disliked items
        if request.disliked_items:
            for item in request.disliked_items:
                item_clean = item.strip()
                item_lower = item_clean.lower()
                if item_lower and item_lower not in [
                    d.lower() for d in user.preferences.disliked_items
                ]:
                    user.preferences.disliked_items.append(item_clean)
                    updated_fields.append(f"Added disliked item: {item_clean}")
        
        # Remove disliked items
        if request.remove_disliked_items:
            for item in request.remove_disliked_items:
                item_lower = item.lower().strip()
                user.preferences.disliked_items = [
                    d for d in user.preferences.disliked_items
                    if d.lower() != item_lower
                ]
                updated_fields.append(f"Removed disliked item: {item}")
        
        # Save user if any changes were made
        if updated_fields:
            await user.save()
            logger.info(f"Updated preferences for user {user_id}: {updated_fields}")
            
            return UpdatePreferencesResponse(
                success=True,
                message=f"Preferences updated: {', '.join(updated_fields)}",
                updated_fields=updated_fields,
                current_preferences=UserPreferenceRequest(
                    dietary_restrictions=user.preferences.dietary_restrictions,
                    allergies=user.preferences.allergies,
                    favorite_brands=user.preferences.favorite_brands,
                    disliked_items=user.preferences.disliked_items,
                ),
            )
        else:
            return UpdatePreferencesResponse(
                success=False,
                message="No changes were made. Please provide fields to add or remove.",
                updated_fields=[],
                current_preferences=UserPreferenceRequest(
                    dietary_restrictions=user.preferences.dietary_restrictions,
                    allergies=user.preferences.allergies,
                    favorite_brands=user.preferences.favorite_brands,
                    disliked_items=user.preferences.disliked_items,
                ),
            )

