# utils.py

from .models import Internship, CustomUser
def calculate_compatibility(student, internship):
    """
    Calculate the compatibility score between a student and an internship.

    :param student: CustomUser instance representing the student.
    :param internship: Internship instance.
    :return: Compatibility score (float).
    """
    # Skill Match Score
    student_skills = set(student.skills_list())  # Convert student skills to a set
    internship_skills = set(internship.required_skills_list())  # Convert required skills to a set

    if not internship_skills:
        skill_match_score = 0
    else:
        matching_skills = student_skills.intersection(internship_skills)
        skill_match_score = len(matching_skills) / len(internship_skills) * 100

    # Experience Match Score
    required_experience = internship.required_experience if hasattr(internship, 'required_experience') else 0
    student_experience = student.experience if student.experience else 0

    experience_match_score = min(student_experience / required_experience, 1) * 100 if required_experience > 0 else 100

    # Location Match Score (Optional: Add location matching logic if needed)
    location_match_score = 100  # Assuming it's not considered or always matches.

    # Weighted Compatibility Score
    compatibility_score = (
        (skill_match_score * 0.5) +
        (experience_match_score * 0.3) +
        (location_match_score * 0.2)
    )

    return round(compatibility_score, 2)  # Return a rounded score


def get_matching_internships(student):
    """
    Get recommended internships for a student based on the matching algorithm.

    :param student: CustomUser instance representing the student.
    :return: List of tuples (internship, compatibility_score), sorted by score.
    """
    internships = Internship.objects.all()  # Fetch all internships
    recommendations = []

    for internship in internships:
        compatibility_score = calculate_compatibility(student, internship)
        recommendations.append((internship, compatibility_score))

    # Sort internships by compatibility score in descending order
    recommendations.sort(key=lambda x: x[1], reverse=True)

    return recommendations
