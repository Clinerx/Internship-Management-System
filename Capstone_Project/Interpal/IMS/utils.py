import re

def calculate_cosine_similarity(student, internship):
    """
    Calculates an optimized similarity score between a student and an internship.
    If internship skills or other details are invalid or nonsensical, assigns a low score.
    If the internship doesn't match the required criteria (course, college, and skills), assigns a 0% score.
    """
    
    def is_valid_skills(skills):
        """
        Validates the skills field to ensure it is not nonsensical.
        Criteria: Minimum length, presence of realistic skills, and no gibberish.
        """
        if not skills or len(skills.strip()) < 3:
            return False
        
        # Basic regex to check if the skills contain random characters like gibberish
        if re.match(r'^[a-zA-Z0-9]+$', skills.strip()):
            # If the string only contains alphanumeric characters with no real spaces or separators,
            # we assume it could be gibberish
            return False
        
        # Additional validation logic (e.g., checking for common skills)
        return True

    def is_valid_internship(internship):
        """
        Validates the internship details to ensure they are not nonsensical or missing.
        """
        essential_fields = [
            internship.required_skills,
            internship.preferred_college,
            internship.preferred_course
        ]
        
        # Check if any essential field is missing or nonsensical
        for field in essential_fields:
            if not field or len(field.strip()) < 3:
                return False
        
        # Specifically validate skills
        if not is_valid_skills(internship.required_skills):
            return False
        
        return True

    # 1. Check if internship is not recommended (course, college, and skills mismatch)
    if (student.college != internship.preferred_college or
        student.course != internship.preferred_course or
        not is_valid_skills(internship.required_skills)):
        return 0.0  # Return 0% score if the internship doesn't match required criteria

    # Check internship validity
    if not is_valid_internship(internship):
        return 20.0  # Return the minimum matching score for invalid internships

    # 2. Skills matching
    student_skills = set(skill.strip().lower() for skill in (student.skills or '').split(',') if skill.strip())
    internship_skills = set(skill.strip().lower() for skill in (internship.required_skills or '').split(',') if skill.strip())

    if student_skills and internship_skills:
        skill_overlap = len(student_skills & internship_skills) / len(internship_skills)
        skill_overlap = min(skill_overlap + 0.1, 1.0)  # Add slight boost for partial matches
    else:
        skill_overlap = 0.0  # Strong penalty if skills are nonsensical or missing

    # 3. Experience matching
    student_exp = student.experience or 0
    internship_exp = internship.required_experience or 0
    if student_exp > 0 and internship_exp > 0:
        exp_match = 1 - abs(student_exp - internship_exp) / max(student_exp, internship_exp)
    else:
        exp_match = 0.5  # Neutral score if experience is unspecified

    # 4. College matching
    college_match = 1.0 if student.college == internship.preferred_college else 0.8

    # 5. Course matching
    course_match = 1.0 if student.course == internship.preferred_course else 0.8

    # Weight distribution
    weights = {
        'skills': 0.5,    # Skills are critical
        'experience': 0.2,  # Experience is moderately important
        'college': 0.15,   # College matching
        'course': 0.15     # Course matching
    }

    # Final weighted score
    weighted_similarity = (
        weights['skills'] * skill_overlap +
        weights['experience'] * exp_match +
        weights['college'] * college_match +
        weights['course'] * course_match
    )

    # Normalize the score to range 50-100
    normalized_score = 50 + weighted_similarity * 50

    # Additional penalty for nonsensical skills (if missed earlier)
    if not is_valid_skills(internship.required_skills):
        normalized_score *= 0.4  # Apply a 60% penalty for nonsensical skills

    return round(normalized_score, 2)
