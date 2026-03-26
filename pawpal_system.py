"""
pawpal_system.py
Core logic layer for PawPal+ — the pet care scheduling system.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional


@dataclass
class Task:
    """Represents a single pet care task."""

    description: str
    due_time: str                        # "HH:MM" format
    due_date: date = field(default_factory=date.today)
    completed: bool = False
    frequency: str = "once"             # "once", "daily", "weekly"

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True


@dataclass
class Pet:
    """Represents a pet with health info and its own task list."""

    name: str
    species: str
    dietary_restrictions: str = ""
    allergies: str = ""
    health_conditions: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's task list."""
        self.tasks.append(task)

    def edit_task(self, index: int, **kwargs) -> None:
        """Update fields on the task at the given index.

        Example: pet.edit_task(0, due_time="09:00", description="Late walk")
        Raises IndexError if index is out of range.
        """
        task = self.tasks[index]
        for key, value in kwargs.items():
            setattr(task, key, value)

    def list_tasks(self) -> list[Task]:
        """Return all tasks for this pet."""
        return self.tasks


class Owner:
    """Represents a pet owner who manages one or more pets."""

    def __init__(self, name: str) -> None:
        self.name: str = name
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's list."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """Remove the first pet matching the given name. No-op if not found."""
        self.pets = [p for p in self.pets if p.name != pet_name]

    def list_pets(self) -> list[Pet]:
        """Return all pets belonging to this owner."""
        return self.pets

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return all (pet, task) pairs across every pet."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]


class Scheduler:
    """
    The algorithmic brain of PawPal+.
    Retrieves and organizes tasks across all pets owned by a given Owner.
    """

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def sort_tasks(self) -> list[tuple[Pet, Task]]:
        """Return all tasks sorted chronologically by due_date then due_time."""
        pairs = self.owner.get_all_tasks()
        return sorted(pairs, key=lambda pair: (pair[1].due_date, pair[1].due_time))

    def filter_tasks(
        self,
        completed: Optional[bool] = None,
        pet_name: Optional[str] = None,
    ) -> list[tuple[Pet, Task]]:
        """Filter tasks by completion status and/or pet name.

        Both parameters are optional and can be combined.
        """
        pairs = self.owner.get_all_tasks()
        if completed is not None:
            pairs = [(p, t) for p, t in pairs if t.completed == completed]
        if pet_name is not None:
            pairs = [(p, t) for p, t in pairs if p.name == pet_name]
        return pairs

    def detect_conflicts(self) -> list[str]:
        """Detect tasks for the same pet at the same date and time.

        Returns a list of human-readable warning strings.
        """
        warnings: list[str] = []
        seen: dict[tuple[str, date, str], list[str]] = {}

        for pet, task in self.owner.get_all_tasks():
            key = (pet.name, task.due_date, task.due_time)
            seen.setdefault(key, []).append(task.description)

        for (pet_name, due_date, due_time), descriptions in seen.items():
            if len(descriptions) > 1:
                conflict_list = " | ".join(descriptions)
                warnings.append(
                    f"CONFLICT — {pet_name} on {due_date} at {due_time}: "
                    f"[{conflict_list}]"
                )
        return warnings

    def handle_recurring(self, pet: Pet, task: Task) -> None:
        """Mark a recurring task complete and schedule the next occurrence.

        'daily' advances due_date by 1 day; 'weekly' by 7 days.
        'once' tasks are only marked complete — no follow-up is created.
        """
        task.mark_complete()

        if task.frequency == "daily":
            next_date = task.due_date + timedelta(days=1)
        elif task.frequency == "weekly":
            next_date = task.due_date + timedelta(weeks=1)
        else:
            return

        next_task = Task(
            description=task.description,
            due_time=task.due_time,
            due_date=next_date,
            completed=False,
            frequency=task.frequency,
        )
        pet.add_task(next_task)
