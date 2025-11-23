"""
SQLAlchemy database models.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    Float,
)
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class DataSourceType(str, enum.Enum):
    """Data source types."""
    GITHUB = "github"
    TWITTER = "twitter"
    GMAIL = "gmail"
    CALENDAR = "calendar"
    SLACK = "slack"
    SPOTIFY = "spotify"
    FITBIT = "fitbit"
    APPLE_HEALTH = "apple_health"
    BANK = "bank"
    RSS = "rss"
    TOGGL = "toggl"
    RESCUE_TIME = "rescue_time"


class DataSourceStatus(str, enum.Enum):
    """Data source connection status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"


class User(Base, TimestampMixin):
    """User model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    # Privacy settings
    gdpr_consent = Column(Boolean, default=False, nullable=False)
    data_retention_days = Column(Integer, default=365, nullable=False)
    anonymize_old_data = Column(Boolean, default=False, nullable=False)

    # Relationships
    data_sources = relationship("DataSource", back_populates="user", cascade="all, delete-orphan")
    metrics = relationship("Metric", back_populates="user", cascade="all, delete-orphan")
    insights = relationship("Insight", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")


class DataSource(Base, TimestampMixin):
    """Data source connection model."""
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    source_type = Column(Enum(DataSourceType), nullable=False)
    status = Column(Enum(DataSourceStatus), default=DataSourceStatus.PENDING, nullable=False)

    # OAuth credentials (encrypted)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)

    # Metadata
    last_sync_at = Column(DateTime, nullable=True)
    sync_error = Column(Text, nullable=True)
    config = Column(JSON, nullable=True)  # Source-specific configuration

    # Relationships
    user = relationship("User", back_populates="data_sources")
    raw_data = relationship("RawData", back_populates="data_source", cascade="all, delete-orphan")


class RawData(Base, TimestampMixin):
    """Raw data from external sources."""
    __tablename__ = "raw_data"

    id = Column(Integer, primary_key=True, index=True)
    data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False)
    external_id = Column(String(255), nullable=True, index=True)  # ID from external source

    # Data
    data_type = Column(String(100), nullable=False, index=True)  # commit, tweet, email, etc.
    content = Column(JSON, nullable=False)  # Actual data content
    timestamp = Column(DateTime, nullable=False, index=True)  # When the event occurred

    # Metadata
    metadata = Column(JSON, nullable=True)  # Additional metadata

    # Relationships
    data_source = relationship("DataSource", back_populates="raw_data")


class Metric(Base, TimestampMixin):
    """Aggregated metrics."""
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Metric info
    metric_type = Column(String(100), nullable=False, index=True)  # productivity, emotion, etc.
    metric_name = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)

    # Metadata
    metadata = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User", back_populates="metrics")


class Insight(Base, TimestampMixin):
    """AI-generated insights."""
    __tablename__ = "insights"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Insight info
    insight_type = Column(String(100), nullable=False, index=True)  # daily_summary, recommendation, etc.
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)

    # AI metadata
    model_used = Column(String(100), nullable=True)
    confidence_score = Column(Float, nullable=True)
    metadata = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User", back_populates="insights")


class Goal(Base, TimestampMixin):
    """User goals and habits."""
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Goal info
    goal_type = Column(String(50), nullable=False)  # habit, target, milestone
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_value = Column(Float, nullable=True)
    current_value = Column(Float, default=0.0, nullable=False)

    # Timeline
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)

    # Metadata
    metadata = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User", back_populates="goals")


class AuditLog(Base, TimestampMixin):
    """Audit log for security and compliance."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Action info
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(Integer, nullable=True)

    # Request info
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)

    # Result
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)

    # Metadata
    metadata = Column(JSON, nullable=True)
