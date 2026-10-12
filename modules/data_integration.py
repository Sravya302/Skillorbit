
import csv
import json
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database import create_table, get_connection

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

# Extra dashboard fields are optional.
JSON_FIELDS = {
    "spoken_languages",
    "certifications",
    "internships",
    "soft_skills",
}

OPTIONAL_FIELDS = [
    "batch",
    "status",
    "cgpa",
    "percentage",
    "email",
    "spoken_languages",
    "certifications",
    "internships",
    "soft_skills",
    "linkedin",
    "github",
    "success_score",
    "risk_flag",
]


def parse_list(value):
    """Accept a semicolon-separated list or a JSON list."""
    value = (value or "").strip()

    if not value:
        return []

    if value.startswith("["):
        try:
            result = json.loads(value)
            if isinstance(result, list):
                return [
                    str(item).strip()
                    for item in result
                    if str(item).strip()
                ]
        except json.JSONDecodeError:
            pass

    return [
        item.strip()
        for item in value.split(";")
        if item.strip()
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
    cleaned["skills"] = ";".join(parse_list(cleaned["skills"]))

    for field in OPTIONAL_FIELDS:
        cleaned[field] = (row.get(field) or "").strip()

    # Validate optional numeric fields only when provided.
    for field in ("cgpa", "percentage", "success_score"):
        value = cleaned[field]
        if value:
            try:
                number = float(value)
                if field == "cgpa" and not 0 <= number <= 10:
                    raise ValueError
                if field in ("percentage", "success_score") and not 0 <= number <= 100:
                    raise ValueError
                cleaned[field] = number
            except ValueError:
                return None, (
                    f"Row {line_number}: {field} must be "
                    + ("0-10" if field == "cgpa" else "0-100")
                )
        else:
            cleaned[field] = None

    # Store list fields as JSON so SQLite can retain each item.
    for field in JSON_FIELDS:
        cleaned[field] = json.dumps(parse_list(cleaned[field]))

    return cleaned, None


def import_students():
    if not CSV_FILE.exists():
        raise FileNotFoundError(f"CSV file not found: {CSV_FILE}")

    create_table()

    imported = 0
    skipped = 0
    seen_ids = set()

    columns = REQUIRED_COLUMNS + OPTIONAL_FIELDS
    placeholders = ", ".join("?" for _ in columns)
    column_sql = ", ".join(columns)
    update_sql = ", ".join(
        f"{column} = excluded.{column}"
        for column in columns
        if column != "student_id"
    )

    with CSV_FILE.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("CSV file is empty or has no header")

        reader.fieldnames = [name.strip() for name in reader.fieldnames]

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

                values = []
                for column in columns:
                    value = student.get(column)

                    # An older CSV has no extra fields. Preserve the
                    # existing database value rather than erasing it.
                    if column in OPTIONAL_FIELDS and not value:
                        value = None

                    values.append(value)

                # Use COALESCE on optional values so importing an old CSV
                # won't overwrite existing extra dashboard information.
                optional_updates = ", ".join(
                    f"{column} = COALESCE(excluded.{column}, students.{column})"
                    for column in OPTIONAL_FIELDS
                )
                safe_update_sql = ", ".join([
                    ", ".join(
                        f"{column} = excluded.{column}"
                        for column in REQUIRED_COLUMNS
                        if column != "student_id"
                    ),
                    optional_updates,
                ])

                try:
                    conn.execute(
                        f"""
                        INSERT INTO students ({column_sql})
                        VALUES ({placeholders})
                        ON CONFLICT(student_id) DO UPDATE SET
                            {safe_update_sql}
                        """,
                        values,
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
