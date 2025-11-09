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
)
from models import UserPreference


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
                preferences=user_preferences,
            )
            
            return UserResponse(
                user_id=user.user_id,
                name=user.name,
                email=user.email,
                phone=user.phone,
                household_id=user.household_id,
                is_active=user.is_active,
                joined_date=user.joined_date.isoformat() if user.joined_date else "",
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
                household_id=user.household_id,
                is_active=user.is_active,
                joined_date=user.joined_date.isoformat() if user.joined_date else "",
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

