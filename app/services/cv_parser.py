import re
from datetime import datetime


def extract_years_experience(text: str) -> int:
    """
    Trích số năm kinh nghiệm từ CV với nhiều pattern
    Cải thiện: Tính từ các công việc nếu không tìm thấy số năm rõ ràng
    """
    patterns = [
        r'(\d+)\s*\+?\s*(?:years?|năm)\s*(?:of\s+)?experience',
        r'(\d+)\s*\+?\s*(?:years?|năm)',
        r'(?:hơn|over|more\s+than)\s+(\d+)\s*(?:years?|năm)',
        r'(\d+)\s*(?:years?|năm)\s*(?:kinh\s+nghiệm|experience)',
        r'experience[:\s]+(\d+)\s*(?:years?|năm)',
        r'(\d+)\s*(?:years?|năm)\s*(?:kn|kinh nghiệm)',
    ]

    text_lower = text.lower()
    years_found = []
    
    for pattern in patterns:
        matches = re.finditer(pattern, text_lower)
        for match in matches:
            try:
                years = int(match.group(1))
                if 0 < years <= 50:  # Hợp lý
                    years_found.append(years)
            except:
                continue
    
    # Nếu tìm thấy số năm rõ ràng, trả về số lớn nhất
    if years_found:
        return max(years_found)
    
    # Fallback: Tính từ các công việc (tìm các khoảng thời gian)
    # Pattern: MM/YYYY - MM/YYYY hoặc YYYY - YYYY
    date_patterns = [
        r'(\d{1,2})[/-](\d{4})\s*[-–—]\s*(\d{1,2})[/-](\d{4})',  # MM/YYYY - MM/YYYY
        r'(\d{4})\s*[-–—]\s*(\d{4})',  # YYYY - YYYY
        r'(\d{4})\s*[-–—]\s*(?:present|hiện tại|nay)',  # YYYY - present
    ]
    
    total_months = 0
    for pattern in date_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            try:
                if len(match.groups()) == 4:  # MM/YYYY - MM/YYYY
                    start_month, start_year = int(match.group(1)), int(match.group(2))
                    end_month, end_year = int(match.group(3)), int(match.group(4))
                    months = (end_year - start_year) * 12 + (end_month - start_month)
                elif len(match.groups()) == 2:  # YYYY - YYYY hoặc YYYY - present
                    start_year = int(match.group(1))
                    if match.group(2).lower() in ['present', 'hiện tại', 'nay']:
                        from datetime import datetime
                        end_year = datetime.now().year
                    else:
                        end_year = int(match.group(2))
                    months = (end_year - start_year) * 12
                else:
                    continue
                
                if 0 < months <= 600:  # Hợp lý (0-50 năm)
                    total_months += months
            except:
                continue
    
    # Chuyển tháng sang năm (làm tròn)
    if total_months > 0:
        return round(total_months / 12)
    
    return 0


def extract_position(text: str) -> str:
    """Trích xuất vị trí công việc từ CV"""
    text_lower = text.lower()
    
    # Mapping vị trí với keywords - mở rộng danh sách
    mapping = {
        "Business Analyst": ["business analyst", "ba", "business analysis", "functional analyst"],
        "Data Engineer": ["data engineer", "data engineering", "etl engineer", "big data engineer"],
        "Data Analyst": ["data analyst", "data analysis", "business intelligence analyst", "bi analyst"],
        "Data Scientist": ["data scientist", "data science"],
        "Backend Engineer": ["backend engineer", "backend developer", "server developer", "api developer"],
        "Frontend Engineer": ["frontend engineer", "frontend developer", "ui developer", "web developer"],
        "Fullstack Engineer": ["fullstack", "full stack", "full-stack engineer", "full-stack developer"],
        "AI Engineer": ["ai engineer", "machine learning engineer", "ml engineer", "deep learning engineer"],
        "DevOps Engineer": ["devops engineer", "devops", "sre", "site reliability engineer"],
        "Software Engineer": ["software engineer", "software developer", "developer", "programmer"],
        "Mobile Developer": ["mobile developer", "ios developer", "android developer", "react native"],
        "Product Manager": ["product manager", "pm", "product owner"],
        "Project Manager": ["project manager", "project management", "scrum master"],
        "QA Engineer": ["qa engineer", "qa", "quality assurance", "test engineer", "tester"],
        "System Analyst": ["system analyst", "systems analyst", "it analyst"],
        "Business Intelligence": ["business intelligence", "bi developer", "bi engineer"],
    }

    text_lower = text.lower()
    
    # Tìm trong toàn bộ CV (không chỉ 50 dòng đầu)
    # Ưu tiên tìm trong 150 dòng đầu (thông tin cá nhân, kinh nghiệm, mục tiêu)
    lines = text.splitlines()[:150]
    text_to_search = "\n".join(lines).lower()
    
    # Tìm vị trí với độ ưu tiên (từ cụ thể đến chung)
    # Sắp xếp theo độ dài keyword (dài hơn = cụ thể hơn)
    found_positions = []
    for position, keywords in mapping.items():
        for kw in keywords:
            # Sử dụng word boundary để match chính xác hơn
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, text_to_search, re.IGNORECASE):
                # Tính điểm ưu tiên (keyword dài hơn = ưu tiên hơn)
                priority = len(kw)
                found_positions.append((priority, position))
                break  # Chỉ lấy position đầu tiên match
    
    if found_positions:
        # Sắp xếp theo priority và trả về position có priority cao nhất
        found_positions.sort(key=lambda x: x[0], reverse=True)
        return found_positions[0][1]
    
    # Fallback: Tìm trong toàn bộ CV nếu không tìm thấy ở 150 dòng đầu
    for position, keywords in mapping.items():
        for kw in keywords:
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, text_lower, re.IGNORECASE):
                return position

    return ""




def extract_summary(text: str) -> str:
    """
    Lấy đoạn giới thiệu bản thân từ CV
    """
    text_lower = text.lower()
    lines = text.splitlines()
    
    # Tìm section Summary/About/Objective
    summary_keywords = ["summary", "about", "objective", "giới thiệu", 
                       "profile", "overview", "mô tả"]
    
    start_idx = -1
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(kw in line_lower for kw in summary_keywords):
            start_idx = i
            break
    
    if start_idx != -1:
        # Lấy các dòng trong section Summary (tối đa 10 dòng)
        summary_lines = []
        for line in lines[start_idx+1:start_idx+11]:
            line_clean = line.strip()
            if line_clean and len(line_clean) > 20:
                summary_lines.append(line_clean)
        if summary_lines:
            return " ".join(summary_lines)
    
    # Fallback: Lấy các dòng dài ở đầu CV (sau tên)
    summary_lines = []
    for i, line in enumerate(lines[3:15]):  # Bỏ qua 3 dòng đầu (thường là tên, email)
        line_clean = line.strip()
        if len(line_clean) > 30 and len(line_clean) < 300:
            # Bỏ các dòng có email, phone, URL
            if "@" not in line_clean and not re.search(r"(\+84|0)\d{9,10}", line_clean):
                if not re.search(r"https?://", line_clean.lower()):
                    summary_lines.append(line_clean)
                    if len(summary_lines) >= 3:
                        break
    
    return " ".join(summary_lines) if summary_lines else ""


def extract_experiences(text: str) -> list:
    """
    Trích xuất kinh nghiệm làm việc (WORK EXPERIENCE) từ CV
    Tìm section "WORK EXPERIENCE" hoặc "Kinh nghiệm" và trích xuất các mục
    """
    experiences = []
    text_lower = text.lower()
    lines = text.splitlines()
    
    # Tìm section WORK EXPERIENCE / Kinh nghiệm
    experience_keywords = [
        "work experience", "professional experience", "employment history",
        "kinh nghiệm", "kinh nghiệm làm việc", "quá trình làm việc",
        "career", "work history", "employment"
    ]
    
    start_idx = -1
    end_idx = len(lines)
    
    # Tìm điểm bắt đầu section
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        # Tìm header của section
        if any(kw in line_lower for kw in experience_keywords):
            # Kiểm tra xem có phải là header không (thường là dòng ngắn, có thể có dấu ":")
            if len(line.strip()) < 50 or ":" in line:
                start_idx = i + 1  # Bắt đầu từ dòng sau header
                break
    
    # Tìm điểm kết thúc section (section tiếp theo)
    if start_idx != -1:
        next_sections = ["education", "học vấn", "skills", "kỹ năng", 
                        "projects", "dự án", "certificates", "chứng chỉ",
                        "awards", "giải thưởng", "languages", "ngôn ngữ"]
        
        for i in range(start_idx, min(start_idx + 50, len(lines))):
            line_lower = lines[i].lower().strip()
            # Nếu gặp section khác hoặc dòng trống nhiều
            if any(section in line_lower for section in next_sections):
                if len(line_lower) < 30:  # Có thể là header section mới
                    end_idx = i
                    break
    
    # Trích xuất từ section
    if start_idx != -1:
        current_exp = []
        for i in range(start_idx, end_idx):
            line = lines[i].strip()
            if not line:
                # Dòng trống - kết thúc một mục experience
                if current_exp:
                    exp_text = " ".join(current_exp)
                    if len(exp_text) > 15 and exp_text not in experiences:
                        experiences.append(exp_text)
                    current_exp = []
                continue
            
            # Bỏ các dòng chỉ có số, ký tự đặc biệt
            if re.search(r'[a-zA-ZÀ-ỹ]', line) and len(line) > 5:
                # Bỏ các dòng có format ngày tháng đơn thuần
                if not re.match(r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$', line):
                    current_exp.append(line)
        
        # Thêm mục cuối cùng
        if current_exp:
            exp_text = " ".join(current_exp)
            if len(exp_text) > 15 and exp_text not in experiences:
                experiences.append(exp_text)
    
    # Fallback: Nếu không tìm thấy section, tìm các dòng có từ khóa
    if not experiences:
        for line in lines:
            line_lower = line.lower()
            line_clean = line.strip()
            
            # Tìm dòng có thông tin về công việc
            if (any(k in line_lower for k in ["worked at", "company", "developer", 
                                             "engineer", "analyst", "tại", "công ty",
                                             "position", "vị trí", "role", "vai trò"]) 
                and len(line_clean) > 10 and len(line_clean) < 300):
                # Bỏ các dòng chỉ có số hoặc format ngày
                if re.search(r'[a-zA-ZÀ-ỹ]', line_clean):
                    if line_clean not in experiences:
                        experiences.append(line_clean)
    
    return experiences[:15]  # Tăng lên 15 mục


def extract_projects(text: str) -> list:
    """
    Trích xuất dự án (PROJECTS) từ CV
    Tìm section "PROJECTS" hoặc "Dự án" và trích xuất các mục
    """
    projects = []
    text_lower = text.lower()
    lines = text.splitlines()
    
    # Tìm section PROJECTS / Dự án
    project_keywords = [
        "projects", "dự án", "portfolio", "personal projects", 
        "side projects", "open source", "project experience"
    ]
    
    start_idx = -1
    end_idx = len(lines)
    
    # Tìm điểm bắt đầu section
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        if any(kw in line_lower for kw in project_keywords):
            # Kiểm tra xem có phải là header không
            if len(line.strip()) < 50 or ":" in line:
                start_idx = i + 1
                break
    
    # Tìm điểm kết thúc section
    if start_idx != -1:
        next_sections = ["education", "học vấn", "skills", "kỹ năng",
                        "certificates", "chứng chỉ", "awards", "languages"]
        
        for i in range(start_idx, min(start_idx + 50, len(lines))):
            line_lower = lines[i].lower().strip()
            if any(section in line_lower for section in next_sections):
                if len(line_lower) < 30:
                    end_idx = i
                    break
    
    # Trích xuất từ section
    if start_idx != -1:
        current_project = []
        for i in range(start_idx, end_idx):
            line = lines[i].strip()
            if not line:
                # Dòng trống - kết thúc một mục project
                if current_project:
                    project_text = " ".join(current_project)
                    if len(project_text) > 15 and project_text not in projects:
                        projects.append(project_text)
                    current_project = []
                continue
            
            # Bỏ các dòng chỉ có số, ký tự đặc biệt
            if re.search(r'[a-zA-ZÀ-ỹ]', line) and len(line) > 5:
                current_project.append(line)
        
        # Thêm mục cuối cùng
        if current_project:
            project_text = " ".join(current_project)
            if len(project_text) > 15 and project_text not in projects:
                projects.append(project_text)
    
    # Fallback: Nếu không tìm thấy section, tìm các dòng có từ khóa
    if not projects:
        for line in lines:
            line_lower = line.lower()
            line_clean = line.strip()
            
            if (any(k in line_lower for k in ["project", "system", "application", 
                                            "app", "website", "platform", "tool",
                                            "dự án", "hệ thống", "ứng dụng"]) 
                and len(line_clean) > 10 and len(line_clean) < 300):
                if re.search(r'[a-zA-ZÀ-ỹ]', line_clean):
                    if line_clean not in projects:
                        projects.append(line_clean)
    
    return projects[:15]  # Tăng lên 15 mục
