"""Training Structure Value Objects.

This module defines the structure types and configurations for training schedules.
"""

from datetime import date, timedelta
from enum import Enum
from typing import ClassVar

from pydantic import BaseModel, Field, field_validator, model_validator


class StructureType(str, Enum):
    """Enumeration of training structure types.
    
    Attributes:
        WEEKLY: Fixed days of the week (e.g., Mon/Wed/Fri)
        CYCLIC: Rotating pattern of days on/off (e.g., 3 days on, 1 day off)
    """
    
    WEEKLY = "WEEKLY"
    CYCLIC = "CYCLIC"
    
    def __str__(self) -> str:
        """Return human-readable string representation."""
        return self.value.capitalize()


class WeekDay(str, Enum):
    """Enumeration of days of the week."""
    
    MONDAY = "MON"
    TUESDAY = "TUE"
    WEDNESDAY = "WED"
    THURSDAY = "THU"
    FRIDAY = "FRI"
    SATURDAY = "SAT"
    SUNDAY = "SUN"
    
    @classmethod
    def get_full_name(cls, day: str) -> str:
        """Get full day name from abbreviation.
        
        Args:
            day: Day abbreviation (MON, TUE, etc.)
            
        Returns:
            str: Full day name (Monday, Tuesday, etc.)
        """
        name_map = {
            cls.MONDAY.value: "Monday",
            cls.TUESDAY.value: "Tuesday",
            cls.WEDNESDAY.value: "Wednesday",
            cls.THURSDAY.value: "Thursday",
            cls.FRIDAY.value: "Friday",
            cls.SATURDAY.value: "Saturday",
            cls.SUNDAY.value: "Sunday",
        }
        return name_map.get(day, day)
    
    @classmethod
    def get_all_days(cls) -> list[str]:
        """Get list of all day abbreviations.
        
        Returns:
            list[str]: All day abbreviations in order
        """
        return [day.value for day in cls]
    
    @classmethod
    def get_weekday_index(cls, day: str) -> int:
        """Get weekday index (0=Monday, 6=Sunday).
        
        Args:
            day: Day abbreviation (MON, TUE, etc.)
            
        Returns:
            int: Weekday index (0-6)
        """
        day_map = {
            cls.MONDAY.value: 0,
            cls.TUESDAY.value: 1,
            cls.WEDNESDAY.value: 2,
            cls.THURSDAY.value: 3,
            cls.FRIDAY.value: 4,
            cls.SATURDAY.value: 5,
            cls.SUNDAY.value: 6,
        }
        return day_map.get(day, 0)


class WeeklyStructure(BaseModel):
    """Value object for weekly training structure.
    
    Represents a training schedule based on fixed days of the week.
    
    Attributes:
        days_per_week: Number of training days per week (3-7)
        selected_days: List of selected day abbreviations (MON, TUE, WED, etc.)
    """
    
    days_per_week: int = Field(ge=3, le=7, description="Number of training days per week")
    selected_days: list[str] = Field(min_length=3, max_length=7, description="Selected training days")
    
    # Valid day abbreviations
    VALID_DAYS: ClassVar[list[str]] = [day.value for day in WeekDay]
    
    @field_validator("selected_days")
    @classmethod
    def validate_days(cls, v: list[str]) -> list[str]:
        """Validate that all selected days are valid abbreviations.
        
        Args:
            v: List of day abbreviations
            
        Returns:
            list[str]: Validated list of day abbreviations
            
        Raises:
            ValueError: If any day is invalid or there are duplicates
        """
        # Check for duplicates
        if len(v) != len(set(v)):
            raise ValueError("Selected days must not contain duplicates")
        
        # Validate each day
        for day in v:
            if day not in cls.VALID_DAYS:
                raise ValueError(
                    f"Invalid day '{day}'. Must be one of: {', '.join(cls.VALID_DAYS)}"
                )
        
        return v
    
    @model_validator(mode="after")
    def validate_consistency(self) -> "WeeklyStructure":
        """Validate that selected_days length matches days_per_week.
        
        Returns:
            WeeklyStructure: Validated instance
            
        Raises:
            ValueError: If selected_days length doesn't match days_per_week
        """
        if len(self.selected_days) != self.days_per_week:
            raise ValueError(
                f"Number of selected days ({len(self.selected_days)}) must match "
                f"days_per_week ({self.days_per_week})"
            )
        return self
    
    def get_ordered_days(self) -> list[str]:
        """Get selected days in week order (Monday first).
        
        Returns:
            list[str]: Selected days sorted by weekday order
        """
        day_order = {day: idx for idx, day in enumerate(WeekDay.get_all_days())}
        return sorted(self.selected_days, key=lambda d: day_order.get(d, 999))
    
    def get_rest_days(self) -> list[str]:
        """Get list of rest days (days not in selected_days).
        
        Returns:
            list[str]: Days of the week that are rest days
        """
        all_days = set(WeekDay.get_all_days())
        selected_set = set(self.selected_days)
        return sorted(all_days - selected_set, key=lambda d: WeekDay.get_weekday_index(d))
    
    def is_training_day(self, day: str) -> bool:
        """Check if a given day is a training day.
        
        Args:
            day: Day abbreviation (MON, TUE, etc.)
            
        Returns:
            bool: True if day is a training day
        """
        return day in self.selected_days
    
    def get_next_training_day(self, current_day: str) -> str | None:
        """Get the next training day after the given day.
        
        Args:
            current_day: Current day abbreviation
            
        Returns:
            str | None: Next training day, or None if current_day is invalid
        """
        if current_day not in WeekDay.get_all_days():
            return None
        
        ordered_days = self.get_ordered_days()
        current_idx = WeekDay.get_weekday_index(current_day)
        
        # Find next training day
        for _ in range(7):  # Check up to 7 days ahead
            current_idx = (current_idx + 1) % 7
            next_day = WeekDay.get_all_days()[current_idx]
            if next_day in ordered_days:
                return next_day
        
        return None
    
    def generate_schedule(self, start_date: date, weeks: int = 4) -> list[tuple[date, str]]:
        """Generate a training schedule for the specified number of weeks.
        
        Args:
            start_date: Starting date for the schedule
            weeks: Number of weeks to generate (default 4)
            
        Returns:
            list[tuple[date, str]]: List of (date, day_abbreviation) tuples for training days
        """
        schedule = []
        current_date = start_date
        end_date = start_date + timedelta(weeks=weeks)
        
        while current_date < end_date:
            # Get weekday (0=Monday, 6=Sunday)
            weekday_idx = current_date.weekday()
            day_abbr = WeekDay.get_all_days()[weekday_idx]
            
            if self.is_training_day(day_abbr):
                schedule.append((current_date, day_abbr))
            
            current_date += timedelta(days=1)
        
        return schedule
    
    def get_weekly_pattern(self) -> str:
        """Get a visual representation of the weekly pattern.
        
        Returns:
            str: Pattern like "T-R-T-R-T-R-R" (T=training, R=rest)
        """
        ordered_days = WeekDay.get_all_days()
        pattern = []
        for day in ordered_days:
            pattern.append("T" if self.is_training_day(day) else "R")
        return "-".join(pattern)
    
    class Config:
        """Pydantic model configuration."""
        frozen = True  # Make immutable (value object)


class CyclicStructure(BaseModel):
    """Value object for cyclic training structure.
    
    Represents a training schedule based on rotating days on/off pattern.
    
    Attributes:
        days_on: Number of consecutive training days (1-6)
        days_off: Number of consecutive rest days (1-3)
    """
    
    days_on: int = Field(ge=1, le=6, description="Consecutive training days")
    days_off: int = Field(ge=1, le=3, description="Consecutive rest days")
    
    @field_validator("days_on")
    @classmethod
    def validate_days_on(cls, v: int) -> int:
        """Validate days_on is within reasonable limits.
        
        Args:
            v: Number of days on
            
        Returns:
            int: Validated days_on
            
        Raises:
            ValueError: If days_on is unreasonable
        """
        if v < 1:
            raise ValueError("days_on must be at least 1")
        if v > 6:
            raise ValueError("days_on should not exceed 6 for proper recovery")
        return v
    
    @field_validator("days_off")
    @classmethod
    def validate_days_off(cls, v: int) -> int:
        """Validate days_off is within reasonable limits.
        
        Args:
            v: Number of days off
            
        Returns:
            int: Validated days_off
            
        Raises:
            ValueError: If days_off is unreasonable
        """
        if v < 1:
            raise ValueError("days_off must be at least 1")
        if v > 3:
            raise ValueError("days_off should not exceed 3 to maintain training frequency")
        return v
    
    @model_validator(mode="after")
    def validate_cycle_length(self) -> "CyclicStructure":
        """Validate that total cycle length is reasonable.
        
        Returns:
            CyclicStructure: Validated instance
            
        Raises:
            ValueError: If cycle length is too short or too long
        """
        cycle_length = self.days_on + self.days_off
        
        if cycle_length < 2:
            raise ValueError("Total cycle length must be at least 2 days")
        
        if cycle_length > 9:
            raise ValueError(
                f"Total cycle length ({cycle_length} days) is too long. "
                "Consider using a weekly structure instead."
            )
        
        # Warn if training frequency is too low
        training_frequency = (self.days_on / cycle_length) * 7
        if training_frequency < 3:
            raise ValueError(
                f"This cycle results in only {training_frequency:.1f} training days per week. "
                "Minimum 3 days per week recommended for hypertrophy."
            )
        
        return self
    
    @property
    def cycle_length(self) -> int:
        """Get total length of one training cycle.
        
        Returns:
            int: Total days in one cycle (days_on + days_off)
        """
        return self.days_on + self.days_off
    
    @property
    def weekly_frequency(self) -> float:
        """Calculate average training days per week.
        
        Returns:
            float: Average number of training days per week
        """
        return (self.days_on / self.cycle_length) * 7
    
    def is_training_day(self, day_number: int) -> bool:
        """Check if a given day number in the cycle is a training day.
        
        Args:
            day_number: Day number in the cycle (0-indexed)
            
        Returns:
            bool: True if day is a training day
        """
        cycle_position = day_number % self.cycle_length
        return cycle_position < self.days_on
    
    def generate_schedule(self, start_date: date, weeks: int = 4) -> list[tuple[date, int, bool]]:
        """Generate a training schedule for the specified number of weeks.
        
        Args:
            start_date: Starting date for the schedule
            weeks: Number of weeks to generate (default 4)
            
        Returns:
            list[tuple[date, int, bool]]: List of (date, cycle_day, is_training) tuples
        """
        schedule = []
        current_date = start_date
        end_date = start_date + timedelta(weeks=weeks)
        day_in_cycle = 0
        
        while current_date < end_date:
            is_training = self.is_training_day(day_in_cycle)
            cycle_day = (day_in_cycle % self.cycle_length) + 1  # 1-indexed for display
            schedule.append((current_date, cycle_day, is_training))
            
            current_date += timedelta(days=1)
            day_in_cycle += 1
        
        return schedule
    
    def get_training_days_in_range(self, start_date: date, end_date: date) -> int:
        """Calculate number of training days in a date range.
        
        Args:
            start_date: Start of range
            end_date: End of range
            
        Returns:
            int: Number of training days in the range
        """
        total_days = (end_date - start_date).days + 1
        full_cycles = total_days // self.cycle_length
        remaining_days = total_days % self.cycle_length
        
        # Count training days in full cycles
        training_days = full_cycles * self.days_on
        
        # Count training days in remaining partial cycle
        training_days += min(remaining_days, self.days_on)
        
        return training_days
    
    def get_cycle_pattern(self) -> str:
        """Get a visual representation of one cycle.
        
        Returns:
            str: Pattern like "T-T-T-R" (T=training, R=rest)
        """
        pattern = ["T"] * self.days_on + ["R"] * self.days_off
        return "-".join(pattern)
    
    def get_rest_ratio(self) -> float:
        """Calculate the ratio of rest days to training days.
        
        Returns:
            float: Rest-to-training ratio
        """
        return self.days_off / self.days_on
    
    class Config:
        """Pydantic model configuration."""
        frozen = True  # Make immutable (value object)


def validate_structure_for_split(
    structure_type: StructureType,
    structure_data: WeeklyStructure | CyclicStructure,
    split_frequency: int
) -> tuple[bool, str | None]:
    """Validate that a training structure is appropriate for a split's frequency.
    
    Args:
        structure_type: Type of structure (WEEKLY or CYCLIC)
        structure_data: The structure configuration
        split_frequency: Required training frequency for the split
        
    Returns:
        tuple[bool, str | None]: (is_valid, error_message)
    """
    if structure_type == StructureType.WEEKLY:
        if not isinstance(structure_data, WeeklyStructure):
            return False, "Structure data must be WeeklyStructure for WEEKLY type"
        
        if structure_data.days_per_week < split_frequency:
            return False, (
                f"Weekly structure has {structure_data.days_per_week} days but split "
                f"requires {split_frequency} days per week"
            )
    
    elif structure_type == StructureType.CYCLIC:
        if not isinstance(structure_data, CyclicStructure):
            return False, "Structure data must be CyclicStructure for CYCLIC type"
        
        avg_frequency = structure_data.weekly_frequency
        if avg_frequency < split_frequency - 0.5:  # Allow small tolerance
            return False, (
                f"Cyclic structure averages {avg_frequency:.1f} days/week but split "
                f"requires approximately {split_frequency} days per week"
            )
    
    return True, None
