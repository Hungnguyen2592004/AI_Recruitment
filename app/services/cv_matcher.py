def match_cv_with_jd(candidate_skills, required_skills, 
                     candidate_position="", target_position="",
                     candidate_years=0, required_years=0):
    """
    Tính điểm matching giữa CV và JD dựa trên:
    - Skills matching (60%)
    - Position matching (20%)
    - Years of experience (20%)
    """
    total_score = 0
    matched_skills = []
    missing_skills = []
    
    # 1. Skills matching (60% trọng số)
    if required_skills:
        candidate_set = set([s.lower().strip() for s in candidate_skills])
        required_set = set([s.lower().strip() for s in required_skills])
        
        # Tìm exact matches
        matched_skills = list(candidate_set & required_set)
        
        # Tìm partial matches (một skill chứa skill kia)
        partial_matches = []
        for req_skill in required_set:
            if req_skill not in matched_skills:
                for cand_skill in candidate_set:
                    if req_skill in cand_skill or cand_skill in req_skill:
                        partial_matches.append(req_skill)
                        break
        
        # Tính điểm: exact match = 100%, partial match = 50%
        if len(required_set) > 0:
            exact_score = (len(matched_skills) / len(required_set)) * 60
            partial_score = (len(partial_matches) / len(required_set)) * 60 * 0.5
            skills_score = min(exact_score + partial_score, 60)
            total_score += skills_score
        
        missing_skills = list(required_set - candidate_set - set(partial_matches))
    else:
        # Nếu không có required skills, cho điểm dựa trên số skills có
        if candidate_skills:
            total_score += min(len(candidate_skills) * 5, 30)  # Tối đa 30 điểm
        missing_skills = []
    
    # 2. Position matching (20% trọng số)
    if target_position and candidate_position:
        target_lower = target_position.lower().strip()
        candidate_lower = candidate_position.lower().strip()
        
        # Exact match (chính xác)
        if target_lower == candidate_lower:
            total_score += 20
        # Partial match - một trong hai chứa từ khóa của kia
        elif target_lower in candidate_lower or candidate_lower in target_lower:
            total_score += 15
        # Word match - có từ khóa chung (ví dụ: "analyst" trong cả hai)
        else:
            target_words = set([w for w in target_lower.split() if len(w) > 3])
            candidate_words = set([w for w in candidate_lower.split() if len(w) > 3])
            common_words = target_words & candidate_words
            
            if common_words:
                # Có từ khóa chung
                if len(common_words) >= 2:
                    total_score += 12  # Nhiều từ khóa chung
                else:
                    total_score += 8   # Một từ khóa chung
            # Related position (có từ khóa liên quan)
            elif any(word in candidate_lower for word in ["engineer", "developer", "analyst", "scientist", "manager"]):
                if any(word in target_lower for word in ["engineer", "developer", "analyst", "scientist", "manager"]):
                    total_score += 5
    
    # 3. Years of experience matching (20% trọng số)
    if required_years > 0:
        if candidate_years >= required_years:
            total_score += 20
        elif candidate_years > 0:
            # Tính phần trăm đạt được
            experience_ratio = candidate_years / required_years
            total_score += min(experience_ratio * 20, 20)
    elif candidate_years > 0:
        # Nếu không có yêu cầu về năm kinh nghiệm, nhưng candidate có kinh nghiệm
        total_score += min(candidate_years * 2, 10)  # Tối đa 10 điểm
    
    # Đảm bảo điểm không vượt quá 100
    final_score = round(min(total_score, 100), 2)
    
    return {
        "score": final_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills
    }
