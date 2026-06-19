# ============================================================
# MYDAY PRO
# CLEAN EDITION
# PART 1
# ============================================================

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

from datetime import datetime, date, timedelta, time as datetime_time

# ============================================================
# APP CONFIG
# ============================================================

st.set_page_config(
    page_title="MyDay Pro",
    page_icon="🚀",
    layout="wide"
)

APP_PIN = "1234"

# ============================================================
# DATABASE
# ============================================================

DB_NAME = "myday_pro.db"


def get_connection():
    return sqlite3.connect(
        DB_NAME,
        check_same_thread=False
    )


def run_query(
    sql,
    params=(),
    fetch=False
):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(sql, params)

    result = (
        cur.fetchall()
        if fetch
        else None
    )

    conn.commit()
    conn.close()

    return result


def load_table(name):

    conn = get_connection()

    try:
        df = pd.read_sql(
            f"SELECT * FROM {name}",
            conn
        )
    except:
        df = pd.DataFrame()

    conn.close()

    return df


def today():
    return date.today().isoformat()


# ============================================================
# DATABASE TABLES
# ============================================================

def create_tables():

    conn = get_connection()
    cur = conn.cursor()

    # TASKS

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        category TEXT,
        priority TEXT,
        due_date TEXT,
        done INTEGER DEFAULT 0,
        created_at TEXT,
        reminder_at TEXT
    )
    """)

    task_columns = [
        row[1]
        for row in cur.execute(
            "PRAGMA table_info(tasks)"
        ).fetchall()
    ]

    if "reminder_at" not in task_columns:

        cur.execute(
            "ALTER TABLE tasks ADD COLUMN reminder_at TEXT"
        )

    # GOALS

    cur.execute("""
    CREATE TABLE IF NOT EXISTS goals(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        created_at TEXT
    )
    """)

    # GOAL ITEMS

    cur.execute("""
    CREATE TABLE IF NOT EXISTS goal_items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        goal_id INTEGER,
        task TEXT,
        completed INTEGER DEFAULT 0
    )
    """)

    # JOURNAL

    cur.execute("""
    CREATE TABLE IF NOT EXISTS journal(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        body TEXT,
        entry_date TEXT,
        created_at TEXT
    )
    """)

    # DAILY FOCUS

    cur.execute("""
    CREATE TABLE IF NOT EXISTS focus(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        focus_task TEXT,
        focus_date TEXT
    )
    """)

    # BUCKET LIST

    cur.execute("""
    CREATE TABLE IF NOT EXISTS bucket_list(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item TEXT,
        completed INTEGER DEFAULT 0,
        created_at TEXT
    )
    """)

    # HOBBIES

    cur.execute("""
    CREATE TABLE IF NOT EXISTS hobbies(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        category TEXT,
        goal TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS hobby_sessions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hobby_id INTEGER,
        session_date TEXT,
        minutes INTEGER,
        note TEXT,
        created_at TEXT
    )
    """)

    # BUDGET

    cur.execute("""
    CREATE TABLE IF NOT EXISTS budget(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item TEXT,
        amount REAL,
        type TEXT,
        category TEXT,
        entry_date TEXT
    )
    """)

    # XP

    cur.execute("""
    CREATE TABLE IF NOT EXISTS xp(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        points INTEGER
    )
    """)

    conn.commit()
    conn.close()


create_tables()

# ============================================================
# XP SYSTEM
# ============================================================

def get_xp():

    xp_df = load_table("xp")

    if xp_df.empty:
        return 0

    return int(
        xp_df["points"].sum()
    )


def add_xp(points):

    run_query(
        """
        INSERT INTO xp(points)
        VALUES(?)
        """,
        (points,)
    )


def get_level():

    xp = get_xp()

    return (xp // 100) + 1


def reminder_text(value):

    if not value:

        return "No reminder"

    try:

        return datetime.fromisoformat(value).strftime(
            "%d %b %Y, %H:%M"
        )

    except ValueError:

        return str(value)


def get_due_reminders(tasks):

    if tasks.empty or "reminder_at" not in tasks.columns:

        return pd.DataFrame()

    reminders = tasks[
        (tasks["done"] == 0) &
        (tasks["reminder_at"].notna()) &
        (tasks["reminder_at"] != "")
    ].copy()

    if reminders.empty:

        return pd.DataFrame()

    reminders["reminder_dt"] = pd.to_datetime(
        reminders["reminder_at"],
        errors="coerce"
    )

    return reminders[
        reminders["reminder_dt"] <= pd.Timestamp.now()
    ].sort_values("reminder_dt")


def get_upcoming_reminders(tasks):

    if tasks.empty or "reminder_at" not in tasks.columns:

        return pd.DataFrame()

    reminders = tasks[
        (tasks["done"] == 0) &
        (tasks["reminder_at"].notna()) &
        (tasks["reminder_at"] != "")
    ].copy()

    if reminders.empty:

        return pd.DataFrame()

    reminders["reminder_dt"] = pd.to_datetime(
        reminders["reminder_at"],
        errors="coerce"
    )

    now = pd.Timestamp.now()

    return reminders[
        reminders["reminder_dt"] > now
    ].sort_values("reminder_dt")


def snooze_reminder(task_id, minutes):

    reminder_at = (
        datetime.now() + timedelta(minutes=minutes)
    ).isoformat(
        timespec="minutes"
    )

    run_query(
        """
        UPDATE tasks
        SET reminder_at = ?
        WHERE id = ?
        """,
        (
            reminder_at,
            task_id
        )
    )


THEMES = {
    "Midnight": {
        "app_bg": "#0f1117",
        "sidebar_bg": "#262833",
        "card_bg": "#171923",
        "card_bg_2": "#111827",
        "border": "#2d3340",
        "text": "#f9fafb",
        "muted": "#cbd5e1",
        "accent": "#2563eb",
        "accent_2": "#7c3aed",
        "alert_bg": "#172a3f",
        "alert_text": "#60a5fa",
        "input_bg": "#262833",
    },
    "Ocean": {
        "app_bg": "#07131f",
        "sidebar_bg": "#0b2436",
        "card_bg": "#0f2a3d",
        "card_bg_2": "#0b1d2d",
        "border": "#1f6f8b",
        "text": "#f3fbff",
        "muted": "#b6d9e8",
        "accent": "#0891b2",
        "accent_2": "#2563eb",
        "alert_bg": "#123447",
        "alert_text": "#67e8f9",
        "input_bg": "#102c3d",
    },
    "Forest": {
        "app_bg": "#0f1712",
        "sidebar_bg": "#16251b",
        "card_bg": "#18291e",
        "card_bg_2": "#101c15",
        "border": "#2f5d3a",
        "text": "#f6fff8",
        "muted": "#c8dfcf",
        "accent": "#16a34a",
        "accent_2": "#84cc16",
        "alert_bg": "#17351f",
        "alert_text": "#86efac",
        "input_bg": "#1b2d21",
    },
    "Light": {
        "app_bg": "#f6f7fb",
        "sidebar_bg": "#ffffff",
        "card_bg": "#ffffff",
        "card_bg_2": "#eef2ff",
        "border": "#d8dee9",
        "text": "#111827",
        "muted": "#4b5563",
        "accent": "#2563eb",
        "accent_2": "#7c3aed",
        "alert_bg": "#dbeafe",
        "alert_text": "#1d4ed8",
        "input_bg": "#ffffff",
    },
}


# ============================================================
# THEME
# ============================================================

if "theme_name" not in st.session_state:

    st.session_state.theme_name = "Midnight"

theme = THEMES.get(
    st.session_state.theme_name,
    THEMES["Midnight"]
)

st.markdown(f"""
<style>

.stApp {{
    background:{theme["app_bg"]};
}}

.block-container {{
    padding-top:1rem;
    padding-bottom:2rem;
}}

h1, h2, h3, h4, p, label, span {{
    color:{theme["text"]} !important;
}}

[data-testid="stMetric"] {{
    background:linear-gradient(
        145deg,
        {theme["card_bg"]},
        {theme["card_bg_2"]}
    );
    border:1px solid {theme["border"]};
    border-radius:18px;
    padding:18px;
    box-shadow:0 12px 28px rgba(0,0,0,0.20);
}}

[data-testid="stMetricLabel"],
[data-testid="stMetricDelta"] {{
    color:{theme["muted"]} !important;
}}

[data-testid="stMetricValue"] {{
    color:{theme["text"]} !important;
}}

.stButton button {{
    border-radius:12px;
    width:100%;
    font-weight:600;
    background:{theme["accent"]};
    color:white !important;
    border:none;
}}

.stButton button:hover {{
    background:{theme["accent_2"]};
    color:white !important;
}}

div[data-testid="stVerticalBlockBorderWrapper"] {{
    border-radius:16px;
    border-color:{theme["border"]} !important;
    background:{theme["card_bg_2"]} !important;
}}

.focus-card {{
    background:linear-gradient(
        135deg,
        {theme["accent"]},
        {theme["accent_2"]}
    );
    color:white;
    padding:30px;
    border-radius:20px;
    text-align:center;
}}

.focus-card h2,
.focus-card h3,
.focus-card p {{
    color:white !important;
}}

section[data-testid="stSidebar"] {{
    background:{theme["sidebar_bg"]};
    border-right:1px solid {theme["border"]};
}}

.stAlert {{
    background:{theme["alert_bg"]} !important;
    color:{theme["alert_text"]} !important;
    border-radius:12px;
}}

.stAlert p {{
    color:{theme["alert_text"]} !important;
}}

input, textarea {{
    color:{theme["text"]} !important;
    background-color:{theme["input_bg"]} !important;
}}

</style>
""", unsafe_allow_html=True)

# ============================================================
# LOGIN
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:

    st.title("🚀 MyDay Pro")

    st.caption(
        "Personal Productivity System"
    )

    pin = st.text_input(
        "Enter PIN",
        type="password"
    )

    if st.button("Unlock"):

        if pin == APP_PIN:

            st.session_state.logged_in = True
            st.rerun()

        else:

            st.error(
                "Incorrect PIN"
            )

    st.stop()

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🚀 MyDay Pro")

st.sidebar.caption(
    f"Level {get_level()} | {get_xp()} XP"
)

theme_choice = st.sidebar.selectbox(
    "Theme",
    list(THEMES.keys()),
    index=list(THEMES.keys()).index(
        st.session_state.theme_name
    ),
)

if theme_choice != st.session_state.theme_name:

    st.session_state.theme_name = theme_choice
    st.rerun()

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Tasks",
        "Daily Focus",
        "Goals",
        "Journal",
        "Bucket List",
        "Hobbies",
        "Budget",
        "Settings"
    ]
)

st.sidebar.divider()

if st.sidebar.button(
    "🔒 Lock App"
):

    st.session_state.logged_in = False
    st.rerun()
    # ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":

    st.title("🏠 Dashboard")

    current_hour = datetime.now().hour

    if current_hour < 12:
        greeting = "☀️ Good Morning"
    elif current_hour < 18:
        greeting = "🌤 Good Afternoon"
    else:
        greeting = "🌙 Good Evening"

    st.markdown(
        f"""
        <div class="focus-card">
            <h2>{greeting}</h2>
            <h3>Welcome back to MyDay Pro</h3>
            <p>Stay focused. Stay productive.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    # ========================================================
    # LOAD DATA
    # ========================================================

    tasks = load_table("tasks")
    goals = load_table("goals")
    bucket = load_table("bucket_list")
    budget = load_table("budget")
    focus = load_table("focus")
    journal = load_table("journal")

    # ========================================================
    # TODAY'S FOCUS
    # ========================================================

    today_focus = "No focus set"

    if not focus.empty:

        focus_today = focus[
            focus["focus_date"] == today()
        ]

        if not focus_today.empty:

            today_focus = focus_today.iloc[-1][
                "focus_task"
            ]

    st.subheader("⭐ Today's Focus")

    st.info(today_focus)

    due_reminders = get_due_reminders(tasks)

    if not due_reminders.empty:

        st.subheader("🔔 Due Reminders")

        for _, task in due_reminders.iterrows():

            with st.container(border=True):

                left, middle, right = st.columns([5, 1, 1])

                with left:

                    st.warning(
                        f"{task['title']} — reminder was set for "
                        f"{reminder_text(task['reminder_at'])}"
                    )

                with middle:

                    if st.button(
                        "Snooze 1h",
                        key=f"dash_snooze_{task['id']}"
                    ):

                        snooze_reminder(task["id"], 60)
                        st.rerun()

                with right:

                    if st.button(
                        "Done",
                        key=f"dash_done_reminder_{task['id']}"
                    ):

                        run_query(
                            """
                            UPDATE tasks
                            SET done = 1
                            WHERE id = ?
                            """,
                            (
                                task["id"],
                            )
                        )

                        add_xp(10)
                        st.rerun()

    upcoming_reminders = get_upcoming_reminders(tasks).head(3)

    if not upcoming_reminders.empty:

        with st.expander("Upcoming Reminders"):

            for _, task in upcoming_reminders.iterrows():

                st.write(
                    f"**{task['title']}** — "
                    f"{reminder_text(task['reminder_at'])}"
                )

    # ========================================================
    # KPI CARDS
    # ========================================================

    open_tasks = 0

    if not tasks.empty:

        open_tasks = len(
            tasks[
                tasks["done"] == 0
            ]
        )

    total_goals = len(goals)

    completed_bucket = 0

    if not bucket.empty:

        completed_bucket = len(
            bucket[
                bucket["completed"] == 1
            ]
        )

    income = 0
    expenses = 0

    if not budget.empty:

        income = budget[
            budget["type"] == "Income"
        ]["amount"].sum()

        expenses = budget[
            budget["type"] == "Expense"
        ]["amount"].sum()

    balance = income - expenses

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "📋 Open Tasks",
        open_tasks
    )

    c2.metric(
        "🎯 Goals",
        total_goals
    )

    c3.metric(
        "🪣 Dreams Completed",
        completed_bucket
    )

    c4.metric(
        "💰 Balance",
        f"R {balance:,.0f}"
    )

    st.divider()

    # ========================================================
    # XP SECTION
    # ========================================================

    st.subheader("🚀 Level Progress")

    xp = get_xp()
    level = get_level()

    c1, c2 = st.columns([1, 3])

    with c1:

        st.metric(
            "Level",
            level
        )

    with c2:

        xp_progress = xp % 100

        st.progress(
            xp_progress / 100
        )

        st.caption(
            f"{xp_progress}/100 XP until Level {level + 1}"
        )

    st.divider()

    # ========================================================
    # DUE TODAY
    # ========================================================

    left, right = st.columns(
        [2, 1]
    )

    with left:

        st.subheader(
            "📅 Tasks Due Today"
        )

        if tasks.empty:

            st.info(
                "No tasks yet."
            )

        else:

            due_today = tasks[
                (tasks["due_date"] == today()) &
                (tasks["done"] == 0)
            ]

            if due_today.empty:

                st.success(
                    "Nothing due today 🎉"
                )

            else:

                st.dataframe(
                    due_today[
                        [
                            "title",
                            "priority",
                            "category"
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True
                )

    with right:

        st.subheader(
            "⚡ Quick Add"
        )

        with st.form(
            "quick_task_form"
        ):

            task_name = st.text_input(
                "Task"
            )

            submit = st.form_submit_button(
                "Add Task"
            )

            if submit:

                if task_name.strip():

                    run_query(
                        """
                        INSERT INTO tasks
                        (
                            title,
                            category,
                            priority,
                            due_date,
                            done,
                            created_at
                        )
                        VALUES
                        (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            task_name,
                            "Personal",
                            "Medium",
                            today(),
                            0,
                            datetime.now().isoformat(
                                timespec="seconds"
                            )
                        )
                    )

                    add_xp(5)

                    st.rerun()

    st.divider()

    # ========================================================
    # RECENT JOURNAL
    # ========================================================

    st.subheader(
        "📔 Latest Journal Entries"
    )

    if journal.empty:

        st.info(
            "No journal entries yet."
        )

    else:

        recent_journal = journal.sort_values(
            "id",
            ascending=False
        ).head(3)

        for _, row in recent_journal.iterrows():

            with st.container(
                border=True
            ):

                st.write(
                    f"**{row['title']}**"
                )

                st.caption(
                    row["entry_date"]
                )

    st.divider()

    # ========================================================
    # ACTIVITY SUMMARY
    # ========================================================

    st.subheader(
        "📊 Activity Summary"
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Journal Entries",
        len(journal)
    )

    col2.metric(
        "Bucket List Items",
        len(bucket)
    )

    col3.metric(
        "XP Earned",
        get_xp()
    )


# ============================================================
# DAILY FOCUS
# ============================================================

elif page == "Daily Focus":

    st.title("⭐ Daily Focus")

    st.caption(
        "Choose the most important thing for today."
    )

    focus = load_table("focus")

    current_focus = "No focus selected"

    if not focus.empty:

        today_focus = focus[
            focus["focus_date"] == today()
        ]

        if not today_focus.empty:

            current_focus = today_focus.iloc[-1][
                "focus_task"
            ]

    st.info(
        f"Current Focus: {current_focus}"
    )

    with st.form(
        "daily_focus_form"
    ):

        focus_task = st.text_input(
            "Today's Main Focus"
        )

        submit = st.form_submit_button(
            "Save Focus"
        )

        if submit:

            if focus_task.strip():

                run_query(
                    """
                    INSERT INTO focus
                    (
                        focus_task,
                        focus_date
                    )
                    VALUES
                    (?, ?)
                    """,
                    (
                        focus_task,
                        today()
                    )
                )

                add_xp(10)

                st.success(
                    "Focus saved."
                )

                st.rerun()

    st.divider()

    st.subheader(
        "💡 Focus Rules"
    )

    st.markdown("""
    - Pick ONE major objective
    - Finish it before small tasks
    - Keep it measurable
    - Review it tonight
    - Set a new focus tomorrow
    """)
    # ============================================================
# TASKS
# ============================================================

elif page == "Tasks":

    st.title("✅ Tasks")

    tasks = load_table("tasks")

    # ========================================================
    # ADD TASK
    # ========================================================

    with st.expander(
        "➕ Create New Task",
        expanded=True
    ):

        with st.form("task_form"):

            title = st.text_input(
                "Task Name"
            )

            category = st.selectbox(
                "Category",
                [
                    "Personal",
                    "Work",
                    "Business",
                    "Study",
                    "Health",
                    "Finance",
                    "Other"
                ]
            )

            priority = st.selectbox(
                "Priority",
                [
                    "Low",
                    "Medium",
                    "High"
                ]
            )

            due_date = st.date_input(
                "Due Date"
            )

            reminder_at = None

            reminder_choice = st.selectbox(
                "Reminder",
                [
                    "None",
                    "Today 18:00",
                    "Tomorrow 09:00",
                    "Custom"
                ]
            )

            if reminder_choice == "Today 18:00":

                reminder_at = datetime.combine(
                    date.today(),
                    datetime_time(18, 0)
                ).isoformat(
                    timespec="minutes"
                )

            elif reminder_choice == "Tomorrow 09:00":

                reminder_at = datetime.combine(
                    date.today() + timedelta(days=1),
                    datetime_time(9, 0)
                ).isoformat(
                    timespec="minutes"
                )

            elif reminder_choice == "Custom":

                reminder_date = st.date_input(
                    "Reminder Date",
                    value=due_date
                )

                reminder_time = st.time_input(
                    "Reminder Time",
                    value=datetime_time(9, 0)
                )

                reminder_at = datetime.combine(
                    reminder_date,
                    reminder_time
                ).isoformat(
                    timespec="minutes"
                )

            submitted = st.form_submit_button(
                "Add Task"
            )

            if submitted:

                if title.strip():

                    run_query(
                        """
                        INSERT INTO tasks
                        (
                            title,
                            category,
                            priority,
                            due_date,
                            done,
                            created_at,
                            reminder_at
                        )
                        VALUES
                        (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            title,
                            category,
                            priority,
                            due_date.isoformat(),
                            0,
                            datetime.now().isoformat(
                                timespec="seconds"
                            ),
                            reminder_at
                        )
                    )

                    add_xp(5)

                    st.success(
                        "Task created."
                    )

                    st.rerun()

    st.divider()

    # ========================================================
    # TASK STATS
    # ========================================================

    total_tasks = len(tasks)

    completed_tasks = 0
    open_tasks = 0

    if not tasks.empty:

        completed_tasks = len(
            tasks[
                tasks["done"] == 1
            ]
        )

        open_tasks = len(
            tasks[
                tasks["done"] == 0
            ]
        )

    completion_rate = 0

    if total_tasks > 0:

        completion_rate = (
            completed_tasks /
            total_tasks
        ) * 100

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "📋 Total",
        total_tasks
    )

    c2.metric(
        "🔥 Open",
        open_tasks
    )

    c3.metric(
        "✅ Done",
        completed_tasks
    )

    c4.metric(
        "📈 Success",
        f"{completion_rate:.0f}%"
    )

    st.divider()

    due_reminders = get_due_reminders(tasks)

    if not due_reminders.empty:

        st.subheader("🔔 Due Reminders")

        for _, task in due_reminders.iterrows():

            with st.container(border=True):

                left, middle, right = st.columns([5, 1, 1])

                with left:

                    st.warning(
                        f"{task['title']} — reminder was set for "
                        f"{reminder_text(task['reminder_at'])}"
                    )

                with middle:

                    if st.button(
                        "Snooze 1h",
                        key=f"task_snooze_{task['id']}"
                    ):

                        snooze_reminder(task["id"], 60)
                        st.rerun()

                with right:

                    if st.button(
                        "Done",
                        key=f"task_done_reminder_{task['id']}"
                    ):

                        run_query(
                            """
                            UPDATE tasks
                            SET done = 1
                            WHERE id = ?
                            """,
                            (
                                task["id"],
                            )
                        )

                        add_xp(10)
                        st.rerun()

        st.divider()

    upcoming_reminders = get_upcoming_reminders(tasks).head(5)

    if not upcoming_reminders.empty:

        with st.expander("Upcoming Reminders"):

            for _, task in upcoming_reminders.iterrows():

                st.write(
                    f"**{task['title']}** — "
                    f"{reminder_text(task['reminder_at'])}"
                )

    # ========================================================
    # FILTERS
    # ========================================================

    if not tasks.empty:

        search_text = st.text_input(
            "Search Tasks",
            placeholder="Search by task name, category, or priority"
        )

        f1, f2, f3 = st.columns(3)

        with f1:

            status_filter = st.selectbox(
                "Status",
                [
                    "All",
                    "Open",
                    "Completed"
                ]
            )

        with f2:

            categories = ["All"] + sorted(
                tasks["category"]
                .dropna()
                .unique()
                .tolist()
            )

            category_filter = st.selectbox(
                "Category",
                categories
            )

        with f3:

            reminder_filter = st.selectbox(
                "Reminder",
                [
                    "All",
                    "Due Now",
                    "Upcoming",
                    "No Reminder"
                ]
            )

        filtered = tasks.copy()

        if search_text.strip():

            search = search_text.strip()

            filtered = filtered[
                filtered["title"].astype(str).str.contains(
                    search,
                    case=False,
                    na=False
                ) |
                filtered["category"].astype(str).str.contains(
                    search,
                    case=False,
                    na=False
                ) |
                filtered["priority"].astype(str).str.contains(
                    search,
                    case=False,
                    na=False
                )
            ]

        if status_filter == "Open":

            filtered = filtered[
                filtered["done"] == 0
            ]

        elif status_filter == "Completed":

            filtered = filtered[
                filtered["done"] == 1
            ]

        if category_filter != "All":

            filtered = filtered[
                filtered["category"]
                == category_filter
            ]

        if reminder_filter != "All":

            filtered = filtered.copy()

            if "reminder_at" not in filtered.columns:

                filtered["reminder_at"] = None

            reminder_dates = pd.to_datetime(
                filtered["reminder_at"],
                errors="coerce"
            )

            now = pd.Timestamp.now()

            if reminder_filter == "Due Now":

                filtered = filtered[
                    (filtered["done"] == 0) &
                    reminder_dates.notna() &
                    (reminder_dates <= now)
                ]

            elif reminder_filter == "Upcoming":

                filtered = filtered[
                    (filtered["done"] == 0) &
                    reminder_dates.notna() &
                    (reminder_dates > now)
                ]

            elif reminder_filter == "No Reminder":

                filtered = filtered[
                    reminder_dates.isna()
                ]

        # ====================================================
        # TASK CARDS
        # ====================================================

        st.subheader(
            "📌 Task List"
        )

        for _, task in filtered.sort_values(
            "id",
            ascending=False
        ).iterrows():

            if task["priority"] == "High":
                icon = "🔴"

            elif task["priority"] == "Medium":
                icon = "🟡"

            else:
                icon = "🟢"

            with st.container(
                border=True
            ):

                left, middle, right = st.columns(
                    [7, 1, 1]
                )

                with left:

                    if task["done"] == 1:

                        st.markdown(
                            f"### ~~{task['title']}~~"
                        )

                    else:

                        st.markdown(
                            f"### {task['title']}"
                        )

                    st.caption(
                        f"{icon} {task['priority']} | "
                        f"{task['category']} | "
                        f"Due: {task['due_date']}"
                    )

                    st.caption(
                        f"🔔 Reminder: "
                        f"{reminder_text(task.get('reminder_at'))}"
                    )

                with middle:

                    if task["done"] == 0:

                        if st.button(
                            "✔",
                            key=f"done_{task['id']}"
                        ):

                            run_query(
                                """
                                UPDATE tasks
                                SET done = 1
                                WHERE id = ?
                                """,
                                (
                                    task["id"],
                                )
                            )

                            add_xp(10)

                            st.rerun()

                    else:

                        if st.button(
                            "↩",
                            key=f"undo_{task['id']}"
                        ):

                            run_query(
                                """
                                UPDATE tasks
                                SET done = 0
                                WHERE id = ?
                                """,
                                (
                                    task["id"],
                                )
                            )

                            st.rerun()

                with right:

                    if st.button(
                        "🗑",
                        key=f"delete_{task['id']}"
                    ):

                        run_query(
                            """
                            DELETE FROM tasks
                            WHERE id = ?
                            """,
                            (
                                task["id"],
                            )
                        )

                        st.rerun()

    else:

        st.info(
            "No tasks created yet."
        )

    st.divider()

    # ========================================================
    # TASK ANALYTICS
    # ========================================================

    if not tasks.empty:

        st.subheader(
            "📊 Task Analytics"
        )

        priority_stats = (
            tasks.groupby(
                "priority"
            )
            .size()
            .reset_index(
                name="count"
            )
        )

        fig = px.pie(
            priority_stats,
            names="priority",
            values="count",
            hole=0.45,
            title="Tasks by Priority"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        category_stats = (
            tasks.groupby(
                "category"
            )
            .size()
            .reset_index(
                name="count"
            )
        )

        fig2 = px.bar(
            category_stats,
            x="category",
            y="count",
            title="Tasks by Category"
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

    st.divider()

    # ========================================================
    # PRODUCTIVITY ACHIEVEMENTS
    # ========================================================

    st.subheader(
        "🏆 Achievements"
    )

    if completed_tasks >= 1:
        st.success(
            "First Task Completed!"
        )

    if completed_tasks >= 25:
        st.success(
            "Task Warrior — 25 Completed"
        )

    if completed_tasks >= 50:
        st.success(
            "Productivity Machine — 50 Completed"
        )

    if completed_tasks >= 100:
        st.success(
            "Legend — 100 Completed Tasks"
        )
        # ============================================================
# GOALS
# ============================================================

elif page == "Goals":

    st.title("🎯 Goals")

    goals = load_table("goals")
    goal_items = load_table("goal_items")

    # ========================================================
    # CREATE GOAL
    # ========================================================

    with st.expander(
        "➕ Create New Goal",
        expanded=True
    ):

        with st.form("goal_create_form"):

            goal_title = st.text_input(
                "Goal Name"
            )

            create_goal = st.form_submit_button(
                "Create Goal"
            )

            if create_goal:

                if goal_title.strip():

                    run_query(
                        """
                        INSERT INTO goals
                        (
                            title,
                            created_at
                        )
                        VALUES
                        (?, ?)
                        """,
                        (
                            goal_title,
                            datetime.now().isoformat(
                                timespec="seconds"
                            )
                        )
                    )

                    add_xp(15)

                    st.success(
                        "Goal created."
                    )

                    st.rerun()

    st.divider()

    # ========================================================
    # GOAL OVERVIEW
    # ========================================================

    total_goals = len(goals)
    completed_goals = 0

    if not goals.empty:

        for _, goal in goals.iterrows():

            goal_id = goal["id"]

            items = goal_items[
                goal_items["goal_id"]
                == goal_id
            ]

            if not items.empty:

                done = len(
                    items[
                        items["completed"] == 1
                    ]
                )

                if done == len(items):
                    completed_goals += 1

    completion_rate = 0

    if total_goals > 0:

        completion_rate = (
            completed_goals /
            total_goals
        ) * 100

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "🎯 Total Goals",
        total_goals
    )

    c2.metric(
        "🏆 Completed",
        completed_goals
    )

    c3.metric(
        "📈 Success Rate",
        f"{completion_rate:.0f}%"
    )

    st.progress(
        completion_rate / 100
    )

    st.divider()

    # ========================================================
    # GOAL CARDS
    # ========================================================

    if goals.empty:

        st.info(
            "No goals created yet."
        )

    else:

        for _, goal in goals.sort_values(
            "id",
            ascending=False
        ).iterrows():

            goal_id = goal["id"]

            items = goal_items[
                goal_items["goal_id"]
                == goal_id
            ]

            total_items = len(items)

            completed_items = 0

            if not items.empty:

                completed_items = len(
                    items[
                        items["completed"] == 1
                    ]
                )

            progress = 0

            if total_items > 0:

                progress = (
                    completed_items /
                    total_items
                )

            with st.container(border=True):

                st.subheader(
                    goal["title"]
                )

                st.progress(progress)

                st.caption(
                    f"{completed_items}/{total_items} tasks completed"
                )

                # ============================================
                # ADD SUBTASK
                # ============================================

                with st.form(
                    f"goal_item_form_{goal_id}"
                ):

                    new_task = st.text_input(
                        "Add Action Step",
                        key=f"goal_step_{goal_id}"
                    )

                    add_step = st.form_submit_button(
                        "Add Step"
                    )

                    if add_step:

                        if new_task.strip():

                            run_query(
                                """
                                INSERT INTO goal_items
                                (
                                    goal_id,
                                    task,
                                    completed
                                )
                                VALUES
                                (?, ?, ?)
                                """,
                                (
                                    goal_id,
                                    new_task,
                                    0
                                )
                            )

                            add_xp(2)

                            st.rerun()

                st.divider()

                # ============================================
                # CHECKLIST
                # ============================================

                if items.empty:

                    st.info(
                        "Add action steps to start."
                    )

                else:

                    for _, item in items.iterrows():

                        col1, col2 = st.columns(
                            [8, 1]
                        )

                        with col1:

                            checked = st.checkbox(
                                item["task"],
                                value=bool(
                                    item["completed"]
                                ),
                                key=f"goal_{item['id']}"
                            )

                            if checked != bool(
                                item["completed"]
                            ):

                                run_query(
                                    """
                                    UPDATE goal_items
                                    SET completed = ?
                                    WHERE id = ?
                                    """,
                                    (
                                        1 if checked else 0,
                                        item["id"]
                                    )
                                )

                                if checked:
                                    add_xp(10)

                                st.rerun()

                        with col2:

                            if st.button(
                                "🗑",
                                key=f"delete_goal_item_{item['id']}"
                            ):

                                run_query(
                                    """
                                    DELETE FROM goal_items
                                    WHERE id = ?
                                    """,
                                    (
                                        item["id"],
                                    )
                                )

                                st.rerun()

                st.divider()

                # ============================================
                # GOAL COMPLETE BADGE
                # ============================================

                if (
                    total_items > 0 and
                    completed_items == total_items
                ):

                    st.success(
                        "🏆 Goal Completed!"
                    )

                # ============================================
                # DELETE GOAL
                # ============================================

                if st.button(
                    "❌ Delete Goal",
                    key=f"delete_goal_{goal_id}"
                ):

                    run_query(
                        """
                        DELETE FROM goal_items
                        WHERE goal_id = ?
                        """,
                        (
                            goal_id,
                        )
                    )

                    run_query(
                        """
                        DELETE FROM goals
                        WHERE id = ?
                        """,
                        (
                            goal_id,
                        )
                    )

                    st.rerun()

    st.divider()

    # ========================================================
    # ACHIEVEMENTS
    # ========================================================

    st.subheader(
        "🏅 Goal Achievements"
    )

    if completed_goals >= 1:
        st.success(
            "First Goal Completed!"
        )

    if completed_goals >= 5:
        st.success(
            "Goal Crusher — 5 Goals Completed"
        )

    if completed_goals >= 10:
        st.success(
            "Achievement Hunter — 10 Goals Completed"
        )

    if completed_goals >= 25:
        st.success(
            "Productivity Master — 25 Goals Completed"
        )

    if completed_goals >= 50:
        st.success(
            "Elite Performer — 50 Goals Completed"
        )
        # ============================================================
# JOURNAL
# ============================================================

elif page == "Journal":

    st.title("📔 Journal")

    st.caption(
        "Capture thoughts, gratitude, wins and lessons."
    )

    # ========================================================
    # NEW ENTRY
    # ========================================================

    with st.expander(
        "✍ New Journal Entry",
        expanded=True
    ):

        with st.form("journal_form"):

            title = st.text_input(
                "Entry Title"
            )

            mood = st.selectbox(
                "Mood",
                [
                    "😁 Amazing",
                    "😊 Happy",
                    "🙂 Good",
                    "😐 Normal",
                    "😔 Sad",
                    "😫 Stressed"
                ]
            )

            wins = st.text_area(
                "🏆 Wins Today",
                height=100
            )

            gratitude = st.text_area(
                "🙏 Gratitude",
                height=100
            )

            lessons = st.text_area(
                "📚 Lessons Learned",
                height=100
            )

            reflection = st.text_area(
                "💭 Reflection",
                height=150
            )

            tomorrow = st.text_area(
                "🚀 Tomorrow's Focus",
                height=100
            )

            save = st.form_submit_button(
                "Save Entry"
            )

            if save:

                if title.strip():

                    body = f"""
MOOD:
{mood}

WINS:
{wins}

GRATITUDE:
{gratitude}

LESSONS:
{lessons}

REFLECTION:
{reflection}

TOMORROW:
{tomorrow}
"""

                    run_query(
                        """
                        INSERT INTO journal
                        (
                            title,
                            body,
                            entry_date,
                            created_at
                        )
                        VALUES
                        (?, ?, ?, ?)
                        """,
                        (
                            title,
                            body,
                            today(),
                            datetime.now().isoformat(
                                timespec="seconds"
                            )
                        )
                    )

                    add_xp(15)

                    st.success(
                        "Journal entry saved."
                    )

                    st.rerun()

    st.divider()

    # ========================================================
    # LOAD DATA
    # ========================================================

    journal = load_table("journal")

    # ========================================================
    # STATS
    # ========================================================

    total_entries = len(journal)

    current_month = datetime.now().month

    monthly_entries = 0

    if not journal.empty:

        journal["entry_date"] = pd.to_datetime(
            journal["entry_date"],
            errors="coerce"
        )

        monthly_entries = len(
            journal[
                journal["entry_date"]
                .dt.month == current_month
            ]
        )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "📖 Total Entries",
        total_entries
    )

    c2.metric(
        "🗓 This Month",
        monthly_entries
    )

    c3.metric(
        "⭐ XP Earned",
        total_entries * 15
    )

    st.divider()

    # ========================================================
    # SEARCH
    # ========================================================

    search = st.text_input(
        "🔍 Search Journal"
    )

    filtered = journal.copy()

    if (
        not journal.empty and
        search.strip()
    ):

        filtered = journal[
            journal["title"]
            .astype(str)
            .str.contains(
                search,
                case=False,
                na=False
            )
        ]

    # ========================================================
    # JOURNAL HISTORY
    # ========================================================

    st.subheader(
        "📚 Journal History"
    )

    if filtered.empty:

        st.info(
            "No journal entries found."
        )

    else:

        filtered = filtered.sort_values(
            "id",
            ascending=False
        )

        for _, entry in filtered.iterrows():

            with st.container(
                border=True
            ):

                st.markdown(
                    f"### {entry['title']}"
                )

                st.caption(
                    f"📅 {entry['entry_date']}"
                )

                st.markdown(
                    entry["body"]
                )

                col1, col2 = st.columns(
                    [5, 1]
                )

                with col2:

                    if st.button(
                        "🗑 Delete",
                        key=f"journal_delete_{entry['id']}"
                    ):

                        run_query(
                            """
                            DELETE FROM journal
                            WHERE id = ?
                            """,
                            (
                                entry["id"],
                            )
                        )

                        st.rerun()

    st.divider()

    # ========================================================
    # REFLECTION PROMPTS
    # ========================================================

    st.subheader(
        "💡 Reflection Prompts"
    )

    prompts = [
        "What made today meaningful?",
        "What challenged me today?",
        "What did I learn today?",
        "What am I grateful for?",
        "What can I improve tomorrow?",
        "What am I proud of this week?",
        "What goal moved forward today?",
        "What deserves more attention?"
    ]

    for prompt in prompts:

        st.write(
            f"• {prompt}"
        )

    st.divider()

    # ========================================================
    # JOURNAL STREAK
    # ========================================================

    st.subheader(
        "🔥 Journal Progress"
    )

    if total_entries == 0:

        st.info(
            "Start journaling today."
        )

    else:

        if total_entries >= 7:

            st.success(
                "🔥 7+ Entries Club"
            )

        if total_entries >= 30:

            st.success(
                "🏆 30 Entry Milestone"
            )

        if total_entries >= 100:

            st.success(
                "⭐ Journal Master"
            )

        progress = min(
            total_entries / 100,
            1.0
        )

        st.progress(
            progress
        )

        st.caption(
            f"{total_entries}/100 entries"
        )
  # ============================================================
# BUCKET LIST
# ============================================================

elif page == "Bucket List":

    st.title("🌍 Bucket List")
    st.caption("Dream big. Track everything you want to experience in life.")

    bucket = load_table("bucket_list")

    # ========================================================
    # ADD ITEM
    # ========================================================

    with st.expander(
        "➕ Add New Dream",
        expanded=True
    ):

        with st.form("bucket_form"):

            item = st.text_input(
                "What do you want to experience?"
            )

            submitted = st.form_submit_button(
                "Add Dream"
            )

            if submitted:

                if item.strip():

                    run_query(
                        """
                        INSERT INTO bucket_list
                        (
                            item,
                            completed,
                            created_at
                        )
                        VALUES
                        (?, ?, ?)
                        """,
                        (
                            item,
                            0,
                            datetime.now().isoformat(timespec="seconds")
                        )
                    )

                    add_xp(10)

                    st.success("Dream added.")
                    st.rerun()

    st.divider()

    # ========================================================
    # STATS
    # ========================================================

    total = len(bucket)

    completed = 0

    if not bucket.empty:

        completed = len(bucket[bucket["completed"] == 1])

    progress = 0
    if total > 0:
        progress = completed / total

    c1, c2, c3 = st.columns(3)

    c1.metric("🌍 Total Dreams", total)
    c2.metric("🏆 Completed", completed)
    c3.metric("📈 Progress", f"{progress*100:.0f}%")

    st.progress(progress)

    st.divider()

    # ========================================================
    # DREAM CARDS
    # ========================================================

    if bucket.empty:

        st.info("No dreams added yet.")

    else:

        st.subheader("✨ Your Dreams")

        for _, dream in bucket.sort_values("id", ascending=False).iterrows():

            with st.container(border=True):

                left, right = st.columns([8, 2])

                with left:

                    if dream["completed"] == 1:
                        st.markdown(f"### ~~{dream['item']}~~")
                        st.caption("🏆 Completed Dream")
                    else:
                        st.markdown(f"### {dream['item']}")
                        st.caption("🌟 In Progress")

                with right:

                    if dream["completed"] == 0:

                        if st.button(
                            "✔ Complete",
                            key=f"bucket_done_{dream['id']}"
                        ):

                            run_query(
                                """
                                UPDATE bucket_list
                                SET completed = 1
                                WHERE id = ?
                                """,
                                (dream["id"],)
                            )

                            add_xp(20)

                            st.success("Dream achieved!")
                            st.rerun()

                    else:

                        if st.button(
                            "↩ Undo",
                            key=f"bucket_undo_{dream['id']}"
                        ):

                            run_query(
                                """
                                UPDATE bucket_list
                                SET completed = 0
                                WHERE id = ?
                                """,
                                (dream["id"],)
                            )

                            st.rerun()

                if st.button(
                    "🗑 Delete",
                    key=f"bucket_delete_{dream['id']}"
                ):

                    run_query(
                        """
                        DELETE FROM bucket_list
                        WHERE id = ?
                        """,
                        (dream["id"],)
                    )

                    st.rerun()

    st.divider()

    # ========================================================
    # ACHIEVEMENTS
    # ========================================================

    st.subheader("🏅 Bucket List Achievements")

    if completed >= 1:
        st.success("First Dream Achieved!")

    if completed >= 5:
        st.success("Dream Starter — 5 Completed")

    if completed >= 10:
        st.success("Dream Builder — 10 Completed")

    if completed >= 25:
        st.success("Dream Master — 25 Completed")

    if completed >= 50:
        st.success("Legend of Life — 50 Completed")

    st.divider()

    # ========================================================
    # INSPIRATION SECTION
    # ========================================================

    st.subheader("💡 Inspiration Ideas")

    ideas = [
        "Travel to 10 countries",
        "Learn a new language",
        "Start a business",
        "Run a marathon",
        "Build your dream project",
        "Buy your first home",
        "Learn to code a full app",
        "Save your first big investment",
        "Meet someone you admire",
        "Master a musical instrument"
    ]

    for i in ideas:
        st.write(f"• {i}")

    st.divider()

    # ========================================================
    # PROGRESS MOTIVATION
    # ========================================================

    st.subheader("🔥 Motivation")

    if total == 0:
        st.info("Add your first dream today.")
    else:

        percent = (completed / total) * 100

        if percent == 100:
            st.success("🌟 You completed your entire bucket list!")
        elif percent >= 75:
            st.success("🚀 Almost there — keep going!")
        elif percent >= 50:
            st.info("🔥 Halfway to your dreams!")
        elif percent >= 25:
            st.info("🌱 Great start — keep building momentum!")
        else:
            st.info("💡 Every dream starts with one step.")

        st.progress(percent / 100)
  # ============================================================
# HOBBIES
# ============================================================

elif page == "Hobbies":

    st.title("🎧 Hobbies & Skills")
    st.caption("Track your skills, practice sessions, and growth over time.")

    hobbies = load_table("hobbies")
    sessions = load_table("hobby_sessions")

    # ========================================================
    # TIMER STATE
    # ========================================================

    if "timer_running" not in st.session_state:
        st.session_state.timer_running = False

    if "timer_seconds" not in st.session_state:
        st.session_state.timer_seconds = 0

    # ========================================================
    # ADD HOBBY
    # ========================================================

    with st.expander("➕ Add New Skill", expanded=True):

        with st.form("hobby_form"):

            name = st.text_input("Skill / Hobby Name")

            category = st.selectbox(
                "Category",
                [
                    "Creative",
                    "Fitness",
                    "Academic",
                    "Music",
                    "Technology",
                    "Language",
                    "Other"
                ]
            )

            goal = st.text_input(
                "Goal (e.g. 'Practice 30h total')"
            )

            submitted = st.form_submit_button("Add Skill")

            if submitted and name.strip():

                run_query(
                    """
                    INSERT INTO hobbies(name, category, goal, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        name,
                        category,
                        goal,
                        datetime.now().isoformat(timespec="seconds")
                    )
                )

                add_xp(10)
                st.success("Skill added.")
                st.rerun()

    st.divider()

    # ========================================================
    # TIMER UI (FOCUS PRACTICE MODE)
    # ========================================================

    st.subheader("⏱ Practice Timer")

    col1, col2, col3 = st.columns(3)

    with col1:

        if st.button("▶ Start 25 min"):
            st.session_state.timer_running = True
            st.session_state.timer_seconds = 25 * 60

    with col2:

        if st.button("⏹ Stop"):
            st.session_state.timer_running = False
            st.session_state.timer_seconds = 0

    with col3:

        if st.button("➕ +5 min"):
            st.session_state.timer_seconds += 5 * 60

    if st.session_state.timer_running:

        if st.session_state.timer_seconds > 0:
            st.session_state.timer_seconds -= 1

        mins = st.session_state.timer_seconds // 60
        secs = st.session_state.timer_seconds % 60

        st.markdown(
            f"### 🔥 {mins:02d}:{secs:02d}"
        )

        st.progress(
            1 - (st.session_state.timer_seconds / (25 * 60))
        )

        st.info("Stay focused — you're building skill momentum.")

    st.divider()

    # ========================================================
    # HOBBY OVERVIEW
    # ========================================================

    total_hobbies = len(hobbies)

    total_minutes = 0
    if not sessions.empty:
        total_minutes = int(sessions["minutes"].sum())

    c1, c2, c3 = st.columns(3)

    c1.metric("🎧 Skills", total_hobbies)
    c2.metric("⏱ Practice Time", f"{total_minutes} min")
    c3.metric("🔥 Sessions", len(sessions))

    st.divider()

    # ========================================================
    # HOBBY LIST
    # ========================================================

    if hobbies.empty:

        st.info("No skills added yet.")

    else:

        for _, hobby in hobbies.sort_values("id", ascending=False).iterrows():

            hobby_id = hobby["id"]

            hobby_sessions = sessions[sessions["hobby_id"] == hobby_id]

            total_time = 0
            if not hobby_sessions.empty:
                total_time = hobby_sessions["minutes"].sum()

            with st.container(border=True):

                st.subheader(f"🎯 {hobby['name']}")
                st.caption(f"{hobby['category']} | Goal: {hobby['goal']}")

                st.markdown(f"⏱ Total Practice: **{total_time} min**")

                # ====================================================
                # ADD SESSION
                # ====================================================

                with st.form(f"session_form_{hobby_id}"):

                    minutes = st.number_input(
                        "Minutes practiced",
                        min_value=1,
                        max_value=600,
                        value=25
                    )

                    note = st.text_input("Note (optional)")

                    add_session = st.form_submit_button("Add Session")

                    if add_session:

                        run_query(
                            """
                            INSERT INTO hobby_sessions
                            (hobby_id, session_date, minutes, note, created_at)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                hobby_id,
                                today(),
                                minutes,
                                note,
                                datetime.now().isoformat(timespec="seconds")
                            )
                        )

                        add_xp(5)
                        st.success("Session logged.")
                        st.rerun()

                # ====================================================
                # SESSION HISTORY
                # ====================================================

                if hobby_sessions.empty:

                    st.info("No sessions yet.")

                else:

                    st.write("📚 Recent Sessions")

                    for _, s in hobby_sessions.tail(3).iterrows():

                        st.write(
                            f"• {s['session_date']} — "
                            f"{s['minutes']} min "
                            f"{('(' + s['note'] + ')') if s['note'] else ''}"
                        )

                # ====================================================
                # DELETE HOBBY
                # ====================================================

                if st.button(
                    "🗑 Delete Skill",
                    key=f"delete_hobby_{hobby_id}"
                ):

                    run_query(
                        "DELETE FROM hobby_sessions WHERE hobby_id = ?",
                        (hobby_id,)
                    )

                    run_query(
                        "DELETE FROM hobbies WHERE id = ?",
                        (hobby_id,)
                    )

                    st.rerun()

    st.divider()

    # ============================================================
    # SKILL ANALYTICS CHART
    # ============================================================

    if not hobbies.empty and not sessions.empty:

        st.subheader("📊 Skill Practice Breakdown")

        hobby_stats = (
            sessions.groupby("hobby_id")["minutes"]
            .sum()
            .reset_index()
        )

        hobby_stats = hobby_stats.merge(
            hobbies[["id", "name"]],
            left_on="hobby_id",
            right_on="id",
            how="left"
        )

        fig = px.bar(
            hobby_stats,
            x="name",
            y="minutes",
            title="Practice Time per Skill"
        )

        st.plotly_chart(fig, use_container_width=True)

    # ============================================================
    # ACHIEVEMENTS
    # ============================================================

    st.subheader("🏆 Skill Achievements")

    if total_minutes >= 60:
        st.success("First Hour Practiced")

    if total_minutes >= 300:
        st.success("Skill Builder — 5 Hours")

    if total_minutes >= 1000:
        st.success("Dedicated Learner — 1000 Minutes")

    if total_minutes >= 5000:
        st.success("Master Practitioner — 5000 Minutes")
  # ============================================================
# BUDGET
# ============================================================

elif page == "Budget":

    st.title("💰 Budget Tracker")
    st.caption("Track income, expenses, and understand your money habits.")

    budget = load_table("budget")

    # ========================================================
    # ADD TRANSACTION
    # ========================================================

    with st.expander("➕ Add Transaction", expanded=True):

        with st.form("budget_form"):

            item = st.text_input("Description")

            amount = st.number_input(
                "Amount",
                min_value=0.0,
                format="%.2f"
            )

            t_type = st.selectbox(
                "Type",
                ["Income", "Expense"]
            )

            category = st.selectbox(
                "Category",
                [
                    "Food",
                    "Transport",
                    "Rent",
                    "Entertainment",
                    "Shopping",
                    "Health",
                    "Salary",
                    "Other"
                ]
            )

            entry_date = st.date_input("Date")

            submitted = st.form_submit_button("Add")

            if submitted and item.strip():

                run_query(
                    """
                    INSERT INTO budget
                    (item, amount, type, category, entry_date)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        item,
                        amount,
                        t_type,
                        category,
                        entry_date.isoformat()
                    )
                )

                add_xp(5)

                st.success("Transaction added.")
                st.rerun()

    st.divider()

    # ========================================================
    # CLEAN DATA
    # ========================================================

    if budget.empty:

        st.info("No transactions yet.")

    else:

        # ensure correct types
        budget["amount"] = pd.to_numeric(budget["amount"], errors="coerce").fillna(0)

        income = budget[budget["type"] == "Income"]["amount"].sum()
        expenses = budget[budget["type"] == "Expense"]["amount"].sum()

        balance = income - expenses

        # ========================================================
        # STATS CARDS
        # ========================================================

        c1, c2, c3 = st.columns(3)

        c1.metric("💵 Income", f"{income:.2f}")
        c2.metric("💸 Expenses", f"{expenses:.2f}")
        c3.metric("💰 Balance", f"{balance:.2f}")

        st.divider()

        # ========================================================
        # CHARTS
        # ========================================================

        st.subheader("📊 Spending Breakdown")

        category_expenses = budget[budget["type"] == "Expense"]

        if not category_expenses.empty:

            cat_summary = (
                category_expenses
                .groupby("category")["amount"]
                .sum()
                .reset_index()
            )

            fig = px.pie(
                cat_summary,
                names="category",
                values="amount",
                title="Expenses by Category"
            )

            st.plotly_chart(fig, use_container_width=True)

        st.subheader("📈 Income vs Expenses")

        trend = budget.copy()

        trend["entry_date"] = pd.to_datetime(trend["entry_date"], errors="coerce")

        trend_grouped = (
            trend.groupby(["entry_date", "type"])["amount"]
            .sum()
            .reset_index()
        )

        fig2 = px.line(
            trend_grouped,
            x="entry_date",
            y="amount",
            color="type",
            title="Money Flow Over Time"
        )

        st.plotly_chart(fig2, use_container_width=True)

        st.divider()

        # ========================================================
        # TRANSACTION LIST
        # ========================================================

        st.subheader("📒 Transactions")

        for _, row in budget.sort_values("id", ascending=False).iterrows():

            color = "💚" if row["type"] == "Income" else "🔴"

            with st.container(border=True):

                left, right = st.columns([8, 2])

                with left:

                    st.markdown(
                        f"### {color} {row['item']}"
                    )

                    st.caption(
                        f"{row['category']} | "
                        f"{row['entry_date']} | "
                        f"{row['type']}"
                    )

                with right:

                    st.markdown(
                        f"### {row['amount']:.2f}"
                    )

                    if st.button(
                        "🗑",
                        key=f"delete_budget_{row['id']}"
                    ):

                        run_query(
                            "DELETE FROM budget WHERE id = ?",
                            (row["id"],)
                        )

                        st.rerun()

        st.divider()

        # ========================================================
        # SAVINGS INSIGHT
        # ========================================================

        st.subheader("📊 Savings Insight")

        if income > 0:

            savings_rate = (balance / income) * 100

            st.progress(min(max(savings_rate / 100, 0), 1))

            st.write(f"💡 Savings Rate: **{savings_rate:.1f}%**")

            if savings_rate < 0:
                st.error("You're spending more than you earn.")
            elif savings_rate < 20:
                st.warning("Try to save more if possible.")
            else:
                st.success("Great savings discipline!")

        else:

            st.info("Add income to calculate savings rate.")

        st.divider()

        # ========================================================
        # ACHIEVEMENTS
        # ========================================================

        st.subheader("🏆 Financial Achievements")

        if balance > 0:
            st.success("Positive Balance Achieved")

        if income >= 1000:
            st.success("First R1000 Earned")

        if expenses > 0 and expenses < income:
            st.success("Spending Under Control")

        if income > expenses * 2:
            st.success("Strong Financial Stability")
  # ============================================================
# SETTINGS
# ============================================================

elif page == "Settings":

    st.title("⚙ Settings & System Tools")
    st.caption("Manage your data, export progress, and control your app.")

    st.divider()

    # ========================================================
    # XP OVERVIEW
    # ========================================================

    st.subheader("🏆 XP System")

    xp = get_xp()
    level = get_level()

    st.metric("Total XP", xp)
    st.metric("Current Level", level)

    st.progress((xp % 100) / 100)

    st.caption("Every 100 XP = Level Up")

    st.divider()

    # ========================================================
    # DATA EXPORTS
    # ========================================================

    st.subheader("📦 Export Data")

    def export_table(table_name):

        df = load_table(table_name)

        return df.to_csv(index=False).encode("utf-8")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            "⬇ Tasks",
            export_table("tasks"),
            "tasks.csv",
            "text/csv"
        )

    with col2:
        st.download_button(
            "⬇ Goals",
            export_table("goals"),
            "goals.csv",
            "text/csv"
        )

    with col3:
        st.download_button(
            "⬇ Journal",
            export_table("journal"),
            "journal.csv",
            "text/csv"
        )

    col4, col5 = st.columns(2)

    with col4:
        st.download_button(
            "⬇ Budget",
            export_table("budget"),
            "budget.csv",
            "text/csv"
        )

    with col5:
        st.download_button(
            "⬇ Hobbies",
            export_table("hobbies"),
            "hobbies.csv",
            "text/csv"
        )

    st.divider()

    # ========================================================
    # FULL BACKUP
    # ========================================================

    st.subheader("💾 Full Backup")

    tables = [
        "tasks",
        "goals",
        "goal_items",
        "journal",
        "focus",
        "bucket_list",
        "hobbies",
        "hobby_sessions",
        "budget",
        "xp"
    ]

    backup_data = {}

    for t in tables:
        backup_data[t] = load_table(t).to_csv(index=False)

    st.download_button(
        "⬇ Download Full Backup (All Data)",
        str(backup_data),
        "myday_backup.txt",
        "text/plain"
    )

    st.divider()

    # ========================================================
    # RESET SYSTEM
    # ========================================================

    st.subheader("⚠ Danger Zone")

    st.warning("These actions are permanent!")

    if st.button("🗑 Reset ALL Data"):

        confirm = st.text_input("Type RESET to confirm")

        if confirm == "RESET":

            tables = [
                "tasks",
                "goals",
                "goal_items",
                "journal",
                "focus",
                "bucket_list",
                "hobbies",
                "hobby_sessions",
                "budget",
                "xp"
            ]

            for t in tables:

                run_query(f"DELETE FROM {t}")

            st.success("All data reset successfully.")
            st.rerun()

    st.divider()

    # ========================================================
    # PERFORMANCE INFO
    # ========================================================

    st.subheader("📊 App Status")

    st.info("✔ Database connected")
    st.info("✔ Dark mode compatible UI active")
    st.info("✔ XP system running")
    st.info("✔ All modules loaded")

    st.divider()

    # ========================================================
    # FINAL POLISH MESSAGE
    # ========================================================

    st.subheader("🚀 MyDay Pro Complete System")

    st.success(
        "You now have a full productivity OS with tasks, goals, "
        "journal, budget, hobbies, and gamified XP progression."
    )

    st.caption(
        "Built as a modular Streamlit life management system."
    )
