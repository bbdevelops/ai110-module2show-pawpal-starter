"""
pawpal_system.py
Core logic layer for PawPal+ — the pet care scheduling system.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field, fields as dataclass_fields, replace as dataclass_replace
from datetime import date, timedelta
from pathlib import Path
from typing import Optional


@dataclass
class Task:
    """Represents a single pet care task."""

    description: str
    due_time: str                        # "HH:MM" format
    due_date: date = field(default_factory=date.today)
    completed: bool = False
    frequency: str = "once"             # "once", "daily", "weekly"
    priority: str = "medium"            # "low", "medium", "high"
    duration_minutes: int = 0

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
        Raises ValueError if an unknown Task field is provided.
        """
        valid = {f.name for f in dataclass_fields(Task)}
        for key in kwargs:
            if key not in valid:
                raise ValueError(f"'{key}' is not a valid Task field")
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
        """Remove all pets matching the given name. No-op if not found."""
        self.pets = [p for p in self.pets if p.name != pet_name]

    def list_pets(self) -> list[Pet]:
        """Return all pets belonging to this owner."""
        return self.pets

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return all (pet, task) pairs across every pet."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]

    def save_to_json(self, filepath: str = "data.json") -> None:
        """Serialize this owner and all pets/tasks to a JSON file."""
        def task_to_dict(t: Task) -> dict:
            return {
                "description": t.description,
                "due_time": t.due_time,
                "due_date": t.due_date.isoformat(),
                "completed": t.completed,
                "frequency": t.frequency,
                "priority": t.priority,
                "duration_minutes": t.duration_minutes,
            }

        def pet_to_dict(p: Pet) -> dict:
            return {
                "name": p.name,
                "species": p.species,
                "dietary_restrictions": p.dietary_restrictions,
                "allergies": p.allergies,
                "health_conditions": p.health_conditions,
                "tasks": [task_to_dict(t) for t in p.tasks],
            }

        data = {"name": self.name, "pets": [pet_to_dict(p) for p in self.pets]}
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_json(cls, filepath: str = "data.json") -> "Owner":
        """Load an Owner (with all pets and tasks) from a JSON file.

        Returns a fresh Owner named 'Jordan' if the file does not exist.
        """
        if not Path(filepath).exists():
            return cls(name="Jordan")

        with open(filepath) as f:
            data = json.load(f)

        owner = cls(name=data["name"])
        for pet_data in data.get("pets", []):
            pet = Pet(
                name=pet_data["name"],
                species=pet_data["species"],
                dietary_restrictions=pet_data.get("dietary_restrictions", ""),
                allergies=pet_data.get("allergies", ""),
                health_conditions=pet_data.get("health_conditions", ""),
            )
            for task_data in pet_data.get("tasks", []):
                pet.add_task(Task(
                    description=task_data["description"],
                    due_time=task_data["due_time"],
                    due_date=date.fromisoformat(task_data["due_date"]),
                    completed=task_data.get("completed", False),
                    frequency=task_data.get("frequency", "once"),
                    priority=task_data.get("priority", "medium"),
                    duration_minutes=task_data.get("duration_minutes", 0),
                ))
            owner.add_pet(pet)
        return owner


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

    def sort_by_priority(self) -> list[tuple[Pet, Task]]:
        """Return all tasks sorted by priority (high → medium → low), then by time."""
        _rank = {"high": 0, "medium": 1, "low": 2}
        pairs = self.owner.get_all_tasks()
        return sorted(pairs, key=lambda pair: (_rank.get(pair[1].priority, 1), pair[1].due_date, pair[1].due_time))

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
        tasks_by_slot: dict[tuple[str, date, str], list[str]] = {}
        for pet, task in self.owner.get_all_tasks():
            key = (pet.name, task.due_date, task.due_time)
            tasks_by_slot.setdefault(key, []).append(task.description)
        return [
            f"CONFLICT — {pet_name} on {due_date} at {due_time}: [{' | '.join(descs)}]"
            for (pet_name, due_date, due_time), descs in tasks_by_slot.items()
            if len(descs) > 1
        ]

    def handle_recurring(self, pet: Pet, task: Task) -> None:
        """Mark a recurring task complete and schedule the next occurrence.

        'daily' advances due_date by 1 day; 'weekly' by 7 days.
        'once' tasks are only marked complete — no follow-up is created.
        """
        if task not in pet.tasks:
            raise ValueError(f"Task '{task.description}' does not belong to {pet.name}")
        task.mark_complete()

        if task.frequency == "daily":
            next_date = task.due_date + timedelta(days=1)
        elif task.frequency == "weekly":
            next_date = task.due_date + timedelta(weeks=1)
        else:
            return

        pet.add_task(dataclass_replace(task, due_date=next_date, completed=False))

    # ── Private helpers for time arithmetic ───────────────────────────────

    def _parse_hhmm(self, hhmm: str) -> int:
        """Convert 'HH:MM' string to total minutes since midnight."""
        h, m = hhmm.split(":")
        return int(h) * 60 + int(m)

    def _minutes_to_hhmm(self, minutes: int) -> str:
        """Convert total minutes since midnight back to 'HH:MM' string."""
        return f"{minutes // 60:02d}:{minutes % 60:02d}"

    def find_next_available_slot(
        self,
        pet_name: str,
        duration_minutes: int,
        search_date: Optional[date] = None,
        day_start: str = "08:00",
        day_end: str = "20:00",
        max_days_ahead: int = 7,
    ) -> Optional[tuple[date, str]]:
        """Return (date, 'HH:MM') for the earliest open slot of at least
        duration_minutes, scanning up to max_days_ahead days from search_date.
        Returns None if no slot is found in that window.

        Raises ValueError for invalid inputs (bad duration, inverted window,
        or unknown pet name).
        """
        if duration_minutes <= 0:
            raise ValueError("duration_minutes must be a positive integer")
        if self._parse_hhmm(day_start) >= self._parse_hhmm(day_end):
            raise ValueError("day_start must be earlier than day_end")

        pet = next((p for p in self.owner.pets if p.name == pet_name), None)
        if pet is None:
            raise ValueError(f"No pet named '{pet_name}' found")

        candidate_date = search_date or date.today()
        win_start = self._parse_hhmm(day_start)
        win_end = self._parse_hhmm(day_end)

        for offset in range(max_days_ahead + 1):
            target = candidate_date + timedelta(days=offset)

            # Build sorted occupied intervals [start_min, end_min) for this day.
            # Tasks with duration_minutes == 0 produce empty intervals and are ignored.
            intervals = sorted(
                (
                    (self._parse_hhmm(t.due_time),
                     self._parse_hhmm(t.due_time) + t.duration_minutes)
                    for t in pet.tasks
                    if t.due_date == target
                ),
                key=lambda iv: iv[0],
            )

            probe = win_start
            for occ_start, occ_end in intervals:
                if occ_start - probe >= duration_minutes:
                    return (target, self._minutes_to_hhmm(probe))
                probe = max(probe, occ_end)

            if win_end - probe >= duration_minutes:
                return (target, self._minutes_to_hhmm(probe))

        return None
