import sqlite3

DB_NAME = "skillorbit.db"


def get_connection():
    """Connect to the SkillOrbit SQLite database."""
    return sqlite3.connect(DB_NAME)


def create_table():
    """Create the students table if it doesn't exist."""
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


if __name__ == "__main__":
    create_table()
    print("SkillOrbit database and students table are ready!")