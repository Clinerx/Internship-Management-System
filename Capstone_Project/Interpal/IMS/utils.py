# utils.py

from .models import Internship, CustomUser

def calculate_matching_score(user, internship):
    # Extract required skills for internship and student skills
    required_skills = set(internship.required_skills_list())
    user_skills = set(user.skills_list())

    # Calculate skill match (percentage of required skills that the user has)
    skill_match = len(required_skills.intersection(user_skills)) / len(required_skills) if required_skills else 0

    # Calculate experience match (whether the user meets the desired experience)
    experience_match = min(user.experience, internship.desired_experience) / internship.desired_experience if internship.desired_experience else 1

    # Calculate overall compatibility score (could be weighted based on importance)
    total_score = (skill_match + experience_match) / 2  # Average the two scores (you can adjust this formula as needed)

    return total_score

def get_matching_internships(user):
    internships = Internship.objects.all()
    matches = []

    for internship in internships:
        # Calculate compatibility score for each internship
        score = calculate_matching_score(user, internship)
        matches.append((internship, score))

    # Sort by highest score
    matches.sort(key=lambda x: x[1], reverse=True)

    # Return the top 8 matches (you can adjust the number of matches shown)
    return matches[:8]
