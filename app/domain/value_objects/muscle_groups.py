"""
Muscle group value objects for exercise classification.

Defines the 18 muscle groups used in hypertrophy training volume tracking.
Each muscle group can receive fractional volume contributions from exercises.
"""

from enum import Enum


class MuscleGroup(str, Enum):
    """
    Enumeration of the 18 muscle groups tracked for hypertrophy training.
    
    These groups represent the primary muscle targets for volume tracking.
    Exercises contribute fractionally (0.25, 0.5, 0.75, 1.0) to each muscle group.
    
    Minimum 10 sets per muscle per week recommended for hypertrophy.
    Maximum 20-25 sets per muscle per week before recovery limits.
    """
    
    # Upper Body - Push
    CHEST = "CHEST"
    FRONT_DELTS = "FRONT_DELTS"
    SIDE_DELTS = "SIDE_DELTS"
    REAR_DELTS = "REAR_DELTS"
    TRICEPS = "TRICEPS"
    
    # Upper Body - Pull
    LATS = "LATS"
    TRAPS_RHOMBOIDS = "TRAPS_RHOMBOIDS"
    ELBOW_FLEXORS = "ELBOW_FLEXORS"  # Biceps, brachialis, brachioradialis
    FOREARMS = "FOREARMS"
    
    # Core & Posterior Chain
    SPINAL_ERECTORS = "SPINAL_ERECTORS"
    ABS = "ABS"
    OBLIQUES = "OBLIQUES"
    
    # Lower Body
    GLUTES = "GLUTES"
    QUADRICEPS = "QUADRICEPS"
    HAMSTRINGS = "HAMSTRINGS"
    ADDUCTORS = "ADDUCTORS"
    CALVES = "CALVES"
    
    @property
    def display_name(self) -> str:
        """
        Return human-readable display name for the muscle group.
        
        Returns:
            str: Formatted display name suitable for UI presentation
            
        Examples:
            >>> MuscleGroup.CHEST.display_name
            'Chest'
            >>> MuscleGroup.TRAPS_RHOMBOIDS.display_name
            'Traps & Rhomboids'
            >>> MuscleGroup.ELBOW_FLEXORS.display_name
            'Elbow Flexors (Biceps)'
        """
        display_names = {
            MuscleGroup.CHEST: "Chest",
            MuscleGroup.LATS: "Lats",
            MuscleGroup.TRAPS_RHOMBOIDS: "Traps & Rhomboids",
            MuscleGroup.REAR_DELTS: "Rear Delts",
            MuscleGroup.FRONT_DELTS: "Front Delts",
            MuscleGroup.SIDE_DELTS: "Side Delts",
            MuscleGroup.TRICEPS: "Triceps",
            MuscleGroup.ELBOW_FLEXORS: "Elbow Flexors (Biceps)",
            MuscleGroup.FOREARMS: "Forearms",
            MuscleGroup.SPINAL_ERECTORS: "Spinal Erectors",
            MuscleGroup.ABS: "Abs",
            MuscleGroup.OBLIQUES: "Obliques",
            MuscleGroup.GLUTES: "Glutes",
            MuscleGroup.QUADRICEPS: "Quadriceps",
            MuscleGroup.HAMSTRINGS: "Hamstrings",
            MuscleGroup.ADDUCTORS: "Adductors",
            MuscleGroup.CALVES: "Calves",
        }
        return display_names[self]
    
    @property
    def category(self) -> str:
        """
        Return the anatomical category of the muscle group.
        
        Returns:
            str: Category name (Upper Push, Upper Pull, Core, Lower Body)
            
        Examples:
            >>> MuscleGroup.CHEST.category
            'Upper Push'
            >>> MuscleGroup.LATS.category
            'Upper Pull'
            >>> MuscleGroup.QUADRICEPS.category
            'Lower Body'
        """
        categories = {
            MuscleGroup.CHEST: "Upper Push",
            MuscleGroup.FRONT_DELTS: "Upper Push",
            MuscleGroup.SIDE_DELTS: "Upper Push",
            MuscleGroup.REAR_DELTS: "Upper Pull",
            MuscleGroup.TRICEPS: "Upper Push",
            MuscleGroup.LATS: "Upper Pull",
            MuscleGroup.TRAPS_RHOMBOIDS: "Upper Pull",
            MuscleGroup.ELBOW_FLEXORS: "Upper Pull",
            MuscleGroup.FOREARMS: "Upper Pull",
            MuscleGroup.SPINAL_ERECTORS: "Core & Posterior",
            MuscleGroup.ABS: "Core & Posterior",
            MuscleGroup.OBLIQUES: "Core & Posterior",
            MuscleGroup.GLUTES: "Lower Body",
            MuscleGroup.QUADRICEPS: "Lower Body",
            MuscleGroup.HAMSTRINGS: "Lower Body",
            MuscleGroup.ADDUCTORS: "Lower Body",
            MuscleGroup.CALVES: "Lower Body",
        }
        return categories[self]
    
    def __str__(self) -> str:
        """String representation returns display name."""
        return self.display_name
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"MuscleGroup.{self.name}"
    
    @classmethod
    def get_by_category(cls, category: str) -> list["MuscleGroup"]:
        """
        Get all muscle groups in a specific category.
        
        Args:
            category: Category name (e.g., "Upper Push", "Lower Body")
            
        Returns:
            list[MuscleGroup]: All muscle groups in that category
            
        Examples:
            >>> MuscleGroup.get_by_category("Upper Push")
            [MuscleGroup.CHEST, MuscleGroup.FRONT_DELTS, ...]
        """
        return [mg for mg in cls if mg.category == category]
    
    @classmethod
    def all_upper_body(cls) -> list["MuscleGroup"]:
        """Get all upper body muscle groups (push + pull)."""
        return [mg for mg in cls if mg.category in ("Upper Push", "Upper Pull")]
    
    @classmethod
    def all_lower_body(cls) -> list["MuscleGroup"]:
        """Get all lower body muscle groups."""
        return cls.get_by_category("Lower Body")
    
    @classmethod
    def all_core(cls) -> list["MuscleGroup"]:
        """Get all core muscle groups."""
        return cls.get_by_category("Core & Posterior")
