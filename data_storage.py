import sqlite3
from datetime import datetime

DB_NAME = "temperature_feedback.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_code TEXT,
        person_index INTEGER,
        sex TEXT,
        age_group TEXT,
        temp INTEGER,
        recommended_temp INTEGER,
        feels TEXT,
        clothes TEXT,
        activity TEXT,
        position TEXT,
        weight REAL,
        feedback TEXT,
        timestamp TEXT
    )
    """)

    conn.commit()
    conn.close()


def save_feedback_to_db(code, person_index, user, best_temp, feedback):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO feedback_logs (
        room_code,
        person_index,
        sex,
        age_group,
        temp,
        recommended_temp,
        feels,
        clothes,
        activity,
        position,
        weight,
        feedback,
        timestamp
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        code,
        person_index,
        user["sex"],
        user["age_group"],
        user["temp"],
        best_temp,
        user["feels"],
        user["clothes"],
        user["activity"],
        user["position"],
        user["weight"],
        feedback,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()