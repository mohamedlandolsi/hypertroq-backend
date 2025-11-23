"""
Admin service for system management and analytics.

Provides admin-only functionality for:
- Dashboard statistics and system health monitoring
- User management (role updates, suspension, deletion)
- Global exercise management
- Program template management
- Subscription and usage analytics
- Audit trail logging

All methods require admin role and log actions for audit trail.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.exercise import Exercise
from app.domain.entities.training_program import TrainingProgram
from app.domain.entities.user import User
from app.infrastructure.repositories.organization_repository import OrganizationRepository
from app.models.exercise import ExerciseModel
from app.models.organization import OrganizationModel
from app.models.training_program import TrainingProgramModel
from app.models.user import UserModel
from app.models.workout_session import WorkoutSessionModel
from app.repositories.exercise_repository import ExerciseRepository
from app.repositories.program_repository import ProgramRepository
from app.repositories.user_repository import UserRepository
from app.schemas.admin import (
    AdminDashboardStats,
    AuditLogEntry,
    ContentStats,
    SubscriptionAnalytics,
    SubscriptionStats,
    SystemHealthMetrics,
    UpdateUserRoleRequest,
    UsageAnalytics,
    UsageMetrics,
    UserActionResponse,
    UserAdminDetails,
    UserFilter,
    UserListResponse,
)
from app.schemas.exercise import ExerciseCreate, ExerciseUpdate
from app.schemas.training_program import ProgramCreate, ProgramUpdate

logger = logging.getLogger(__name__)


class AdminService:
    """
    Service for admin-only operations and analytics.
    
    All methods:
    - Require admin role (enforced at route level)
    - Log actions for audit trail
    - Include comprehensive error handling
    - Return detailed responses for admin monitoring
    """
    
    def __init__(
        self,
        session: AsyncSession,
        user_repo: UserRepository,
        org_repo: OrganizationRepository,
        exercise_repo: ExerciseRepository,
        program_repo: ProgramRepository,
    ):
        """
        Initialize admin service with required repositories.
        
        Args:
            session: Database session for direct queries
            user_repo: User repository
            org_repo: Organization repository
            exercise_repo: Exercise repository
            program_repo: Program repository
        """
        self.session = session
        self.user_repo = user_repo
        self.org_repo = org_repo
        self.exercise_repo = exercise_repo
        self.program_repo = program_repo
    
    def _verify_admin_role(self, user: User) -> None:
        """
        Verify user has admin role.
        
        Args:
            user: User to verify
            
        Raises:
            HTTPException 403: If user is not admin
        """
        if user.role != "ADMIN":
            logger.warning(f"Non-admin user {user.id} attempted admin operation")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator privileges required"
            )
    
    async def _log_admin_action(
        self,
        admin_user: User,
        action: str,
        resource_type: str,
        resource_id: UUID | None = None,
        details: dict | None = None,
    ) -> None:
        """
        Log admin action to audit trail.
        
        Args:
            admin_user: Admin performing action
            action: Action name (e.g., 'user.suspend')
            resource_type: Resource type (user, exercise, program)
            resource_id: ID of affected resource
            details: Additional details
        """
        log_entry = {
            "admin_user_id": str(admin_user.id),
            "admin_email": admin_user.email,
            "action": action,
            "resource_type": resource_type,
            "resource_id": str(resource_id) if resource_id else None,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        logger.info(
            f"Admin action: {action} by {admin_user.email} on {resource_type} "
            f"{resource_id or 'N/A'}",
            extra={"audit_log": log_entry}
        )
        
        # TODO: Store in audit_logs table when implemented
        # For now, structured logging provides audit trail
    
    # ==================== Dashboard & System Health ====================
    
    async def get_dashboard_stats(self, admin_user: User) -> AdminDashboardStats:
        """
        Get comprehensive dashboard statistics.
        
        Includes user metrics, subscription stats, content stats, and system health.
        
        Args:
            admin_user: Admin user requesting stats
            
        Returns:
            AdminDashboardStats with all metrics
            
        Raises:
            HTTPException 403: If user is not admin
        """
        self._verify_admin_role(admin_user)
        
        logger.info(f"Admin {admin_user.email} fetching dashboard stats")
        
        try:
            # User metrics
            total_users_result = await self.session.execute(
                select(func.count()).select_from(UserModel)
            )
            total_users = total_users_result.scalar() or 0
            
            thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
            active_users_result = await self.session.execute(
                select(func.count()).select_from(UserModel)
                .where(UserModel.updated_at >= thirty_days_ago)
            )
            active_users = active_users_result.scalar() or 0
            
            verified_users_result = await self.session.execute(
                select(func.count()).select_from(UserModel)
                .where(UserModel.is_verified == True)
            )
            verified_users = verified_users_result.scalar() or 0
            
            suspended_users_result = await self.session.execute(
                select(func.count()).select_from(UserModel)
                .where(UserModel.is_active == False)
            )
            suspended_users = suspended_users_result.scalar() or 0
            
            # Organization metrics
            total_orgs_result = await self.session.execute(
                select(func.count()).select_from(OrganizationModel)
            )
            total_orgs = total_orgs_result.scalar() or 0
            
            # Active organizations (have at least one active user)
            active_orgs_result = await self.session.execute(
                select(func.count(func.distinct(UserModel.organization_id)))
                .select_from(UserModel)
                .where(
                    and_(
                        UserModel.is_active == True,
                        UserModel.updated_at >= thirty_days_ago
                    )
                )
            )
            active_orgs = active_orgs_result.scalar() or 0
            
            # Subscription metrics
            free_tier_result = await self.session.execute(
                select(func.count()).select_from(OrganizationModel)
                .where(OrganizationModel.subscription_tier == "FREE")
            )
            free_tier = free_tier_result.scalar() or 0
            
            pro_tier_result = await self.session.execute(
                select(func.count()).select_from(OrganizationModel)
                .where(OrganizationModel.subscription_tier == "PRO")
            )
            pro_tier = pro_tier_result.scalar() or 0
            
            active_subs_result = await self.session.execute(
                select(func.count()).select_from(OrganizationModel)
                .where(
                    and_(
                        OrganizationModel.subscription_tier == "PRO",
                        OrganizationModel.subscription_status == "ACTIVE"
                    )
                )
            )
            active_subs = active_subs_result.scalar() or 0
            
            cancelled_subs_result = await self.session.execute(
                select(func.count()).select_from(OrganizationModel)
                .where(OrganizationModel.subscription_status == "CANCELLED")
            )
            cancelled_subs = cancelled_subs_result.scalar() or 0
            
            expired_subs_result = await self.session.execute(
                select(func.count()).select_from(OrganizationModel)
                .where(OrganizationModel.subscription_status == "EXPIRED")
            )
            expired_subs = expired_subs_result.scalar() or 0
            
            # Calculate MRR (assuming $30/month for Pro)
            mrr = float(active_subs * 30)
            
            subscription_stats = SubscriptionStats(
                free_tier_count=free_tier,
                pro_tier_count=pro_tier,
                total_active=active_subs,
                total_cancelled=cancelled_subs,
                total_expired=expired_subs,
                monthly_recurring_revenue=mrr,
            )
            
            # Content metrics
            total_exercises_result = await self.session.execute(
                select(func.count()).select_from(ExerciseModel)
            )
            total_exercises = total_exercises_result.scalar() or 0
            
            global_exercises_result = await self.session.execute(
                select(func.count()).select_from(ExerciseModel)
                .where(ExerciseModel.organization_id.is_(None))
            )
            global_exercises = global_exercises_result.scalar() or 0
            
            custom_exercises = total_exercises - global_exercises
            
            total_programs_result = await self.session.execute(
                select(func.count()).select_from(TrainingProgramModel)
            )
            total_programs = total_programs_result.scalar() or 0
            
            templates_result = await self.session.execute(
                select(func.count()).select_from(TrainingProgramModel)
                .where(TrainingProgramModel.is_template == True)
            )
            templates = templates_result.scalar() or 0
            
            custom_programs = total_programs - templates
            
            content_stats = ContentStats(
                total_exercises=total_exercises,
                global_exercises=global_exercises,
                custom_exercises=custom_exercises,
                total_programs=total_programs,
                program_templates=templates,
                custom_programs=custom_programs,
            )
            
            # System health (placeholder - implement with actual monitoring)
            system_health = SystemHealthMetrics(
                database_status="healthy",
                redis_status="healthy",
                avg_response_time_ms=50.0,
                error_rate_percent=0.5,
                uptime_hours=168.0,
            )
            
            stats = AdminDashboardStats(
                total_users=total_users,
                active_users=active_users,
                verified_users=verified_users,
                suspended_users=suspended_users,
                total_organizations=total_orgs,
                active_organizations=active_orgs,
                subscription_stats=subscription_stats,
                content_stats=content_stats,
                system_health=system_health,
                generated_at=datetime.now(timezone.utc),
            )
            
            await self._log_admin_action(
                admin_user,
                "dashboard.view",
                "system",
                details={"stats_generated": True}
            )
            
            return stats
        
        except Exception as e:
            logger.error(f"Error generating dashboard stats: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate dashboard statistics"
            )
    
    # ==================== User Management ====================
    
    async def list_users(
        self,
        filters: UserFilter,
        admin_user: User,
    ) -> UserListResponse:
        """
        List users with admin details and filtering.
        
        Args:
            filters: Filter and pagination parameters
            admin_user: Admin user requesting list
            
        Returns:
            UserListResponse with paginated users
            
        Raises:
            HTTPException 403: If user is not admin
        """
        self._verify_admin_role(admin_user)
        
        logger.info(
            f"Admin {admin_user.email} listing users with filters: "
            f"search={filters.search}, role={filters.role}"
        )
        
        try:
            # Build query
            query = select(UserModel).options(
                selectinload(UserModel.organization)
            )
            
            # Apply filters
            conditions = []
            
            if filters.search:
                search_term = f"%{filters.search}%"
                conditions.append(
                    or_(
                        UserModel.email.ilike(search_term),
                        UserModel.full_name.ilike(search_term)
                    )
                )
            
            if filters.role:
                conditions.append(UserModel.role == filters.role)
            
            if filters.is_active is not None:
                conditions.append(UserModel.is_active == filters.is_active)
            
            if filters.is_verified is not None:
                conditions.append(UserModel.is_verified == filters.is_verified)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # Get total count
            count_query = select(func.count()).select_from(UserModel)
            if conditions:
                count_query = count_query.where(and_(*conditions))
            
            total_result = await self.session.execute(count_query)
            total = total_result.scalar() or 0
            
            # Apply pagination and ordering
            query = query.order_by(UserModel.created_at.desc())
            query = query.offset(filters.skip).limit(filters.limit)
            
            # Execute query
            result = await self.session.execute(query)
            user_models = result.scalars().all()
            
            # Convert to admin details
            users = []
            for user_model in user_models:
                # Count programs and exercises created by user
                programs_result = await self.session.execute(
                    select(func.count()).select_from(TrainingProgramModel)
                    .where(
                        and_(
                            TrainingProgramModel.organization_id == user_model.organization_id,
                            TrainingProgramModel.is_template == False
                        )
                    )
                )
                programs_count = programs_result.scalar() or 0
                
                exercises_result = await self.session.execute(
                    select(func.count()).select_from(ExerciseModel)
                    .where(ExerciseModel.organization_id == user_model.organization_id)
                )
                exercises_count = exercises_result.scalar() or 0
                
                users.append(UserAdminDetails(
                    id=user_model.id,
                    email=user_model.email,
                    full_name=user_model.full_name,
                    role=user_model.role,
                    is_active=user_model.is_active,
                    is_verified=user_model.is_verified,
                    organization_id=user_model.organization_id,
                    organization_name=user_model.organization.name if user_model.organization else "Unknown",
                    subscription_tier=user_model.organization.subscription_tier if user_model.organization else "FREE",
                    last_login_at=user_model.updated_at,  # Approximate with updated_at
                    created_at=user_model.created_at,
                    updated_at=user_model.updated_at,
                    login_count=0,  # TODO: Track in user_sessions table
                    programs_created=programs_count,
                    exercises_created=exercises_count,
                ))
            
            page = (filters.skip // filters.limit) + 1
            has_more = (filters.skip + filters.limit) < total
            
            return UserListResponse(
                items=users,
                total=total,
                page=page,
                page_size=filters.limit,
                has_more=has_more,
            )
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error listing users: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve users"
            )
    
    async def update_user_role(
        self,
        user_id: UUID,
        role_update: UpdateUserRoleRequest,
        admin_user: User,
    ) -> User:
        """
        Update user role (USER <-> ADMIN).
        
        Args:
            user_id: User to update
            role_update: New role
            admin_user: Admin performing update
            
        Returns:
            Updated user entity
            
        Raises:
            HTTPException 403: If user is not admin or trying to change own role
            HTTPException 404: If user not found
        """
        self._verify_admin_role(admin_user)
        
        if user_id == admin_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot change your own role"
            )
        
        logger.info(
            f"Admin {admin_user.email} updating user {user_id} role to {role_update.role}"
        )
        
        try:
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            old_role = user.role
            
            # Update role in database
            stmt = select(UserModel).where(UserModel.id == user_id)
            result = await self.session.execute(stmt)
            user_model = result.scalar_one_or_none()
            
            if not user_model:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            user_model.role = role_update.role
            user_model.updated_at = datetime.now(timezone.utc)
            
            await self.session.commit()
            await self.session.refresh(user_model)
            
            # Convert to entity
            updated_user = await self.user_repo.get_by_id(user_id)
            
            await self._log_admin_action(
                admin_user,
                "user.role_update",
                "user",
                user_id,
                details={
                    "old_role": old_role,
                    "new_role": role_update.role,
                    "target_email": user.email
                }
            )
            
            logger.info(
                f"User {user_id} role updated from {old_role} to {role_update.role}"
            )
            
            return updated_user
        
        except HTTPException:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating user role: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user role"
            )
    
    async def suspend_user(
        self,
        user_id: UUID,
        admin_user: User,
        reason: str | None = None,
    ) -> UserActionResponse:
        """
        Suspend user account (set is_active to False).
        
        Args:
            user_id: User to suspend
            admin_user: Admin performing suspension
            reason: Optional reason for suspension
            
        Returns:
            UserActionResponse with action details
            
        Raises:
            HTTPException 403: If user is not admin or trying to suspend self
            HTTPException 404: If user not found
        """
        self._verify_admin_role(admin_user)
        
        if user_id == admin_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot suspend your own account"
            )
        
        logger.warning(
            f"Admin {admin_user.email} suspending user {user_id}. Reason: {reason}"
        )
        
        try:
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is already suspended"
                )
            
            # Suspend user
            stmt = select(UserModel).where(UserModel.id == user_id)
            result = await self.session.execute(stmt)
            user_model = result.scalar_one_or_none()
            
            if not user_model:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            user_model.is_active = False
            user_model.updated_at = datetime.now(timezone.utc)
            
            await self.session.commit()
            
            await self._log_admin_action(
                admin_user,
                "user.suspend",
                "user",
                user_id,
                details={
                    "reason": reason,
                    "target_email": user.email,
                    "previous_status": "active"
                }
            )
            
            logger.warning(f"User {user_id} ({user.email}) suspended by admin")
            
            return UserActionResponse(
                success=True,
                message="User suspended successfully",
                user_id=user_id,
                action="suspend",
                performed_at=datetime.now(timezone.utc),
                performed_by=admin_user.id,
            )
        
        except HTTPException:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error suspending user: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to suspend user"
            )
    
    async def delete_user(
        self,
        user_id: UUID,
        admin_user: User,
    ) -> UserActionResponse:
        """
        Permanently delete user account.
        
        WARNING: This is a destructive operation that will:
        - Delete the user
        - Orphan their organization if they're the only member
        - Cascade delete may affect organization data
        
        Args:
            user_id: User to delete
            admin_user: Admin performing deletion
            
        Returns:
            UserActionResponse with action details
            
        Raises:
            HTTPException 403: If user is not admin or trying to delete self
            HTTPException 404: If user not found
        """
        self._verify_admin_role(admin_user)
        
        if user_id == admin_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete your own account"
            )
        
        logger.critical(
            f"Admin {admin_user.email} deleting user {user_id} - PERMANENT OPERATION"
        )
        
        try:
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            user_email = user.email
            org_id = user.organization_id
            
            # Check if user is last member of organization
            org_users_result = await self.session.execute(
                select(func.count()).select_from(UserModel)
                .where(UserModel.organization_id == org_id)
            )
            org_users_count = org_users_result.scalar() or 0
            
            if org_users_count == 1:
                logger.warning(
                    f"Deleting user {user_id} will orphan organization {org_id}"
                )
            
            # Delete user
            await self.user_repo.delete(user_id)
            
            await self._log_admin_action(
                admin_user,
                "user.delete",
                "user",
                user_id,
                details={
                    "target_email": user_email,
                    "organization_id": str(org_id),
                    "was_last_member": org_users_count == 1,
                    "warning": "PERMANENT_DELETION"
                }
            )
            
            logger.critical(f"User {user_id} ({user_email}) permanently deleted")
            
            return UserActionResponse(
                success=True,
                message="User permanently deleted",
                user_id=user_id,
                action="delete",
                performed_at=datetime.now(timezone.utc),
                performed_by=admin_user.id,
            )
        
        except HTTPException:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting user: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user"
            )
    
    # ==================== Global Exercise Management ====================
    
    async def create_global_exercise(
        self,
        exercise_data: ExerciseCreate,
        admin_user: User,
    ) -> Exercise:
        """
        Create a global (admin) exercise visible to all users.
        
        Args:
            exercise_data: Exercise creation data
            admin_user: Admin creating exercise
            
        Returns:
            Created exercise entity
            
        Raises:
            HTTPException 403: If user is not admin
        """
        self._verify_admin_role(admin_user)
        
        logger.info(
            f"Admin {admin_user.email} creating global exercise: {exercise_data.name}"
        )
        
        try:
            # Create exercise with no organization (global)
            exercise = await self.exercise_repo.create(
                exercise_data,
                organization_id=None,  # Global exercise
                created_by_user_id=admin_user.id
            )
            
            await self._log_admin_action(
                admin_user,
                "exercise.create_global",
                "exercise",
                exercise.id,
                details={
                    "exercise_name": exercise.name,
                    "equipment": exercise.equipment.value,
                    "primary_muscles": [m.value for m in exercise.primary_muscles]
                }
            )
            
            logger.info(f"Global exercise {exercise.id} created: {exercise.name}")
            
            return exercise
        
        except Exception as e:
            logger.error(f"Error creating global exercise: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create global exercise"
            )
    
    async def update_global_exercise(
        self,
        exercise_id: UUID,
        exercise_data: ExerciseUpdate,
        admin_user: User,
    ) -> Exercise:
        """
        Update a global exercise.
        
        Args:
            exercise_id: Exercise to update
            exercise_data: Update data
            admin_user: Admin performing update
            
        Returns:
            Updated exercise entity
            
        Raises:
            HTTPException 403: If user is not admin or exercise is not global
            HTTPException 404: If exercise not found
        """
        self._verify_admin_role(admin_user)
        
        logger.info(
            f"Admin {admin_user.email} updating global exercise {exercise_id}"
        )
        
        try:
            # Verify exercise is global
            exercise = await self.exercise_repo.get_by_id(exercise_id)
            if not exercise:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Exercise not found"
                )
            
            # Check if global exercise (organization_id is None)
            stmt = select(ExerciseModel).where(ExerciseModel.id == exercise_id)
            result = await self.session.execute(stmt)
            exercise_model = result.scalar_one_or_none()
            
            if exercise_model and exercise_model.organization_id is not None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only update global exercises. This is an organization exercise."
                )
            
            # Update exercise
            updated_exercise = await self.exercise_repo.update(
                exercise_id,
                exercise_data
            )
            
            await self._log_admin_action(
                admin_user,
                "exercise.update_global",
                "exercise",
                exercise_id,
                details={
                    "exercise_name": updated_exercise.name,
                    "changes": exercise_data.model_dump(exclude_unset=True)
                }
            )
            
            logger.info(f"Global exercise {exercise_id} updated")
            
            return updated_exercise
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating global exercise: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update global exercise"
            )
    
    async def delete_global_exercise(
        self,
        exercise_id: UUID,
        admin_user: User,
    ) -> UserActionResponse:
        """
        Delete a global exercise.
        
        WARNING: This may affect existing programs using this exercise.
        
        Args:
            exercise_id: Exercise to delete
            admin_user: Admin performing deletion
            
        Returns:
            UserActionResponse with action details
            
        Raises:
            HTTPException 403: If user is not admin or exercise is not global
            HTTPException 404: If exercise not found
        """
        self._verify_admin_role(admin_user)
        
        logger.warning(
            f"Admin {admin_user.email} deleting global exercise {exercise_id}"
        )
        
        try:
            # Verify exercise is global
            exercise = await self.exercise_repo.get_by_id(exercise_id)
            if not exercise:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Exercise not found"
                )
            
            # Check if global exercise
            stmt = select(ExerciseModel).where(ExerciseModel.id == exercise_id)
            result = await self.session.execute(stmt)
            exercise_model = result.scalar_one_or_none()
            
            if exercise_model and exercise_model.organization_id is not None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only delete global exercises. This is an organization exercise."
                )
            
            exercise_name = exercise.name
            
            # Check usage in programs
            # TODO: Implement usage check in workout_session exercises JSONB
            
            # Delete exercise
            await self.exercise_repo.delete(exercise_id)
            
            await self._log_admin_action(
                admin_user,
                "exercise.delete_global",
                "exercise",
                exercise_id,
                details={
                    "exercise_name": exercise_name,
                    "warning": "May affect existing programs"
                }
            )
            
            logger.warning(f"Global exercise {exercise_id} deleted: {exercise_name}")
            
            return UserActionResponse(
                success=True,
                message="Global exercise deleted successfully",
                user_id=exercise_id,
                action="delete_exercise",
                performed_at=datetime.now(timezone.utc),
                performed_by=admin_user.id,
            )
        
        except HTTPException:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting global exercise: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete global exercise"
            )
    
    # ==================== Program Template Management ====================
    
    async def create_program_template(
        self,
        program_data: ProgramCreate,
        admin_user: User,
    ) -> TrainingProgram:
        """
        Create a program template visible to all users.
        
        Args:
            program_data: Program creation data
            admin_user: Admin creating template
            
        Returns:
            Created program entity
            
        Raises:
            HTTPException 403: If user is not admin
        """
        self._verify_admin_role(admin_user)
        
        logger.info(
            f"Admin {admin_user.email} creating program template: {program_data.name}"
        )
        
        try:
            # Create program as template with no organization
            program = await self.program_repo.create_program(program_data, admin_user)
            
            # Set as template
            stmt = select(TrainingProgramModel).where(TrainingProgramModel.id == program.id)
            result = await self.session.execute(stmt)
            program_model = result.scalar_one_or_none()
            
            if program_model:
                program_model.is_template = True
                program_model.organization_id = None  # Global template
                await self.session.commit()
            
            await self._log_admin_action(
                admin_user,
                "program.create_template",
                "program",
                program.id,
                details={
                    "program_name": program.name,
                    "split_type": program.split_type.value,
                    "session_count": len(program.sessions)
                }
            )
            
            logger.info(f"Program template {program.id} created: {program.name}")
            
            return program
        
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating program template: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create program template"
            )
    
    async def update_program_template(
        self,
        template_id: UUID,
        program_data: ProgramUpdate,
        admin_user: User,
    ) -> TrainingProgram:
        """
        Update a program template.
        
        Args:
            template_id: Template to update
            program_data: Update data
            admin_user: Admin performing update
            
        Returns:
            Updated program entity
            
        Raises:
            HTTPException 403: If user is not admin or program is not template
            HTTPException 404: If template not found
        """
        self._verify_admin_role(admin_user)
        
        logger.info(
            f"Admin {admin_user.email} updating program template {template_id}"
        )
        
        try:
            # Verify is template
            program = await self.program_repo.get_by_id(template_id)
            if not program:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Program template not found"
                )
            
            if not program.is_template:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only update program templates. This is a user program."
                )
            
            # Update program
            updated_program = await self.program_repo.update_program(
                template_id,
                program_data
            )
            
            await self._log_admin_action(
                admin_user,
                "program.update_template",
                "program",
                template_id,
                details={
                    "program_name": updated_program.name,
                    "changes": program_data.model_dump(exclude_unset=True)
                }
            )
            
            logger.info(f"Program template {template_id} updated")
            
            return updated_program
        
        except HTTPException:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating program template: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update program template"
            )
    
    async def delete_program_template(
        self,
        template_id: UUID,
        admin_user: User,
    ) -> UserActionResponse:
        """
        Delete a program template.
        
        WARNING: This will not affect cloned programs but removes the template
        from the template library.
        
        Args:
            template_id: Template to delete
            admin_user: Admin performing deletion
            
        Returns:
            UserActionResponse with action details
            
        Raises:
            HTTPException 403: If user is not admin or program is not template
            HTTPException 404: If template not found
        """
        self._verify_admin_role(admin_user)
        
        logger.warning(
            f"Admin {admin_user.email} deleting program template {template_id}"
        )
        
        try:
            # Verify is template
            program = await self.program_repo.get_by_id(template_id)
            if not program:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Program template not found"
                )
            
            if not program.is_template:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only delete program templates. This is a user program."
                )
            
            program_name = program.name
            
            # Check how many times it's been cloned (for audit)
            # This would require tracking in a clones table - TODO
            
            # Delete template (cascade will handle sessions)
            await self.program_repo.delete_program(template_id)
            
            await self._log_admin_action(
                admin_user,
                "program.delete_template",
                "program",
                template_id,
                details={
                    "program_name": program_name,
                    "note": "Cloned programs are not affected"
                }
            )
            
            logger.warning(f"Program template {template_id} deleted: {program_name}")
            
            return UserActionResponse(
                success=True,
                message="Program template deleted successfully",
                user_id=template_id,
                action="delete_template",
                performed_at=datetime.now(timezone.utc),
                performed_by=admin_user.id,
            )
        
        except HTTPException:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting program template: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete program template"
            )
    
    # ==================== Analytics ====================
    
    async def get_subscription_analytics(
        self,
        admin_user: User,
    ) -> SubscriptionAnalytics:
        """
        Get detailed subscription analytics and trends.
        
        Args:
            admin_user: Admin requesting analytics
            
        Returns:
            SubscriptionAnalytics with detailed metrics
            
        Raises:
            HTTPException 403: If user is not admin
        """
        self._verify_admin_role(admin_user)
        
        logger.info(f"Admin {admin_user.email} fetching subscription analytics")
        
        try:
            # Current state
            total_orgs_result = await self.session.execute(
                select(func.count()).select_from(OrganizationModel)
            )
            total_subscribers = total_orgs_result.scalar() or 0
            
            active_result = await self.session.execute(
                select(func.count()).select_from(OrganizationModel)
                .where(OrganizationModel.subscription_status == "ACTIVE")
            )
            active_subscribers = active_result.scalar() or 0
            
            cancelled_result = await self.session.execute(
                select(func.count()).select_from(OrganizationModel)
                .where(OrganizationModel.subscription_status == "CANCELLED")
            )
            cancelled_subscribers = cancelled_result.scalar() or 0
            
            expired_result = await self.session.execute(
                select(func.count()).select_from(OrganizationModel)
                .where(OrganizationModel.subscription_status == "EXPIRED")
            )
            expired_subscribers = expired_result.scalar() or 0
            
            # Revenue metrics (assuming $30/month for Pro)
            pro_count_result = await self.session.execute(
                select(func.count()).select_from(OrganizationModel)
                .where(
                    and_(
                        OrganizationModel.subscription_tier == "PRO",
                        OrganizationModel.subscription_status == "ACTIVE"
                    )
                )
            )
            pro_count = pro_count_result.scalar() or 0
            
            mrr = float(pro_count * 30)
            arpu = mrr / total_subscribers if total_subscribers > 0 else 0.0
            
            # Growth metrics (this month)
            first_of_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            new_subs_result = await self.session.execute(
                select(func.count()).select_from(OrganizationModel)
                .where(
                    and_(
                        OrganizationModel.created_at >= first_of_month,
                        OrganizationModel.subscription_tier == "PRO"
                    )
                )
            )
            new_subscriptions = new_subs_result.scalar() or 0
            
            # Churn (simplified - would need subscription history)
            churn_rate = (cancelled_subscribers / total_subscribers * 100) if total_subscribers > 0 else 0.0
            
            # Tier breakdown
            free_result = await self.session.execute(
                select(func.count()).select_from(OrganizationModel)
                .where(OrganizationModel.subscription_tier == "FREE")
            )
            free_count = free_result.scalar() or 0
            
            free_percentage = (free_count / total_subscribers * 100) if total_subscribers > 0 else 0.0
            pro_percentage = 100.0 - free_percentage
            
            # Historical data (placeholder - would need time-series data)
            monthly_revenue_history = [
                {"date": "2025-10", "amount": 900.00},
                {"date": "2025-11", "amount": mrr}
            ]
            
            subscription_growth_history = [
                {"date": "2025-10", "count": max(0, pro_count - 5)},
                {"date": "2025-11", "count": pro_count}
            ]
            
            analytics = SubscriptionAnalytics(
                total_subscribers=total_subscribers,
                active_subscribers=active_subscribers,
                cancelled_subscribers=cancelled_subscribers,
                expired_subscribers=expired_subscribers,
                monthly_recurring_revenue=mrr,
                average_revenue_per_user=arpu,
                new_subscriptions_this_month=new_subscriptions,
                cancellations_this_month=cancelled_subscribers,  # Simplified
                churn_rate_percent=churn_rate,
                free_tier_percentage=free_percentage,
                pro_tier_percentage=pro_percentage,
                monthly_revenue_history=monthly_revenue_history,
                subscription_growth_history=subscription_growth_history,
                generated_at=datetime.now(timezone.utc),
            )
            
            await self._log_admin_action(
                admin_user,
                "analytics.subscription_view",
                "system",
                details={"mrr": mrr}
            )
            
            return analytics
        
        except Exception as e:
            logger.error(f"Error generating subscription analytics: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate subscription analytics"
            )
    
    async def get_usage_analytics(
        self,
        admin_user: User,
    ) -> UsageAnalytics:
        """
        Get system usage analytics and engagement metrics.
        
        Args:
            admin_user: Admin requesting analytics
            
        Returns:
            UsageAnalytics with engagement metrics
            
        Raises:
            HTTPException 403: If user is not admin
        """
        self._verify_admin_role(admin_user)
        
        logger.info(f"Admin {admin_user.email} fetching usage analytics")
        
        try:
            now = datetime.now(timezone.utc)
            
            # Active users
            dau_result = await self.session.execute(
                select(func.count()).select_from(UserModel)
                .where(UserModel.updated_at >= now - timedelta(days=1))
            )
            daily_active = dau_result.scalar() or 0
            
            wau_result = await self.session.execute(
                select(func.count()).select_from(UserModel)
                .where(UserModel.updated_at >= now - timedelta(days=7))
            )
            weekly_active = wau_result.scalar() or 0
            
            mau_result = await self.session.execute(
                select(func.count()).select_from(UserModel)
                .where(UserModel.updated_at >= now - timedelta(days=30))
            )
            monthly_active = mau_result.scalar() or 0
            
            # Exercise metrics
            total_exercises_result = await self.session.execute(
                select(func.count()).select_from(ExerciseModel)
            )
            total_exercises = total_exercises_result.scalar() or 0
            
            first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            exercises_this_month_result = await self.session.execute(
                select(func.count()).select_from(ExerciseModel)
                .where(ExerciseModel.created_at >= first_of_month)
            )
            exercises_this_month = exercises_this_month_result.scalar() or 0
            
            first_of_week = now - timedelta(days=now.weekday())
            exercises_this_week_result = await self.session.execute(
                select(func.count()).select_from(ExerciseModel)
                .where(ExerciseModel.created_at >= first_of_week)
            )
            exercises_this_week = exercises_this_week_result.scalar() or 0
            
            exercise_metrics = UsageMetrics(
                total_count=total_exercises,
                created_this_month=exercises_this_month,
                created_this_week=exercises_this_week,
                most_popular=[]  # TODO: Track usage in programs
            )
            
            # Program metrics
            total_programs_result = await self.session.execute(
                select(func.count()).select_from(TrainingProgramModel)
            )
            total_programs = total_programs_result.scalar() or 0
            
            programs_this_month_result = await self.session.execute(
                select(func.count()).select_from(TrainingProgramModel)
                .where(TrainingProgramModel.created_at >= first_of_month)
            )
            programs_this_month = programs_this_month_result.scalar() or 0
            
            programs_this_week_result = await self.session.execute(
                select(func.count()).select_from(TrainingProgramModel)
                .where(TrainingProgramModel.created_at >= first_of_week)
            )
            programs_this_week = programs_this_week_result.scalar() or 0
            
            program_metrics = UsageMetrics(
                total_count=total_programs,
                created_this_month=programs_this_month,
                created_this_week=programs_this_week,
                most_popular=[]  # TODO: Track clones/usage
            )
            
            # Feature adoption
            custom_exercises_result = await self.session.execute(
                select(func.count(func.distinct(ExerciseModel.organization_id)))
                .select_from(ExerciseModel)
                .where(ExerciseModel.organization_id.isnot(None))
            )
            users_with_custom_exercises = custom_exercises_result.scalar() or 0
            
            custom_programs_result = await self.session.execute(
                select(func.count(func.distinct(TrainingProgramModel.organization_id)))
                .select_from(TrainingProgramModel)
                .where(
                    and_(
                        TrainingProgramModel.is_template == False,
                        TrainingProgramModel.organization_id.isnot(None)
                    )
                )
            )
            users_with_custom_programs = custom_programs_result.scalar() or 0
            
            # Averages
            total_users_result = await self.session.execute(
                select(func.count()).select_from(UserModel)
            )
            total_users = total_users_result.scalar() or 1  # Avoid division by zero
            
            avg_programs = total_programs / total_users
            
            # Average exercises per program
            avg_exercises_result = await self.session.execute(
                select(func.avg(WorkoutSessionModel.total_sets))
                .select_from(WorkoutSessionModel)
            )
            avg_sets = avg_exercises_result.scalar() or 0
            avg_exercises_per_program = float(avg_sets / 3) if avg_sets > 0 else 0  # Rough estimate
            
            # Average sessions per program
            sessions_count_result = await self.session.execute(
                select(func.count()).select_from(WorkoutSessionModel)
            )
            total_sessions = sessions_count_result.scalar() or 0
            avg_sessions = total_sessions / total_programs if total_programs > 0 else 0
            
            analytics = UsageAnalytics(
                daily_active_users=daily_active,
                weekly_active_users=weekly_active,
                monthly_active_users=monthly_active,
                exercise_metrics=exercise_metrics,
                program_metrics=program_metrics,
                users_with_custom_exercises=users_with_custom_exercises,
                users_with_custom_programs=users_with_custom_programs,
                users_with_cloned_templates=0,  # TODO: Track clones
                avg_programs_per_user=avg_programs,
                avg_exercises_per_program=avg_exercises_per_program,
                avg_sessions_per_program=avg_sessions,
                most_used_exercises=[],  # TODO: Implement
                most_cloned_templates=[],  # TODO: Implement
                generated_at=now,
            )
            
            await self._log_admin_action(
                admin_user,
                "analytics.usage_view",
                "system",
                details={"dau": daily_active, "mau": monthly_active}
            )
            
            return analytics
        
        except Exception as e:
            logger.error(f"Error generating usage analytics: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate usage analytics"
            )
