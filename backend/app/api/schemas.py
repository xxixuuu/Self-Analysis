"""
Pydantic schemas for API requests and responses.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Data Source schemas
class DataSourceCreate(BaseModel):
    source_type: str
    config: Optional[Dict[str, Any]] = None


class DataSourceResponse(BaseModel):
    id: int
    source_type: str
    status: str
    last_sync_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Metric schemas
class MetricCreate(BaseModel):
    metric_type: str
    metric_name: str
    value: float
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class MetricResponse(BaseModel):
    id: int
    metric_type: str
    metric_name: str
    value: float
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# Insight schemas
class InsightResponse(BaseModel):
    id: int
    insight_type: str
    title: str
    content: str
    timestamp: datetime
    model_used: Optional[str] = None
    confidence_score: Optional[float] = None

    class Config:
        from_attributes = True


# Dashboard schemas
class DashboardStats(BaseModel):
    data_sources_connected: int
    total_activities: int
    insights_generated: int
    days_tracked: int


class ActivityOverview(BaseModel):
    date: str
    commits: int
    emails: int
    tweets: int
    total_activities: int


class ProductivityScore(BaseModel):
    date: str
    score: float
    category: str


class DashboardData(BaseModel):
    stats: DashboardStats
    recent_activities: List[Dict[str, Any]]
    recent_insights: List[InsightResponse]
    productivity_trend: List[ProductivityScore]


# Collection schemas
class CollectionTrigger(BaseModel):
    data_source_id: int
    force: bool = False


class CollectionResult(BaseModel):
    data_source_id: int
    success: bool
    items_collected: int
    error: Optional[str] = None


# Goal schemas
class GoalCreate(BaseModel):
    goal_type: str
    title: str
    description: Optional[str] = None
    target_value: Optional[float] = None
    start_date: datetime
    end_date: Optional[datetime] = None


class GoalResponse(BaseModel):
    id: int
    goal_type: str
    title: str
    description: Optional[str] = None
    target_value: Optional[float] = None
    current_value: float
    start_date: datetime
    end_date: Optional[datetime] = None
    is_active: bool
    is_completed: bool
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Query schemas
class NaturalLanguageQuery(BaseModel):
    query: str


class QueryResponse(BaseModel):
    query: str
    answer: str
    model_used: str
    confidence: Optional[float] = None


# Export schemas
class ExportRequest(BaseModel):
    format: str = "json"  # json, csv
    include_raw_data: bool = True
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
