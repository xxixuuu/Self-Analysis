"""
OAuth2 authentication routes.
"""
import logging
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.dependencies import get_db, get_current_user
from app.db.models import User, DataSource, DataSourceType, DataSourceStatus
from app.core.config import settings
from app.core.security import encryption_manager, generate_state_token
from app.core.redis import redis_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/oauth", tags=["OAuth2"])


# GitHub OAuth2
@router.get("/github/authorize")
async def github_authorize(
    user: User = Depends(get_current_user),
):
    """
    Initiate GitHub OAuth2 flow.

    Returns:
        Redirect to GitHub authorization page
    """
    if not settings.github_client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GitHub OAuth not configured",
        )

    # Generate state token for CSRF protection
    state = generate_state_token()

    # Store state in Redis (expires in 10 minutes)
    await redis_client.set(f"oauth_state:{state}", str(user.id), expire=600)

    # GitHub OAuth URL
    auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.github_client_id}"
        f"&redirect_uri={settings.github_redirect_uri}"
        f"&scope=repo,user"
        f"&state={state}"
    )

    return RedirectResponse(url=auth_url)


@router.get("/github/callback")
async def github_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle GitHub OAuth2 callback.

    Args:
        code: Authorization code from GitHub
        state: State token for CSRF protection
        db: Database session

    Returns:
        Redirect to frontend with success/error
    """
    # Verify state token
    user_id = await redis_client.get(f"oauth_state:{state}")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state token",
        )

    # Delete state token
    await redis_client.delete(f"oauth_state:{state}")

    try:
        # Exchange code for access token
        import httpx

        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": settings.github_client_id,
                    "client_secret": settings.github_client_secret,
                    "code": code,
                    "redirect_uri": settings.github_redirect_uri,
                },
            )

            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange code for token",
                )

            token_data = token_response.json()
            access_token = token_data.get("access_token")

            if not access_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No access token received",
                )

        # Encrypt access token
        encrypted_token = encryption_manager.encrypt(access_token)

        # Check if data source already exists
        result = await db.execute(
            select(DataSource).where(
                DataSource.user_id == int(user_id),
                DataSource.source_type == DataSourceType.GITHUB,
            )
        )
        data_source = result.scalar_one_or_none()

        if data_source:
            # Update existing data source
            data_source.access_token = encrypted_token
            data_source.status = DataSourceStatus.ACTIVE
            data_source.sync_error = None
        else:
            # Create new data source
            data_source = DataSource(
                user_id=int(user_id),
                source_type=DataSourceType.GITHUB,
                access_token=encrypted_token,
                status=DataSourceStatus.ACTIVE,
            )
            db.add(data_source)

        await db.commit()

        # Redirect to frontend success page
        return RedirectResponse(
            url=f"{settings.cors_origins[0]}/sources?success=github"
        )

    except Exception as e:
        logger.error(f"GitHub OAuth error: {e}")
        return RedirectResponse(
            url=f"{settings.cors_origins[0]}/sources?error=github"
        )


# Google OAuth2 (Gmail, Calendar)
@router.get("/google/authorize")
async def google_authorize(
    service: str = Query(..., regex="^(gmail|calendar)$"),
    user: User = Depends(get_current_user),
):
    """
    Initiate Google OAuth2 flow.

    Args:
        service: Service to authorize (gmail or calendar)

    Returns:
        Redirect to Google authorization page
    """
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured",
        )

    # Generate state token
    state = generate_state_token()

    # Store state and service type in Redis
    await redis_client.set(
        f"oauth_state:{state}",
        f"{user.id}:{service}",
        expire=600,
    )

    # Define scopes based on service
    if service == "gmail":
        scopes = "https://www.googleapis.com/auth/gmail.readonly"
    else:  # calendar
        scopes = "https://www.googleapis.com/auth/calendar.readonly"

    # Google OAuth URL
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.google_client_id}"
        f"&redirect_uri={settings.google_redirect_uri}"
        f"&response_type=code"
        f"&scope={scopes}"
        f"&access_type=offline"
        f"&state={state}"
    )

    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Google OAuth2 callback.

    Args:
        code: Authorization code from Google
        state: State token for CSRF protection
        db: Database session

    Returns:
        Redirect to frontend with success/error
    """
    # Verify state token
    state_data = await redis_client.get(f"oauth_state:{state}")
    if not state_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state token",
        )

    # Parse state data
    user_id, service = state_data.split(":")

    # Delete state token
    await redis_client.delete(f"oauth_state:{state}")

    try:
        # Exchange code for access token
        import httpx

        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "code": code,
                    "redirect_uri": settings.google_redirect_uri,
                    "grant_type": "authorization_code",
                },
            )

            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange code for token",
                )

            token_data = token_response.json()
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")

            if not access_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No access token received",
                )

        # Encrypt tokens
        encrypted_access = encryption_manager.encrypt(access_token)
        encrypted_refresh = encryption_manager.encrypt(refresh_token) if refresh_token else None

        # Calculate expiration
        expires_in = token_data.get("expires_in", 3600)
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        # Determine source type
        source_type = DataSourceType.GMAIL if service == "gmail" else DataSourceType.CALENDAR

        # Check if data source already exists
        result = await db.execute(
            select(DataSource).where(
                DataSource.user_id == int(user_id),
                DataSource.source_type == source_type,
            )
        )
        data_source = result.scalar_one_or_none()

        if data_source:
            # Update existing data source
            data_source.access_token = encrypted_access
            data_source.refresh_token = encrypted_refresh
            data_source.token_expires_at = expires_at
            data_source.status = DataSourceStatus.ACTIVE
            data_source.sync_error = None
        else:
            # Create new data source
            data_source = DataSource(
                user_id=int(user_id),
                source_type=source_type,
                access_token=encrypted_access,
                refresh_token=encrypted_refresh,
                token_expires_at=expires_at,
                status=DataSourceStatus.ACTIVE,
            )
            db.add(data_source)

        await db.commit()

        # Redirect to frontend success page
        return RedirectResponse(
            url=f"{settings.cors_origins[0]}/sources?success={service}"
        )

    except Exception as e:
        logger.error(f"Google OAuth error: {e}")
        return RedirectResponse(
            url=f"{settings.cors_origins[0]}/sources?error={service}"
        )


# Twitter OAuth2
@router.get("/twitter/authorize")
async def twitter_authorize(
    user: User = Depends(get_current_user),
):
    """
    Initiate Twitter OAuth2 flow.

    Returns:
        Redirect to Twitter authorization page
    """
    if not settings.twitter_client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Twitter OAuth not configured",
        )

    # Generate state token
    state = generate_state_token()

    # Store state in Redis
    await redis_client.set(f"oauth_state:{state}", str(user.id), expire=600)

    # Twitter OAuth URL (OAuth 2.0)
    auth_url = (
        f"https://twitter.com/i/oauth2/authorize"
        f"?response_type=code"
        f"&client_id={settings.twitter_client_id}"
        f"&redirect_uri={settings.twitter_redirect_uri}"
        f"&scope=tweet.read%20users.read%20like.read"
        f"&state={state}"
        f"&code_challenge=challenge"
        f"&code_challenge_method=plain"
    )

    return RedirectResponse(url=auth_url)


@router.get("/twitter/callback")
async def twitter_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Twitter OAuth2 callback.

    Args:
        code: Authorization code from Twitter
        state: State token for CSRF protection
        db: Database session

    Returns:
        Redirect to frontend with success/error
    """
    # Verify state token
    user_id = await redis_client.get(f"oauth_state:{state}")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state token",
        )

    # Delete state token
    await redis_client.delete(f"oauth_state:{state}")

    try:
        # Exchange code for access token
        import httpx
        import base64

        # Create Basic Auth header
        auth_str = f"{settings.twitter_client_id}:{settings.twitter_client_secret}"
        auth_bytes = base64.b64encode(auth_str.encode()).decode()

        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://api.twitter.com/2/oauth2/token",
                headers={
                    "Authorization": f"Basic {auth_bytes}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.twitter_redirect_uri,
                    "code_verifier": "challenge",
                },
            )

            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange code for token",
                )

            token_data = token_response.json()
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")

            if not access_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No access token received",
                )

        # Encrypt tokens
        encrypted_access = encryption_manager.encrypt(access_token)
        encrypted_refresh = encryption_manager.encrypt(refresh_token) if refresh_token else None

        # Calculate expiration
        expires_in = token_data.get("expires_in", 7200)
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        # Check if data source already exists
        result = await db.execute(
            select(DataSource).where(
                DataSource.user_id == int(user_id),
                DataSource.source_type == DataSourceType.TWITTER,
            )
        )
        data_source = result.scalar_one_or_none()

        if data_source:
            # Update existing data source
            data_source.access_token = encrypted_access
            data_source.refresh_token = encrypted_refresh
            data_source.token_expires_at = expires_at
            data_source.status = DataSourceStatus.ACTIVE
            data_source.sync_error = None
        else:
            # Create new data source
            data_source = DataSource(
                user_id=int(user_id),
                source_type=DataSourceType.TWITTER,
                access_token=encrypted_access,
                refresh_token=encrypted_refresh,
                token_expires_at=expires_at,
                status=DataSourceStatus.ACTIVE,
            )
            db.add(data_source)

        await db.commit()

        # Redirect to frontend success page
        return RedirectResponse(
            url=f"{settings.cors_origins[0]}/sources?success=twitter"
        )

    except Exception as e:
        logger.error(f"Twitter OAuth error: {e}")
        return RedirectResponse(
            url=f"{settings.cors_origins[0]}/sources?error=twitter"
        )


# Disconnect data source
@router.delete("/disconnect/{source_type}")
async def disconnect_data_source(
    source_type: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Disconnect a data source.

    Args:
        source_type: Data source type (github, twitter, gmail, calendar)
        user: Current user
        db: Database session

    Returns:
        Success message
    """
    # Map string to enum
    type_map = {
        "github": DataSourceType.GITHUB,
        "twitter": DataSourceType.TWITTER,
        "gmail": DataSourceType.GMAIL,
        "calendar": DataSourceType.CALENDAR,
    }

    if source_type not in type_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid source type",
        )

    # Find and delete data source
    result = await db.execute(
        select(DataSource).where(
            DataSource.user_id == user.id,
            DataSource.source_type == type_map[source_type],
        )
    )
    data_source = result.scalar_one_or_none()

    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found",
        )

    await db.delete(data_source)
    await db.commit()

    return {"message": f"{source_type} disconnected successfully"}
