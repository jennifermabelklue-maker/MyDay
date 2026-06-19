import streamlit as st
import requests

API = "http://localhost:8000"

st.set_page_config(page_title="MyDay V4", layout="wide")

# ============================================================
# SESSION
# ============================================================

if "token" not in st.session_state:
    st.session_state.token = None


# ============================================================
# LOGIN / REGISTER
# ============================================================

if st.session_state.token is None:

    st.title("🚀 MyDay Pro V4")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login"):
            res = requests.post(API + "/login", json={
                "username": u,
                "password": p
            })

            if res.status_code == 200:
                st.session_state.token = res.json()["token"]
                st.rerun()
            else:
                st.error("Login failed")

    with tab2:
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")

        if st.button("Create"):
            requests.post(API + "/register", json={
                "username": nu,
                "password": np
            })
            st.success("Account created")

    st.stop()


# ============================================================
# APP
# ============================================================

st.sidebar.title("MyDay V4")

page = st.sidebar.radio("Menu", [
    "Dashboard",
    "Tasks"
])

token = st.session_state.token


# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":

    st.title("🏠 Dashboard")

    st.success("Connected to FastAPI backend")

# ============================================================
# TASKS
# ============================================================

elif page == "Tasks":

    st.title("Tasks")

    task = st.text_input("New Task")

    if st.button("Add Task"):

        requests.post(API + "/tasks", json={
            "title": task
        }, params={"token": token})

        st.rerun()

    res = requests.get(API + "/tasks", params={"token": token})

    if res.status_code == 200:
        for t in res.json()["tasks"]:
            st.write("•", t[1])