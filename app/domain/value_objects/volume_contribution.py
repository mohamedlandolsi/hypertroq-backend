"""
Volume contribution value objects for exercise muscle targeting.

Defines fractional volume contributions (0.25, 0.5, 0.75, 1.0) that exercises
provide to muscle groups. Used for accurate volume tracking in hypertrophy training.
"""

from enum import Enum


class VolumeContribution(float, Enum):
    """
    Enumeration of volume contribution levels for exercise-muscle relationships.
    
    Each exercise contributes fractionally to one or more muscle groups.
    Total weekly volume = sum of (sets × contribution) across all exercises.
    
    Contribution Levels:
        - MINIMAL (0.25): Tertiary muscle involvement (e.g., triceps in rows)
        - MODERATE (0.50): Secondary muscle involvement (e.g., front delts in bench press)
        - HIGH (0.75): Strong secondary target (e.g., triceps in close-grip bench)
        - PRIMARY (1.00): Primary target muscle (e.g., chest in bench press)
    
    Examples:
        Barbell Bench Press (4 sets):
            - Chest: 4 × 1.0 = 4.0 sets
            - Front Delts: 4 × 0.5 = 2.0 sets
            - Triceps: 4 × 0.75 = 3.0 sets
        
        Barbell Row (3 sets):
            - Lats: 3 × 1.0 = 3.0 sets
            - Traps/Rhomboids: 3 × 0.75 = 2.25 sets
            - Elbow Flexors: 3 × 0.5 = 1.5 sets
    """
    
    MINIMAL = 0.25
    MODERATE = 0.50
    HIGH = 0.75
    PRIMARY = 1.00
    
    @property
    def display_name(self) -> str:
        """
        Return human-readable display name for the contribution level.
        
        Returns:
            str: Formatted display name suitable for UI presentation
            
        Examples:
            >>> VolumeContribution.PRIMARY.display_name
            'Primary (100%)'
            >>> VolumeContribution.MODERATE.display_name
            'Moderate (50%)'
        """
        display_names = {
            VolumeContribution.MINIMAL: "Minimal (25%)",
            VolumeContribution.MODERATE: "Moderate (50%)",
            VolumeContribution.HIGH: "High (75%)",
            VolumeContribution.PRIMARY: "Primary (100%)",
        }
        return display_names[self]
    
    @property
    def description(self) -> str:
        """
        Return detailed description of the contribution level.
        
        Returns:
            str: Explanation of what this contribution level means
        """
        descriptions = {
            VolumeContribution.MINIMAL: "Tertiary muscle involvement - minimal contribution to volume",
            VolumeContribution.MODERATE: "Secondary muscle involvement - moderate contribution to volume",
            VolumeContribution.HIGH: "Strong secondary target - high contribution to volume",
            VolumeContribution.PRIMARY: "Primary target muscle - full contribution to volume",
        }
        return descriptions[self]
    
    @property
    def percentage(self) -> int:
        """
        Return contribution as integer percentage (0-100).
        
        Returns:
            int: Percentage value (25, 50, 75, or 100)
            
        Examples:
            >>> VolumeContribution.HIGH.percentage
            75
            >>> VolumeContribution.MODERATE.percentage
            50
        """
        return int(self.value * 100)
    
    def calculate_volume(self, sets: int | float) -> float:
        """
        Calculate volume contribution for a given number of sets.
        
        Args:
            sets: Number of sets performed
            
        Returns:
            float: Effective volume contributed to the muscle group
            
        Examples:
            >>> VolumeContribution.PRIMARY.calculate_volume(4)
            4.0
            >>> VolumeContribution.MODERATE.calculate_volume(3)
            1.5
            >>> VolumeContribution.HIGH.calculate_volume(5)
            3.75
        """
        return sets * self.value
    
    def __str__(self) -> str:
        """String representation returns display name."""
        return self.display_name
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"VolumeContribution.{self.name}"
    
    @classmethod
    def from_percentage(cls, percentage: int) -> "VolumeContribution":
        """
        Create VolumeContribution from integer percentage.
        
        Args:
            percentage: Integer percentage (25, 50, 75, or 100)
            
        Returns:
            VolumeContribution: Corresponding enum value
            
        Raises:
            ValueError: If percentage is not 25, 50, 75, or 100
            
        Examples:
            >>> VolumeContribution.from_percentage(75)
            VolumeContribution.HIGH
            >>> VolumeContribution.from_percentage(100)
            VolumeContribution.PRIMARY
        """
        percentage_map = {
            25: cls.MINIMAL,
            50: cls.MODERATE,
            75: cls.HIGH,
            100: cls.PRIMARY,
        }
        
        if percentage not in percentage_map:
            raise ValueError(
                f"Invalid percentage: {percentage}. "
                f"Must be one of: {list(percentage_map.keys())}"
            )
        
        return percentage_map[percentage]
    
    @classmethod
    def from_float(cls, value: float) -> "VolumeContribution":
        """
        Create VolumeContribution from float value.
        
        Args:
            value: Float value (0.25, 0.50, 0.75, or 1.00)
            
        Returns:
            VolumeContribution: Corresponding enum value
            
        Raises:
            ValueError: If value is not a valid contribution level
            
        Examples:
            >>> VolumeContribution.from_float(0.75)
            VolumeContribution.HIGH
            >>> VolumeContribution.from_float(1.0)
            VolumeContribution.PRIMARY
        """
        # Round to 2 decimal places to handle floating point precision
        rounded = round(value, 2)
        
        value_map = {
            0.25: cls.MINIMAL,
            0.50: cls.MODERATE,
            0.75: cls.HIGH,
            1.00: cls.PRIMARY,
        }
        
        if rounded not in value_map:
            raise ValueError(
                f"Invalid contribution value: {value}. "
                f"Must be one of: {list(value_map.keys())}"
            )
        
        return value_map[rounded]
    
    @classmethod
    def validate(cls, value: float) -> bool:
        """
        Validate if a float value is a valid contribution level.
        
        Args:
            value: Float value to validate
            
        Returns:
            bool: True if valid, False otherwise
            
        Examples:
            >>> VolumeContribution.validate(0.75)
            True
            >>> VolumeContribution.validate(0.33)
            False
        """
        try:
            cls.from_float(value)
            return True
        except ValueError:
            return False
