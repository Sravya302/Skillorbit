
"""Calculate explainable student success scores for SkillOrbit."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database import create_table, get_connection


def calculate_success_score(attendance, marks):
    """
    Calculate a score from 0 to 100.

    Attendance contributes 30%.
    Marks contribute 70%.
    """
    attendance = float(attendance)
    marks = float(marks)

    if not 0 <= attendance <= 100:
        raise ValueError("Attendance must be between 0 and 100.")

    if not 0 <= marks <= 100:
        raise ValueError("Marks must be between 0 and 100.")

    score = (attendance * 0.30) + (marks * 0.70)
    return round(score, 2)


def calculate_all_student_scores():
    """Calculate scores for every student currently in the database."""
    create_table()

    with get_connection() as conn:
        students = conn.execute("""
            SELECT student_id, name, attendance, marks
            FROM students
            ORDER BY student_id
        """).fetchall()

    results = []

    for student_id, name, attendance, marks in students:
        score = calculate_success_score(attendance, marks)

        results.append({
            "student_id": student_id,
            "name": name,
            "attendance": attendance,
            "marks": marks,
            "success_score": score,
        })

    return results


if __name__ == "__main__":
    for student in calculate_all_student_scores():
        print(
            f"{student['student_id']} | "
            f"{student['name']} | "
            f"Success Score: {student['success_score']}"
        )
