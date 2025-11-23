"""
Admin-specific schemas for dashboard, analytics, and user management.

These schemas provide admin-only views of system data with additional
fields and metrics not exposed to regular users.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ==================== Dashboard Stats ====================


class SystemHealthMetrics(BaseModel):
    """System health and performance metrics."""
    
    database_status: str = Field(description="Database connection status (healthy/degraded/down)")
    redis_status: str = Field(description="Redis connection status (healthy/degraded/down)")
    avg_response_time_ms: float = Field(description="Average API response time in milliseconds")
    error_rate_percent: float = Field(description="Error rate as percentage")
    uptime_hours: float = Field(description="System uptime in hours")
    
    class Config:
        json_schema_extra = {
            "example": {
                "database_status": "healthy",
                "redis_status": "healthy",
                "avg_response_time_ms": 45.2,
                "error_rate_percent": 0.5,
                "uptime_hours": 168.5
            }
        }


class SubscriptionStats(BaseModel):
    """Subscription tier statistics."""
    
    free_tier_count: int = Field(description="Number of free tier organizations")
    pro_tier_count: int = Field(description="Number of pro tier organizations")
    total_active: int = Field(description="Total active subscriptions")
    total_cancelled: int = Field(description="Total cancelled subscriptions")
    total_expired: int = Field(description="Total expired subscriptions")
    monthly_recurring_revenue: float = Field(description="MRR in USD")
    
    class Config:
        json_schema_extra = {
            "example": {
                "free_tier_count": 150,
                "pro_tier_count": 45,
                "total_active": 45,
                "total_cancelled": 5,
                "total_expired": 2,
                "monthly_recurring_revenue": 1350.00
            }
        }


class ContentStats(BaseModel):
    """Content creation statistics."""
    
    total_exercises: int = Field(description="Total exercises in system")
    global_exercises: int = Field(description="Admin-created global exercises")
    custom_exercises: int = Field(description="User-created custom exercises")
    total_programs: int = Field(description="Total training programs")
    program_templates: int = Field(description="Admin-created templates")
    custom_programs: int = Field(description="User-created programs")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_exercises": 250,
                "global_exercises": 200,
                "custom_exercises": 50,
                "total_programs": 120,
                "program_templates": 15,
                "custom_programs": 105
            }
        }


class AdminDashboardStats(BaseModel):
    """
    Comprehensive dashboard statistics for admin overview.
    
    Provides high-level metrics for system monitoring and management.
    """
    
    # User metrics
    total_users: int = Field(description="Total registered users")
    active_users: int = Field(description="Users active in last 30 days")
    verified_users: int = Field(description="Users with verified email")
    suspended_users: int = Field(description="Suspended user accounts")
    
    # Organization metrics
    total_organizations: int = Field(description="Total organizations")
    active_organizations: int = Field(description="Organizations with active users")
    
    # Subscription metrics
    subscription_stats: SubscriptionStats
    
    # Content metrics
    content_stats: ContentStats
    
    # System health
    system_health: SystemHealthMetrics
    
    # Timestamp
    generated_at: datetime = Field(description="When stats were generated")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_users": 500,
                "active_users": 320,
                "verified_users": 450,
                "suspended_users": 5,
                "total_organizations": 195,
                "active_organizations": 180,
                "subscription_stats": {
                    "free_tier_count": 150,
                    "pro_tier_count": 45,
                    "total_active": 45,
                    "total_cancelled": 5,
                    "total_expired": 2,
                    "monthly_recurring_revenue": 1350.00
                },
                "content_stats": {
                    "total_exercises": 250,
                    "global_exercises": 200,
                    "custom_exercises": 50,
                    "total_programs": 120,
                    "program_templates": 15,
                    "custom_programs": 105
                },
                "system_health": {
                    "database_status": "healthy",
                    "redis_status": "healthy",
                    "avg_response_time_ms": 45.2,
                    "error_rate_percent": 0.5,
                    "uptime_hours": 168.5
                },
                "generated_at": "2025-11-23T10:00:00Z"
            }
        }


# ==================== User Management ====================


class UserAdminDetails(BaseModel):
    """
    User details with admin-only fields.
    
    Includes additional information not exposed in regular user responses.
    """
    
    id: UUID
    email: str
    full_name: str | None = None
    role: str = Field(description="User role (USER, ADMIN)")
    is_active: bool
    is_verified: bool
    
    # Organization info
    organization_id: UUID
    organization_name: str
    subscription_tier: str = Field(description="Organization subscription tier")
    
    # Activity metrics
    last_login_at: datetime | None = Field(description="Last successful login")
    created_at: datetime
    updated_at: datetime
    
    # Admin-only fields
    login_count: int = Field(default=0, description="Total number of logins")
    programs_created: int = Field(default=0, description="Programs created by user")
    exercises_created: int = Field(default=0, description="Custom exercises created")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "full_name": "John Doe",
                "role": "USER",
                "is_active": True,
                "is_verified": True,
                "organization_id": "223e4567-e89b-12d3-a456-426614174001",
                "organization_name": "John's Gym",
                "subscription_tier": "PRO",
                "last_login_at": "2025-11-23T09:00:00Z",
                "created_at": "2025-10-01T10:00:00Z",
                "updated_at": "2025-11-23T09:00:00Z",
                "login_count": 45,
                "programs_created": 3,
                "exercises_created": 5
            }
        }


class UserListResponse(BaseModel):
    """Paginated list of users with admin details."""
    
    items: list[UserAdminDetails]
    total: int = Field(description="Total matching users")
    page: int = Field(description="Current page number (1-indexed)")
    page_size: int = Field(description="Items per page")
    has_more: bool = Field(description="Whether more pages exist")
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 500,
                "page": 1,
                "page_size": 20,
                "has_more": True
            }
        }


class UserFilter(BaseModel):
    """Filters for user list queries."""
    
    search: str | None = Field(None, description="Search in email and name")
    role: str | None = Field(None, description="Filter by role")
    is_active: bool | None = Field(None, description="Filter by active status")
    is_verified: bool | None = Field(None, description="Filter by verification status")
    subscription_tier: str | None = Field(None, description="Filter by org subscription tier")
    skip: int = Field(0, ge=0, description="Pagination offset")
    limit: int = Field(20, ge=1, le=100, description="Items per page")
    
    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str | None) -> str | None:
        """Validate role is valid."""
        if v is not None and v not in ["USER", "ADMIN"]:
            raise ValueError("Role must be USER or ADMIN")
        return v
    
    @field_validator("subscription_tier")
    @classmethod
    def validate_subscription_tier(cls, v: str | None) -> str | None:
        """Validate subscription tier is valid."""
        if v is not None and v not in ["FREE", "PRO"]:
            raise ValueError("Subscription tier must be FREE or PRO")
        return v


class UpdateUserRoleRequest(BaseModel):
    """Request to update user role."""
    
    role: str = Field(description="New role (USER or ADMIN)")
    
    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role is valid."""
        if v not in ["USER", "ADMIN"]:
            raise ValueError("Role must be USER or ADMIN")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "ADMIN"
            }
        }


class UserActionResponse(BaseModel):
    """Response for user actions (suspend, delete, etc.)."""
    
    success: bool
    message: str
    user_id: UUID
    action: str = Field(description="Action performed (suspend, delete, etc.)")
    performed_at: datetime
    performed_by: UUID = Field(description="Admin user who performed action")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "User suspended successfully",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "action": "suspend",
                "performed_at": "2025-11-23T10:00:00Z",
                "performed_by": "223e4567-e89b-12d3-a456-426614174001"
            }
        }


# ==================== Analytics ====================


class SubscriptionAnalytics(BaseModel):
    """
    Detailed subscription analytics for business intelligence.
    
    Provides insights into subscription trends, revenue, and churn.
    """
    
    # Current state
    total_subscribers: int
    active_subscribers: int
    cancelled_subscribers: int
    expired_subscribers: int
    
    # Revenue metrics
    monthly_recurring_revenue: float = Field(description="Total MRR in USD")
    average_revenue_per_user: float = Field(description="ARPU in USD")
    
    # Growth metrics
    new_subscriptions_this_month: int
    cancellations_this_month: int
    churn_rate_percent: float = Field(description="Monthly churn rate")
    
    # Tier breakdown
    free_tier_percentage: float
    pro_tier_percentage: float
    
    # Historical data (last 12 months)
    monthly_revenue_history: list[dict] = Field(
        description="Revenue by month (date, amount)"
    )
    subscription_growth_history: list[dict] = Field(
        description="Subscriber count by month (date, count)"
    )
    
    # Timestamp
    generated_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_subscribers": 45,
                "active_subscribers": 43,
                "cancelled_subscribers": 2,
                "expired_subscribers": 0,
                "monthly_recurring_revenue": 1350.00,
                "average_revenue_per_user": 31.40,
                "new_subscriptions_this_month": 5,
                "cancellations_this_month": 1,
                "churn_rate_percent": 2.3,
                "free_tier_percentage": 76.9,
                "pro_tier_percentage": 23.1,
                "monthly_revenue_history": [
                    {"date": "2025-10", "amount": 1200.00},
                    {"date": "2025-11", "amount": 1350.00}
                ],
                "subscription_growth_history": [
                    {"date": "2025-10", "count": 40},
                    {"date": "2025-11", "count": 45}
                ],
                "generated_at": "2025-11-23T10:00:00Z"
            }
        }


class UsageMetrics(BaseModel):
    """Usage metrics for a specific resource type."""
    
    total_count: int
    created_this_month: int
    created_this_week: int
    most_popular: list[dict] = Field(
        description="Most popular items (id, name, usage_count)"
    )


class UsageAnalytics(BaseModel):
    """
    System usage analytics for understanding user behavior.
    
    Tracks content creation, feature usage, and engagement metrics.
    """
    
    # User engagement
    daily_active_users: int = Field(description="Users active in last 24 hours")
    weekly_active_users: int = Field(description="Users active in last 7 days")
    monthly_active_users: int = Field(description="Users active in last 30 days")
    
    # Content usage
    exercise_metrics: UsageMetrics
    program_metrics: UsageMetrics
    
    # Feature adoption
    users_with_custom_exercises: int
    users_with_custom_programs: int
    users_with_cloned_templates: int
    
    # Activity trends
    avg_programs_per_user: float
    avg_exercises_per_program: float
    avg_sessions_per_program: float
    
    # Top statistics
    most_used_exercises: list[dict] = Field(
        description="Top 10 exercises by usage (id, name, count)"
    )
    most_cloned_templates: list[dict] = Field(
        description="Top 10 templates by clones (id, name, clone_count)"
    )
    
    # Timestamp
    generated_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "daily_active_users": 120,
                "weekly_active_users": 280,
                "monthly_active_users": 320,
                "exercise_metrics": {
                    "total_count": 250,
                    "created_this_month": 15,
                    "created_this_week": 3,
                    "most_popular": []
                },
                "program_metrics": {
                    "total_count": 120,
                    "created_this_month": 25,
                    "created_this_week": 6,
                    "most_popular": []
                },
                "users_with_custom_exercises": 45,
                "users_with_custom_programs": 78,
                "users_with_cloned_templates": 65,
                "avg_programs_per_user": 2.4,
                "avg_exercises_per_program": 12.5,
                "avg_sessions_per_program": 3.8,
                "most_used_exercises": [],
                "most_cloned_templates": [],
                "generated_at": "2025-11-23T10:00:00Z"
            }
        }


# ==================== Audit Trail ====================


class AuditLogEntry(BaseModel):
    """Single audit log entry for admin actions."""
    
    id: UUID
    admin_user_id: UUID = Field(description="Admin who performed action")
    admin_email: str = Field(description="Email of admin user")
    action: str = Field(description="Action performed (e.g., 'user.suspend', 'exercise.create')")
    resource_type: str = Field(description="Type of resource affected (user, exercise, program)")
    resource_id: UUID | None = Field(description="ID of affected resource")
    details: dict = Field(description="Additional action details")
    ip_address: str | None = Field(description="IP address of admin")
    user_agent: str | None = Field(description="User agent of admin")
    created_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "423e4567-e89b-12d3-a456-426614174003",
                "admin_user_id": "123e4567-e89b-12d3-a456-426614174000",
                "admin_email": "admin@hypertroq.com",
                "action": "user.suspend",
                "resource_type": "user",
                "resource_id": "223e4567-e89b-12d3-a456-426614174001",
                "details": {
                    "reason": "Terms of service violation",
                    "previous_status": "active"
                },
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0...",
                "created_at": "2025-11-23T10:00:00Z"
            }
        }


class AuditLogResponse(BaseModel):
    """Paginated audit log response."""
    
    items: list[AuditLogEntry]
    total: int
    page: int
    page_size: int
    has_more: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 1500,
                "page": 1,
                "page_size": 50,
                "has_more": True
            }
        }
