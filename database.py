
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DB_NAME = PROJECT_ROOT / "skillorbit.db"

# Existing columns are preserved. New columns are added safely.
NEW_COLUMNS = {
    "batch": "TEXT",
    "status": "TEXT",
    "cgpa": "REAL",
    "percentage": "REAL",
    "email": "TEXT",
    "spoken_languages": "TEXT NOT NULL DEFAULT '[]'",
    "certifications": "TEXT NOT NULL DEFAULT '[]'",
    "internships": "TEXT NOT NULL DEFAULT '[]'",
    "soft_skills": "TEXT NOT NULL DEFAULT '[]'",
    "linkedin": "TEXT",
    "github": "TEXT",
    "success_score": "REAL",
    "risk_flag": "TEXT",
}


def get_connection():
    """Connect to the project SQLite database."""
    return sqlite3.connect(DB_NAME)


def create_table():
    """Create the original students table if it doesn't exist."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                year INTEGER NOT NULL,
                attendance REAL NOT NULL,
                marks REAL NOT NULL,
                skills TEXT
            )
        """)

        existing = {
            row[1]
            for row in conn.execute("PRAGMA table_info(students)")
        }

        for column, definition in NEW_COLUMNS.items():
            if column not in existing:
                conn.execute(
                    f"ALTER TABLE students ADD COLUMN {column} {definition}"
                )


if __name__ == "__main__":
    create_table()
    print(f"Database ready: {DB_NAME}")
    print("Existing student records and columns have been preserved.")
