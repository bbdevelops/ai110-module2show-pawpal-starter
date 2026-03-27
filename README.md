# PawPal+ (Module 2 Project)

**PawPal+** is a pet care scheduling assistant built with Python and Streamlit. It helps a busy pet owner stay consistent with daily routines by tracking tasks across multiple pets, generating a sorted daily schedule, detecting time conflicts, and automatically rescheduling recurring tasks.

---

## System Architecture

PawPal+ is built around four Python classes in `pawpal_system.py`:

| Class | Responsibility |
|---|---|
| **Task** | A single care activity. Holds description, scheduled time, due date, completion status, recurrence frequency, priority, and duration. |
| **Pet** | An individual animal with health context (dietary restrictions, allergies, health conditions) and a personal task list. Supports adding, editing, and listing tasks. |
| **Owner** | The top-level entity. Manages a collection of pets and exposes `get_all_tasks()` which returns every `(Pet, Task)` pair across all pets — the data contract the rest of the system depends on. |
| **Scheduler** | The algorithmic layer. Takes an Owner and reads tasks fresh on every call. Responsible for sorting, filtering, conflict detection, and recurring task automation. |

### Class Relationships

```
Owner "1" --> "0..*" Pet : has
Pet   "1" --> "0..*" Task : has
Owner "1" --> "1"    Scheduler : uses
```

---

## Smarter Scheduling

The `Scheduler` class implements five algorithmic features:

1. **Sort by time** — `sort_tasks()` returns all tasks across all pets in chronological order (by due date, then due time). Tasks added in any order are always displayed correctly.

2. **Sort by priority** — `sort_by_priority()` returns tasks ordered high → medium → low, using a rank map `{"high": 0, "medium": 1, "low": 2}`. Time is used as a tiebreaker within the same priority level. Both sort modes are user-selectable in the UI via a **Sort ▾** popover.

3. **Filter tasks** — `filter_tasks(completed, pet_name)` narrows the task list by completion status, pet name, or both. Useful for showing only today's pending tasks or a single pet's schedule. Accessible in the UI via a **Filter ▾** popover alongside a live summary (`Showing X of Y tasks`).

4. **Conflict detection** — `detect_conflicts()` scans for any two tasks assigned to the same pet at the same date and time, returning human-readable warnings rather than crashing. Fires immediately when a task is added and again on "Generate Schedule".

5. **Recurring task automation** — `handle_recurring(pet, task)` marks a task complete and automatically creates the next occurrence: +1 day for `"daily"` tasks, +7 days for `"weekly"` tasks. All fields (priority, duration, frequency) are copied to the next occurrence via `dataclasses.replace()`. One-time tasks are only marked complete.

---

## Running the Demo

The CLI demo in `main.py` creates one Owner (Jordan), two Pets (Mochi the dog and Luna the cat), and six tasks. It exercises all five Scheduler features and prints richly formatted output using the `rich` library (tables, panels, color-coded priority).

```bash
python main.py
```

Expected output includes: a schedule sorted by time, a schedule sorted by priority, a conflict warning for Luna's 08:00 overlap, a filtered pending task list, a Mochi-only filtered view, a recurring task being completed and rescheduled (with all fields preserved), a task edit, and a pet being added then removed.

---

## Running the Tests

```bash
python -m pytest
```

The test suite in `tests/test_pawpal.py` covers:

| Test | What it verifies |
|---|---|
| `test_task_mark_complete` | `mark_complete()` flips `completed` from False to True |
| `test_add_task_increases_count` | `add_task()` grows the pet's task list by exactly 1 |
| `test_sort_tasks_chronological` | `sort_tasks()` returns tasks in ascending time order across multiple pets |
| `test_filter_tasks_by_completed_status` | `filter_tasks(completed=True)` returns only finished tasks |
| `test_detect_conflicts_same_pet_same_time` | `detect_conflicts()` flags same-pet same-time collisions |
| `test_handle_recurring_daily` | Completing a daily task creates a new task dated tomorrow |

**Confidence level: ★★★★☆** — all happy paths and the most important edge cases are covered. Gaps: no test for `edit_task` validation, weekly recurrence, or an owner with zero pets.

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## Project Structure

```
pawpal_system.py      # Core logic: Task, Pet, Owner, Scheduler
main.py               # CLI demo script (rich-formatted output)
app.py                # Streamlit UI — sort, filter, complete, and edit tasks
tests/
  test_pawpal.py      # Pytest suite
Mermaid.js            # UML class diagram source (paste into mermaid.live)
reflection.md         # Design decisions and AI collaboration notes
```
