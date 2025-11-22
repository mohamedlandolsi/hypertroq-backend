"""
Exercise domain entity for resistance training exercises.

Represents exercises with muscle group targeting and volume contribution tracking.
Exercises can be global (admin-created, available to all) or organization-specific.
"""

from datetime import datetime
from typing import Dict, List
from uuid import UUID

from app.domain.entities.base import Entity
from app.domain.value_objects.equipment import Equipment
from app.domain.value_objects.muscle_groups import MuscleGroup
from app.domain.value_objects.volume_contribution import VolumeContribution


class Exercise(Entity):
    """
    Exercise entity representing a resistance training exercise.
    
    Exercises define how volume is distributed across muscle groups.
    Each exercise targets one or more muscles with fractional contributions.
    
    Business Rules:
        - Sum of muscle contributions should be >= 1.0 (at least one primary target)
        - Global exercises (is_global=True) are available to all organizations
        - User-created exercises belong to a specific organization
        - Exercise names should be unique within organization scope
        - At least one muscle must have PRIMARY (1.0) contribution
    
    Examples:
        Barbell Bench Press:
            - Chest: 1.0 (PRIMARY)
            - Front Delts: 0.5 (MODERATE)
            - Triceps: 0.75 (HIGH)
            Total contribution: 2.25
        
        Barbell Row:
            - Lats: 1.0 (PRIMARY)
            - Traps/Rhomboids: 0.75 (HIGH)
            - Elbow Flexors: 0.5 (MODERATE)
            Total contribution: 2.25
    """
    
    def __init__(
        self,
        name: str,
        equipment: Equipment,
        muscle_contributions: Dict[MuscleGroup, VolumeContribution],
        description: str = "",
        image_url: str | None = None,
        is_global: bool = False,
        created_by_user_id: UUID | None = None,
        organization_id: UUID | None = None,
        id: UUID | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        """
        Initialize Exercise entity.
        
        Args:
            name: Exercise name (e.g., "Barbell Bench Press")
            equipment: Equipment type used
            muscle_contributions: Mapping of muscle groups to contribution levels
            description: Exercise description and instructions
            image_url: URL to exercise demonstration image/video
            is_global: True if admin-created (available to all), False if user-created
            created_by_user_id: User who created the exercise (None for global)
            organization_id: Organization that owns the exercise (None for global)
            id: Unique identifier (auto-generated if None)
            created_at: Creation timestamp
            updated_at: Last update timestamp
            
        Raises:
            ValueError: If muscle_contributions validation fails
        """
        super().__init__(id, created_at, updated_at)
        
        self._name = name.strip()
        self._equipment = equipment
        self._muscle_contributions = muscle_contributions
        self._description = description.strip()
        self._image_url = image_url
        self._is_global = is_global
        self._created_by_user_id = created_by_user_id
        self._organization_id = organization_id
        
        # Validate muscle contributions on initialization
        self._validate_muscle_contributions()
        
        # Validate global exercise constraints
        self._validate_global_constraints()
    
    # ==================== Properties ====================
    
    @property
    def name(self) -> str:
        """Exercise name."""
        return self._name
    
    @property
    def equipment(self) -> Equipment:
        """Equipment type used for this exercise."""
        return self._equipment
    
    @property
    def muscle_contributions(self) -> Dict[MuscleGroup, VolumeContribution]:
        """Mapping of muscle groups to their volume contribution levels."""
        return self._muscle_contributions.copy()
    
    @property
    def description(self) -> str:
        """Exercise description and instructions."""
        return self._description
    
    @property
    def image_url(self) -> str | None:
        """URL to exercise demonstration image or video."""
        return self._image_url
    
    @property
    def is_global(self) -> bool:
        """True if admin-created exercise available to all organizations."""
        return self._is_global
    
    @property
    def created_by_user_id(self) -> UUID | None:
        """User who created the exercise (None for global exercises)."""
        return self._created_by_user_id
    
    @property
    def organization_id(self) -> UUID | None:
        """Organization that owns the exercise (None for global exercises)."""
        return self._organization_id
    
    # ==================== Business Logic Methods ====================
    
    def calculate_total_volume(self, sets: int) -> Dict[MuscleGroup, float]:
        """
        Calculate volume contribution to each muscle group for given sets.
        
        Args:
            sets: Number of sets performed
            
        Returns:
            Dict mapping muscle groups to effective volume (sets × contribution)
            
        Examples:
            >>> exercise = Exercise(...)  # Bench press
            >>> exercise.calculate_total_volume(4)
            {
                MuscleGroup.CHEST: 4.0,
                MuscleGroup.FRONT_DELTS: 2.0,
                MuscleGroup.TRICEPS: 3.0
            }
        """
        if sets < 0:
            raise ValueError("Sets cannot be negative")
        
        return {
            muscle: contribution.calculate_volume(sets)
            for muscle, contribution in self._muscle_contributions.items()
        }
    
    def get_primary_muscles(self) -> List[MuscleGroup]:
        """
        Get muscle groups that are primary targets (1.0 contribution).
        
        Returns:
            List of muscle groups with PRIMARY contribution
            
        Examples:
            >>> exercise.get_primary_muscles()
            [MuscleGroup.CHEST]
        """
        return [
            muscle
            for muscle, contribution in self._muscle_contributions.items()
            if contribution == VolumeContribution.PRIMARY
        ]
    
    def get_secondary_muscles(self) -> List[MuscleGroup]:
        """
        Get muscle groups that are secondary targets (< 1.0 contribution).
        
        Returns:
            List of muscle groups with non-primary contribution, sorted by contribution level
            
        Examples:
            >>> exercise.get_secondary_muscles()
            [MuscleGroup.TRICEPS, MuscleGroup.FRONT_DELTS]  # Ordered by contribution
        """
        secondary = [
            (muscle, contribution)
            for muscle, contribution in self._muscle_contributions.items()
            if contribution != VolumeContribution.PRIMARY
        ]
        
        # Sort by contribution level (descending)
        secondary.sort(key=lambda x: x[1].value, reverse=True)
        
        return [muscle for muscle, _ in secondary]
    
    def get_all_targeted_muscles(self) -> List[MuscleGroup]:
        """
        Get all muscle groups targeted by this exercise, sorted by contribution.
        
        Returns:
            List of all muscle groups, ordered from highest to lowest contribution
        """
        sorted_muscles = sorted(
            self._muscle_contributions.items(),
            key=lambda x: x[1].value,
            reverse=True
        )
        return [muscle for muscle, _ in sorted_muscles]
    
    def get_total_contribution(self) -> float:
        """
        Get sum of all muscle contributions.
        
        Returns:
            Total contribution across all muscles
            
        Examples:
            >>> exercise.get_total_contribution()
            2.25  # Chest(1.0) + Front Delts(0.5) + Triceps(0.75)
        """
        return sum(contribution.value for contribution in self._muscle_contributions.values())
    
    def targets_muscle(self, muscle: MuscleGroup, min_contribution: VolumeContribution | None = None) -> bool:
        """
        Check if exercise targets a specific muscle group.
        
        Args:
            muscle: Muscle group to check
            min_contribution: Minimum contribution level required (optional)
            
        Returns:
            True if exercise targets the muscle at or above minimum contribution
            
        Examples:
            >>> exercise.targets_muscle(MuscleGroup.CHEST)
            True
            >>> exercise.targets_muscle(MuscleGroup.CHEST, VolumeContribution.PRIMARY)
            True
            >>> exercise.targets_muscle(MuscleGroup.LATS)
            False
        """
        if muscle not in self._muscle_contributions:
            return False
        
        if min_contribution is None:
            return True
        
        return self._muscle_contributions[muscle].value >= min_contribution.value
    
    def is_compound(self) -> bool:
        """
        Check if exercise is compound (targets multiple muscle groups).
        
        Returns:
            True if exercise targets 2+ muscle groups
        """
        return len(self._muscle_contributions) >= 2
    
    def is_isolation(self) -> bool:
        """
        Check if exercise is isolation (single muscle group).
        
        Returns:
            True if exercise targets only 1 muscle group
        """
        return len(self._muscle_contributions) == 1
    
    # ==================== Update Methods ====================
    
    def update_details(
        self,
        name: str | None = None,
        description: str | None = None,
        equipment: Equipment | None = None,
        image_url: str | None = None,
    ) -> None:
        """
        Update exercise details.
        
        Args:
            name: New exercise name
            description: New description
            equipment: New equipment type
            image_url: New image URL
            
        Raises:
            ValueError: If validation fails
        """
        if name is not None:
            self._name = name.strip()
            if not self._name:
                raise ValueError("Exercise name cannot be empty")
        
        if description is not None:
            self._description = description.strip()
        
        if equipment is not None:
            self._equipment = equipment
        
        if image_url is not None:
            self._image_url = image_url
        
        self._updated_at = datetime.utcnow()
    
    def update_muscle_contributions(
        self,
        muscle_contributions: Dict[MuscleGroup, VolumeContribution]
    ) -> None:
        """
        Update muscle group targeting and contributions.
        
        Args:
            muscle_contributions: New muscle contribution mapping
            
        Raises:
            ValueError: If validation fails
        """
        self._muscle_contributions = muscle_contributions
        self._validate_muscle_contributions()
        self._updated_at = datetime.utcnow()
    
    def set_image_url(self, url: str | None) -> None:
        """Set or clear exercise image URL."""
        self._image_url = url
        self._updated_at = datetime.utcnow()
    
    # ==================== Validation ====================
    
    def _validate_muscle_contributions(self) -> None:
        """
        Validate muscle contributions meet business rules.
        
        Rules:
            1. At least one muscle group must be targeted
            2. Total contribution should be >= 1.0
            3. At least one muscle must have PRIMARY (1.0) contribution
            
        Raises:
            ValueError: If validation fails
        """
        if not self._muscle_contributions:
            raise ValueError("Exercise must target at least one muscle group")
        
        total_contribution = sum(
            contribution.value for contribution in self._muscle_contributions.values()
        )
        
        if total_contribution < 1.0:
            raise ValueError(
                f"Total muscle contribution ({total_contribution}) must be >= 1.0. "
                f"Exercise should have at least one primary target."
            )
        
        has_primary = any(
            contribution == VolumeContribution.PRIMARY
            for contribution in self._muscle_contributions.values()
        )
        
        if not has_primary:
            raise ValueError(
                "Exercise must have at least one muscle with PRIMARY (1.0) contribution"
            )
    
    def _validate_global_constraints(self) -> None:
        """
        Validate global exercise constraints.
        
        Rules:
            - Global exercises should not have organization_id
            - Global exercises should not have created_by_user_id (or it's an admin)
            - Non-global exercises must have organization_id
            
        Raises:
            ValueError: If validation fails
        """
        if self._is_global:
            if self._organization_id is not None:
                raise ValueError("Global exercises cannot belong to an organization")
        else:
            if self._organization_id is None:
                raise ValueError("Non-global exercises must have an organization_id")
    
    # ==================== Equality & Representation ====================
    
    def __str__(self) -> str:
        """String representation."""
        muscle_list = ", ".join(
            f"{muscle.display_name} ({contribution.percentage}%)"
            for muscle, contribution in sorted(
                self._muscle_contributions.items(),
                key=lambda x: x[1].value,
                reverse=True
            )
        )
        return f"{self._name} ({self._equipment.display_name}) - {muscle_list}"
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"Exercise(id={self.id}, name='{self._name}', "
            f"equipment={self._equipment.name}, "
            f"is_global={self._is_global}, "
            f"muscles={len(self._muscle_contributions)})"
        )
