"""
tests/test_pawpal.py
Automated pytest suite for PawPal+.
Run with: python -m pytest
"""

from datetime import date, timedelta
from pathlib import Path
import pytest
from pawpal_system import Task, Pet, Owner, Scheduler


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def today():
    return date.today()


@pytest.fixture
def owner_with_two_pets(today):
    owner = Owner(name="Jordan")
    mochi = Pet(name="Mochi", species="dog")
    luna = Pet(name="Luna", species="cat")
    mochi.add_task(Task("Walk",     due_time="07:00", due_date=today))
    mochi.add_task(Task("Feeding",  due_time="12:00", due_date=today))
    luna.add_task(Task("Breakfast", due_time="08:00", due_date=today))
    luna.add_task(Task("Playtime",  due_time="19:00", due_date=today))
    owner.add_pet(mochi)
    owner.add_pet(luna)
    return owner, mochi, luna


# ── Test 1: mark_complete() changes completed status ─────────────────────────

def test_task_mark_complete():
    """mark_complete() must flip completed from False to True."""
    task = Task(description="Give flea treatment", due_time="09:00")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


# ── Test 2: add_task() increases the pet's task count ────────────────────────

def test_add_task_increases_count():
    """add_task() must increase the pet's task list length by exactly 1."""
    pet = Pet(name="Biscuit", species="cat")
    assert len(pet.list_tasks()) == 0
    pet.add_task(Task("Feeding", due_time="07:30"))
    assert len(pet.list_tasks()) == 1
    pet.add_task(Task("Playtime", due_time="15:00"))
    assert len(pet.list_tasks()) == 2


# ── Test 3: sort_tasks() returns chronological order across pets ─────────────

def test_sort_tasks_chronological(owner_with_two_pets):
    """sort_tasks() must return tasks in ascending time order."""
    owner, _, _ = owner_with_two_pets
    scheduler = Scheduler(owner)
    sorted_pairs = scheduler.sort_tasks()
    times = [task.due_time for _, task in sorted_pairs]
    assert times == sorted(times), f"Expected sorted times but got {times}"


# ── Test 4: filter_tasks() by completion status ──────────────────────────────

def test_filter_tasks_by_completed_status(owner_with_two_pets):
    """filter_tasks(completed=True) must return only completed tasks."""
    owner, mochi, _ = owner_with_two_pets
    mochi.list_tasks()[0].mark_complete()
    scheduler = Scheduler(owner)
    done = scheduler.filter_tasks(completed=True)
    assert len(done) == 1
    assert done[0][1].completed is True


# ── Test 5: detect_conflicts() flags same-pet same-time collisions ───────────

def test_detect_conflicts_same_pet_same_time(today):
    """detect_conflicts() must warn when a pet has two tasks at the same time."""
    owner = Owner(name="Alex")
    rex = Pet(name="Rex", species="dog")
    rex.add_task(Task("Walk",    due_time="08:00", due_date=today))
    rex.add_task(Task("Feeding", due_time="08:00", due_date=today))
    owner.add_pet(rex)
    scheduler = Scheduler(owner)
    warnings = scheduler.detect_conflicts()
    assert len(warnings) == 1
    assert "Rex" in warnings[0]
    assert "08:00" in warnings[0]


# ── Test 6: handle_recurring() creates next occurrence ───────────────────────

def test_handle_recurring_daily(today):
    """handle_recurring() on a daily task must create a new task dated tomorrow."""
    owner = Owner(name="Sam")
    pet = Pet(name="Noodle", species="cat")
    task = Task("Breakfast", due_time="07:00", due_date=today, frequency="daily")
    pet.add_task(task)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    initial_count = len(pet.list_tasks())
    scheduler.handle_recurring(pet, task)

    assert task.completed is True
    assert len(pet.list_tasks()) == initial_count + 1
    new_task = pet.list_tasks()[-1]
    assert new_task.due_date == today + timedelta(days=1)
    assert new_task.completed is False
    assert new_task.frequency == "daily"


# ── Test 7: sort_by_priority() returns high → medium → low ───────────────────

def test_sort_by_priority_order(today):
    """sort_by_priority() must return tasks ordered high, then medium, then low."""
    owner = Owner(name="Casey")
    pet = Pet(name="Peanut", species="dog")
    pet.add_task(Task("Afternoon walk", due_time="15:00", due_date=today, priority="low"))
    pet.add_task(Task("Medication",     due_time="09:00", due_date=today, priority="high"))
    pet.add_task(Task("Feeding",        due_time="12:00", due_date=today, priority="medium"))
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    sorted_pairs = scheduler.sort_by_priority()
    priorities = [task.priority for _, task in sorted_pairs]
    assert priorities == ["high", "medium", "low"], f"Expected high/medium/low but got {priorities}"


# ── Test 8: filter_tasks(pet_name=...) isolates a single pet ─────────────────

def test_filter_tasks_by_pet_name(owner_with_two_pets):
    """filter_tasks(pet_name='Mochi') must return only Mochi's tasks."""
    owner, mochi, _ = owner_with_two_pets
    scheduler = Scheduler(owner)

    result = scheduler.filter_tasks(pet_name="Mochi")

    assert len(result) == len(mochi.list_tasks())
    for pet, _ in result:
        assert pet.name == "Mochi", f"Expected only Mochi but got {pet.name}"


# ── Test 9: handle_recurring() with weekly frequency advances by 7 days ──────

def test_handle_recurring_weekly(today):
    """handle_recurring() on a weekly task must schedule the next occurrence 7 days out."""
    owner = Owner(name="Morgan")
    pet = Pet(name="Gizmo", species="rabbit")
    task = Task(
        "Nail trim",
        due_time="10:00",
        due_date=today,
        frequency="weekly",
        priority="high",
        duration_minutes=15,
    )
    pet.add_task(task)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    initial_count = len(pet.list_tasks())
    scheduler.handle_recurring(pet, task)

    assert task.completed is True
    assert len(pet.list_tasks()) == initial_count + 1
    new_task = pet.list_tasks()[-1]
    assert new_task.due_date == today + timedelta(weeks=1)
    assert new_task.completed is False
    assert new_task.frequency == "weekly"
    assert new_task.priority == "high"
    assert new_task.duration_minutes == 15


# ── Test 10: handle_recurring() with "once" does NOT create a new task ────────

def test_handle_recurring_once_no_new_task(today):
    """handle_recurring() on a one-time task must complete it without adding a follow-up."""
    owner = Owner(name="Riley")
    pet = Pet(name="Pepper", species="cat")
    task = Task("Vet visit", due_time="11:00", due_date=today, frequency="once")
    pet.add_task(task)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    initial_count = len(pet.list_tasks())
    scheduler.handle_recurring(pet, task)

    assert task.completed is True
    assert len(pet.list_tasks()) == initial_count, (
        "A 'once' task must not generate a follow-up task"
    )


# ── Test 11: edit_task() updates valid fields and rejects invalid ones ────────

def test_edit_task_validation():
    """edit_task() must apply valid field changes and raise ValueError for unknown fields."""
    pet = Pet(name="Coco", species="dog")
    pet.add_task(Task("Walk", due_time="08:00"))

    # Valid edit — due_time and description should both update
    pet.edit_task(0, due_time="09:30", description="Late walk")
    assert pet.list_tasks()[0].due_time == "09:30"
    assert pet.list_tasks()[0].description == "Late walk"

    # Invalid field — must raise ValueError, not silently ignore
    with pytest.raises(ValueError, match="not a valid Task field"):
        pet.edit_task(0, nonexistent_field="oops")


# ── Test 12: Owner with no pets returns empty results without crashing ────────

def test_owner_no_pets_empty_results():
    """sort_tasks(), detect_conflicts(), and filter_tasks() must all return [] for an owner with no pets."""
    owner = Owner(name="NewUser")
    scheduler = Scheduler(owner)

    assert scheduler.sort_tasks() == []
    assert scheduler.detect_conflicts() == []
    assert scheduler.filter_tasks() == []


# ── Test 13: find_next_available_slot() returns the first gap that fits ───────

def test_find_next_available_slot_basic(today):
    """find_next_available_slot() must return the correct start time for the first gap."""
    owner = Owner(name="Zara")
    pet = Pet(name="Boba", species="dog")
    # 08:00–08:30 and 10:00–10:20 are occupied; a 45-min request should land at 08:30
    pet.add_task(Task("Walk",    due_time="08:00", due_date=today, duration_minutes=30))
    pet.add_task(Task("Feeding", due_time="10:00", due_date=today, duration_minutes=20))
    owner.add_pet(pet)
    result = Scheduler(owner).find_next_available_slot("Boba", 45, search_date=today)
    assert result == (today, "08:30")


# ── Test 14: find_next_available_slot() rolls to the next day when today is full

def test_find_next_available_slot_rolls_to_next_day(today):
    """find_next_available_slot() must advance to the next day when today has no gap."""
    owner = Owner(name="Zara")
    pet = Pet(name="Boba", species="dog")
    pet.add_task(Task("Block A", due_time="08:00", due_date=today, duration_minutes=360))  # 08:00–14:00
    pet.add_task(Task("Block B", due_time="14:00", due_date=today, duration_minutes=360))  # 14:00–20:00
    owner.add_pet(pet)
    result = Scheduler(owner).find_next_available_slot(
        "Boba", 30, search_date=today, day_start="08:00", day_end="20:00", max_days_ahead=3
    )
    assert result == (today + timedelta(days=1), "08:00")


# ── Test 15: find_next_available_slot() returns None after exhausting all days ─

def test_find_next_available_slot_returns_none_when_exhausted(today):
    """find_next_available_slot() must return None when no slot is found within max_days_ahead."""
    owner = Owner(name="Zara")
    pet = Pet(name="Boba", species="dog")
    for offset in range(2):
        pet.add_task(Task("Block", due_time="08:00",
                          due_date=today + timedelta(days=offset), duration_minutes=720))
    owner.add_pet(pet)
    result = Scheduler(owner).find_next_available_slot(
        "Boba", 30, search_date=today, day_start="08:00", day_end="20:00", max_days_ahead=1
    )
    assert result is None


# ── Test 16: save_to_json / load_from_json roundtrip preserves all data ───────

def test_save_load_roundtrip(tmp_path, today):
    """save_to_json() then load_from_json() must restore every field exactly."""
    owner = Owner(name="Robin")
    pet = Pet(name="Finn", species="dog", allergies="chicken")
    tomorrow = today + timedelta(days=1)
    pet.add_task(Task("Walk",    due_time="07:00", due_date=today,    frequency="daily",  priority="high",   duration_minutes=30))
    pet.add_task(Task("Vet",     due_time="14:00", due_date=tomorrow, frequency="once",   priority="medium", duration_minutes=60, completed=True))
    owner.add_pet(pet)

    filepath = str(tmp_path / "data.json")
    owner.save_to_json(filepath)
    loaded = Owner.load_from_json(filepath)

    assert loaded.name == "Robin"
    assert len(loaded.pets) == 1
    loaded_pet = loaded.pets[0]
    assert loaded_pet.name == "Finn"
    assert loaded_pet.allergies == "chicken"
    assert len(loaded_pet.tasks) == 2

    t0, t1 = loaded_pet.tasks
    assert t0.description == "Walk"
    assert t0.due_date == today          # restored as date, not string
    assert isinstance(t0.due_date, date)
    assert t0.frequency == "daily"
    assert t0.priority == "high"
    assert t0.duration_minutes == 30
    assert t0.completed is False

    assert t1.description == "Vet"
    assert t1.due_date == tomorrow
    assert t1.completed is True


# ── Test 17: load_from_json with missing file returns a default Owner ──────────

def test_load_from_json_missing_file_returns_default():
    """load_from_json() must return a fresh Owner when the file does not exist."""
    result = Owner.load_from_json("__nonexistent_pawpal_data__.json")
    assert isinstance(result, Owner)
    assert result.name == "Jordan"
    assert result.pets == []
