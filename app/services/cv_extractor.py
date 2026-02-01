import re


def extract_email(text: str) -> str | None:
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else None


def extract_phone(text: str) -> str | None:
    """
    Trích xuất số điện thoại từ CV
    Format Việt Nam: 0xxxxxxxxx (10 số) hoặc +84xxxxxxxxx
    """
    # Tìm trong 50 dòng đầu (thông tin liên hệ)
    lines = text.splitlines()[:50]
    
    # Pattern cho số điện thoại Việt Nam
    patterns = [
        r'(?:phone|điện thoại|mobile|sdt|tel)[\s:]*([0\+84]\d{9,10})',  # Có label
        r'\b(0[3|5|7|8|9]\d{8})\b',  # 10 số bắt đầu bằng 0 và số thứ 2 là 3,5,7,8,9
        r'\b(\+84[3|5|7|8|9]\d{8})\b',  # +84 format
        r'\b(0\d{9})\b',  # 10 số bắt đầu bằng 0
    ]
    
    for line in lines:
        line_lower = line.lower()
        # Bỏ qua dòng có từ khóa không phải phone
        if any(kw in line_lower for kw in ["fax", "tax", "account", "bank"]):
            continue
            
        for pattern in patterns:
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                phone = match.group(1) if match.lastindex else match.group(0)
                # Loại bỏ ký tự không phải số và +
                phone_clean = re.sub(r'[^\d+]', '', phone)
                # Validate: phải có 10-11 số (0xxxxxxxxx hoặc +84xxxxxxxxx)
                if phone_clean.startswith('+84'):
                    if len(phone_clean) == 12:  # +84xxxxxxxxx
                        return phone_clean
                elif phone_clean.startswith('0'):
                    if len(phone_clean) == 10:  # 0xxxxxxxxx
                        return phone_clean
                elif phone_clean.startswith('84'):
                    if len(phone_clean) == 11:  # 84xxxxxxxxx -> chuyển về 0
                        return '0' + phone_clean[2:]
    
    return None

import re

def extract_name(text: str) -> str:
    """
    Trích xuất tên từ CV với nhiều phương pháp:
    1. Tìm từ pattern "Họ tên:" hoặc "Name:"
    2. Tìm từ các dòng đầu CV (dòng có format tên hợp lệ)
    3. Tìm từ email (fallback)
    """
    
    forbidden_keywords = [
        "địa chỉ", "address", "bank", "account", "sdt", "phone",
        "email", "ngày", "tháng", "năm", "họ tên", "name", 
        "cv", "resume", "curriculum", "vitae", "contact",
        "mobile", "tel", "linkedin", "github", "facebook", "http"
    ]
    
    # Method 1: Tìm pattern "Họ tên:" hoặc "Name:" hoặc "Full Name:"
    name_patterns = [
        r"(?:họ\s+tên|name|full\s+name)[\s:]+([A-Za-zÀ-ỹ\s]{5,50})",
        r"(?:họ\s+tên|name|full\s+name)[\s:]+([A-Z][a-zÀ-ỹ]+\s+[A-Z][a-zÀ-ỹ]+(?:\s+[A-Z][a-zÀ-ỹ]+){0,3})"
    ]
    
    for pattern in name_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            name = match.group(1).strip()
            # Loại bỏ ký tự đặc biệt ở cuối
            name = re.sub(r'[,\.;:]+$', '', name)
            words = name.split()
            if 2 <= len(words) <= 5:
                # Kiểm tra không chứa từ khóa và không có email/phone
                name_lower = name.lower()
                if not any(kw in name_lower for kw in forbidden_keywords):
                    if "@" not in name and not re.search(r"(\+84|0)\d{9,10}", name):
                        return name.title()
    
    # Method 1.5: Tìm tên từ dòng đầu tiên có format tên (có thể không có label)
    lines = text.splitlines()
    for i, line in enumerate(lines[:5]):  # Chỉ xem 5 dòng đầu
        line = line.strip()
        if not line:
            continue
        
        # Bỏ dòng có email, phone, URL
        if "@" in line or re.search(r"(\+84|0)\d{9,10}", line) or re.search(r"https?://", line.lower()):
            continue
        
        # Bỏ dòng quá dài hoặc quá ngắn
        if len(line) < 5 or len(line) > 60:
            continue
        
        # Kiểm tra xem có phải tên không (chủ yếu là chữ cái, có khoảng trắng)
        if re.match(r'^[A-Za-zÀ-ỹ\s]{5,60}$', line):
            words = line.split()
            # Tên thường có 2-5 từ, mỗi từ bắt đầu bằng chữ hoa hoặc có thể là tên Việt Nam
            if 2 <= len(words) <= 5:
                # Kiểm tra không có từ khóa
                line_lower = line.lower()
                if not any(kw in line_lower for kw in forbidden_keywords):
                    # Format lại tên: mỗi từ bắt đầu bằng chữ hoa
                    name_parts = [w.capitalize() for w in words]
                    return " ".join(name_parts)
    
    # Method 2: Tìm từ các dòng đầu CV (dòng có format tên hợp lệ)
    lines = text.splitlines()
    
    for i, line in enumerate(lines[:40]):  # Tăng lên 40 dòng để tìm tên tốt hơn
        line = line.strip()
        if not line:
            continue
            
        line_lower = line.lower()
        
        # Bỏ dòng quá dài (có thể là địa chỉ hoặc mô tả)
        if len(line) > 80:  # Tăng lên 80 để bắt được tên dài hơn
            continue
        
        # Bỏ dòng chứa email hoặc phone
        if "@" in line or re.search(r"(\+84|0)\d{9,10}", line):
            continue
        
        # Bỏ dòng có URL
        if re.search(r"https?://", line_lower):
            continue
        
        # Bỏ dòng có quá nhiều số (có thể là địa chỉ, ngày tháng)
        digit_count = len(re.findall(r"\d", line))
        if digit_count > 4:
            continue
        
        # Bỏ từ khóa hệ thống
        if any(kw in line_lower for kw in forbidden_keywords):
            continue
        
        # Bỏ dòng chỉ có số, ký tự đặc biệt hoặc ký hiệu
        if re.match(r"^[\d\s\W_]+$", line):
            continue
        
        words = line.split()
        
        # Tên thường có 2-5 từ
        if 2 <= len(words) <= 5:
            # Làm sạch từng từ
            valid_words = []
            for word in words:
                # Loại bỏ ký tự đặc biệt ở đầu/cuối
                clean_word = re.sub(r'^[\W\d_]+|[\W\d_]+$', '', word)
                # Kiểm tra có chứa chữ cái và độ dài hợp lý
                if re.search(r'[a-zA-ZÀ-ỹ]', clean_word) and 2 <= len(clean_word) <= 20:
                    valid_words.append(clean_word)
            
            if len(valid_words) >= 2:
                full_name = " ".join(valid_words)
                # Kiểm tra xem có phải tên hợp lệ không (chủ yếu là chữ cái)
                # Cho phép dấu phẩy, chấm ở cuối
                if re.match(r"^[A-Za-zÀ-ỹ\s]+[,.\.]?$", full_name):
                    full_name = full_name.rstrip(',.')
                    # Kiểm tra lại không có từ khóa
                    if not any(kw in full_name.lower() for kw in forbidden_keywords):
                        if len(full_name.split()) >= 2:
                            return full_name.title()
    
    # Method 3: Extract from email (fallback - chỉ khi không tìm thấy bằng cách khác)
    email_match = re.search(r"([a-zA-Z0-9._%+-]+)@", text)
    if email_match:
        email_prefix = email_match.group(1)
        # Loại bỏ số và ký tự đặc biệt, chỉ giữ chữ cái
        name_from_email = re.sub(r'[^a-zA-ZÀ-ỹ]', '', email_prefix)
        # Nếu có đủ chữ cái (ít nhất 8 ký tự), có thể là tên
        if 8 <= len(name_from_email) <= 30:
            # Tách tên từ email (ví dụ: nguyenvanhung -> Nguyễn Văn Hùng)
            # Tạm thời return dạng title case với khoảng trắng
            # Đây là fallback, không hoàn hảo nhưng tốt hơn không có gì
            return name_from_email.title()
    
    return ""


def extract_skills(text: str) -> list[str]:
    """Trích xuất kỹ năng từ CV với danh sách mở rộng"""
    skills_list = [
        # Programming Languages
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", 
        "php", "ruby", "swift", "kotlin", "scala", "r", "matlab",
        
        # Web Frameworks
        "react", "vue", "angular", "next.js", "nuxt.js", "svelte",
        "django", "flask", "fastapi", "spring", "express", "nest.js",
        "laravel", "rails", "asp.net",
        
        # Databases
        "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
        "cassandra", "dynamodb", "oracle", "sqlite", "mariadb",
        
        # Cloud & DevOps
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
        "jenkins", "gitlab ci", "github actions", "ci/cd", "ansible",
        "chef", "puppet", "prometheus", "grafana",
        
        # Data & ML
        "machine learning", "deep learning", "data science", "data engineering",
        "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras",
        "spark", "hadoop", "kafka", "airflow", "dbt", "snowflake",
        "tableau", "power bi", "looker",
        
        # Tools & Others
        "git", "linux", "bash", "shell scripting", "rest api", "graphql",
        "microservices", "agile", "scrum", "jira", "confluence",
        
        # Mobile
        "react native", "flutter", "ios", "android", "swift", "kotlin",
        
        # Testing
        "jest", "pytest", "selenium", "cypress", "junit",
    ]

    found = []
    text_lower = text.lower()
    
    # Tìm section Skills nếu có
    skills_section = ""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(kw in line_lower for kw in ["skills", "kỹ năng", "technical skills", 
                                           "technologies", "tech stack"]):
            # Lấy 20 dòng tiếp theo
            skills_section = "\n".join(lines[i:i+20]).lower()
            break
    
    # Tìm trong section Skills hoặc toàn bộ text
    search_text = skills_section if skills_section else text_lower
    
    for skill in skills_list:
        skill_lower = skill.lower()
        # Tìm exact match hoặc word boundary
        pattern = r'\b' + re.escape(skill_lower) + r'\b'
        if re.search(pattern, search_text, re.IGNORECASE):
            if skill not in found:
                found.append(skill)

    return found


def extract_date_of_birth(text: str) -> str | None:
    """
    Trích xuất ngày tháng năm sinh từ CV
    Các format: DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD, DD/MM/YY
    """
    patterns = [
        r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',  # DD/MM/YYYY hoặc DD-MM-YYYY
        r'\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b',    # YYYY-MM-DD
        r'\b(ngày\s+\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4})\b',  # Tiếng Việt
    ]
    
    text_lower = text.lower()
    # Tìm trong phần đầu CV (thông tin cá nhân)
    lines = text.splitlines()[:30]
    
    for line in lines:
        line_lower = line.lower()
        # Bỏ qua nếu là ngày tháng trong kinh nghiệm
        if any(kw in line_lower for kw in ["experience", "kinh nghiệm", "worked", "from", "to"]):
            continue
            
        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                # Kiểm tra xem có phải năm sinh hợp lý không (1900-2010)
                date_str = match.group(1)
                year_match = re.search(r'\d{4}', date_str)
                if year_match:
                    year = int(year_match.group())
                    if 1900 <= year <= 2010:
                        return date_str
    
    return None


def extract_address(text: str) -> str | None:
    """
    Trích xuất địa chỉ từ CV
    Tìm các dòng chứa từ khóa: địa chỉ, address, location
    """
    keywords = ["địa chỉ", "address", "location", "nơi ở", "residence", "địa điểm"]
    text_lower = text.lower()
    lines = text.splitlines()[:40]  # Tăng số dòng quét
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        for keyword in keywords:
            if keyword in line_lower:
                # Lấy phần sau dấu ":" hoặc "="
                for separator in [":", "=", "-"]:
                    if separator in line:
                        parts = line.split(separator, 1)
                        if len(parts) > 1:
                            addr = parts[1].strip()
                            if addr and len(addr) > 5 and len(addr) < 200:
                                # Bỏ các dòng có email, phone
                                if "@" not in addr and not re.search(r"(\+84|0)\d{9,10}", addr):
                                    return addr
                
                # Hoặc lấy dòng tiếp theo (nếu dòng hiện tại chỉ là label)
                if len(line.strip()) < 30 and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line and len(next_line) > 5 and len(next_line) < 200:
                        # Bỏ các dòng có email, phone, URL
                        if "@" not in next_line and not re.search(r"(\+84|0)\d{9,10}", next_line):
                            if not re.search(r"https?://", next_line.lower()):
                                return next_line
    
    return None


def extract_social_links(text: str) -> list[str]:
    """
    Trích xuất link mạng xã hội: LinkedIn, GitHub, Facebook, etc.
    Hỗ trợ cả URL đầy đủ và dạng rút gọn
    """
    patterns = [
        # Full URLs
        r'https?://(?:www\.)?(linkedin\.com/[^\s\)\]]+)',
        r'https?://(?:www\.)?(github\.com/[^\s\)\]]+)',
        r'https?://(?:www\.)?(facebook\.com/[^\s\)\]]+)',
        r'https?://(?:www\.)?(twitter\.com/[^\s\)\]]+)',
        r'https?://(?:www\.)?(x\.com/[^\s\)\]]+)',
        r'https?://(?:www\.)?(instagram\.com/[^\s\)\]]+)',
        r'https?://(?:www\.)?(youtube\.com/[^\s\)\]]+)',
        r'https?://(?:www\.)?(behance\.net/[^\s\)\]]+)',
        r'https?://(?:www\.)?(dribbble\.com/[^\s\)\]]+)',
        r'https?://(?:www\.)?(portfolio[^\s\)\]]+)',
        # Short forms (github.com/username)
        r'\b(github\.com/[a-zA-Z0-9_-]+)',
        r'\b(linkedin\.com/in/[a-zA-Z0-9_-]+)',
    ]
    
    found = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            url_part = match.group(1) if match.lastindex else match.group(0)
            # Tạo full URL
            if url_part.startswith("http"):
                full_url = url_part
            else:
                full_url = f"https://{url_part}"
            
            # Loại bỏ ký tự thừa ở cuối
            full_url = re.sub(r'[.,;)\]]+$', '', full_url)
            
            if full_url not in found and len(full_url) < 200:
                found.append(full_url)
    
    return found


def extract_education(text: str) -> list[dict]:
    """
    Trích xuất thông tin học vấn từ CV
    Tìm các section: Education, Học vấn, Trình độ học vấn
    """
    education_keywords = [
        "education", "học vấn", "trình độ học vấn", "học tập", "academic",
        "university", "đại học", "college", "cao đẳng", "institute", "viện",
        "degree", "bằng cấp", "bachelor", "master", "phd", "tiến sĩ", "thạc sĩ", "cử nhân"
    ]
    
    education_list = []
    text_lower = text.lower()
    lines = text.splitlines()
    
    # Tìm section Education
    education_start = -1
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        # Kiểm tra xem có phải là header section không
        if any(kw in line_lower for kw in education_keywords):
            # Kiểm tra xem có phải là header (thường ngắn hoặc có dấu :)
            if len(line.strip()) < 50 or ":" in line:
                education_start = i + 1  # Bắt đầu từ dòng sau header
                break
    
    if education_start == -1:
        # Fallback: Tìm các dòng có từ khóa education trong toàn bộ CV
        for i, line in enumerate(lines):
            line_lower = line.lower()
            line_clean = line.strip()
            
            # Bỏ dòng quá ngắn hoặc quá dài
            if len(line_clean) < 10 or len(line_clean) > 200:
                continue
            
            # Bỏ dòng có email, phone, URL
            if "@" in line_clean or re.search(r"(\+84|0)\d{9,10}", line_clean) or re.search(r"https?://", line_lower):
                continue
            
            if any(kw in line_lower for kw in ["university", "đại học", "college", "cao đẳng", 
                                               "bachelor", "master", "phd", "cử nhân", "thạc sĩ", "institute", "viện"]):
                edu_dict = {}
                # Tìm tên trường
                if any(kw in line_lower for kw in ["university", "đại học", "college", "cao đẳng", "institute", "viện", "school"]):
                    edu_dict["school"] = line_clean
                # Tìm bằng cấp
                if any(kw in line_lower for kw in ["bachelor", "cử nhân", "master", "thạc sĩ", "phd", "tiến sĩ", "degree"]):
                    edu_dict["degree"] = line_clean
                # Tìm năm
                year_match = re.search(r'\b(19|20)\d{2}\b', line_clean)
                if year_match:
                    edu_dict["year"] = year_match.group(0)
                
                if edu_dict:
                    education_list.append(edu_dict)
        return education_list[:10]  # Tăng lên 10 mục
    
    # Lấy các dòng trong section Education (tối đa 30 dòng)
    education_lines = lines[education_start:education_start + 30]
    
    current_edu = {}
    for line in education_lines:
        line = line.strip()
        if not line:
            if current_edu:
                education_list.append(current_edu)
                current_edu = {}
            continue
        
        # Bỏ dòng có email, phone, URL
        if "@" in line or re.search(r"(\+84|0)\d{9,10}", line) or re.search(r"https?://", line.lower()):
            continue
        
        # Tìm tên trường/trường đại học
        if any(kw in line.lower() for kw in ["university", "đại học", "college", "cao đẳng", "institute", "viện", "school"]):
            if "school" not in current_edu:
                current_edu["school"] = line
            elif "school" in current_edu and len(line) > len(current_edu.get("school", "")):
                current_edu["school"] = line
        
        # Tìm bằng cấp
        if any(kw in line.lower() for kw in ["bachelor", "cử nhân", "master", "thạc sĩ", "phd", "tiến sĩ", "degree", "bằng"]):
            if "degree" not in current_edu:
                current_edu["degree"] = line
        
        # Tìm chuyên ngành
        if any(kw in line.lower() for kw in ["major", "chuyên ngành", "specialization"]):
            if "major" not in current_edu:
                current_edu["major"] = line
        
        # Tìm năm
        year_match = re.search(r'\b(19|20)\d{2}\b', line)
        if year_match and "year" not in current_edu:
            current_edu["year"] = year_match.group()
    
    if current_edu:
        education_list.append(current_edu)
    
    # Cải thiện: Nếu không tìm thấy đủ thông tin, thử tìm trong toàn bộ CV
    if len(education_list) == 0:
        # Tìm các dòng có từ khóa trường học, bằng cấp
        for i, line in enumerate(lines):
            line_clean = line.strip()
            if len(line_clean) < 10 or len(line_clean) > 200:
                continue
            
            # Bỏ dòng có email, phone, URL
            if "@" in line_clean or re.search(r"(\+84|0)\d{9,10}", line_clean) or re.search(r"https?://", line_clean.lower()):
                continue
            
            line_lower = line_clean.lower()
            edu_dict = {}
            
            # Tìm tên trường
            if any(kw in line_lower for kw in ["university", "đại học", "college", "cao đẳng", "institute", "viện", "school", "trường"]):
                edu_dict["school"] = line_clean
            
            # Tìm bằng cấp
            if any(kw in line_lower for kw in ["bachelor", "cử nhân", "master", "thạc sĩ", "phd", "tiến sĩ", "degree", "bằng", "engineer", "kỹ sư"]):
                if "degree" not in edu_dict:
                    edu_dict["degree"] = line_clean
            
            # Tìm chuyên ngành
            if any(kw in line_lower for kw in ["major", "chuyên ngành", "specialization", "ngành"]):
                if "major" not in edu_dict:
                    # Lấy phần sau "chuyên ngành:" hoặc "major:"
                    for sep in [":", "-", "–"]:
                        if sep in line_clean:
                            parts = line_clean.split(sep, 1)
                            if len(parts) > 1:
                                edu_dict["major"] = parts[1].strip()
                                break
                    if "major" not in edu_dict:
                        edu_dict["major"] = line_clean
            
            # Tìm năm
            year_match = re.search(r'\b(19|20)\d{2}\b', line_clean)
            if year_match:
                year = year_match.group()
                if 1950 <= int(year) <= 2030:  # Năm hợp lý
                    edu_dict["year"] = year
            
            # Thêm vào danh sách nếu có ít nhất 1 field
            if edu_dict:
                # Kiểm tra xem đã có trong danh sách chưa
                is_duplicate = False
                for existing in education_list:
                    if existing.get("school") == edu_dict.get("school"):
                        is_duplicate = True
                        # Merge thông tin nếu cần
                        for key, value in edu_dict.items():
                            if key not in existing or not existing[key]:
                                existing[key] = value
                        break
                
                if not is_duplicate:
                    education_list.append(edu_dict)
    
    return education_list[:10]  # Tăng lên 10 mục học vấn
