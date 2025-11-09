"""
Router for user-related endpoints and authentication.
"""
from fastapi import APIRouter

from api.controllers.user_controller import UserController
from api.serializers import (
    SignupRequest,
    LoginRequest,
    UserResponse,
    JoinHouseholdRequest,
    CreateHouseholdRequest,
    HouseholdResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

controller = UserController()


@router.post("/signup", response_model=UserResponse, status_code=201)
async def signup(request: SignupRequest):
    """
    Create a new user account.
    
    This endpoint allows new users to register with email and password.
    
    **Note**: Email is optional but recommended for account recovery.
    """
    return await controller.signup(request)


@router.post("/login", response_model=UserResponse)
async def login(request: LoginRequest):
    """
    Authenticate a user with email and password.
    
    Returns the user information upon successful authentication.
    """
    return await controller.login(request)


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """
    Get a user's information by user_id.
    """
    return await controller.get_user_by_id(user_id)


@router.post("/users/{user_id}/households", response_model=HouseholdResponse, status_code=201)
async def create_household_endpoint(
    user_id: str,
    request: CreateHouseholdRequest,
):
    """
    Create a new household for a user.
    
    This endpoint allows a user to create a new household if they don't have an invite code.
    The invite code is automatically generated and returned in the response.
    
    **Note**: A user can only belong to one household at a time.
    """
    return await controller.create_household(user_id, request)


@router.get("/households/{household_id}", response_model=HouseholdResponse)
async def get_household(household_id: str):
    """
    Get household information by household_id.
    
    Returns all household metadata including the invite code, address, members, etc.
    """
    return await controller.get_household_by_id(household_id)


@router.post("/users/{user_id}/join-household")
async def join_household_endpoint(
    user_id: str,
    request: JoinHouseholdRequest,
):
    """
    Add a user to a household using an invite code.
    
    The invite code is generated when a household is first created. Users must provide
    the correct invite code to join a household.
    
    **Note**: A user can only belong to one household at a time.
    """
    return await controller.join_household(user_id, request)

