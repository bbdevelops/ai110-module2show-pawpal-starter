import streamlit as st
from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

st.markdown("### Tasks")
st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")

if "owner" not in st.session_state:
    st.session_state["owner"] = Owner(name=owner_name)
owner = st.session_state["owner"]

col1, col2, col3, col4 = st.columns(4)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
with col4:
    due_time = st.time_input("Due time")

if st.button("Add task"):
    existing = [p for p in owner.list_pets() if p.name == pet_name]
    pet = existing[0] if existing else Pet(name=pet_name, species=species)
    if not existing:
        owner.add_pet(pet)
    task = Task(
        description=task_title,
        due_time=due_time.strftime("%H:%M"),
        due_date=date.today(),
        priority=priority,
        duration_minutes=int(duration),
    )
    pet.add_task(task)

all_tasks = owner.get_all_tasks()
if all_tasks:
    st.write("Current tasks:")
    st.table([
        {"Pet": p.name, "Task": t.description, "Time": t.due_time,
         "Priority": t.priority, "Duration (min)": t.duration_minutes, "Done": t.completed}
        for p, t in all_tasks
    ])
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("This button should call your scheduling logic once you implement it.")

if st.button("Generate schedule"):
    scheduler = Scheduler(owner)
    conflicts = scheduler.detect_conflicts()
    sorted_tasks = scheduler.sort_tasks()

    if conflicts:
        for warning in conflicts:
            st.warning(warning)
    else:
        st.success("No scheduling conflicts detected!")

    if sorted_tasks:
        st.subheader("Today's Schedule")
        st.table([
            {"Pet": p.name, "Task": t.description, "Date": str(t.due_date),
             "Time": t.due_time, "Priority": t.priority, "Done": "✓" if t.completed else "○"}
            for p, t in sorted_tasks
        ])
    else:
        st.info("No tasks scheduled yet.")
