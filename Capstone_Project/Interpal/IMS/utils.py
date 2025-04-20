import math

def calculate_cosine_similarity(student, internship):
    """
    Calculates a similarity score using cosine similarity between a student and an internship.
    """

    def vectorize_skills(student_skills, internship_skills):
        """Create binary vectors for skills."""
        all_skills = set(student_skills) | set(internship_skills)  # Union of all skills
        student_vector = [1 if skill in student_skills else 0 for skill in all_skills]
        internship_vector = [1 if skill in internship_skills else 0 for skill in all_skills]
        return student_vector, internship_vector

    def cosine_similarity(vec1, vec2):
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a ** 2 for a in vec1))
        magnitude2 = math.sqrt(sum(b ** 2 for b in vec2))
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0  # Avoid division by zero
        return dot_product / (magnitude1 * magnitude2)

    def normalize_experience(exp, max_exp):
        """Normalize experience to a scale of 0 to 1."""
        return exp / max_exp if max_exp > 0 else 0

    # Extract and clean skills
    student_skills = set(skill.strip().lower() for skill in (student.skills or '').split(',') if skill.strip())
    internship_skills = set(skill.strip().lower() for skill in (internship.required_skills or '').split(',') if skill.strip())

    # Vectorize skills
    student_skill_vector, internship_skill_vector = vectorize_skills(student_skills, internship_skills)

    # Calculate skill similarity
    skill_similarity = cosine_similarity(student_skill_vector, internship_skill_vector)

    # College similarity (binary: match = 1, no match = 0)
    college_similarity = 1.0 if student.college == internship.preferred_college else 0.0

    # Course similarity (binary: match = 1, no match = 0)
    course_similarity = 1.0 if student.course == internship.preferred_course else 0.0

    # If neither college nor course aligns, exclude this internship
    if college_similarity == 0.0 and course_similarity == 0.0:
        return 0.0

    # Experience similarity (scaled and treated as a single-dimension vector)
    student_exp = student.experience or 0
    internship_exp = internship.required_experience or 0
    normalized_student_exp = normalize_experience(student_exp, max(student_exp, internship_exp))
    normalized_internship_exp = normalize_experience(internship_exp, max(student_exp, internship_exp))
    experience_similarity = cosine_similarity([normalized_student_exp], [normalized_internship_exp])

    # Combine similarities with weights
    weights = {
        'skills': 0.4,
        'college': 0.3,
        'course': 0.2,
        'experience': 0.1
    }

    overall_similarity = (
        weights['skills'] * skill_similarity +
        weights['college'] * college_similarity +
        weights['course'] * course_similarity +
        weights['experience'] * experience_similarity
    )

    # Scale the score to range 50-100
    final_score = 50 + overall_similarity * 50

    # Ensure strong scores for college and course alignment
    if college_similarity == 1.0 and course_similarity == 1.0:
        final_score = max(final_score, 80)  # Boost for full alignment

    return round(final_score, 2)

