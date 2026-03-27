import streamlit as st
from datetime import date, time, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Smart pet care scheduling — sort, filter, detect conflicts, and automate recurring tasks.")

# ─── Session state: owner persists across reruns ──────────────────────────
if "owner" not in st.session_state:
    st.session_state["owner"] = Owner(name="Jordan")
owner: Owner = st.session_state["owner"]
scheduler = Scheduler(owner)

# ─── Pets ─────────────────────────────────────────────────────────────────
st.subheader("Pets")
col_pname, col_species, col_btn = st.columns([2, 2, 1])
with col_pname:
    new_pet_name = st.text_input("Pet name", key="new_pet_name")
with col_species:
    new_species = st.selectbox("Species", ["cat", "dog",  "other"], key="new_species")
with col_btn:
    st.write("")  # spacer so button aligns with inputs
    add_pet_btn = st.button("Add pet")

if add_pet_btn:
    name = new_pet_name.strip()
    if name:
        if not any(p.name == name for p in owner.list_pets()):
            owner.add_pet(Pet(name=name, species=new_species))
            st.success(f"Added {name} the {new_species}!")
        else:
            st.info(f"{name} is already in the roster.")
    else:
        st.warning("Enter a pet name.")

if owner.list_pets():
    st.markdown("**Roster:** " + " · ".join(f"{p.name} ({p.species})" for p in owner.list_pets()))

st.divider()

# ─── Add a Task ───────────────────────────────────────────────────────────
st.subheader("Add a Task")

pet_names = [p.name for p in owner.list_pets()]
if not pet_names:
    st.info("Add a pet above before scheduling tasks.")
else:
    col1, col2 = st.columns(2)
    with col1:
        task_pet = st.selectbox("Assign to pet", pet_names, key="task_pet")
    with col2:
        task_title = st.text_input("Task title", placeholder="e.g. Morning walk", key="task_title")

    col3, col4, col5, col6, col7 = st.columns(5)
    with col3:
        due_time_input = st.time_input("Due time", key="task_due_time")
    with col4:
        due_date_input = st.date_input("Due date", value=date.today(), key="task_due_date")
    with col5:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=1, key="task_priority")
    with col6:
        frequency = st.selectbox("Repeat", ["once", "daily", "weekly"], key="task_freq")
    with col7:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20, key="task_duration")

    if st.button("Add task"):
        title = task_title.strip()
        if title:
            pet = next(p for p in owner.list_pets() if p.name == task_pet)
            pet.add_task(Task(
                description=title,
                due_time=due_time_input.strftime("%H:%M"),
                due_date=due_date_input,
                priority=priority,
                frequency=frequency,
                duration_minutes=int(duration),
            ))
            st.success(f"Added '{title}' to {task_pet}.")
            # Immediate conflict check after adding
            conflicts = scheduler.detect_conflicts()
            for w in conflicts:
                st.warning(w)
        else:
            st.warning("Enter a task title.")

st.divider()

# ─── Task List with Filters ───────────────────────────────────────────────
st.subheader("Task List")

btn_col1, btn_col2, _ = st.columns([1, 1, 4])

with btn_col1:
    with st.popover("Sort ▾", use_container_width=True):
        sort_by = st.radio("Sort by", ["Time", "Priority"], key="sort_by")

with btn_col2:
    with st.popover("Filter ▾", use_container_width=True):
        pet_filter = st.selectbox("Pet", ["All"] + pet_names, key="filter_pet")
        status_filter = st.radio("Status", ["All", "Pending", "Done"], key="filter_status")

completed_arg = {"Pending": False, "Done": True, "All": None}[status_filter]
pet_arg = None if pet_filter == "All" else pet_filter

if sort_by == "Priority":
    base = scheduler.sort_by_priority()
else:
    base = scheduler.sort_tasks()
filtered = [
    (p, t) for p, t in base
    if (completed_arg is None or t.completed == completed_arg)
    and (pet_arg is None or p.name == pet_arg)
]

# Active state summary
pills = [f"sorted by {sort_by.lower()}"]
if pet_filter != "All":
    pills.append(pet_filter)
if status_filter != "All":
    pills.append(status_filter.lower())
st.caption(f"Showing {len(filtered)} of {len(owner.get_all_tasks())} tasks · {' · '.join(pills)}")

if filtered:
    for pet, task in filtered:
        freq_tag = f" `{task.frequency}`" if task.frequency != "once" else ""
        done_icon = "✅" if task.completed else "🔲"
        st.markdown(
            f"{done_icon} **{task.description}**{freq_tag} — "
            f"🐾 {pet.name} · {task.due_date} {task.due_time} · "
            f"{task.priority} priority · {task.duration_minutes} min"
        )
else:
    st.info("No tasks match the current filter.")

st.divider()

# ─── Task Actions: Complete & Edit ───────────────────────────────────────
st.subheader("Task Actions")

all_pairs = scheduler.sort_tasks()
if not all_pairs:
    st.info("No tasks yet. Add some above.")
else:
    task_labels = [
        f"{t.description} — {p.name} ({t.due_date} {t.due_time})"
        for p, t in all_pairs
    ]
    sel_idx = st.selectbox(
        "Select a task",
        range(len(task_labels)),
        format_func=lambda i: task_labels[i],
        key="selected_task_idx",
    )
    sel_pet, sel_task = all_pairs[sel_idx]

    # ── Mark Complete ─────────────────────────────────────────────────────
    if sel_task.completed:
        st.info("This task is already completed.")
    else:
        if st.button("Mark Complete"):
            freq = sel_task.frequency
            if freq == "daily":
                next_d = sel_task.due_date + timedelta(days=1)
            elif freq == "weekly":
                next_d = sel_task.due_date + timedelta(weeks=1)
            else:
                next_d = None
            scheduler.handle_recurring(sel_pet, sel_task)
            if next_d:
                st.success(f"Done! Next '{sel_task.description}' auto-scheduled for {next_d}.")
            else:
                st.success(f"'{sel_task.description}' marked complete.")
            st.rerun()

    # ── Edit Task ─────────────────────────────────────────────────────────
    with st.expander("Edit this task"):
        t_h, t_m = int(sel_task.due_time.split(":")[0]), int(sel_task.due_time.split(":")[1])
        with st.form("edit_form"):
            new_desc = st.text_input("Description", value=sel_task.description)
            ecol1, ecol2 = st.columns(2)
            with ecol1:
                new_time = st.time_input("Due time", value=time(t_h, t_m))
            with ecol2:
                new_date = st.date_input("Due date", value=sel_task.due_date)
            ecol3, ecol4, ecol5 = st.columns(3)
            with ecol3:
                pri_opts = ["low", "medium", "high"]
                new_pri = st.selectbox("Priority", pri_opts, index=pri_opts.index(sel_task.priority))
            with ecol4:
                freq_opts = ["once", "daily", "weekly"]
                new_freq = st.selectbox("Repeat", freq_opts, index=freq_opts.index(sel_task.frequency))
            with ecol5:
                new_dur = st.number_input(
                    "Duration (min)", min_value=1, max_value=240,
                    value=max(1, sel_task.duration_minutes)
                )
            if st.form_submit_button("Save changes"):
                idx = sel_pet.tasks.index(sel_task)
                sel_pet.edit_task(
                    idx,
                    description=new_desc.strip() or sel_task.description,
                    due_time=new_time.strftime("%H:%M"),
                    due_date=new_date,
                    priority=new_pri,
                    frequency=new_freq,
                    duration_minutes=int(new_dur),
                )
                st.success("Task updated!")
                st.rerun()

st.divider()

# ─── Full Schedule ─────────────────────────────────────────────────────────
st.subheader("Full Schedule")
st.caption("All tasks with conflict detection. Choose sort order below.")

sched_sort = st.radio("Sort schedule by", ["Time", "Priority"], horizontal=True, key="sched_sort")

if st.button("Generate schedule"):
    conflicts = scheduler.detect_conflicts()
    sorted_tasks = scheduler.sort_by_priority() if sched_sort == "Priority" else scheduler.sort_tasks()

    if conflicts:
        for w in conflicts:
            st.warning(w)
    else:
        st.success("No scheduling conflicts detected!")

    if sorted_tasks:
        _pri_label = {"high": "🔴 high", "medium": "🟡 medium", "low": "🟢 low"}
        st.table([
            {
                "Pet": p.name,
                "Task": t.description,
                "Date": str(t.due_date),
                "Time": t.due_time,
                "Priority": _pri_label.get(t.priority, t.priority),
                "Repeat": t.frequency,
                "Done": "✅" if t.completed else "○",
            }
            for p, t in sorted_tasks
        ])
    else:
        st.info("No tasks scheduled yet.")
