import sqlite3
from datetime import date, datetime, time as datetime_time

import pandas as pd
import plotly.express as px
import streamlit as st

APP_PIN = "1234"

st.set_page_config(page_title="MyDay", page_icon="MyDay", layout="wide")


def db():
    return sqlite3.connect("myday.db", check_same_thread=False)


def init_db():
    conn = db()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT,
        due_date TEXT,
        priority TEXT,
        done INTEGER DEFAULT 0,
        created_at TEXT,
        reminder_at TEXT
    )""")

    task_columns = [row[1] for row in c.execute("PRAGMA table_info(tasks)").fetchall()]
    if "reminder_at" not in task_columns:
        c.execute("ALTER TABLE tasks ADD COLUMN reminder_at TEXT")

    c.execute("""CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        body TEXT,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS habits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        habit TEXT NOT NULL,
        tracked_date TEXT,
        completed INTEGER DEFAULT 0
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS hobbies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        goal TEXT,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS hobby_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hobby_id INTEGER,
        session_date TEXT,
        minutes INTEGER,
        note TEXT,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS mood (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mood TEXT,
        energy INTEGER,
        stress INTEGER,
        note TEXT,
        tracked_date TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS budget (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item TEXT,
        amount REAL,
        type TEXT,
        category TEXT,
        entry_date TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        target TEXT,
        progress INTEGER DEFAULT 0,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS focus_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        focus_date TEXT,
        priority INTEGER DEFAULT 1,
        done INTEGER DEFAULT 0,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS daily_reflections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reflection_date TEXT UNIQUE,
        win TEXT,
        lesson TEXT,
        tomorrow TEXT,
        created_at TEXT
    )""")

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


def completion(done, total):
    return 0 if total == 0 else round((done / total) * 100)


def today_focus():
    conn = db()
    df = pd.read_sql_query(
        "SELECT * FROM focus_items WHERE focus_date = ? ORDER BY priority ASC, id DESC",
        conn,
        params=(today(),),
    )
    conn.close()
    return df


def latest_reflection():
    conn = db()
    df = pd.read_sql_query(
        "SELECT * FROM daily_reflections ORDER BY reflection_date DESC LIMIT 1",
        conn,
    )
    conn.close()
    return df


def reminder_text(value):
    if not value:
        return "No reminder"
    try:
        return datetime.fromisoformat(value).strftime("%d %b %Y, %H:%M")
    except ValueError:
        return value


def due_reminders(tasks):
    if tasks.empty or "reminder_at" not in tasks.columns:
        return pd.DataFrame()

    open_tasks = tasks[(tasks["done"] == 0) & tasks["reminder_at"].notna() & (tasks["reminder_at"] != "")].copy()
    if open_tasks.empty:
        return pd.DataFrame()

    open_tasks["reminder_dt"] = pd.to_datetime(open_tasks["reminder_at"], errors="coerce")
    now = pd.Timestamp.now()
    return open_tasks[open_tasks["reminder_dt"] <= now].sort_values("reminder_dt")


init_db()

st.markdown("""
<style>
    .main, .stApp { background: #0f1117; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    h1, h2, h3, p, label, span { color: #f9fafb !important; }
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #171923, #111827);
        border: 1px solid #2d3340;
        padding: 16px;
        border-radius: 8px;
        box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);
    }
    [data-testid="stMetricLabel"] { color: #cbd5e1 !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; }
    div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #2d3340 !important;
        background: #121620 !important;
    }
    .stAlert { background: #172a3f !important; color: #60a5fa !important; border-radius: 8px; }
    .stAlert p { color: #60a5fa !important; }
    .stButton button {
        border-radius: 8px;
        border: none;
        background: #2563eb;
        color: white !important;
        font-weight: 600;
    }
    .stButton button:hover { background: #1d4ed8; color: white !important; }
    input, textarea { color: #ffffff !important; background-color: #262833 !important; }
    section[data-testid="stSidebar"] { background-color: #262833; }
</style>
""", unsafe_allow_html=True)

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
        st.error("Wrong PIN.")
    st.info("Default PIN is 1234. Change APP_PIN near the top of the code.")
    st.stop()

st.sidebar.title("MyDay")
st.sidebar.caption("Plan. Track. Improve.")
page = st.sidebar.radio(
    "Menu",
    ["Dashboard", "Focus", "Tasks", "Notes", "Habits", "Hobbies", "Mood", "Budget", "Goals"],
)
if st.sidebar.button("Lock App"):
    st.session_state.logged_in = False
    st.rerun()

if page == "Dashboard":
    st.title("MyDay Dashboard")
    st.caption(date.today().strftime("%A, %d %B %Y"))

    tasks = table("tasks")
    habits = table("habits")
    hobbies = table("hobbies")
    sessions = table("hobby_sessions")
    mood = table("mood")
    budget = table("budget")
    goals = table("goals")
    focus = today_focus()
    reflection = latest_reflection()

    done_tasks = len(tasks[tasks["done"] == 1]) if not tasks.empty else 0
    task_percent = completion(done_tasks, len(tasks))
    open_tasks = len(tasks) - done_tasks
    focus_done = len(focus[focus["done"] == 1]) if not focus.empty else 0
    habit_done = len(habits[(habits["tracked_date"] == today()) & (habits["completed"] == 1)]) if not habits.empty else 0
    income = budget[budget["type"] == "Income"]["amount"].sum() if not budget.empty else 0
    expenses = budget[budget["type"] == "Expense"]["amount"].sum() if not budget.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Open Tasks", open_tasks)
    c2.metric("Task Progress", f"{task_percent}%")
    c3.metric("Focus Today", f"{focus_done}/{len(focus)}")
    c4.metric("Balance", f"R {income - expenses:,.2f}")
    if not tasks.empty:
        st.progress(task_percent / 100)

    st.divider()
    left, right = st.columns([2, 1])
    with left:
        st.subheader("Today Focus")
        if focus.empty:
            st.info("No focus items yet. Add your top priorities on the Focus page.")
        else:
            for _, item in focus.iterrows():
                status = "Done" if item["done"] else "Open"
                st.write(f"**{item['priority']}. {item['title']}** - {status}")
        if not reflection.empty:
            latest = reflection.iloc[0]
            with st.expander("Latest Reflection"):
                st.write(f"**Win:** {latest['win'] or 'Nothing written yet'}")
                st.write(f"**Lesson:** {latest['lesson'] or 'Nothing written yet'}")
                st.write(f"**Tomorrow:** {latest['tomorrow'] or 'Nothing written yet'}")

    with right:
        st.subheader("Quick Add Task")
        with st.form("quick_task"):
            title = st.text_input("Task")
            if st.form_submit_button("Add") and title.strip():
                query(
                    "INSERT INTO tasks (title, category, due_date, priority, done, created_at, reminder_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (title.strip(), "Personal", today(), "Medium", 0, datetime.now().isoformat(timespec="seconds"), None),
                )
                st.rerun()

    st.divider()
    reminders = due_reminders(tasks)
    if not reminders.empty:
        st.subheader("Reminders")
        for _, task in reminders.iterrows():
            st.warning(f"{task['title']} - reminder was set for {reminder_text(task['reminder_at'])}")
        st.divider()

    a, b, c = st.columns(3)
    a.metric("Habits Today", habit_done)
    b.metric("Hobbies", len(hobbies))
    c.metric("Goals", len(goals))

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Due Today")
        if tasks.empty:
            st.info("No tasks yet.")
        else:
            due = tasks[(tasks["due_date"] == today()) & (tasks["done"] == 0)]
            if due.empty:
                st.success("Nothing due today.")
            else:
                st.dataframe(due[["title", "category", "priority", "due_date"]], use_container_width=True, hide_index=True)

    with col2:
        st.subheader("Hobby Time")
        if sessions.empty or hobbies.empty:
            st.info("No hobby sessions yet.")
        else:
            stats = sessions.merge(hobbies[["id", "name"]], left_on="hobby_id", right_on="id", how="left")
            stats = stats.groupby("name")["minutes"].sum().reset_index()
            stats["hours"] = stats["minutes"] / 60
            st.plotly_chart(px.bar(stats, x="name", y="hours", title="Hours Per Hobby"), use_container_width=True)

elif page == "Focus":
    st.title("Focus Mode")
    st.caption("Pick your top priorities, finish them, and reflect at the end of the day.")
    tab1, tab2, tab3 = st.tabs(["Today", "Reflection", "History"])

    with tab1:
        with st.form("add_focus"):
            title = st.text_input("Priority", placeholder="Example: Finish maths homework")
            priority = st.selectbox("Priority number", [1, 2, 3, 4, 5])
            focus_date = st.date_input("Date", value=date.today())
            if st.form_submit_button("Add Priority"):
                if title.strip():
                    query(
                        "INSERT INTO focus_items (title, focus_date, priority, done, created_at) VALUES (?, ?, ?, ?, ?)",
                        (title.strip(), focus_date.isoformat(), int(priority), 0, datetime.now().isoformat(timespec="seconds")),
                    )
                    st.rerun()
                st.warning("Write the priority first.")

        focus = today_focus()
        if focus.empty:
            st.info("No priorities for today yet.")
        else:
            done_count = len(focus[focus["done"] == 1])
            st.metric("Today's Focus Progress", f"{done_count}/{len(focus)}")
            st.progress(done_count / len(focus))
            for _, item in focus.iterrows():
                with st.container(border=True):
                    c1, c2, c3 = st.columns([5, 1, 1])
                    with c1:
                        status = "Done" if item["done"] else "Open"
                        st.write(f"**{item['priority']}. {item['title']}**")
                        st.caption(f"{item['focus_date']} | {status}")
                    with c2:
                        label = "Undo" if item["done"] else "Done"
                        new_done = 0 if item["done"] else 1
                        if st.button(label, key=f"focus_toggle_{item['id']}"):
                            query("UPDATE focus_items SET done = ? WHERE id = ?", (new_done, item["id"]))
                            st.rerun()
                    with c3:
                        if st.button("Delete", key=f"focus_delete_{item['id']}"):
                            query("DELETE FROM focus_items WHERE id = ?", (item["id"],))
                            st.rerun()

    with tab2:
        existing = query("SELECT win, lesson, tomorrow FROM daily_reflections WHERE reflection_date = ?", (today(),), fetch=True)
        current_win = existing[0][0] if existing else ""
        current_lesson = existing[0][1] if existing else ""
        current_tomorrow = existing[0][2] if existing else ""
        with st.form("reflection"):
            win = st.text_area("Biggest win today", value=current_win)
            lesson = st.text_area("What did you learn?", value=current_lesson)
            tomorrow = st.text_area("What should tomorrow-you remember?", value=current_tomorrow)
            if st.form_submit_button("Save Reflection"):
                query(
                    """INSERT OR REPLACE INTO daily_reflections
                    (id, reflection_date, win, lesson, tomorrow, created_at)
                    VALUES ((SELECT id FROM daily_reflections WHERE reflection_date = ?), ?, ?, ?, ?, ?)""",
                    (today(), today(), win.strip(), lesson.strip(), tomorrow.strip(), datetime.now().isoformat(timespec="seconds")),
                )
                st.rerun()

    with tab3:
        focus = table("focus_items")
        reflections = table("daily_reflections")
        if focus.empty:
            st.info("No focus history yet.")
        else:
            summary = focus.groupby("focus_date")["done"].agg(["sum", "count"]).reset_index()
            summary["percent"] = (summary["sum"] / summary["count"] * 100).round(0)
            st.plotly_chart(px.line(summary, x="focus_date", y="percent", markers=True, title="Focus Completion Over Time"), use_container_width=True)
            st.dataframe(focus.sort_values(["focus_date", "priority"], ascending=[False, True]), use_container_width=True, hide_index=True)
        if not reflections.empty:
            st.subheader("Past Reflections")
            st.dataframe(reflections.sort_values("reflection_date", ascending=False), use_container_width=True, hide_index=True)

elif page == "Tasks":
    st.title("Tasks")
    with st.form("add_task"):
        title = st.text_input("Task name")
        category = st.selectbox("Category", ["Personal", "School", "Work", "Business", "Health", "Other"])
        due_date = st.date_input("Due date")
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        add_reminder = st.checkbox("Add reminder")

        reminder_at = None
        if add_reminder:
            reminder_date = st.date_input("Reminder date", value=due_date)
            reminder_time = st.time_input("Reminder time", value=datetime_time(9, 0))
            reminder_at = datetime.combine(reminder_date, reminder_time).isoformat(timespec="minutes")

        if st.form_submit_button("Add Task"):
            if title.strip():
                query(
                    "INSERT INTO tasks (title, category, due_date, priority, done, created_at, reminder_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (title.strip(), category, due_date.isoformat(), priority, 0, datetime.now().isoformat(timespec="seconds"), reminder_at),
                )
                st.rerun()
            st.warning("Add a task name.")

    tasks = table("tasks")
    if tasks.empty:
        st.info("No tasks yet.")
    else:
        reminders = due_reminders(tasks)
        if not reminders.empty:
            st.subheader("Due Reminders")
            for _, task in reminders.iterrows():
                st.warning(f"{task['title']} - reminder was set for {reminder_text(task['reminder_at'])}")

        f1, f2 = st.columns(2)
        status_filter = f1.selectbox("Status", ["All", "Open", "Done"])
        priority_filter = f2.selectbox("Priority", ["All", "Low", "Medium", "High"])
        filtered = tasks.copy()
        if status_filter == "Open":
            filtered = filtered[filtered["done"] == 0]
        elif status_filter == "Done":
            filtered = filtered[filtered["done"] == 1]
        if priority_filter != "All":
            filtered = filtered[filtered["priority"] == priority_filter]
        for _, task in filtered.sort_values("id", ascending=False).iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([5, 1, 1])
                with c1:
                    status = "Done" if task["done"] else "Open"
                    st.write(f"**{task['title']}**")
                    st.caption(f"{task['category']} | {task['priority']} | Due {task['due_date']} | {status}")
                    st.caption(f"Reminder: {reminder_text(task.get('reminder_at'))}")
                with c2:
                    label = "Undo" if task["done"] else "Done"
                    new_done = 0 if task["done"] else 1
                    if st.button(label, key=f"task_toggle_{task['id']}"):
                        query("UPDATE tasks SET done = ? WHERE id = ?", (new_done, task["id"]))
                        st.rerun()
                with c3:
                    if st.button("Delete", key=f"delete_task_{task['id']}"):
                        query("DELETE FROM tasks WHERE id = ?", (task["id"],))
                        st.rerun()

elif page == "Notes":
    st.title("Notes")
    with st.form("add_note"):
        title = st.text_input("Title")
        body = st.text_area("Note", height=180)
        if st.form_submit_button("Save Note"):
            if title.strip():
                query("INSERT INTO notes (title, body, created_at) VALUES (?, ?, ?)", (title.strip(), body, datetime.now().isoformat(timespec="seconds")))
                st.rerun()
            st.warning("Title is required.")
    notes = table("notes")
    search = st.text_input("Search notes")
    if not notes.empty and search:
        notes = notes[notes["title"].str.contains(search, case=False, na=False) | notes["body"].str.contains(search, case=False, na=False)]
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

elif page == "Habits":
    st.title("Habits")
    with st.form("track_habit"):
        habit = st.text_input("Habit")
        completed = st.checkbox("Completed today")
        if st.form_submit_button("Track"):
            if habit.strip():
                query("INSERT INTO habits (habit, tracked_date, completed) VALUES (?, ?, ?)", (habit.strip(), today(), 1 if completed else 0))
                st.rerun()
            st.warning("Habit name is required.")
    habits = table("habits")
    if habits.empty:
        st.info("No habits yet.")
    else:
        summary = habits.groupby("habit")["completed"].sum().reset_index()
        st.plotly_chart(px.bar(summary, x="habit", y="completed", title="Habit Wins"), use_container_width=True)
        st.dataframe(habits.sort_values("id", ascending=False), use_container_width=True, hide_index=True)

elif page == "Hobbies":
    st.title("Hobby Tracker")
    st.caption("Add hobbies, remove hobbies, and track how much time you spend on them.")
    tab1, tab2, tab3 = st.tabs(["My Hobbies", "Track Time", "Stats"])
    with tab1:
        with st.form("add_hobby"):
            name = st.text_input("Hobby name", placeholder="Example: Drawing, Guitar, Gym, Coding")
            category = st.selectbox("Category", ["Creative", "Fitness", "Learning", "Music", "Gaming", "Outdoor", "Social", "Other"])
            goal = st.text_input("Goal", placeholder="Example: Practice 3 times a week")
            if st.form_submit_button("Add Hobby"):
                if name.strip():
                    query("INSERT INTO hobbies (name, category, goal, created_at) VALUES (?, ?, ?, ?)", (name.strip(), category, goal.strip(), datetime.now().isoformat(timespec="seconds")))
                    st.rerun()
                st.warning("Add a hobby name first.")
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
        hobbies = table("hobbies")
        if hobbies.empty:
            st.info("Add a hobby first before tracking time.")
        else:
            hobby_options = {f"{row['name']} ({row['category']})": row["id"] for _, row in hobbies.sort_values("name").iterrows()}
            with st.form("track_hobby_session"):
                selected = st.selectbox("Choose hobby", list(hobby_options.keys()))
                session_date = st.date_input("Date", value=date.today())
                minutes = st.number_input("Minutes spent", min_value=1, max_value=1440, value=30, step=5)
                note = st.text_area("Note", placeholder="What did you do or improve?")
                if st.form_submit_button("Save Session"):
                    query("INSERT INTO hobby_sessions (hobby_id, session_date, minutes, note, created_at) VALUES (?, ?, ?, ?, ?)", (hobby_options[selected], session_date.isoformat(), int(minutes), note.strip(), datetime.now().isoformat(timespec="seconds")))
                    st.rerun()
            sessions = table("hobby_sessions")
            if not sessions.empty:
                view = sessions.merge(hobbies[["id", "name", "category"]], left_on="hobby_id", right_on="id", how="left")
                st.dataframe(view[["session_date", "name", "category", "minutes", "note"]].sort_values("session_date", ascending=False), use_container_width=True, hide_index=True)
    with tab3:
        hobbies = table("hobbies")
        sessions = table("hobby_sessions")
        if hobbies.empty or sessions.empty:
            st.info("Track some hobby time first to see stats.")
        else:
            stats = sessions.merge(hobbies[["id", "name", "category"]], left_on="hobby_id", right_on="id", how="left")
            total_hours = stats["minutes"].sum() / 60
            top_hobby = stats.groupby("name")["minutes"].sum().sort_values(ascending=False).index[0]
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Hours", f"{total_hours:.1f}")
            c2.metric("Sessions", len(stats))
            c3.metric("Top Hobby", top_hobby)
            by_hobby = stats.groupby("name")["minutes"].sum().reset_index()
            by_hobby["hours"] = by_hobby["minutes"] / 60
            st.plotly_chart(px.bar(by_hobby, x="name", y="hours", title="Hours Per Hobby"), use_container_width=True)

elif page == "Mood":
    st.title("Mood Tracker")
    with st.form("add_mood"):
        mood = st.selectbox("Mood", ["Amazing", "Good", "Okay", "Tired", "Stressed", "Sad"])
        energy = st.slider("Energy", 1, 10, 5)
        stress = st.slider("Stress", 1, 10, 5)
        note = st.text_area("Note")
        if st.form_submit_button("Save Mood"):
            query("INSERT INTO mood (mood, energy, stress, note, tracked_date) VALUES (?, ?, ?, ?, ?)", (mood, energy, stress, note, today()))
            st.rerun()
    moods = table("mood")
    if moods.empty:
        st.info("No mood entries yet.")
    else:
        c1, c2 = st.columns(2)
        c1.metric("Average Energy", f"{moods['energy'].mean():.1f}")
        c2.metric("Average Stress", f"{moods['stress'].mean():.1f}")
        st.plotly_chart(px.line(moods, x="tracked_date", y=["energy", "stress"], markers=True, title="Energy vs Stress"), use_container_width=True)
        st.dataframe(moods.sort_values("id", ascending=False), use_container_width=True, hide_index=True)

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
                query("INSERT INTO budget (item, amount, type, category, entry_date) VALUES (?, ?, ?, ?, ?)", (item.strip(), amount, kind, category, entry_date.isoformat()))
                st.rerun()
            st.warning("Item and amount are required.")
    budget = table("budget")
    if budget.empty:
        st.info("No budget entries yet.")
    else:
        income = budget[budget["type"] == "Income"]["amount"].sum()
        expense = budget[budget["type"] == "Expense"]["amount"].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Income", f"R {income:,.2f}")
        c2.metric("Expenses", f"R {expense:,.2f}")
        c3.metric("Balance", f"R {income - expense:,.2f}")
        expenses = budget[budget["type"] == "Expense"]
        if not expenses.empty:
            st.plotly_chart(px.pie(expenses, names="category", values="amount", title="Expenses by Category"), use_container_width=True)
        st.dataframe(budget.sort_values("id", ascending=False), use_container_width=True, hide_index=True)

elif page == "Goals":
    st.title("Goals")
    with st.form("add_goal"):
        title = st.text_input("Goal")
        target = st.text_input("Target")
        progress = st.slider("Progress", 0, 100, 0)
        if st.form_submit_button("Add Goal"):
            if title.strip():
                query("INSERT INTO goals (title, target, progress, created_at) VALUES (?, ?, ?, ?)", (title.strip(), target, progress, datetime.now().isoformat(timespec="seconds")))
                st.rerun()
            st.warning("Goal title is required.")
    goals = table("goals")
    if goals.empty:
        st.info("No goals yet.")
    else:
        st.metric("Average Goal Progress", f"{goals['progress'].mean():.0f}%")
        for _, goal in goals.sort_values("id", ascending=False).iterrows():
            with st.container(border=True):
                st.write(f"**{goal['title']}**")
                st.caption(goal["target"])
                st.progress(int(goal["progress"]) / 100)
                new_progress = st.slider("Update progress", 0, 100, int(goal["progress"]), key=f"progress_{goal['id']}")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Save Progress", key=f"save_goal_{goal['id']}"):
                        query("UPDATE goals SET progress = ? WHERE id = ?", (new_progress, goal["id"]))
                        st.rerun()
                with c2:
                    if st.button("Delete Goal", key=f"delete_goal_{goal['id']}"):
                        query("DELETE FROM goals WHERE id = ?", (goal["id"],))
                        st.rerun()
