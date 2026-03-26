# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

The UML design used four classes connected in a clear hierarchy: Owner → Pet → Task, with Scheduler as a separate service that the Owner uses to organize tasks.

- **Task** — the smallest unit of work. Holds a description, scheduled time (HH:MM string), due date, completion status, and recurrence frequency ("once", "daily", "weekly"). Its only behavior is `mark_complete()`, keeping it a pure data object with one action.
- **Pet** — represents an individual animal. Stores identifying info (name, species) plus health/care context (dietary restrictions, allergies, health conditions). Owns a list of Tasks and is responsible for adding, editing, and listing them.
- **Owner** — the top-level entity. Manages a collection of Pets and provides `get_all_tasks()`, which flattens all pets' tasks into `(Pet, Task)` pairs so the rest of the system always knows which pet a task belongs to. Also handles adding and removing pets.
- **Scheduler** — the algorithmic layer. Takes an Owner at construction and reads tasks fresh on every call. Responsible for sorting tasks chronologically, filtering by status or pet, detecting time conflicts, and auto-scheduling the next occurrence of recurring tasks.


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
