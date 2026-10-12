
import json
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, send_from_directory

from database import create_table, get_connection
from modules.success_score import calculate_success_score
from modules.risk_flags import identify_risk
PROJECT_ROOT = Path(__file__).resolve().parent
DASHBOARDS_DIR = PROJECT_ROOT / "dashboards"

app = Flask(__name__)


def parse_list(value):
    """Convert stored JSON lists or semicolon-separated text into lists."""
    if not value:
        return []

    try:
        result = json.loads(value)
        if isinstance(result, list):
            return result
    except (json.JSONDecodeError, TypeError):
        pass

    return [
        item.strip()
        for item in str(value).split(";")
        if item.strip()
    ]


@app.get("/")
def home():
    return jsonify({
        "message": "SkillOrbit API is running",
        "students_endpoint": "/api/students",
    })


@app.get("/api/students")
def get_students():
    create_table()

    with get_connection() as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute("""
            SELECT *
            FROM students
            ORDER BY student_id
        """).fetchall()

    students = []

    for row in rows:
        student = dict(row)

        # Core student details
        student["id"] = student["student_id"]
        student["roll"] = student["student_id"]
        student["rollId"] = student["student_id"]
        student["branch"] = student["department"]
        student["batch"] = (
            student.get("batch")
            or {
                1: "1st Year",
                2: "2nd Year",
                3: "3rd Year",
                4: "Final Year",
            }.get(student["year"], "")
        )

        # Skills and dashboard arrays
        student["softwareSkills"] = parse_list(student.get("skills"))
        student["spokenLanguages"] = parse_list(
            student.get("spoken_languages")
        )
        student["certifications"] = parse_list(
            student.get("certifications")
        )
        student["internships"] = parse_list(
            student.get("internships")
        )
        student["softSkills"] = parse_list(
            student.get("soft_skills")
        )

        # Keep both database and dashboard field names available.
        # Calculate analytics for the API response.
        score = calculate_success_score(
            student["attendance"],
            student["marks"],
        )
        risk = identify_risk(
            student["attendance"],
            student["marks"],
        )

        student["success_score"] = score
        student["successScore"] = score

        student["risk_flag"] = risk["risk_flag"]
        student["riskFlag"] = risk["risk_flag"]
        student["riskReasons"] = risk["reasons"]

        student["cgpaVal"] = student.get("cgpa")
        # Do not invent missing academic or contact information.
        student["status"] = student.get("status") or "Current Student"
        student["email"] = student.get("email") or ""
        student["linkedin"] = student.get("linkedin") or ""
        student["github"] = student.get("github") or ""

        students.append(student)

    return jsonify(students)


@app.get("/dashboards/<path:filename>")
def dashboard(filename):
    return send_from_directory(DASHBOARDS_DIR, filename)


if __name__ == "__main__":
    create_table()
    app.run(debug=True)


