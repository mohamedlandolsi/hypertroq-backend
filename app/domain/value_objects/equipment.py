"""
Equipment type value objects for exercise classification.

Defines equipment types used in resistance training exercises.
Each exercise is performed with one primary equipment type.
"""

from enum import Enum


class Equipment(str, Enum):
    """
    Enumeration of equipment types used in resistance training.
    
    Equipment type affects exercise selection, progression strategies,
    and workout programming. Used for filtering and organizing exercises.
    
    Examples:
        - BARBELL: Bench press, squat, deadlift
        - DUMBBELL: Dumbbell press, rows, curls
        - CABLE: Cable flyes, tricep pushdowns, face pulls
        - MACHINE: Leg press, chest press, lat pulldown
        - BODYWEIGHT: Pull-ups, push-ups, dips
    """
    
    BARBELL = "BARBELL"
    DUMBBELL = "DUMBBELL"
    CABLE = "CABLE"
    MACHINE = "MACHINE"
    SMITH_MACHINE = "SMITH_MACHINE"
    BODYWEIGHT = "BODYWEIGHT"
    KETTLEBELL = "KETTLEBELL"
    RESISTANCE_BAND = "RESISTANCE_BAND"
    OTHER = "OTHER"
    
    @property
    def display_name(self) -> str:
        """
        Return human-readable display name for the equipment type.
        
        Returns:
            str: Formatted display name suitable for UI presentation
            
        Examples:
            >>> Equipment.BARBELL.display_name
            'Barbell'
            >>> Equipment.SMITH_MACHINE.display_name
            'Smith Machine'
            >>> Equipment.RESISTANCE_BAND.display_name
            'Resistance Band'
        """
        display_names = {
            Equipment.BARBELL: "Barbell",
            Equipment.DUMBBELL: "Dumbbell",
            Equipment.CABLE: "Cable",
            Equipment.MACHINE: "Machine",
            Equipment.SMITH_MACHINE: "Smith Machine",
            Equipment.BODYWEIGHT: "Bodyweight",
            Equipment.KETTLEBELL: "Kettlebell",
            Equipment.RESISTANCE_BAND: "Resistance Band",
            Equipment.OTHER: "Other",
        }
        return display_names[self]
    
    @property
    def is_free_weight(self) -> bool:
        """
        Check if equipment is a free weight (requires stabilization).
        
        Returns:
            bool: True for barbells, dumbbells, kettlebells
            
        Examples:
            >>> Equipment.BARBELL.is_free_weight
            True
            >>> Equipment.MACHINE.is_free_weight
            False
        """
        return self in (
            Equipment.BARBELL,
            Equipment.DUMBBELL,
            Equipment.KETTLEBELL,
        )
    
    @property
    def is_fixed_path(self) -> bool:
        """
        Check if equipment uses a fixed movement path.
        
        Returns:
            bool: True for machines and Smith machines
            
        Examples:
            >>> Equipment.MACHINE.is_fixed_path
            True
            >>> Equipment.DUMBBELL.is_fixed_path
            False
        """
        return self in (Equipment.MACHINE, Equipment.SMITH_MACHINE)
    
    @property
    def requires_equipment(self) -> bool:
        """
        Check if equipment requires gym equipment (not bodyweight).
        
        Returns:
            bool: False only for bodyweight and resistance bands
            
        Examples:
            >>> Equipment.BODYWEIGHT.requires_equipment
            False
            >>> Equipment.BARBELL.requires_equipment
            True
        """
        return self not in (Equipment.BODYWEIGHT, Equipment.RESISTANCE_BAND)
    
    @property
    def icon(self) -> str:
        """
        Get emoji/icon for the equipment type (for UI display).
        
        Returns:
            str: Emoji or symbol representing the equipment
        """
        icons = {
            Equipment.BARBELL: "🏋️",
            Equipment.DUMBBELL: "💪",
            Equipment.CABLE: "🔗",
            Equipment.MACHINE: "⚙️",
            Equipment.SMITH_MACHINE: "🔲",
            Equipment.BODYWEIGHT: "🧘",
            Equipment.KETTLEBELL: "⚫",
            Equipment.RESISTANCE_BAND: "〰️",
            Equipment.OTHER: "❓",
        }
        return icons[self]
    
    def __str__(self) -> str:
        """String representation returns display name."""
        return self.display_name
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"Equipment.{self.name}"
    
    @classmethod
    def for_home_gym(cls) -> list["Equipment"]:
        """
        Get equipment types suitable for home gym workouts.
        
        Returns:
            list[Equipment]: Equipment typically available at home
            
        Examples:
            >>> Equipment.for_home_gym()
            [Equipment.DUMBBELL, Equipment.BODYWEIGHT, Equipment.KETTLEBELL, Equipment.RESISTANCE_BAND]
        """
        return [
            Equipment.DUMBBELL,
            Equipment.BODYWEIGHT,
            Equipment.KETTLEBELL,
            Equipment.RESISTANCE_BAND,
        ]
    
    @classmethod
    def for_commercial_gym(cls) -> list["Equipment"]:
        """
        Get equipment types typically available in commercial gyms.
        
        Returns:
            list[Equipment]: All equipment except OTHER
        """
        return [eq for eq in cls if eq != Equipment.OTHER]
    
    @classmethod
    def free_weights(cls) -> list["Equipment"]:
        """Get all free weight equipment types."""
        return [eq for eq in cls if eq.is_free_weight]
    
    @classmethod
    def machines(cls) -> list["Equipment"]:
        """Get all machine-based equipment types."""
        return [eq for eq in cls if eq.is_fixed_path]
