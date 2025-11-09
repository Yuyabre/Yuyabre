"""
Router for Splitwise OAuth authentication endpoints.
"""
from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from api.controllers.splitwise_auth_controller import SplitwiseAuthController

router = APIRouter(prefix="/auth/splitwise", tags=["Splitwise Auth"])

controller = SplitwiseAuthController()


class SplitwiseCallbackRequest(BaseModel):
    """Request model for Splitwise OAuth callback."""
    user_id: str
    oauth_token: str
    oauth_verifier: str


@router.get("/authorize")
async def authorize(
    user_id: str = Query(...),
    callback_url: str = Query(..., description="Callback URL for OAuth redirect")
):
    """
    Get authorization URL for connecting Splitwise account.
    
    Args:
        user_id: Internal user ID
        callback_url: Callback URL where Splitwise will redirect after authorization
        
    Returns:
        Authorization URL
    """
    return await controller.get_authorization_url(user_id, callback_url)


@router.get("/callback")
async def callback(
    oauth_token: str = Query(..., alias="oauth_token"),
    oauth_verifier: str = Query(..., alias="oauth_verifier")
):
    """
    Handle OAuth callback from Splitwise.
    
    This endpoint is called by Splitwise after user authorization.
    
    Args:
        oauth_token: OAuth token from callback
        oauth_verifier: OAuth verifier from callback
        
    Returns:
        HTML response with success message
    """
    result = await controller.handle_callback(oauth_token, oauth_verifier)
    
    # Return HTML response that can be displayed or auto-closed
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Splitwise Authorization</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }}
            .container {{
                background: white;
                padding: 2rem;
                border-radius: 10px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                text-align: center;
                max-width: 400px;
            }}
            .success {{
                color: #10b981;
                font-size: 3rem;
                margin-bottom: 1rem;
            }}
            h1 {{
                color: #1f2937;
                margin: 0 0 1rem 0;
            }}
            p {{
                color: #6b7280;
                margin: 0.5rem 0;
            }}
            .close-btn {{
                margin-top: 1.5rem;
                padding: 0.75rem 2rem;
                background: #667eea;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 1rem;
            }}
            .close-btn:hover {{
                background: #5568d3;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success">✓</div>
            <h1>Authorization Successful!</h1>
            <p>{result['message']}</p>
            <p>You can close this window now.</p>
            <button class="close-btn" onclick="window.close()">Close Window</button>
        </div>
        <script>
            // Auto-close after 3 seconds if opened in popup
            setTimeout(function() {{
                if (window.opener) {{
                    window.close();
                }}
            }}, 3000);
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


@router.post("")
async def handle_callback_post(request: SplitwiseCallbackRequest):
    """
    Handle OAuth callback from frontend.
    
    This endpoint receives OAuth token and verifier from the frontend
    and exchanges them for access tokens, storing them in the database.
    
    Args:
        request: Callback request with user_id, oauth_token, and oauth_verifier
        
    Returns:
        Success message
    """
    return await controller.handle_callback_post(
        request.user_id,
        request.oauth_token,
        request.oauth_verifier
    )


@router.get("/status/{user_id}")
async def get_status(user_id: str):
    """
    Check authorization status for a user.
    
    Args:
        user_id: Internal user ID
        
    Returns:
        Authorization status
    """
    return await controller.get_authorization_status(user_id)

