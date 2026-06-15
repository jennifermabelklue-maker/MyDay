import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import date, datetime

APP_PIN = "1234"

st.set_page_config(page_title="MyDay", page_icon="🌤️", layout="wide")


# ============================================================
# DATABASE
# ============================================================

def db():
    return sqlite3.connect("myday.db", check_same_thread=False)


def init_db():
    conn = db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT,
            due_date TEXT,
            priority TEXT,
            done INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            body TEXT,
            created_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit TEXT NOT NULL,
            tracked_date TEXT,
            completed INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS hobbies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            goal TEXT,
            created_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS hobby_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hobby_id INTEGER,
            session_date TEXT,
            minutes INTEGER,
            note TEXT,
            created_at TEXT,
            FOREIGN KEY (hobby_id) REFERENCES hobbies(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS mood (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mood TEXT,
            energy INTEGER,
            stress INTEGER,
            note TEXT,
            tracked_date TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS budget (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT,
            amount REAL,
            type TEXT,
            category TEXT,
            entry_date TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            target TEXT,
            progress INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def query(sql, params=(), fetch=False):
    conn = db()
    c = conn.cursor()
    c.execute(sql, params)
    data = c.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return data


def table(name):
    conn = db()
    df = pd.read_sql_query(f"SELECT * FROM {name}", conn)
    conn.close()
    return df


def today():
    return date.today().isoformat()


init_db()


# ============================================================
# STYLE
# ============================================================

st.markdown("""
<style>
    .main {
        background: #f6f7fb;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    h1, h2, h3 {
        color: #111827;
    }

    [data-testid="stMetric"] {
        background: white;
        border: 1px solid #e5e7eb;
        padding: 16px;
        border-radius: 8px;
    }

    .stButton button {
        border-radius: 8px;
        border: none;
        background: #2563eb;
        color: white;
        font-weight: 600;
    }

    .stButton button:hover {
        background: #1d4ed8;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# LOGIN
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("MyDay")
    st.caption("Your private daily dashboard.")

    pin = st.text_input("Enter PIN", type="password")

    if st.button("Unlock"):
        if pin == APP_PIN:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Wrong PIN.")

    st.info("Default PIN is 1234. Change APP_PIN near the top of the code.")
    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("MyDay")
st.sidebar.caption("Plan. Track. Improve.")

page = st.sidebar.radio(
    "Menu",
    ["Dashboard", "Tasks", "Notes", "Habits", "Hobbies", "Mood", "Budget", "Goals"]
)

if st.sidebar.button("Lock App"):
    st.session_state.logged_in = False
    st.rerun()


# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":
    st.title("MyDay Dashboard")
    st.caption(date.today().strftime("%A, %d %B %Y"))

    tasks = table("tasks")
    notes = table("notes")
    habits = table("habits")
    hobbies = table("hobbies")
    hobby_sessions = table("hobby_sessions")
    mood = table("mood")
    budget = table("budget")

    open_tasks = len(tasks[tasks["done"] == 0]) if not tasks.empty else 0
    done_tasks = len(tasks[tasks["done"] == 1]) if not tasks.empty else 0
    completed_habits = len(habits[(habits["tracked_date"] == today()) & (habits["completed"] == 1)]) if not habits.empty else 0
    hobby_minutes = hobby_sessions["minutes"].sum() if not hobby_sessions.empty else 0

    income = budget[budget["type"] == "Income"]["amount"].sum() if not budget.empty else 0
    expenses = budget[budget["type"] == "Expense"]["amount"].sum() if not budget.empty else 0
    balance = income - expenses

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Open Tasks", open_tasks)
    c2.metric("Habits Today", completed_habits)
    c3.metric("Hobbies", len(hobbies))
    c4.metric("Balance", f"R {balance:,.2f}")

    st.divider()

    left, right = st.columns([2, 1])

    with left:
        st.subheader("Due Today")

        if tasks.empty:
            st.info("No tasks yet.")
        else:
            due_today = tasks[(tasks["due_date"] == today()) & (tasks["done"] == 0)]

            if due_today.empty:
                st.success("Nothing due today.")
            else:
                st.dataframe(
                    due_today[["title", "category", "priority", "due_date"]],
                    use_container_width=True,
                    hide_index=True
                )

    with right:
        st.subheader("Quick Add Task")

        with st.form("quick_task"):
            title = st.text_input("Task")

            if st.form_submit_button("Add"):
                if title.strip():
                    query(
                        """
                        INSERT INTO tasks (title, category, due_date, priority, done, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (title, "Personal", today(), "Medium", 0, datetime.now().isoformat(timespec="seconds"))
                    )
                    st.rerun()

    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Mood Trend")

        if mood.empty:
            st.info("No mood data yet.")
        else:
            fig = px.line(mood, x="tracked_date", y=["energy", "stress"], markers=True)
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("Hobby Time")

        if hobby_sessions.empty or hobbies.empty:
            st.info("No hobby sessions yet.")
        else:
            hobby_stats = hobby_sessions.merge(
                hobbies[["id", "name"]],
                left_on="hobby_id",
                right_on="id",
                how="left"
            )
            hobby_stats = hobby_stats.groupby("name")["minutes"].sum().reset_index()
            hobby_stats["hours"] = hobby_stats["minutes"] / 60

            fig = px.bar(hobby_stats, x="name", y="hours", title="Hours Per Hobby")
            st.plotly_chart(fig, use_container_width=True)

    st.caption(f"Total hobby time tracked: {hobby_minutes / 60:.1f} hours")


# ============================================================
# TASKS
# ============================================================

elif page == "Tasks":
    st.title("Tasks")

    with st.form("add_task"):
        title = st.text_input("Task name")
        category = st.selectbox("Category", ["Personal", "School", "Work", "Business", "Health", "Other"])
        due_date = st.date_input("Due date")
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])

        if st.form_submit_button("Add Task"):
            if title.strip():
                query(
                    """
                    INSERT INTO tasks (title, category, due_date, priority, done, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (title, category, due_date.isoformat(), priority, 0, datetime.now().isoformat(timespec="seconds"))
                )
                st.rerun()
            else:
                st.warning("Add a task name.")

    tasks = table("tasks")

    if tasks.empty:
        st.info("No tasks yet.")
    else:
        status_filter = st.selectbox("Status", ["All", "Open", "Done"])

        filtered = tasks.copy()

        if status_filter == "Open":
            filtered = filtered[filtered["done"] == 0]
        elif status_filter == "Done":
            filtered = filtered[filtered["done"] == 1]

        for _, task in filtered.sort_values("id", ascending=False).iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([5, 1, 1])

                with c1:
                    status = "Done" if task["done"] else "Open"
                    st.write(f"**{task['title']}**")
                    st.caption(f"{task['category']} | {task['priority']} | Due {task['due_date']} | {status}")

                with c2:
                    if task["done"] == 0:
                        if st.button("Done", key=f"done_{task['id']}"):
                            query("UPDATE tasks SET done = 1 WHERE id = ?", (task["id"],))
                            st.rerun()
                    else:
                        if st.button("Undo", key=f"undo_{task['id']}"):
                            query("UPDATE tasks SET done = 0 WHERE id = ?", (task["id"],))
                            st.rerun()

                with c3:
                    if st.button("Delete", key=f"delete_task_{task['id']}"):
                        query("DELETE FROM tasks WHERE id = ?", (task["id"],))
                        st.rerun()


# ============================================================
# NOTES
# ============================================================

elif page == "Notes":
    st.title("Notes")

    with st.form("add_note"):
        title = st.text_input("Title")
        body = st.text_area("Note", height=180)

        if st.form_submit_button("Save Note"):
            if title.strip():
                query(
                    "INSERT INTO notes (title, body, created_at) VALUES (?, ?, ?)",
                    (title, body, datetime.now().isoformat(timespec="seconds"))
                )
                st.rerun()
            else:
                st.warning("Title is required.")

    notes = table("notes")
    search = st.text_input("Search notes")

    if not notes.empty and search:
        notes = notes[
            notes["title"].str.contains(search, case=False, na=False) |
            notes["body"].str.contains(search, case=False, na=False)
        ]

    if notes.empty:
        st.info("No notes found.")
    else:
        for _, note in notes.sort_values("id", ascending=False).iterrows():
            with st.expander(note["title"]):
                st.write(note["body"])
                st.caption(note["created_at"])

                if st.button("Delete Note", key=f"delete_note_{note['id']}"):
                    query("DELETE FROM notes WHERE id = ?", (note["id"],))
                    st.rerun()


# ============================================================
# HABITS
# ============================================================

elif page == "Habits":
    st.title("Habits")

    with st.form("track_habit"):
        habit = st.text_input("Habit")
        completed = st.checkbox("Completed today")

        if st.form_submit_button("Track"):
            if habit.strip():
                query(
                    "INSERT INTO habits (habit, tracked_date, completed) VALUES (?, ?, ?)",
                    (habit, today(), 1 if completed else 0)
                )
                st.rerun()
            else:
                st.warning("Habit name is required.")

    habits = table("habits")

    if habits.empty:
        st.info("No habits yet.")
    else:
        summary = habits.groupby("habit")["completed"].sum().reset_index()
        fig = px.bar(summary, x="habit", y="completed", title="Habit Wins")
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(habits.sort_values("id", ascending=False), use_container_width=True, hide_index=True)


# ============================================================
# HOBBIES
# ============================================================

elif page == "Hobbies":
    st.title("Hobby Tracker")
    st.caption("Add hobbies, remove hobbies, and track how much time you spend on them.")

    tab1, tab2, tab3 = st.tabs(["My Hobbies", "Track Time", "Stats"])

    with tab1:
        st.subheader("Add New Hobby")

        with st.form("add_hobby"):
            name = st.text_input("Hobby name", placeholder="Example: Drawing, Guitar, Gym, Coding")
            category = st.selectbox(
                "Category",
                ["Creative", "Fitness", "Learning", "Music", "Gaming", "Outdoor", "Social", "Other"]
            )
            goal = st.text_input("Goal", placeholder="Example: Practice 3 times a week")

            if st.form_submit_button("Add Hobby"):
                if name.strip():
                    query(
                        """
                        INSERT INTO hobbies (name, category, goal, created_at)
                        VALUES (?, ?, ?, ?)
                        """,
                        (name.strip(), category, goal.strip(), datetime.now().isoformat(timespec="seconds"))
                    )
                    st.rerun()
                else:
                    st.warning("Add a hobby name first.")

        st.divider()
        st.subheader("Your Hobbies")

        hobbies = table("hobbies")

        if hobbies.empty:
            st.info("No hobbies yet.")
        else:
            for _, hobby in hobbies.sort_values("id", ascending=False).iterrows():
                with st.container(border=True):
                    col1, col2 = st.columns([4, 1])

                    with col1:
                        st.write(f"**{hobby['name']}**")
                        st.caption(f"{hobby['category']} | Goal: {hobby['goal'] or 'No goal yet'}")

                    with col2:
                        if st.button("Remove", key=f"remove_hobby_{hobby['id']}"):
                            query("DELETE FROM hobby_sessions WHERE hobby_id = ?", (hobby["id"],))
                            query("DELETE FROM hobbies WHERE id = ?", (hobby["id"],))
                            st.rerun()

    with tab2:
        st.subheader("Track Hobby Time")

        hobbies = table("hobbies")

        if hobbies.empty:
            st.info("Add a hobby first before tracking time.")
        else:
            hobby_options = {
                f"{row['name']} ({row['category']})": row["id"]
                for _, row in hobbies.sort_values("name").iterrows()
            }

            with st.form("track_hobby_session"):
                selected_hobby = st.selectbox("Choose hobby", list(hobby_options.keys()))
                session_date = st.date_input("Date", value=date.today())
                minutes = st.number_input("Minutes spent", min_value=1, max_value=1440, value=30, step=5)
                note = st.text_area("Note", placeholder="What did you do or improve?")

                if st.form_submit_button("Save Session"):
                    query(
                        """
                        INSERT INTO hobby_sessions (
                            hobby_id, session_date, minutes, note, created_at
                        )
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            hobby_options[selected_hobby],
                            session_date.isoformat(),
                            int(minutes),
                            note.strip(),
                            datetime.now().isoformat(timespec="seconds")
                        )
                    )
                    st.rerun()

            sessions = table("hobby_sessions")

            if sessions.empty:
                st.info("No hobby sessions tracked yet.")
            else:
                session_view = sessions.merge(
                    hobbies[["id", "name", "category"]],
                    left_on="hobby_id",
                    right_on="id",
                    how="left"
                )

                session_view = session_view[
                    ["session_date", "name", "category", "minutes", "note"]
                ].sort_values("session_date", ascending=False)

                st.dataframe(session_view, use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("Hobby Stats")

        hobbies = table("hobbies")
        sessions = table("hobby_sessions")

        if hobbies.empty or sessions.empty:
            st.info("Track some hobby time first to see stats.")
        else:
            stats = sessions.merge(
                hobbies[["id", "name", "category"]],
                left_on="hobby_id",
                right_on="id",
                how="left"
            )

            total_minutes = int(stats["minutes"].sum())
            total_hours = total_minutes / 60
            total_sessions = len(stats)
            top_hobby = stats.groupby("name")["minutes"].sum().sort_values(ascending=False).index[0]

            c1, c2, c3 = st.columns(3)
            c1.metric("Total Hours", f"{total_hours:.1f}")
            c2.metric("Sessions", total_sessions)
            c3.metric("Top Hobby", top_hobby)

            by_hobby = stats.groupby("name")["minutes"].sum().reset_index()
            by_hobby["hours"] = by_hobby["minutes"] / 60

            fig = px.bar(
                by_hobby,
                x="name",
                y="hours",
                title="Hours Per Hobby",
                labels={"name": "Hobby", "hours": "Hours"}
            )
            st.plotly_chart(fig, use_container_width=True)

            stats["session_date"] = pd.to_datetime(stats["session_date"], errors="coerce")

            timeline = stats.groupby(["session_date", "name"])["minutes"].sum().reset_index()
            timeline["hours"] = timeline["minutes"] / 60

            fig2 = px.line(
                timeline,
                x="session_date",
                y="hours",
                color="name",
                markers=True,
                title="Hobby Time Over Time",
                labels={"session_date": "Date", "hours": "Hours"}
            )
            st.plotly_chart(fig2, use_container_width=True)


# ============================================================
# MOOD
# ============================================================

elif page == "Mood":
    st.title("Mood Tracker")

    with st.form("add_mood"):
        mood = st.selectbox("Mood", ["Amazing", "Good", "Okay", "Tired", "Stressed", "Sad"])
        energy = st.slider("Energy", 1, 10, 5)
        stress = st.slider("Stress", 1, 10, 5)
        note = st.text_area("Note")

        if st.form_submit_button("Save Mood"):
            query(
                "INSERT INTO mood (mood, energy, stress, note, tracked_date) VALUES (?, ?, ?, ?, ?)",
                (mood, energy, stress, note, today())
            )
            st.rerun()

    moods = table("mood")

    if moods.empty:
        st.info("No mood entries yet.")
    else:
        fig = px.line(moods, x="tracked_date", y=["energy", "stress"], markers=True)
        st.plotly_chart(fig, use_container_width=True)

        mood_counts = moods["mood"].value_counts().reset_index()
        mood_counts.columns = ["mood", "count"]

        fig2 = px.bar(mood_counts, x="mood", y="count", title="Mood Count")
        st.plotly_chart(fig2, use_container_width=True)

        st.dataframe(moods.sort_values("id", ascending=False), use_container_width=True, hide_index=True)


# ============================================================
# BUDGET
# ============================================================

elif page == "Budget":
    st.title("Budget Tracker")

    with st.form("add_budget"):
        item = st.text_input("Item")
        amount = st.number_input("Amount", min_value=0.0, step=10.0)
        kind = st.selectbox("Type", ["Income", "Expense"])
        category = st.selectbox("Category", ["Food", "Transport", "Shopping", "School", "Business", "Bills", "Savings", "Other"])
        entry_date = st.date_input("Date")

        if st.form_submit_button("Add Entry"):
            if item.strip() and amount > 0:
                query(
                    "INSERT INTO budget (item, amount, type, category, entry_date) VALUES (?, ?, ?, ?, ?)",
                    (item, amount, kind, category, entry_date.isoformat())
                )
                st.rerun()
            else:
                st.warning("Item and amount are required.")

    budget = table("budget")

    if budget.empty:
        st.info("No budget entries yet.")
    else:
        income = budget[budget["type"] == "Income"]["amount"].sum()
        expense = budget[budget["type"] == "Expense"]["amount"].sum()
        balance = income - expense

        c1, c2, c3 = st.columns(3)
        c1.metric("Income", f"R {income:,.2f}")
        c2.metric("Expenses", f"R {expense:,.2f}")
        c3.metric("Balance", f"R {balance:,.2f}")

        expenses = budget[budget["type"] == "Expense"]

        if not expenses.empty:
            fig = px.pie(expenses, names="category", values="amount", title="Expenses by Category")
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(budget.sort_values("id", ascending=False), use_container_width=True, hide_index=True)


# ============================================================
# GOALS
# ============================================================

elif page == "Goals":
    st.title("Goals")

    with st.form("add_goal"):
        title = st.text_input("Goal")
        target = st.text_input("Target")
        progress = st.slider("Progress", 0, 100, 0)

        if st.form_submit_button("Add Goal"):
            if title.strip():
                query(
                    "INSERT INTO goals (title, target, progress, created_at) VALUES (?, ?, ?, ?)",
                    (title, target, progress, datetime.now().isoformat(timespec="seconds"))
                )
                st.rerun()
            else:
                st.warning("Goal title is required.")

    goals = table("goals")

    if goals.empty:
        st.info("No goals yet.")
    else:
        for _, goal in goals.sort_values("id", ascending=False).iterrows():
            with st.container(border=True):
                st.write(f"**{goal['title']}**")
                st.caption(goal["target"])
                st.progress(int(goal["progress"]))

                new_progress = st.slider(
                    "Update progress",
                    0,
                    100,
                    int(goal["progress"]),
                    key=f"progress_{goal['id']}"
                )

                c1, c2 = st.columns(2)

                with c1:
                    if st.button("Save Progress", key=f"save_goal_{goal['id']}"):
                        query("UPDATE goals SET progress = ? WHERE id = ?", (new_progress, goal["id"]))
                        st.rerun()

                with c2:
                    if st.button("Delete Goal", key=f"delete_goal_{goal['id']}"):
                        query("DELETE FROM goals WHERE id = ?", (goal["id"],))
                        st.rerun()