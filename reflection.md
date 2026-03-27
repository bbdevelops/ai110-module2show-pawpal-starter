# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

The UML design uses four classes connected in a clear hierarchy: Owner → Pet → Task, with Scheduler as a separate service that the Owner uses to organize tasks.

- **Task** — the smallest unit of work. Holds a description, scheduled time (HH:MM string), due date, completion status, and recurrence frequency ("once", "daily", "weekly"). Its only behavior is `mark_complete()`, keeping it a pure data object with one action.
- **Pet** — represents an individual animal. Stores identifying info (name, species) plus health/care context (dietary restrictions, allergies, health conditions). Owns a list of Tasks and is responsible for adding, editing, and listing them.
- **Owner** — the top-level entity. Manages a collection of Pets and provides `get_all_tasks()`, which flattens all pets' tasks into `(Pet, Task)` pairs so the rest of the system always knows which pet a task belongs to. Also handles adding and removing pets.
- **Scheduler** — the algorithmic layer. Takes an Owner at construction and reads tasks fresh on every call. Responsible for sorting tasks chronologically, filtering by status or pet, detecting time conflicts, and auto-scheduling the next occurrence of recurring tasks.


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes, it changed slightly after I asked Claude to review the skeleton of pawpal_system.py.

- **edit_task() method** Initially, edit_task was able to silently set unknown fields. The solution was to validate kwargs against the actual fields of the Task dataclass before applying them. This catches typos like descrption="Walk" at the call site instead of silently corrupting the object. Without this change there was the possibility of the user accidentally, and silently adding fields that shouldn't exist.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

Time was the obvious foundation — every real care task has a when, and chronological order is the minimum useful output for a daily schedule. Priority came second because not all tasks carry equal urgency; a heartworm pill missed is more consequential than playtime skipped. Recurrence reduced the biggest practical pain point for a daily routine app — having to re-add the same tasks every day.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

Duration overlap was evaluated and intentionally left out. Implementing it would require every task to have a reliable duration, and it would change conflict detection from a simple equality check into an interval-intersection problem. The tradeoff favors simplicity: the owner is responsible for leaving buffer time, and the warning system catches the most obvious error (exact double-booking) without that added complexity.

Also, the conflict detection method detect_conflicts() uses a compact list comprehension that is idiomatic Python but slightly harder to scan. A loop-based version was evaluated and rejected because the added verbosity wasn't justified for a 10-line function.

---

## 3. AI Collaboration

**a. How you used AI**
- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

AI (Claude via Claude Code) was used at every phase, but the role shifted as the project matured:

- **Phase 1 — Design brainstorming:** I described the four-class hierarchy and asked Claude to generate the initial Mermaid.js UML. This was the fastest win — getting a visual diagram in seconds gave me something concrete to critique and correct rather than starting from scratch.
- **Phase 2 — Scaffolding and docstrings:** I used Claude to generate class skeletons and stub out method signatures from the UML, then filled in the logic myself. I also used the "Generate documentation" action to add one-line docstrings after the logic was finalized, not before — writing docs for code that's already working is more accurate.
- **Phase 4 — Algorithm brainstorming:** I opened a fresh chat session scoped to scheduling logic only and asked Claude to suggest a lightweight conflict detection strategy. Keeping this separate from the core implementation chat avoided the AI mixing up context between design and algorithm sessions.
- **Phase 5 — Test generation:** I asked Claude to draft the pytest suite against the finalized `pawpal_system.py`. I reviewed each test before saving it — AI-generated tests are a starting point, not a finished product.

The most effective prompt pattern throughout was "Given this specific file, do X" (using `#file:` references) rather than open-ended questions. Specific context produced specific, usable output.

**b. Judgment and verification**
- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

The clearest example of rejecting an AI suggestion was during `detect_conflicts()`. Claude's first version raised a `ValueError` when a conflict was found — the function crashed the program. I rejected this because the requirement was a warning system, not an exception. A pet owner adding a second 8:00 AM task shouldn't see their app break; they should see a yellow banner. I rewrote the function to collect all conflicts into a list of human-readable strings and return them, leaving the decision of what to do with the warning to the caller (UI or CLI). I verified the behavior by writing `test_detect_conflicts_same_pet_same_time` before touching the UI, confirming the function returned a non-empty list rather than throwing.

---

## 4. Testing and Verification

**a. What you tested**
- What behaviors did you test?
- Why were these tests important?

The pytest suite covers all five Scheduler features plus the core class behaviors:

- **Task completion** — `mark_complete()` flips `completed` from False to True (the simplest possible sanity check).
- **Task addition** — `add_task()` grows the pet's task list by exactly one.
- **Chronological sort** — `sort_tasks()` returns tasks in ascending date/time order even when added out of order.
- **Priority sort** — `sort_by_priority()` returns tasks in high → medium → low order.
- **Filter by status** — `filter_tasks(completed=True)` returns only finished tasks and nothing else.
- **Filter by pet name** — `filter_tasks(pet_name=...)` returns only that pet's tasks.
- **Conflict detection** — `detect_conflicts()` flags same-pet same-time collisions as warning strings.
- **Daily recurrence** — completing a daily task adds a new task dated tomorrow with all fields preserved.
- **Weekly recurrence** — completing a weekly task adds a new task 7 days out.
- **One-time task** — completing a "once" task marks it done without generating a follow-up.
- **Empty owner edge case** — all three Scheduler methods return `[]` safely when the owner has no pets.
- **edit_task validation** — valid updates apply correctly; unknown field names raise `ValueError`.

These tests mattered because the Scheduler has no UI safety net — if `sort_by_priority()` returns tasks in the wrong order, a pet owner gets a misleading schedule with no error message. Tests are the only way to catch logic bugs in a stateless service layer.

**b. Confidence**
- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

**★★★★★** — All 12 tests pass. The suite covers both happy paths and the edge cases most likely to cause silent failures (empty owner, one-time vs recurring, unknown fields). The one area I would add coverage if time allowed is duration-based overlap: two tasks for the same pet at 08:00 and 08:15, where the first task takes 30 minutes. The current conflict check only catches exact time matches, so that overlap goes undetected. A future test would assert that `detect_conflicts()` flags it.

---

## 5. Reflection

**a. What went well**
- What part of this project are you most satisfied with?

The CLI-first workflow was the best structural decision of the project. Building and verifying all logic in `main.py` before touching Streamlit meant I never had to debug business logic inside a UI event loop. Every Streamlit bug I encountered was genuinely a UI wiring problem, not a hidden flaw in the backend — and that distinction made debugging fast. The `(Pet, Task)` tuple as the universal data contract was also the right call: once the Scheduler always returned pairs, every display function knew exactly what it was working with.

**b. What you would improve**
- If you had another iteration, what would you improve or redesign?

Two things stand out for a next iteration:

1. **Duration-aware conflict detection.** The current check flags exact double-bookings but misses overlapping tasks (e.g., a 30-minute walk starting at 07:45 overlaps an 08:00 feeding). Fixing this requires storing reliable duration estimates and switching from an equality check to an interval-intersection algorithm — more complex, but more honest about the real constraint.
2. **Data persistence.** Every app restart wipes the schedule. Saving to JSON via `json.dump` / `json.load` with Python's `dataclasses.asdict()` would make the app genuinely usable for a real pet owner rather than a demo.

**c. Key takeaway**
- What is one important thing you learned about designing systems or working with AI on this project?

The most valuable skill in AI-assisted development is knowing when to say "that's wrong for this design." AI tools produce output fast — faster than I can reason about correctness — which means the temptation is to accept suggestions and move on. The moments that mattered most in this project were the ones where I slowed down: reading the generated code line by line, asking "does this fit my design contract," and rewriting the parts that didn't. AI is a strong first draft, not a finished answer. The lead architect role is real, even when the AI writes most of the code.
