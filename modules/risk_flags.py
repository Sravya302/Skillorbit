
"""Identify students who may need academic support."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database import create_table, get_connection


def identify_risk(attendance, marks):
    attendance = float(attendance)
    marks = float(marks)

    reasons = []

    if attendance < 60:
        reasons.append("Low attendance")

    if marks < 50:
        reasons.append("Low marks")

    if len(reasons) == 2:
        risk = "High"
    elif len(reasons) == 1:
        risk = "Medium"
    else:
        risk = "Low"

    return {"risk_flag": risk, "reasons": reasons}


def analyze_student_risks():
    create_table()

    with get_connection() as conn:
        students = conn.execute("""
            SELECT student_id, name, attendance, marks
            FROM students
            ORDER BY student_id
        """).fetchall()

    results = []

    for student_id, name, attendance, marks in students:
        assessment = identify_risk(attendance, marks)

        results.append({
            "student_id": student_id,
            "name": name,
            "attendance": attendance,
            "marks": marks,
            **assessment,
        })

    return results


if __name__ == "__main__":
    for student in analyze_student_risks():
        reasons = ", ".join(student["reasons"]) or "No risk indicators"
        print(
            f"{student['student_id']} | {student['name']} | "
            f"Risk: {student['risk_flag']} | {reasons}"
        )
