"""
tests/test_pawpal.py
Automated pytest suite for PawPal+.
Run with: python -m pytest
"""

from datetime import date, timedelta
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
