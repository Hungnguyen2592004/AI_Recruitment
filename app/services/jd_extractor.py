"""
Hàm extract chuyên biệt cho Job Description (JD)
Tập trung vào việc trích xuất yêu cầu từ mô tả công việc
"""
import re
from app.services.cv_parser import extract_position, extract_years_experience
from app.services.cv_extractor import extract_skills


def extract_jd_requirements(jd_text: str) -> dict:
    """
    Trích xuất các yêu cầu từ Job Description
    
    Returns:
        {
            "position": str,
            "years": int,
            "skills": list[str],
            "requirements": list[str]  # Các yêu cầu khác
        }
    """
    jd_lower = jd_text.lower()
    
    # 1. Extract position - ưu tiên tìm trong tiêu đề hoặc dòng đầu
    # Tìm trong 10 dòng đầu tiên (thường là tiêu đề)
    first_lines = "\n".join(jd_text.splitlines()[:10])
    position = extract_position(first_lines)
    
    # Nếu không tìm thấy, tìm trong các pattern đặc biệt cho JD
    if not position:
        # Pattern cho tiếng Việt và tiếng Anh
        position_patterns = [
            # Tiếng Việt: "TUYỂN THỰC TẬP SINH BUSINESS ANALYST", "TUYỂN BUSINESS ANALYST"
            r'(?:tuyển|tìm|recruit|hiring|looking\s+for)\s+(?:thực\s+tập\s+sinh|intern|trainee)?\s*([a-z\s]+?)(?:engineer|developer|analyst|manager|scientist|ba|developer)',
            # "Vị trí: Business Analyst", "Position: Data Engineer"
            r'(?:vị\s+trí|position|role|chức\s+danh)[:\s]+([a-z\s]+?)(?:engineer|developer|analyst|manager|scientist|ba)',
            # "Business Analyst cho...", "Data Engineer for..."
            r'([a-z\s]+?)(?:engineer|developer|analyst|manager|scientist|ba)(?:\s+cho|\s+for|\s+\(|$)',
            # Tìm trực tiếp tên vị trí trong tiêu đề
            r'(?:^|\n)\s*(?:tuyển|tìm|recruit|hiring)\s+([A-Z][a-z\s]+?(?:Engineer|Developer|Analyst|Manager|Scientist|BA))',
        ]
        for pattern in position_patterns:
            match = re.search(pattern, jd_text, re.IGNORECASE | re.MULTILINE)
            if match:
                pos_text = match.group(1).strip()
                # Map về position chuẩn
                position = normalize_position(pos_text)
                if position:
                    break
    
    # Nếu vẫn không tìm thấy, dùng extract_position trên toàn bộ text
    if not position:
        position = extract_position(jd_text)
    
    # 2. Extract years of experience - tìm trong phần yêu cầu
    years = extract_years_experience(jd_text)
    
    # Tìm thêm các pattern đặc biệt cho JD
    if years == 0:
        years_patterns = [
            r'(?:yêu cầu|requirement|require|yêu cầu có)\s+(?:ít nhất|at least|minimum)\s+(\d+)\s*(?:năm|years?)',
            r'(?:kinh nghiệm|experience)\s+(?:ít nhất|at least|minimum)\s+(\d+)\s*(?:năm|years?)',
            r'(\d+)\+?\s*(?:năm|years?)\s*(?:kinh nghiệm|experience)',
        ]
        for pattern in years_patterns:
            match = re.search(pattern, jd_lower)
            if match:
                try:
                    years = int(match.group(1))
                    break
                except:
                    continue
    
    # 3. Extract skills - tìm trong phần yêu cầu kỹ năng
    skills = extract_skills(jd_text)
    
    # Tìm thêm skills trong các section đặc biệt
    skill_sections = [
        r'(?:yêu cầu|requirement|kỹ năng|skills?)[:\s]+(.*?)(?:\n\n|\n[A-Z]|$)',
        r'(?:phải có|must have|required)[:\s]+(.*?)(?:\n\n|\n[A-Z]|$)',
        r'(?:ưu tiên|preferred|nice to have)[:\s]+(.*?)(?:\n\n|\n[A-Z]|$)',
    ]
    
    for pattern in skill_sections:
        matches = re.finditer(pattern, jd_text, re.IGNORECASE | re.DOTALL)
        for match in matches:
            section_text = match.group(1)
            section_skills = extract_skills(section_text)
            for skill in section_skills:
                if skill not in skills:
                    skills.append(skill)
    
    # 4. Extract các yêu cầu khác (optional)
    requirements = []
    requirement_keywords = [
        r'(?:yêu cầu|requirement|phải có|must have)[:\s]+(.+?)(?:\n|$)',
        r'(?:ưu tiên|preferred|nice to have)[:\s]+(.+?)(?:\n|$)',
    ]
    
    for pattern in requirement_keywords:
        matches = re.finditer(pattern, jd_text, re.IGNORECASE)
        for match in matches:
            req_text = match.group(1).strip()
            if len(req_text) > 10 and len(req_text) < 200:
                requirements.append(req_text)
    
    return {
        "position": position or "",
        "years": years,
        "skills": skills,
        "requirements": requirements[:10]  # Giới hạn 10 yêu cầu
    }


def normalize_position(position_text: str) -> str:
    """
    Chuẩn hóa tên vị trí về format chuẩn
    """
    if not position_text:
        return ""
    
    position_lower = position_text.lower().strip()
    
    # Loại bỏ các từ không cần thiết
    position_lower = re.sub(r'\b(thực\s+tập\s+sinh|intern|trainee|junior|senior|lead|principal)\b', '', position_lower)
    position_lower = position_lower.strip()
    
    mapping = {
        "business analyst": "Business Analyst",
        "ba": "Business Analyst",
        "data engineer": "Data Engineer",
        "data analyst": "Data Analyst",
        "data scientist": "Data Scientist",
        "backend engineer": "Backend Engineer",
        "frontend engineer": "Frontend Engineer",
        "fullstack": "Fullstack Engineer",
        "full stack": "Fullstack Engineer",
        "ai engineer": "AI Engineer",
        "ml engineer": "AI Engineer",
        "machine learning engineer": "AI Engineer",
        "devops": "DevOps Engineer",
        "software engineer": "Software Engineer",
        "mobile developer": "Mobile Developer",
        "product manager": "Product Manager",
        "project manager": "Project Manager",
        "qa engineer": "QA Engineer",
        "system analyst": "System Analyst",
        "erp": "ERP Developer",
        "erp developer": "ERP Developer",
        "erp consultant": "ERP Consultant",
    }
    
    # Tìm exact match hoặc partial match
    for key, value in mapping.items():
        if key in position_lower:
            return value
    
    # Nếu không match, trả về text gốc với title case (giữ nguyên nếu đã là title case)
    if position_text.isupper() or position_text.istitle():
        return position_text.strip()
    return position_text.title().strip() if position_text else ""
