"""
User Service - Business logic for user management and authentication.
"""
from typing import Optional
from loguru import logger

from models import User, Household, UserPreference
from utils.auth import get_password_hash, verify_password


class UserService:
    """
    Service class for managing users and authentication.
    
    Provides business logic for user signup, login, and household management.
    """
    
    async def signup(
        self,
        name: str,
        email: Optional[str],
        password: str,
        phone: Optional[str] = None,
        splitwise_user_id: Optional[str] = None,
        preferences: Optional[UserPreference] = None,
    ) -> User:
        """
        Create a new user account.
        
        Args:
            name: User's full name
            email: User's email address (optional but recommended)
            password: Plain text password (will be hashed)
            phone: User's phone number (optional)
            splitwise_user_id: User's Splitwise ID (optional)
            preferences: User dietary preferences (optional)
            
        Returns:
            User object
            
        Raises:
            ValueError: If email already exists
        """
        # Check if email already exists
        if email:
            existing_user = await User.find_one(User.email == email)
            if existing_user:
                raise ValueError(f"Email {email} is already registered")
        
        # Hash password
        password_hash = get_password_hash(password)
        
        # Create user preferences if provided
        user_preferences = preferences if preferences else UserPreference()
        
        # Create user
        user = User(
            name=name,
            email=email,
            phone=phone,
            password_hash=password_hash,
            splitwise_user_id=splitwise_user_id,
            preferences=user_preferences,
        )
        
        await user.insert()
        logger.info(f"Created new user: {user.user_id} ({user.name})")
        
        return user
    
    async def login(self, email: str, password: str) -> User:
        """
        Authenticate a user with email and password.
        
        Args:
            email: User's email address
            password: Plain text password
            
        Returns:
            User object if authentication succeeds
            
        Raises:
            ValueError: If email or password is incorrect
        """
        # Find user by email
        user = await User.find_one(User.email == email)
        if not user:
            raise ValueError("Invalid email or password")
        
        # Verify password
        if not user.password_hash or not verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")
        
        # Check if user is active
        if not user.is_active:
            raise ValueError("User account is inactive")
        
        logger.info(f"User logged in: {user.user_id} ({user.name})")
        
        return user
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get a user by their user_id.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            User object if found, None otherwise
        """
        return await User.find_one(User.user_id == user_id)
    
    async def join_household(self, user_id: str, invite_code: str) -> Household:
        """
        Add a user to a household using an invite code.
        
        Args:
            user_id: The user's unique identifier
            invite_code: The household invite code
            
        Returns:
            The Household object the user joined
            
        Raises:
            ValueError: If invite code is invalid or user is already in a household
        """
        # Find household by invite code
        household = await Household.find_one(Household.invite_code == invite_code)
        if not household:
            raise ValueError("Invalid invite code")
        
        # Check if household is active
        if not household.is_active:
            raise ValueError("Household is not active")
        
        # Check if user is already in a household
        user = await User.find_one(User.user_id == user_id)
        if not user:
            raise ValueError("User not found")
        
        if user.household_id:
            raise ValueError("User is already a member of a household")
        
        # Add user to household
        household.add_member(user_id)
        await household.save()
        
        # Update user's household_id
        user.household_id = household.household_id
        await user.save()
        
        logger.info(f"User {user_id} joined household {household.household_id} ({household.name})")
        
        return household
    
    async def create_household(
        self,
        user_id: str,
        name: str,
        address: Optional[str] = None,
        city: Optional[str] = None,
        postal_code: Optional[str] = None,
        country: Optional[str] = None,
        whatsapp_group_id: Optional[str] = None,
        whatsapp_group_name: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Household:
        """
        Create a new household and add the user as the first member.
        
        Args:
            user_id: The user's unique identifier who is creating the household
            name: Name of the household
            address: Street address (optional)
            city: City (optional)
            postal_code: Postal/ZIP code (optional)
            country: Country (optional)
            whatsapp_group_id: WhatsApp group ID or phone number (optional)
            whatsapp_group_name: WhatsApp group name (optional)
            notes: Additional notes (optional)
            
        Returns:
            The created Household object with invite_code
            
        Raises:
            ValueError: If user not found or user is already in a household
        """
        # Check if user exists
        user = await User.find_one(User.user_id == user_id)
        if not user:
            raise ValueError("User not found")
        
        # Check if user is already in a household
        if user.household_id:
            raise ValueError("User is already a member of a household")
        
        # Create household (invite_code is automatically generated)
        household = Household(
            name=name,
            address=address,
            city=city,
            postal_code=postal_code,
            country=country,
            whatsapp_group_id=whatsapp_group_id,
            whatsapp_group_name=whatsapp_group_name,
            notes=notes,
        )
        
        # Add user as first member
        household.add_member(user_id)
        await household.insert()
        
        # Update user's household_id
        user.household_id = household.household_id
        await user.save()
        
        logger.info(f"Created household {household.household_id} ({household.name}) by user {user_id}. Invite code: {household.invite_code}")
        
        return household
    
    async def get_household_by_id(self, household_id: str) -> Optional[Household]:
        """
        Get a household by its household_id.
        
        Args:
            household_id: The household's unique identifier
            
        Returns:
            Household object if found, None otherwise
        """
        return await Household.find_one(Household.household_id == household_id)

