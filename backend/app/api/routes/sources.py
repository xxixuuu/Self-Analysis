"""
Data sources API routes.
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.dependencies import get_db, get_current_user
from app.api.schemas import DataSourceResponse
from app.db.models import User, DataSource
from app.tasks.collection import trigger_collection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data-sources", tags=["Data Sources"])


@router.get("", response_model=List[DataSourceResponse])
async def get_data_sources(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all data sources for current user.

    Args:
        user: Current user
        db: Database session

    Returns:
        List of data sources
    """
    result = await db.execute(
        select(DataSource).where(DataSource.user_id == user.id)
    )
    data_sources = result.scalars().all()

    return data_sources


@router.get("/{data_source_id}", response_model=DataSourceResponse)
async def get_data_source(
    data_source_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific data source.

    Args:
        data_source_id: Data source ID
        user: Current user
        db: Database session

    Returns:
        Data source
    """
    result = await db.execute(
        select(DataSource).where(
            DataSource.id == data_source_id,
            DataSource.user_id == user.id,
        )
    )
    data_source = result.scalar_one_or_none()

    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found",
        )

    return data_source


@router.post("/{data_source_id}/sync")
async def trigger_sync(
    data_source_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger manual sync for a data source.

    Args:
        data_source_id: Data source ID
        user: Current user
        db: Database session

    Returns:
        Success message
    """
    # Verify data source belongs to user
    result = await db.execute(
        select(DataSource).where(
            DataSource.id == data_source_id,
            DataSource.user_id == user.id,
        )
    )
    data_source = result.scalar_one_or_none()

    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found",
        )

    # Trigger collection task
    try:
        trigger_collection.delay(data_source_id, force=True)
        return {"message": "Sync triggered successfully"}
    except Exception as e:
        logger.error(f"Error triggering sync: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger sync",
        )
