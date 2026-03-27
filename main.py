"""
main.py
CLI demo for PawPal+ — prints Today's Schedule and exercises all Scheduler features.
Run with: python main.py
"""

from datetime import date

import sys
sys.stdout.reconfigure(encoding="utf-8")

from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel
from rich.text import Text

from pawpal_system import Task, Pet, Owner, Scheduler

console = Console()

PRIORITY_COLOR = {"high": "red", "medium": "yellow", "low": "green"}


def task_table(pairs, title: str, show_date: bool = False) -> Table:
    """Build a rich Table from a list of (Pet, Task) pairs."""
    table = Table(title=title, box=box.ROUNDED, show_lines=True, title_style="bold cyan")
    table.add_column("Status", justify="center", style="dim", width=6)
    table.add_column("Pet",    style="bold magenta")
    if show_date:
        table.add_column("Date", style="cyan", min_width=10, no_wrap=True)
    table.add_column("Time",     style="cyan")
    table.add_column("Task",     style="white")
    table.add_column("Priority", justify="center")
    table.add_column("Repeat",   style="dim")
    table.add_column("Duration", justify="right", style="dim")

    for pet, task in pairs:
        status = "[green]DONE[/]" if task.completed else "[yellow]TODO[/]"
        pri_color = PRIORITY_COLOR.get(task.priority, "white")
        priority_cell = f"[{pri_color}]{task.priority}[/]"
        row = [status, pet.name]
        if show_date:
            row.append(str(task.due_date))
        row += [task.due_time, task.description, priority_cell, task.frequency, f"{task.duration_minutes} min"]
        table.add_row(*row)
    return table


def main() -> None:
    # ── Build the object graph ──────────────────────────────────────────────
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
    mochi.add_task(Task("Evening walk",   due_time="17:30", due_date=today, frequency="daily",  priority="high",   duration_minutes=30))
    mochi.add_task(Task("Morning walk",   due_time="07:00", due_date=today, frequency="daily",  priority="high",   duration_minutes=30))
    mochi.add_task(Task("Heartworm pill", due_time="08:00", due_date=today, frequency="weekly", priority="high",   duration_minutes=5))

    # Tasks for Luna (cat) — intentional conflict at 08:00 to demo detect_conflicts
    luna.add_task(Task("Breakfast feeding", due_time="08:00", due_date=today, frequency="daily",  priority="high",   duration_minutes=10))
    luna.add_task(Task("Medication",        due_time="08:00", due_date=today, frequency="once",   priority="high",   duration_minutes=5))
    luna.add_task(Task("Playtime",          due_time="19:00", due_date=today, frequency="once",   priority="medium", duration_minutes=20))

    scheduler = Scheduler(owner)

    console.rule("[bold cyan]PawPal+ Demo[/]")
    console.print()

    # ── Today's Schedule (sorted by time) ──────────────────────────────────
    console.print(task_table(scheduler.sort_tasks(), "Today's Schedule — sorted by time"))
    console.print()

    # ── Sort by priority ────────────────────────────────────────────────────
    console.print(task_table(scheduler.sort_by_priority(), "Today's Schedule — sorted by priority"))
    console.print()

    # ── Conflict detection ──────────────────────────────────────────────────
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        conflict_text = "\n".join(f"  [!]  {w}" for w in conflicts)
        console.print(Panel(conflict_text, title="[bold red]Conflict Warnings[/]", border_style="red"))
    else:
        console.print(Panel("[green]No conflicts found.[/]", title="Conflict Check", border_style="green"))
    console.print()

    # ── Filter: pending tasks only ──────────────────────────────────────────
    pending = scheduler.filter_tasks(completed=False)
    console.print(task_table(pending, "Pending Tasks — all pets"))
    console.print()

    # ── Filter: Mochi's tasks only ──────────────────────────────────────────
    console.print(task_table(scheduler.filter_tasks(pet_name="Mochi"), "Mochi's Tasks Only"))
    console.print()

    # ── Recurring task demo ─────────────────────────────────────────────────
    morning_walk = mochi.list_tasks()[1]  # "Morning walk" at 07:00
    before = Text(f"Before  completed={morning_walk.completed}", style="dim")
    scheduler.handle_recurring(mochi, morning_walk)
    next_walk = mochi.list_tasks()[-1]
    after = Text(f"After   completed={morning_walk.completed}", style="green")
    next_line = Text(f"Next    due_date={next_walk.due_date}  completed={next_walk.completed}", style="cyan")
    console.print(Panel(
        Text.assemble(before, "\n", after, "\n", next_line),
        title="[bold]Recurring Task — Mochi's Morning Walk[/]",
        border_style="cyan",
    ))
    console.print()

    # ── Edit task demo ──────────────────────────────────────────────────────
    playtime = luna.list_tasks()[2]
    before_time = playtime.due_time
    luna.edit_task(2, due_time="20:00")
    console.print(Panel(
        f"Before  due_time=[yellow]{before_time}[/]\nAfter   due_time=[green]{playtime.due_time}[/]",
        title="[bold]Edit Task — Luna's Playtime[/]",
        border_style="yellow",
    ))
    console.print()

    # ── Remove pet demo ─────────────────────────────────────────────────────
    temp = Pet(name="Biscuit", species="rabbit")
    owner.add_pet(temp)
    before_names = [p.name for p in owner.list_pets()]
    owner.remove_pet("Biscuit")
    after_names = [p.name for p in owner.list_pets()]
    console.print(Panel(
        f"Before  {before_names}\nAfter   {after_names}",
        title="[bold]Remove Pet — Biscuit[/]",
        border_style="magenta",
    ))
    console.print()

    # ── Find next available slot demo ───────────────────────────────────────
    slot = scheduler.find_next_available_slot(
        pet_name="Mochi",
        duration_minutes=45,
        search_date=today,
        day_start="08:00",
        day_end="20:00",
        max_days_ahead=7,
    )
    if slot:
        slot_date, slot_time = slot
        slot_content = Text.assemble(
            Text("Pet:      Mochi\n",         style="dim"),
            Text("Duration: 45 minutes\n",    style="dim"),
            Text("Window:   08:00 – 20:00\n", style="dim"),
            Text(f"Result:   {slot_date}  {slot_time}", style="bold green"),
        )
    else:
        slot_content = Text("No available slot found within 7 days.", style="red")
    console.print(Panel(slot_content, title="[bold]Find Next Available Slot — Mochi[/]", border_style="cyan"))
    console.print()

    # ── Final schedule ──────────────────────────────────────────────────────
    console.print(task_table(scheduler.sort_tasks(), "Final Schedule (after edits & recurring update)", show_date=True))
    console.rule()


if __name__ == "__main__":
    main()
