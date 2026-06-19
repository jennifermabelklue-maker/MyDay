from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import sqlite3
import hashlib
import jwt as jwt
from datetime import datetime, timedelta

# ============================================================
# CONFIG
# ============================================================

SECRET_KEY = "myday_secret_key_v4"
ALGORITHM = "HS256"

app = FastAPI(title="MyDay Pro V4 API")

DB = "myday_v4.db"

# ============================================================
# DB
# ============================================================

def conn():
    return sqlite3.connect(DB, check_same_thread=False)


def init_db():

    c = conn()
    cur = c.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        status TEXT DEFAULT 'open'
    )
    """)

    c.commit()
    c.close()


init_db()

# ============================================================
# SECURITY
# ============================================================

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()


def create_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except:
        return None


# ============================================================
# MODELS
# ============================================================

class User(BaseModel):
    username: str
    password: str


class Task(BaseModel):
    title: str


# ============================================================
# AUTH ROUTES
# ============================================================

@app.post("/register")
def register(user: User):

    c = conn()
    cur = c.cursor()

    try:
        cur.execute(
            "INSERT INTO users(username, password) VALUES (?, ?)",
            (user.username, hash_password(user.password))
        )
        c.commit()
    except:
        raise HTTPException(status_code=400, detail="User exists")

    return {"message": "created"}


@app.post("/login")
def login(user: User):

    c = conn()
    cur = c.cursor()

    cur.execute(
        "SELECT id FROM users WHERE username=? AND password=?",
        (user.username, hash_password(user.password))
    )

    result = cur.fetchone()

    if not result:
        raise HTTPException(status_code=401, detail="Invalid login")

    token = create_token(result[0])

    return {"token": token}


# ============================================================
# AUTH DEPENDENCY
# ============================================================

def get_user(token: str):

    data = decode_token(token)

    if not data:
        raise HTTPException(status_code=401, detail="Invalid token")

    return data["user_id"]


# ============================================================
# TASK ROUTES
# ============================================================

@app.post("/tasks")
def create_task(task: Task, token: str):

    user_id = get_user(token)

    c = conn()
    cur = c.cursor()

    cur.execute(
        "INSERT INTO tasks(user_id, title) VALUES (?, ?)",
        (user_id, task.title)
    )

    c.commit()

    return {"message": "task created"}


@app.get("/tasks")
def get_tasks(token: str):

    user_id = get_user(token)

    c = conn()
    cur = c.cursor()

    cur.execute(
        "SELECT id, title, status FROM tasks WHERE user_id=?",
        (user_id,)
    )

    return {"tasks": cur.fetchall()}

