
"""Summarize student performance trends for SkillOrbit."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database import create_table, get_connection
from modules.success_score import calculate_success_score


def get_performance_trends():
    create_table()

    with get_connection() as conn:
        students = conn.execute("""
            SELECT student_id, name, department, year,
                   attendance, marks
            FROM students
            ORDER BY student_id
        """).fetchall()

    if not students:
        return {
            "student_count": 0,
            "average_attendance": 0,
            "average_marks": 0,
            "average_success_score": 0,
            "department_averages": {},
        }

    department_scores = {}
    scores = []
    attendance_values = []
    marks_values = []

    for student_id, name, department, year, attendance, marks in students:
        score = calculate_success_score(attendance, marks)
        scores.append(score)
        attendance_values.append(attendance)
        marks_values.append(marks)

        department_scores.setdefault(department, []).append(score)

    department_averages = {
        department: round(sum(values) / len(values), 2)
        for department, values in department_scores.items()
    }

    return {
        "student_count": len(students),
        "average_attendance": round(
            sum(attendance_values) / len(attendance_values), 2
        ),
        "average_marks": round(sum(marks_values) / len(marks_values), 2),
        "average_success_score": round(sum(scores) / len(scores), 2),
        "department_averages": department_averages,
    }


if __name__ == "__main__":
    trends = get_performance_trends()

    print("=== SkillOrbit Performance Trends ===")
    print("Total students:", trends["student_count"])
    print("Average attendance:", trends["average_attendance"], "%")
    print("Average marks:", trends["average_marks"])
    print("Average success score:", trends["average_success_score"])

    print("\nAverage success score by department:")
    for department, average in trends["department_averages"].items():
        print(f"{department}: {average}")
