"""
main.py
CLI demo for PawPal+ — prints Today's Schedule and exercises all Scheduler features.
Run with: python main.py
"""

from datetime import date
from pawpal_system import Task, Pet, Owner, Scheduler


def header(title: str) -> None:
    print(f"\n{'=' * 52}")
    print(f"  {title}")
    print(f"{'=' * 52}")


def main() -> None:
    # ── Build the object graph ────────────────────────────────────────────────
    owner = Owner(name="Jordan")

    mochi = Pet(
        name="Mochi",
        species="dog",
        dietary_restrictions="grain-free",
        health_conditions="hip dysplasia",
    )
    luna = Pet(
        name="Luna",
        species="cat",
        allergies="chicken",
    )

    owner.add_pet(mochi)
    owner.add_pet(luna)

    today = date.today()

    # Tasks for Mochi (dog) — added out of order to show sorting
    mochi.add_task(Task("Evening walk",   due_time="17:30", due_date=today, frequency="daily"))
    mochi.add_task(Task("Morning walk",   due_time="07:00", due_date=today, frequency="daily"))
    mochi.add_task(Task("Heartworm pill", due_time="08:00", due_date=today, frequency="weekly"))

    # Tasks for Luna (cat) — intentional conflict at 08:00 to demo detect_conflicts
    luna.add_task(Task("Breakfast feeding", due_time="08:00", due_date=today, frequency="daily"))
    luna.add_task(Task("Medication",        due_time="08:00", due_date=today, frequency="once"))
    luna.add_task(Task("Playtime",          due_time="19:00", due_date=today, frequency="once"))

    scheduler = Scheduler(owner)

    # ── Today's Schedule (sorted chronologically) ─────────────────────────────
    header("Today's Schedule — All Pets (sorted by time)")
    for pet, task in scheduler.sort_tasks():
        status = "DONE" if task.completed else "TODO"
        print(f"  [{status}]  {task.due_time}  {pet.name:<6}  {task.description}")

    # ── Conflict detection ────────────────────────────────────────────────────
    header("Conflict Warnings")
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for warning in conflicts:
            print(f"  ! {warning}")
    else:
        print("  No conflicts found.")

    # ── Filter: pending tasks only ────────────────────────────────────────────
    header("Pending Tasks — All Pets")
    for pet, task in scheduler.filter_tasks(completed=False):
        print(f"  {pet.name:<6}  {task.due_time}  {task.description}")

    # ── Filter: Mochi's tasks only ────────────────────────────────────────────
    header("Mochi's Tasks Only")
    for pet, task in scheduler.filter_tasks(pet_name="Mochi"):
        status = "DONE" if task.completed else "TODO"
        print(f"  [{status}]  {task.due_time}  {task.description}")

    # ── Recurring task demo ───────────────────────────────────────────────────
    header("Recurring Task — Mark Mochi's Morning Walk Complete")
    morning_walk = mochi.list_tasks()[1]  # "Morning walk" at 07:00
    print(f"  Before: '{morning_walk.description}' | completed={morning_walk.completed}")
    scheduler.handle_recurring(mochi, morning_walk)
    print(f"  After:  '{morning_walk.description}' | completed={morning_walk.completed}")
    next_walk = mochi.list_tasks()[-1]
    print(f"  Next:   '{next_walk.description}' | due_date={next_walk.due_date} | completed={next_walk.completed}")

    # ── Edit task demo ────────────────────────────────────────────────────────
    header("Edit Task — Change Luna's Playtime to 20:00")
    playtime = luna.list_tasks()[2]
    print(f"  Before: due_time={playtime.due_time}")
    luna.edit_task(2, due_time="20:00")
    print(f"  After:  due_time={playtime.due_time}")

    # ── Remove pet demo ───────────────────────────────────────────────────────
    header("Remove Pet — Add then Remove a Temporary Pet")
    temp = Pet(name="Biscuit", species="rabbit")
    owner.add_pet(temp)
    print(f"  Pets before removal: {[p.name for p in owner.list_pets()]}")
    owner.remove_pet("Biscuit")
    print(f"  Pets after removal:  {[p.name for p in owner.list_pets()]}")

    # ── Final schedule ────────────────────────────────────────────────────────
    header("Final Schedule (after edits & recurring update)")
    for pet, task in scheduler.sort_tasks():
        status = "DONE" if task.completed else "TODO"
        print(f"  [{status}]  {task.due_date}  {task.due_time}  {pet.name:<6}  {task.description}")


if __name__ == "__main__":
    main()
