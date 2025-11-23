"""Training Split Entity and Types.

This module defines the training split types and structure for hypertrophy programs.
"""

from enum import Enum


class TrainingSplitType(str, Enum):
    """Enumeration of training split types for hypertrophy programs.
    
    Attributes:
        UPPER_LOWER: 2-day split alternating upper and lower body
        PUSH_PULL_LEGS: 3-day split separating push, pull, and leg movements
        FULL_BODY: Training all major muscle groups in each session
        BRO_SPLIT: Traditional bodybuilding split (chest day, back day, etc.)
        ANTERIOR_POSTERIOR: Front and back body split
        CUSTOM: User-defined custom split configuration
    """
    
    UPPER_LOWER = "UPPER_LOWER"
    PUSH_PULL_LEGS = "PUSH_PULL_LEGS"
    FULL_BODY = "FULL_BODY"
    BRO_SPLIT = "BRO_SPLIT"
    ANTERIOR_POSTERIOR = "ANTERIOR_POSTERIOR"
    CUSTOM = "CUSTOM"
    
    def __str__(self) -> str:
        """Return human-readable string representation."""
        return self.value.replace("_", " ").title()
    
    @property
    def typical_frequency(self) -> int:
        """Return typical training frequency for this split type.
        
        Returns:
            int: Recommended number of sessions per week
        """
        frequency_map = {
            self.UPPER_LOWER: 4,  # ULUL pattern
            self.PUSH_PULL_LEGS: 6,  # PPL twice per week
            self.FULL_BODY: 3,  # 3x per week
            self.BRO_SPLIT: 5,  # 5-day traditional split
            self.ANTERIOR_POSTERIOR: 4,  # Similar to upper/lower
            self.CUSTOM: 4,  # Default for custom
        }
        return frequency_map[self]
    
    @property
    def description(self) -> str:
        """Return description of the training split.
        
        Returns:
            str: Detailed description of the split type
        """
        descriptions = {
            self.UPPER_LOWER: "Alternates between upper body and lower body training days, allowing focused work with adequate recovery.",
            self.PUSH_PULL_LEGS: "Separates training into pushing movements (chest, shoulders, triceps), pulling movements (back, biceps), and legs.",
            self.FULL_BODY: "Trains all major muscle groups in each session, ideal for beginners or maintenance phases.",
            self.BRO_SPLIT: "Traditional bodybuilding split dedicating entire sessions to specific muscle groups (e.g., chest day, back day).",
            self.ANTERIOR_POSTERIOR: "Divides training between anterior chain (front of body) and posterior chain (back of body) movements.",
            self.CUSTOM: "User-defined split allowing complete customization of training structure.",
        }
        return descriptions[self]
    
    @property
    def muscle_group_distribution(self) -> dict[str, list[str]]:
        """Return typical muscle group distribution for this split.
        
        Returns:
            dict: Mapping of session types to muscle groups
        """
        distributions = {
            self.UPPER_LOWER: {
                "Upper": ["CHEST", "LATS", "TRAPS_RHOMBOIDS", "FRONT_DELTS", "SIDE_DELTS", "REAR_DELTS", "TRICEPS", "ELBOW_FLEXORS"],
                "Lower": ["GLUTES", "QUADS", "HAMSTRINGS", "ADDUCTORS", "CALVES", "ABS", "OBLIQUES"],
            },
            self.PUSH_PULL_LEGS: {
                "Push": ["CHEST", "FRONT_DELTS", "SIDE_DELTS", "TRICEPS"],
                "Pull": ["LATS", "TRAPS_RHOMBOIDS", "REAR_DELTS", "ELBOW_FLEXORS"],
                "Legs": ["GLUTES", "QUADS", "HAMSTRINGS", "ADDUCTORS", "CALVES"],
            },
            self.FULL_BODY: {
                "Full Body": ["CHEST", "LATS", "FRONT_DELTS", "SIDE_DELTS", "REAR_DELTS", "TRICEPS", "ELBOW_FLEXORS", 
                             "GLUTES", "QUADS", "HAMSTRINGS", "CALVES"],
            },
            self.BRO_SPLIT: {
                "Chest": ["CHEST", "TRICEPS"],
                "Back": ["LATS", "TRAPS_RHOMBOIDS", "ELBOW_FLEXORS"],
                "Shoulders": ["FRONT_DELTS", "SIDE_DELTS", "REAR_DELTS"],
                "Legs": ["GLUTES", "QUADS", "HAMSTRINGS", "ADDUCTORS", "CALVES"],
                "Arms": ["TRICEPS", "ELBOW_FLEXORS", "FOREARMS"],
            },
            self.ANTERIOR_POSTERIOR: {
                "Anterior": ["CHEST", "FRONT_DELTS", "QUADS", "ABS", "TRICEPS"],
                "Posterior": ["LATS", "TRAPS_RHOMBOIDS", "REAR_DELTS", "HAMSTRINGS", "GLUTES", "ELBOW_FLEXORS"],
            },
            self.CUSTOM: {},
        }
        return distributions[self]
