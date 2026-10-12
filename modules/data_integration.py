
import csv
import sqlite3
from pathlib import Path

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database import create_table, get_connection

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_FILE = PROJECT_ROOT / "data" / "demo_students.csv"

REQUIRED_COLUMNS = [
    "student_id",
    "name",
    "department",
    "year",
    "attendance",
    "marks",
    "skills",
]


def validate_student(row, line_number):
    """Clean and validate one student record."""
    cleaned = {
        key: (row.get(key) or "").strip()
        for key in REQUIRED_COLUMNS
    }

    errors = []

    for field in ("student_id", "name", "department"):
        if not cleaned[field]:
            errors.append(f"Missing {field}")

    try:
        year = int(cleaned["year"])
        if year not in (1, 2, 3, 4):
            errors.append("Year must be between 1 and 4")
    except ValueError:
        year = None
        errors.append("Year must be a whole number")

    try:
        attendance = float(cleaned["attendance"])
        if not 0 <= attendance <= 100:
            errors.append("Attendance must be 0-100")
    except ValueError:
        attendance = None
        errors.append("Invalid attendance")

    try:
        marks = float(cleaned["marks"])
        if not 0 <= marks <= 100:
            errors.append("Marks must be 0-100")
    except ValueError:
        marks = None
        errors.append("Invalid marks")

    if errors:
        return None, f"Row {line_number}: " + ", ".join(errors)

    cleaned["year"] = year
    cleaned["attendance"] = attendance
    cleaned["marks"] = marks
    cleaned["skills"] = ";".join(
        skill.strip()
        for skill in cleaned["skills"].split(";")
        if skill.strip()
    )

    return cleaned, None


def import_students():
    if not CSV_FILE.exists():
        raise FileNotFoundError(f"CSV file not found: {CSV_FILE}")

    create_table()

    imported = 0
    skipped = 0
    seen_ids = set()

    with CSV_FILE.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("CSV file is empty or has no header")

        reader.fieldnames = [
            name.strip() for name in reader.fieldnames
        ]

        missing = set(REQUIRED_COLUMNS) - set(reader.fieldnames)
        if missing:
            raise ValueError(
                f"CSV is missing columns: {', '.join(sorted(missing))}"
            )

        with get_connection() as conn:
            for line_number, row in enumerate(reader, start=2):
                student, error = validate_student(row, line_number)

                if error:
                    print("SKIPPED:", error)
                    skipped += 1
                    continue

                student_id = student["student_id"]

                if student_id in seen_ids:
                    print(f"SKIPPED: Duplicate ID {student_id}")
                    skipped += 1
                    continue

                seen_ids.add(student_id)

                try:
                    conn.execute(
                        """
                        INSERT INTO students
                        (student_id, name, department, year,
                         attendance, marks, skills)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(student_id) DO UPDATE SET
                            name = excluded.name,
                            department = excluded.department,
                            year = excluded.year,
                            attendance = excluded.attendance,
                            marks = excluded.marks,
                            skills = excluded.skills
                        """,
                        (
                            student["student_id"],
                            student["name"],
                            student["department"],
                            student["year"],
                            student["attendance"],
                            student["marks"],
                            student["skills"],
                        ),
                    )
                    imported += 1
                except sqlite3.Error as exc:
                    print(f"SKIPPED: {student_id}: {exc}")
                    skipped += 1

    print("\n--- SkillOrbit Import Report ---")
    print(f"Imported or updated: {imported}")
    print(f"Skipped: {skipped}")
    print("Data integration finished!")


if __name__ == "__main__":
    import_students()
