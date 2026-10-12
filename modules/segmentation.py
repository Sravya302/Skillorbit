
"""Group SkillOrbit students by their success scores."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.success_score import calculate_all_student_scores


def segment_student(score):
    if score >= 80:
        return "High Performer"
    elif score >= 60:
        return "Average Performer"
    else:
        return "Needs Support"


def get_student_segments():
    students = calculate_all_student_scores()

    for student in students:
        student["segment"] = segment_student(
            student["success_score"]
        )

    return students


if __name__ == "__main__":
    students = get_student_segments()

    for student in students:
        print(
            f"{student['student_id']} | {student['name']} | "
            f"Score: {student['success_score']} | "
            f"Group: {student['segment']}"
        )
