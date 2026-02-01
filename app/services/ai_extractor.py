"""
AI-powered CV extraction using LLM APIs
Hỗ trợ OpenAI GPT và các API tương tự
"""
import json
import os
import re
from typing import Optional, Dict, Any


def extract_jd_with_ai(jd_text: str, api_key: Optional[str] = None, provider: str = "gemini") -> Dict[str, Any]:
    """
    Trích xuất thông tin từ Job Description (JD) bằng AI API
    
    Args:
        jd_text: Nội dung mô tả công việc
        api_key: API key (nếu None thì lấy từ env)
        provider: "openai", "anthropic", hoặc "gemini"
    
    Returns:
        Dict chứa: position, years, skills, requirements
    """
    print(f"[JD-AI] Bắt đầu extract JD bằng AI (provider: {provider})...")
    print(f"[JD-AI] JD text length: {len(jd_text)} ký tự")
    print(f"[JD-AI] JD preview (100 ký tự đầu): {jd_text[:100]}...")
    
    # Lấy API key từ env nếu không có
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("[JD-AI] ❌ Không có API key!")
        return {}
    
    # Tạo prompt cho AI để extract JD
    prompt = create_jd_extraction_prompt(jd_text)
    print(f"[JD-AI] Prompt length: {len(prompt)} ký tự")
    
    try:
        if provider.lower() == "openai":
            result = extract_with_openai(prompt, api_key)
        elif provider.lower() == "anthropic":
            result = extract_with_anthropic(prompt, api_key)
        elif provider.lower() == "gemini":
            result = extract_with_gemini(prompt, api_key)
        else:
            print(f"[JD-AI] ❌ Provider không hợp lệ: {provider}")
            return {}
        
        print(f"[JD-AI] Raw AI result: {result}")
        
        # Clean và validate kết quả
        if result:
            cleaned = clean_jd_result(result)
            print(f"[JD-AI] ✓ Cleaned result - Position: {cleaned.get('position')}, Years: {cleaned.get('years')}, Skills: {len(cleaned.get('skills', []))}")
            return cleaned
        else:
            print("[JD-AI] ❌ AI không trả về kết quả")
            return {}
    except Exception as e:
        print(f"[JD-AI] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {}


def create_jd_extraction_prompt(jd_text: str) -> str:
    """Tạo prompt để extract thông tin từ Job Description"""
    # Giới hạn JD text để tránh quá dài
    if len(jd_text) > 10000:
        jd_content = jd_text[:10000] + "\n... (truncated)"
    else:
        jd_content = jd_text
    
    prompt = f"""Bạn là chuyên gia phân tích Job Description (JD) cực kỳ chuyên nghiệp. Nhiệm vụ của bạn là trích xuất CHÍNH XÁC thông tin từ mô tả công việc dưới đây.

MÔ TẢ CÔNG VIỆC (ĐỌC KỸ TỪNG DÒNG, ĐẶC BIỆT LÀ TIÊU ĐỀ VÀ DÒNG ĐẦU):
{jd_content}

HƯỚNG DẪN TRÍCH XUẤT:

1. VỊ TRÍ (position) - QUAN TRỌNG NHẤT - PHẢI TÌM ĐƯỢC:
   - ĐỌC KỸ tiêu đề và 5 dòng đầu tiên của JD - ĐÂY LÀ NƠI THƯỜNG CÓ VỊ TRÍ
   - Tìm vị trí công việc được tuyển dụng
   - Các format thường gặp:
     * "TUYỂN THỰC TẬP SINH BUSINESS ANALYST" → "Business Analyst"
     * "TUYỂN BUSINESS ANALYST (BA)" → "Business Analyst"
     * "Vị trí: Data Engineer" → "Data Engineer"
     * "Position: Software Developer" → "Software Developer"
     * "Tuyển dụng: Backend Engineer" → "Backend Engineer"
   - Loại bỏ các từ: "thực tập sinh", "intern", "trainee", "junior", "senior", "lead", "principal"
   - Trả về tên vị trí chuẩn: "Business Analyst", "Data Engineer", "Software Developer", "Backend Engineer", etc.
   - Nếu không tìm thấy trong tiêu đề, tìm trong toàn bộ JD
   - NẾU KHÔNG TÌM THẤY: để null (nhưng phải cố gắng tìm kỹ trước)

2. SỐ NĂM KINH NGHIỆM YÊU CẦU (years):
   - Tìm số năm kinh nghiệm yêu cầu
   - Format: "3 năm kinh nghiệm", "ít nhất 5 năm", "5+ years experience", "minimum 3 years"
   - Trả về số nguyên (0 nếu không có yêu cầu)

3. KỸ NĂNG YÊU CẦU (skills):
   - Tìm tất cả kỹ năng, công nghệ, tools được yêu cầu
   - Tìm trong phần "Yêu cầu", "Kỹ năng", "Skills", "Must have", "Required"
   - Ví dụ: ["Python", "SQL", "AWS", "Agile", "Docker", "Kubernetes"]

4. YÊU CẦU KHÁC (requirements):
   - Tìm các yêu cầu khác không phải kỹ năng
   - Ví dụ: "Có bằng đại học", "Giao tiếp tốt", "Làm việc nhóm"

YÊU CẦU: BẠN PHẢI TRẢ VỀ JSON THUẦN, KHÔNG CÓ BẤT KỲ TEXT NÀO KHÁC, KHÔNG CÓ MARKDOWN, KHÔNG CÓ GIẢI THÍCH.

TRẢ VỀ JSON VỚI FORMAT SAU (CHỈ JSON, KHÔNG CÓ TEXT THÊM):
{{
    "position": "Tên vị trí chuẩn hoặc null",
    "years": số nguyên (0 nếu không có),
    "skills": ["skill1", "skill2", ...],
    "requirements": ["yêu cầu 1", "yêu cầu 2", ...]
}}

QUAN TRỌNG NHẤT:
- VỊ TRÍ là thông tin QUAN TRỌNG NHẤT - PHẢI đọc KỸ tiêu đề và 5 dòng đầu
- Nếu JD có "TUYỂN THỰC TẬP SINH BUSINESS ANALYST" → position = "Business Analyst"
- Nếu JD có "Vị trí: Data Engineer" → position = "Data Engineer"
- Nếu JD có "Position: Backend Engineer" → position = "Backend Engineer"
- Loại bỏ các từ không cần thiết: "thực tập sinh", "intern", "trainee", "junior", "senior"
- CHỈ TRẢ VỀ JSON THUẦN, BẮT ĐẦU BẰNG {{ VÀ KẾT THÚC BẰNG }}, KHÔNG CÓ MARKDOWN, KHÔNG CÓ GIẢI THÍCH!
"""
    return prompt


def clean_jd_result(data: Dict[str, Any]) -> Dict[str, Any]:
    """Làm sạch và validate kết quả từ AI cho JD"""
    cleaned = {}
    
    # Clean position
    position = data.get("position", "")
    if position and isinstance(position, str):
        position = position.strip()
        # Loại bỏ các từ không cần thiết
        position = re.sub(r'\b(thực\s+tập\s+sinh|intern|trainee|junior|senior|lead|principal)\b', '', position, flags=re.IGNORECASE)
        position = position.strip()
        if position and len(position) > 2:
            cleaned["position"] = position
        else:
            cleaned["position"] = ""
    else:
        cleaned["position"] = ""
    
    # Clean years
    years = data.get("years", 0)
    if isinstance(years, (int, float)):
        cleaned["years"] = max(0, int(years))
    else:
        cleaned["years"] = 0
    
    # Clean skills
    skills = data.get("skills", [])
    if isinstance(skills, list):
        cleaned["skills"] = [str(s).strip() for s in skills if s and str(s).strip()]
    else:
        cleaned["skills"] = []
    
    # Clean requirements
    requirements = data.get("requirements", [])
    if isinstance(requirements, list):
        cleaned["requirements"] = [str(r).strip() for r in requirements if r and str(r).strip()][:10]
    else:
        cleaned["requirements"] = []
    
    return cleaned


def extract_with_ai(cv_text: str, api_key: Optional[str] = None, provider: str = "openai") -> Dict[str, Any]:
    """
    Trích xuất thông tin từ CV bằng AI API
    
    Args:
        cv_text: Nội dung CV
        api_key: API key (nếu None thì lấy từ env)
        provider: "openai", "anthropic", hoặc "gemini"
    
    Returns:
        Dict chứa các thông tin đã extract
    """
    # Lấy API key từ env nếu không có
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        return {}
    
    # Tạo prompt cho AI
    prompt = create_extraction_prompt(cv_text)
    
    try:
        if provider.lower() == "openai":
            return extract_with_openai(prompt, api_key)
        elif provider.lower() == "anthropic":
            return extract_with_anthropic(prompt, api_key)
        elif provider.lower() == "gemini":
            return extract_with_gemini(prompt, api_key)
        else:
            return {}
    except Exception as e:
        print(f"AI extraction error: {e}")
        return {}


def create_extraction_prompt(cv_text: str) -> str:
    """Tạo prompt để extract thông tin từ CV - phiên bản cải thiện"""
    # Tăng giới hạn text lên 30000 ký tự để đảm bảo đủ thông tin (CV có thể dài)
    # Nếu CV quá dài, sẽ cắt nhưng ưu tiên phần đầu (thông tin cá nhân, kinh nghiệm)
    if len(cv_text) > 30000:
        # Lấy 20000 ký tự đầu (thông tin cá nhân, kinh nghiệm) + 10000 ký tự cuối (dự án, kỹ năng)
        cv_content = cv_text[:20000] + "\n\n...[PHẦN GIỮA ĐÃ BỎ QUA]...\n\n" + cv_text[-10000:]
        print(f"[Prompt] CV quá dài ({len(cv_text)} ký tự), đã cắt xuống 30000 ký tự")
    else:
        cv_content = cv_text
        print(f"[Prompt] CV text length: {len(cv_text)} ký tự")
    
    prompt = f"""Bạn là chuyên gia phân tích CV cực kỳ chuyên nghiệp. Nhiệm vụ của bạn là trích xuất CHÍNH XÁC và ĐẦY ĐỦ 100% thông tin từ CV dưới đây.

QUAN TRỌNG: CV này là CV THỰC TẾ của ứng viên. Bạn PHẢI đọc KỸ từng dòng và trích xuất CHÍNH XÁC tất cả thông tin có trong CV. KHÔNG được đoán mò, KHÔNG được bỏ sót.

CV TOÀN VĂN (ĐỌC KỸ TỪNG DÒNG):
{cv_content}

HƯỚNG DẪN TRÍCH XUẤT CHI TIẾT:

1. HỌ TÊN (name):
   - Tìm ở đầu CV, thường sau "Họ tên:", "Name:", "Full Name:", hoặc dòng đầu tiên
   - Lấy tên đầy đủ (2-5 từ), không bao gồm email, số điện thoại
   - Ví dụ: "Nguyễn Văn A", "Trần Thị B"

2. EMAIL (email) - QUAN TRỌNG, PHẢI TÌM:
   - ĐỌC KỸ TỪNG DÒNG trong CV để tìm email
   - Email có format: xxx@xxx.xxx (có dấu @ và dấu chấm sau @)
   - Tìm ở phần đầu CV, sau tên, trong phần "Liên hệ", "Contact", "Thông tin liên hệ"
   - Có thể ở bất kỳ đâu trong CV - PHẢI ĐỌC KỸ TẤT CẢ
   - Lấy email đầu tiên tìm thấy hoặc email chính
   - Ví dụ: "nguyenvana@gmail.com", "thuyngan@company.com"
   - NẾU KHÔNG TÌM THẤY: để null

3. SỐ ĐIỆN THOẠI (phone) - QUAN TRỌNG, PHẢI TÌM:
   - ĐỌC KỸ TỪNG DÒNG trong CV để tìm số điện thoại
   - Số điện thoại Việt Nam: 0xxxxxxxxx (10 số bắt đầu bằng 0) hoặc +84xxxxxxxxx
   - Có thể có dấu cách, dấu gạch ngang: "0123 456 789", "0123-456-789"
   - Tìm ở phần đầu CV, sau tên, trong phần "Liên hệ", "Contact", "Thông tin liên hệ"
   - Có thể ở bất kỳ đâu trong CV - PHẢI ĐỌC KỸ TẤT CẢ
   - Loại bỏ dấu cách, dấu gạch ngang khi trả về
   - Ví dụ: "0123456789", "+84987654321", "0987654321"
   - NẾU KHÔNG TÌM THẤY: để null

4. NGÀY SINH (date_of_birth) - QUAN TRỌNG, PHẢI TÌM:
   - ĐỌC KỸ TỪNG DÒNG trong CV để tìm ngày sinh
   - Format có thể là: DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD, DD.MM.YYYY
   - Hoặc "ngày X tháng Y năm Z", "sinh ngày X/Y/Z"
   - Tìm ở phần đầu CV, sau tên, trong phần "Thông tin cá nhân"
   - Ví dụ: "15/03/1995", "1995-03-15", "15.03.1995", "ngày 15 tháng 3 năm 1995"
   - NẾU KHÔNG TÌM THẤY: để null

5. ĐỊA CHỈ (address) - QUAN TRỌNG, PHẢI TÌM:
   - ĐỌC KỸ TỪNG DÒNG trong CV để tìm địa chỉ
   - Địa chỉ có thể sau "Địa chỉ:", "Address:", "Location:", "Nơi ở:", "Quê quán:"
   - Hoặc trong phần "Thông tin cá nhân", "Liên hệ", "Contact"
   - Địa chỉ thường có: số nhà, tên đường, phường/xã, quận/huyện, tỉnh/thành phố
   - Có thể là 1 dòng hoặc nhiều dòng - LẤY TẤT CẢ
   - Ví dụ: "123 Đường ABC, Phường XYZ, Quận 1, TP.HCM"
   - Hoặc: "Số 123, Đường ABC, Phường XYZ, Quận 1, Thành phố Hồ Chí Minh"
   - NẾU KHÔNG TÌM THẤY: để null

6. VỊ TRÍ (position):
   - Tìm vị trí công việc hiện tại hoặc mong muốn
   - Có thể ở phần "Vị trí:", "Position:", "Current Role:", hoặc trong kinh nghiệm
   - Ví dụ: "Business Analyst", "Data Engineer", "Software Developer"

7. SỐ NĂM KINH NGHIỆM (years_experience):
   - Tính tổng số năm từ tất cả các công việc đã làm
   - Hoặc tìm số năm được ghi rõ: "3 năm kinh nghiệm", "5+ years"
   - Trả về số nguyên (0 nếu không có)

8. KỸ NĂNG (skills):
   - Liệt kê TẤT CẢ kỹ năng: technical skills, soft skills, tools, languages
   - Tìm trong section "Skills", "Kỹ năng", hoặc rải rác trong CV
   - Ví dụ: ["Python", "SQL", "AWS", "Agile", "Communication"]

9. GIỚI THIỆU (summary):
   - Lấy đoạn giới thiệu bản thân, mục tiêu nghề nghiệp
   - Tìm trong section "Summary", "About", "Objective", "Giới thiệu"
   - Hoặc đoạn văn dài ở đầu CV (sau thông tin cá nhân)

10. HỌC VẤN (education):
    - Trích xuất TẤT CẢ các bằng cấp, trường học
    - Mỗi mục gồm: tên trường, bằng cấp, chuyên ngành, năm tốt nghiệp
    - Ví dụ: [{{"school": "Đại học Bách Khoa", "degree": "Cử nhân", "major": "Công nghệ thông tin", "year": "2020"}}]

11. KINH NGHIỆM (experiences):
    - Trích xuất TẤT CẢ các công việc đã làm
    - Mỗi mục gồm: tên công ty, vị trí, thời gian, mô tả công việc
    - Format: "Công ty X - Vị trí Y (Thời gian): Mô tả chi tiết..."
    - Hoặc format tự do nhưng đầy đủ thông tin

12. DỰ ÁN (projects):
    - Trích xuất TẤT CẢ các dự án đã tham gia
    - Mỗi mục gồm: tên dự án, mô tả, công nghệ sử dụng
    - Format: "Tên dự án: Mô tả chi tiết..."

13. MẠNG XÃ HỘI (social_links):
    - Tìm tất cả links: LinkedIn, GitHub, Facebook, Twitter, Portfolio, etc.
    - Format đầy đủ URL: "https://linkedin.com/in/username"

YÊU CẦU: BẠN PHẢI TRẢ VỀ JSON THUẦN, KHÔNG CÓ BẤT KỲ TEXT NÀO KHÁC, KHÔNG CÓ MARKDOWN, KHÔNG CÓ GIẢI THÍCH.

TRẢ VỀ JSON VỚI FORMAT SAU (CHỈ JSON, KHÔNG CÓ TEXT THÊM):

{{
    "name": "Họ và tên đầy đủ hoặc null",
    "email": "email@example.com hoặc null",
    "phone": "0123456789 hoặc null",
    "date_of_birth": "DD/MM/YYYY hoặc null",
    "address": "Địa chỉ đầy đủ hoặc null",
    "position": "Vị trí công việc chính xác hoặc null",
    "years_experience": số nguyên (0 nếu không có),
    "skills": ["skill1", "skill2", ...],
    "summary": "Giới thiệu bản thân đầy đủ hoặc null",
    "education": [
        {{
            "school": "Tên trường",
            "degree": "Bằng cấp",
            "major": "Chuyên ngành",
            "year": "Năm tốt nghiệp"
        }}
    ],
    "experiences": [
        "Mô tả công việc 1 đầy đủ với tên công ty, vị trí, thời gian",
        "Mô tả công việc 2 đầy đủ"
    ],
    "projects": [
        "Mô tả dự án 1 đầy đủ",
        "Mô tả dự án 2 đầy đủ"
    ],
    "social_links": [
        "https://linkedin.com/...",
        "https://github.com/..."
    ]
}}

QUY TẮC QUAN TRỌNG - ĐỌC KỸ:
1. CV trên là CV THỰC TẾ - bạn PHẢI đọc CHÍNH XÁC từ CV, KHÔNG được đoán mò
2. Trích xuất 100% thông tin có trong CV, KHÔNG BỎ SÓT BẤT KỲ THÔNG TIN NÀO
3. Đọc KỸ từng dòng, từng từ trong CV để tìm thông tin
4. Nếu có nhiều mục (nhiều công việc, nhiều dự án, nhiều bằng cấp), trích xuất TẤT CẢ
5. CHỈ TRẢ VỀ JSON THUẦN - BẮT ĐẦU BẰNG {{ VÀ KẾT THÚC BẰNG }} - KHÔNG CÓ ```json, KHÔNG CÓ ```, KHÔNG CÓ GIẢI THÍCH
6. Nếu không tìm thấy: string → null, array → []
7. Đảm bảo format JSON hợp lệ, có thể parse được
8. Ưu tiên thông tin CHÍNH XÁC - nếu THẤY trong CV thì PHẢI trích xuất, nếu KHÔNG THẤY thì để null
9. Đối với địa chỉ: ĐỌC KỸ phần đầu CV, tìm sau "Địa chỉ:", "Address:", "Location:", hoặc dòng có địa chỉ đầy đủ
10. Đối với tên: ĐỌC KỸ dòng đầu tiên hoặc sau "Họ tên:", "Name:", "Full Name:" - phải là tên đầy đủ có khoảng trắng, CHÍNH XÁC như trong CV
11. Đối với số điện thoại: ĐỌC KỸ tìm số có 10-11 chữ số, format 0xxxxxxxxx hoặc +84xxxxxxxxx, CHÍNH XÁC như trong CV
12. Đối với email: ĐỌC KỸ tìm tất cả email có format xxx@xxx.xxx, CHÍNH XÁC như trong CV
13. Đối với học vấn: ĐỌC KỸ tìm tất cả trường học, bằng cấp, chuyên ngành, năm tốt nghiệp - trích xuất TẤT CẢ
14. Đối với kinh nghiệm: ĐỌC KỸ tìm tất cả công việc với tên công ty, vị trí, thời gian, mô tả - trích xuất TẤT CẢ, CHÍNH XÁC như trong CV
15. Đối với dự án: ĐỌC KỸ tìm tất cả dự án với tên, mô tả, công nghệ - trích xuất TẤT CẢ, CHÍNH XÁC như trong CV
16. Đối với kỹ năng: ĐỌC KỸ tìm TẤT CẢ kỹ năng trong CV, không bỏ sót

LƯU Ý QUAN TRỌNG:
- CV trên là CV THỰC TẾ, mọi thông tin bạn trích xuất PHẢI có trong CV
- Nếu bạn không thấy thông tin trong CV, hãy đọc lại KỸ HƠN
- Nếu bạn thấy thông tin trong CV, PHẢI trích xuất CHÍNH XÁC, không được bỏ sót
- Đừng đoán mò - chỉ trích xuất những gì THỰC SỰ có trong CV

NHẮC LẠI: CHỈ TRẢ VỀ JSON THUẦN, KHÔNG CÓ TEXT NÀO KHÁC! ĐỌC KỸ CV VÀ TRÍCH XUẤT CHÍNH XÁC!
"""
    return prompt


def extract_with_openai(prompt: str, api_key: str) -> Dict[str, Any]:
    """Extract với OpenAI API"""
    try:
        import openai
        
        client = openai.OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Hoặc "gpt-4" nếu muốn chính xác hơn
            messages=[
                {"role": "system", "content": "Bạn là chuyên gia phân tích CV. Trả về kết quả dưới dạng JSON hợp lệ."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Thấp để kết quả nhất quán
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        return json.loads(result_text)
    
    except ImportError:
        print("OpenAI library not installed. Install with: pip install openai")
        return {}
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return {}


def extract_with_anthropic(prompt: str, api_key: str) -> Dict[str, Any]:
    """Extract với Anthropic Claude API"""
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=api_key)
        
        message = client.messages.create(
            model="claude-3-haiku-20240307",  # Hoặc "claude-3-sonnet-20240229"
            max_tokens=2000,
            temperature=0.1,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        result_text = message.content[0].text
        # Parse JSON từ response
        # Claude có thể trả về text có JSON, cần extract
        json_start = result_text.find('{')
        json_end = result_text.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = result_text[json_start:json_end]
            return json.loads(json_str)
        return {}
    
    except ImportError:
        print("Anthropic library not installed. Install with: pip install anthropic")
        return {}
    except Exception as e:
        print(f"Anthropic API error: {e}")
        return {}


def extract_with_gemini(prompt: str, api_key: str) -> Dict[str, Any]:
    """Extract với Google Gemini API"""
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        
        # List models trước để tìm model thực tế khả dụng
        model = None
        model_name_used = None
        
        try:
            print("[Gemini] Đang list models để tìm model khả dụng...")
            models = genai.list_models()
            model_list = list(models)
            print(f"[Gemini] Tìm thấy {len(model_list)} models")
            
            # In danh sách models để debug
            print("[Gemini] Danh sách models hỗ trợ generateContent:")
            available_models = []
            for m in model_list:
                if 'generateContent' in m.supported_generation_methods:
                    print(f"  - {m.name}")
                    available_models.append(m)
            
            # Ưu tiên tìm gemini-1.5-flash trong danh sách
            excluded_patterns = ['2.5', '2.0', 'exp', 'ultra', 'computer-use', 'tts', 'image-generation', 'lite']
            
            # Tìm gemini-1.5-flash trong danh sách
            for m in available_models:
                model_name_lower = m.name.lower()
                
                # Bỏ qua model trả phí
                if any(excluded in model_name_lower for excluded in excluded_patterns):
                    continue
                
                # Ưu tiên tìm gemini-1.5-flash
                if '1.5-flash' in model_name_lower and 'gemini' in model_name_lower:
                    try:
                        test_model = genai.GenerativeModel(m.name)
                        # Test model bằng cách thử generate với prompt ngắn
                        try:
                            test_response = test_model.generate_content("test", generation_config={"max_output_tokens": 1})
                            model = test_model
                            model_name_used = m.name
                            print(f"[Gemini] ✓ Sử dụng model: {m.name}")
                            break
                        except Exception as test_e:
                            # Model không thể generate, bỏ qua
                            print(f"[Gemini] Model {m.name} không thể generate: {str(test_e)[:150]}")
                            continue
                    except Exception as e:
                        error_msg = str(e)[:150]
                        print(f"[Gemini] Model {m.name} không khả dụng: {error_msg}")
                        continue
            
            # Nếu không tìm thấy gemini-1.5-flash, thử các model flash khác
            if not model:
                for m in available_models:
                    model_name_lower = m.name.lower()
                    
                    if any(excluded in model_name_lower for excluded in excluded_patterns):
                        continue
                    
                    # Tìm model có flash
                    if 'flash' in model_name_lower and 'gemini' in model_name_lower:
                        try:
                            test_model = genai.GenerativeModel(m.name)
                            try:
                                test_response = test_model.generate_content("test", generation_config={"max_output_tokens": 1})
                                model = test_model
                                model_name_used = m.name
                                print(f"[Gemini] ✓ Sử dụng model: {m.name}")
                                break
                            except Exception as test_e:
                                print(f"[Gemini] Model {m.name} không thể generate: {str(test_e)[:150]}")
                                continue
                        except Exception as e:
                            error_msg = str(e)[:150]
                            print(f"[Gemini] Model {m.name} không khả dụng: {error_msg}")
                            continue
            
            # Nếu vẫn không tìm thấy, thử model pro
            if not model:
                for m in available_models:
                    model_name_lower = m.name.lower()
                    
                    if any(excluded in model_name_lower for excluded in excluded_patterns):
                        continue
                    
                    # Tìm model có pro
                    if 'pro' in model_name_lower and 'gemini' in model_name_lower:
                        try:
                            test_model = genai.GenerativeModel(m.name)
                            try:
                                test_response = test_model.generate_content("test", generation_config={"max_output_tokens": 1})
                                model = test_model
                                model_name_used = m.name
                                print(f"[Gemini] ✓ Sử dụng model: {m.name}")
                                break
                            except Exception as test_e:
                                print(f"[Gemini] Model {m.name} không thể generate: {str(test_e)[:150]}")
                                continue
                        except Exception as e:
                            error_msg = str(e)[:150]
                            print(f"[Gemini] Model {m.name} không khả dụng: {error_msg}")
                            continue
                            
        except Exception as e:
            print(f"[Gemini] Lỗi khi list models: {e}")
            import traceback
            traceback.print_exc()
        
        # Nếu vẫn không tìm thấy từ list_models, thử các model name phổ biến
        if not model:
            model_names = ['gemini-flash-latest', 'gemini-pro-latest', 'gemini-1.5-pro']
            for model_name in model_names:
                try:
                    test_model = genai.GenerativeModel(model_name)
                    # Test model
                    try:
                        test_response = test_model.generate_content("test", generation_config={"max_output_tokens": 1})
                        model = test_model
                        model_name_used = model_name
                        print(f"[Gemini] ✓ Sử dụng model trực tiếp: {model_name}")
                        break
                    except Exception as test_e:
                        print(f"[Gemini] Model {model_name} không thể generate: {str(test_e)[:100]}")
                        continue
                except Exception as e:
                    print(f"[Gemini] Model {model_name} không khả dụng: {str(e)[:100]}")
                    continue
        
        if not model:
            raise Exception(f"Không tìm thấy Gemini model khả dụng. API key: {'***' + api_key[-4:] if len(api_key) > 4 else 'INVALID'}. Vui lòng kiểm tra API key và quyền truy cập.")
        
        # Tạo generation config - thêm response_mime_type để force JSON
        generation_config = {
            "temperature": 0.0,  # Cực thấp để kết quả chính xác nhất
            "max_output_tokens": 8000,  # Tăng lên để đủ cho tất cả thông tin
            "top_p": 0.95,
            "top_k": 40,
        }
        
        # Thử với response_mime_type nếu model hỗ trợ
        try:
            # Một số model Gemini hỗ trợ response_mime_type
            response = model.generate_content(
                prompt,
                generation_config={
                    **generation_config,
                    "response_mime_type": "application/json"
                }
            )
        except Exception as e:
            error_str = str(e)
            
            # Kiểm tra lỗi 404 - model không tồn tại
            if "404" in error_str or "not found" in error_str.lower():
                print(f"[Gemini] Model {model_name_used} không tồn tại (404), tìm model khác...")
                # Tìm model khác từ danh sách
                model_found = False
                try:
                    models = genai.list_models()
                    model_list = list(models)
                    excluded_patterns = ['2.5', '2.0', 'exp', 'ultra', 'computer-use', 'tts', 'image-generation', 'lite']
                    
                    for m in model_list:
                        if 'generateContent' not in m.supported_generation_methods:
                            continue
                        model_name_lower = m.name.lower()
                        if any(excluded in model_name_lower for excluded in excluded_patterns):
                            continue
                        if m.name == model_name_used:
                            continue  # Bỏ qua model đã thử
                        
                        # Thử model khác
                        if ('flash' in model_name_lower or 'pro' in model_name_lower) and 'gemini' in model_name_lower:
                            try:
                                alt_model = genai.GenerativeModel(m.name)
                                # Test model
                                try:
                                    test_response = alt_model.generate_content("test", generation_config={"max_output_tokens": 1})
                                    model = alt_model
                                    model_name_used = m.name
                                    print(f"[Gemini] ✓ Chuyển sang model: {m.name}")
                                    # Thử lại với model mới (không dùng response_mime_type)
                                    response = model.generate_content(prompt, generation_config=generation_config)
                                    model_found = True
                                    break
                                except Exception as test_e:
                                    print(f"[Gemini] Model {m.name} không thể generate: {str(test_e)[:100]}")
                                    continue
                            except Exception as e2:
                                continue
                    
                    if not model_found:
                        raise Exception(f"Không tìm thấy Gemini model khả dụng. Model {model_name_used} không tồn tại. Vui lòng kiểm tra API key.")
                except Exception as e2:
                    if "Không tìm thấy" not in str(e2):
                        raise Exception(f"Model {model_name_used} không tồn tại và không thể tìm model thay thế: {str(e2)[:200]}")
                    raise
            
            # Kiểm tra lỗi quota
            elif "quota" in error_str.lower() or "ResourceExhausted" in error_str or "429" in error_str:
                print(f"[Gemini] Lỗi quota với model {model_name_used}: {error_str[:200]}")
                raise Exception(f"""QUOTA ĐÃ HẾT - API KEY CỦA BẠN ĐÃ HẾT LƯỢNG SỬ DỤNG MIỄN PHÍ.

GIẢI PHÁP:
1. Đợi vài phút (quota có thể reset theo phút/ngày)
2. Kiểm tra quota tại: https://ai.dev/rate-limit
3. Nâng cấp API key lên gói trả phí nếu cần sử dụng nhiều hơn
4. Hoặc tạo API key mới (nếu có thể)

Thông tin chi tiết: https://ai.google.dev/gemini-api/docs/rate-limits""")
            
            # Nếu không hỗ trợ response_mime_type, dùng cách cũ
            else:
                print(f"[Gemini] Không hỗ trợ response_mime_type, dùng cách cũ: {e}")
                try:
                    response = model.generate_content(
                        prompt,
                        generation_config=generation_config
                    )
                except Exception as e2:
                    error_str2 = str(e2)
                    if "404" in error_str2 or "not found" in error_str2.lower():
                        raise Exception(f"Model {model_name_used} không tồn tại. Vui lòng kiểm tra API key và thử lại.")
                    elif "quota" in error_str2.lower() or "ResourceExhausted" in error_str2 or "429" in error_str2:
                        raise Exception(f"""QUOTA ĐÃ HẾT - API KEY CỦA BẠN ĐÃ HẾT LƯỢNG SỬ DỤNG MIỄN PHÍ.

GIẢI PHÁP:
1. Đợi vài phút (quota có thể reset theo phút/ngày)
2. Kiểm tra quota tại: https://ai.dev/rate-limit
3. Nâng cấp API key lên gói trả phí nếu cần sử dụng nhiều hơn
4. Hoặc tạo API key mới (nếu có thể)

Thông tin chi tiết: https://ai.google.dev/gemini-api/docs/rate-limits""")
                    raise
        
        result_text = response.text.strip()
        
        # Loại bỏ markdown code blocks nếu có
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        result_text = result_text.strip()
        
        # Parse JSON từ response
        json_start = result_text.find('{')
        json_end = result_text.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = result_text[json_start:json_end]
            try:
                parsed = json.loads(json_str)
                # Log raw response để debug
                print(f"[Gemini] Raw AI response - Email: {parsed.get('email')}, Phone: {parsed.get('phone')}, Address: {parsed.get('address')}, DOB: {parsed.get('date_of_birth')}")
                # Validate và clean data
                return clean_ai_result(parsed)
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
                print(f"Response text preview: {result_text[:500]}")
                return {}
        
        # Nếu không tìm thấy JSON, thử parse toàn bộ
        try:
            parsed = json.loads(result_text)
            return clean_ai_result(parsed)
        except:
            print(f"Could not parse JSON from Gemini response")
            print(f"Response preview: {result_text[:500]}")
            return {}
    
    except ImportError:
        print("Google Generative AI library not installed. Install with: pip install google-generativeai")
        return {}
    except Exception as e:
        print(f"Gemini API error: {e}")
        import traceback
        traceback.print_exc()
        return {}


def clean_ai_result(data: Dict[str, Any]) -> Dict[str, Any]:
    """Làm sạch và validate kết quả từ AI - cải thiện để giữ lại tất cả thông tin"""
    cleaned = {}
    
    # Clean name - cải thiện logic
    name = data.get("name", "")
    if name and isinstance(name, str):
        name = name.strip()
        # Loại bỏ các giá trị không hợp lệ
        invalid_names = ["null", "none", "n/a", "không xác định", "(không xác định)", 
                        "undefined", "not available", ""]
        if name.lower() not in invalid_names and len(name) >= 3:
            # Loại bỏ email, phone nếu vô tình bị lấy vào
            if "@" not in name and not re.search(r"(\+84|0)\d{9,10}", name):
                cleaned["name"] = name
            else:
                cleaned["name"] = None
        else:
            cleaned["name"] = None
    else:
        cleaned["name"] = None
    
    # Clean email - cải thiện để giữ lại nhiều format hơn
    email = data.get("email", "")
    if email and isinstance(email, str):
        email = email.strip()
        # Kiểm tra format email cơ bản: có @ và có ít nhất 1 ký tự trước @, 1 ký tự sau @
        if "@" in email:
            parts = email.split("@")
            if len(parts) == 2 and len(parts[0]) > 0 and len(parts[1]) > 0:
                # Kiểm tra có dấu chấm trong phần domain hoặc domain hợp lệ
                if "." in parts[1] or len(parts[1]) > 0:
                    cleaned["email"] = email
                else:
                    cleaned["email"] = None
            else:
                cleaned["email"] = None
        else:
            cleaned["email"] = None
    elif email is None:
        cleaned["email"] = None
    else:
        cleaned["email"] = None
    
    # Clean phone - cải thiện để chấp nhận nhiều format hơn
    phone = data.get("phone", "")
    if phone and isinstance(phone, str):
        phone = phone.strip()
        # Loại bỏ ký tự không phải số và +
        phone_clean = "".join(c for c in phone if c.isdigit() or c == "+")
        # Chấp nhận số điện thoại Việt Nam: 10-11 số (0xxxxxxxxx hoặc +84xxxxxxxxx)
        if len(phone_clean) >= 10:
            # Nếu bắt đầu bằng +84, phải có ít nhất 12 ký tự (+84 + 9 số)
            if phone_clean.startswith("+84") and len(phone_clean) >= 12:
                cleaned["phone"] = phone_clean
            # Nếu bắt đầu bằng 0, phải có 10-11 số
            elif phone_clean.startswith("0") and len(phone_clean) >= 10:
                cleaned["phone"] = phone_clean
            # Nếu không có +84 hoặc 0, nhưng có 10-11 số, thêm 0 vào đầu
            elif len(phone_clean) == 10 or len(phone_clean) == 11:
                if not phone_clean.startswith("0"):
                    cleaned["phone"] = "0" + phone_clean
                else:
                    cleaned["phone"] = phone_clean
            else:
                cleaned["phone"] = None
        else:
            cleaned["phone"] = None
    elif phone is None:
        cleaned["phone"] = None
    else:
        cleaned["phone"] = None
    
    # Clean other string fields - giữ lại tất cả thông tin hợp lệ
    for key in ["date_of_birth", "address", "position", "summary"]:
        value = data.get(key, "")
        if value and isinstance(value, str):
            value = value.strip()
            # Chỉ loại bỏ các giá trị thực sự không hợp lệ
            invalid_values = ["null", "none", "n/a", "undefined", "not available", ""]
            if value.lower() not in invalid_values and len(value) > 0:
                cleaned[key] = value
            else:
                cleaned[key] = None
        elif value is None:
            cleaned[key] = None
        else:
            # Nếu không phải string, convert sang string
            cleaned[key] = str(value).strip() if value else None
    
    # Clean years_experience
    years = data.get("years_experience", 0)
    if isinstance(years, (int, float)):
        cleaned["years_experience"] = max(0, int(years))
    else:
        cleaned["years_experience"] = 0
    
    # Clean arrays - giữ lại TẤT CẢ thông tin hợp lệ, không loại bỏ quá nhiều
    for key in ["skills", "education", "experiences", "projects", "social_links"]:
        value = data.get(key, [])
        if isinstance(value, list):
            cleaned_list = []
            for item in value:
                if isinstance(item, dict):
                    # Clean dict items (education) - giữ lại tất cả field có giá trị
                    cleaned_dict = {}
                    for k, v in item.items():
                        if v is not None:
                            v_str = str(v).strip()
                            # Chỉ loại bỏ các giá trị thực sự rỗng
                            if v_str and v_str.lower() not in ["null", "none", "n/a", "undefined", ""]:
                                cleaned_dict[k] = v_str
                    # Thêm vào nếu có ít nhất 1 field hợp lệ
                    if cleaned_dict:
                        cleaned_list.append(cleaned_dict)
                elif item is not None:
                    item_str = str(item).strip()
                    # Giữ lại nếu có nội dung (dù chỉ 1 ký tự)
                    if item_str and item_str.lower() not in ["null", "none", "n/a", "undefined", ""]:
                        # Giữ nguyên toàn bộ, không cắt ngắn
                        cleaned_list.append(item_str)
            cleaned[key] = cleaned_list
        elif value is not None:
            # Nếu không phải list, thử convert
            cleaned[key] = [str(value).strip()] if str(value).strip() else []
        else:
            cleaned[key] = []
    
    return cleaned


def merge_ai_results(ai_result: Dict[str, Any], regex_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge kết quả từ AI và regex
    Ưu tiên AI, nhưng bổ sung từ regex nếu AI thiếu hoặc không đầy đủ
    """
    merged = {}
    
    for key in ["name", "email", "phone", "date_of_birth", "address", "position", 
                "years_experience", "skills", "summary", "education", "experiences", 
                "projects", "social_links"]:
        ai_value = ai_result.get(key)
        regex_value = regex_result.get(key)
        
        # Xử lý theo từng loại
        if key in ["skills", "education", "experiences", "projects", "social_links"]:
            # Arrays: merge và loại bỏ duplicate
            ai_list = ai_value if isinstance(ai_value, list) else []
            regex_list = regex_value if isinstance(regex_value, list) else []
            
            # Kết hợp và loại bỏ duplicate
            combined = []
            seen = set()
            
            # Ưu tiên AI trước
            for item in ai_list:
                if isinstance(item, dict):
                    item_str = json.dumps(item, sort_keys=True)
                else:
                    item_str = str(item).lower().strip()
                
                if item_str not in seen:
                    combined.append(item)
                    seen.add(item_str)
            
            # Bổ sung từ regex nếu chưa có
            for item in regex_list:
                if isinstance(item, dict):
                    item_str = json.dumps(item, sort_keys=True)
                else:
                    item_str = str(item).lower().strip()
                
                if item_str not in seen:
                    combined.append(item)
                    seen.add(item_str)
            
            merged[key] = combined
        
        elif key == "years_experience":
            # Số năm: lấy giá trị lớn hơn
            ai_years = int(ai_value) if isinstance(ai_value, (int, float)) else 0
            regex_years = int(regex_value) if isinstance(regex_value, (int, float)) else 0
            merged[key] = max(ai_years, regex_years)
        
        else:
            # String fields: ưu tiên AI, fallback regex
            if ai_value and isinstance(ai_value, str):
                ai_str = ai_value.strip()
                if ai_str and ai_str.lower() not in ["null", "none", "n/a", ""]:
                    merged[key] = ai_str
                elif regex_value and isinstance(regex_value, str):
                    regex_str = regex_value.strip()
                    if regex_str:
                        merged[key] = regex_str
                    else:
                        merged[key] = None
                else:
                    merged[key] = None
            elif regex_value and isinstance(regex_value, str):
                regex_str = regex_value.strip()
                merged[key] = regex_str if regex_str else None
            else:
                merged[key] = None
    
    return merged
