from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pathlib import Path
import os
import shutil
import json
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.services.cv_reader import read_cv
from app.services.cv_matcher import match_cv_with_jd
from app.services.ai_extractor import extract_with_ai, clean_ai_result
from app.models.database import SessionLocal
from app.models.cv_model import CV

router = APIRouter(prefix="/cv", tags=["CV"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# ================= HELPER =================
def safe_json_loads(value):
    try:
        return json.loads(value) if value else []
    except Exception:
        return []


# ================= ANALYZE =================
@router.post("/analyze")
def analyze_cv(
    file: UploadFile = File(...),
    jd_text: str = Form(...)
):
    # 1. Save file
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2. Read CV
    cv_text = read_cv(file_path)
    
    # Log CV text để debug 
    print(f"[CV] CV text preview (first 500 chars): {cv_text[:500]}")
    print(f"[CV] CV text total length: {len(cv_text)} characters")
    print(f"[CV] CV text has {len(cv_text.splitlines())} lines")

    # 3. Extract from CV bằng AI 
    ai_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or os.getenv("GEMINI_API_KEY")
    ai_provider = os.getenv("AI_PROVIDER", "gemini")
    
    if not ai_api_key:
        raise HTTPException(
            status_code=400,
            detail="API key không được cấu hình. Vui lòng cấu hình OPENAI_API_KEY, ANTHROPIC_API_KEY hoặc GEMINI_API_KEY"
        )
    
    print(f"[AI] Using {ai_provider.upper()} AI for CV extraction...")
    print(f"[AI] CV text length: {len(cv_text)} characters")
    
    # Extract bằng AI
    try:
        ai_result = extract_with_ai(cv_text, ai_api_key, ai_provider)
    except Exception as e:
        error_msg = str(e)
        print(f"[AI] Error during extraction: {error_msg}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi trích xuất thông tin từ CV: {error_msg}"
        )
    
    if not ai_result:
        raise HTTPException(
            status_code=500,
            detail="Không thể trích xuất thông tin từ CV. Vui lòng kiểm tra API key và thử lại."
        )
    
    # Clean và validate kết quả AI
    cleaned_result = clean_ai_result(ai_result)
    
    print(f"[AI] AI extraction completed successfully!")
    print(f"[AI] - Name: {cleaned_result.get('name', 'N/A')}")
    print(f"[AI] - Email: {cleaned_result.get('email', 'N/A')}")
    print(f"[AI] - Phone: {cleaned_result.get('phone', 'N/A')}")
    print(f"[AI] - Address: {cleaned_result.get('address', 'N/A')}")
    print(f"[AI] - Position: {cleaned_result.get('position', 'N/A')}")
    print(f"[AI] - Years: {cleaned_result.get('years_experience', 0)}")
    print(f"[AI] - Skills: {len(cleaned_result.get('skills', []))} items")
    print(f"[AI] - Education: {len(cleaned_result.get('education', []))} items")
    print(f"[AI] - Experiences: {len(cleaned_result.get('experiences', []))} items")
    print(f"[AI] - Projects: {len(cleaned_result.get('projects', []))} items")
    
    # Lấy dữ liệu từ kết quả AI
    name = cleaned_result.get("name") or "(Không xác định)"
    email = cleaned_result.get("email")
    phone = cleaned_result.get("phone")
    date_of_birth = cleaned_result.get("date_of_birth")
    address = cleaned_result.get("address")
    social_links = cleaned_result.get("social_links") or []
    education = cleaned_result.get("education") or []
    candidate_skills = cleaned_result.get("skills") or []
    candidate_years = cleaned_result.get("years_experience") or 0
    summary = cleaned_result.get("summary") or ""
    experiences = cleaned_result.get("experiences") or []
    projects = cleaned_result.get("projects") or []

    # 4. Extract JD bằng AI - để lấy vị trí chính xác
    from app.services.ai_extractor import extract_jd_with_ai
    from app.services.jd_extractor import extract_jd_requirements
    
    print(f"[JD] Bắt đầu extract JD - JD text length: {len(jd_text)}")
    print(f"[JD] JD preview: {jd_text[:200]}...")
    
    # Ưu tiên dùng AI để extract JD
    jd_requirements_ai = extract_jd_with_ai(jd_text, ai_api_key, ai_provider)
    
    # Nếu AI extract thành công, dùng kết quả AI; nếu không, fallback về regex
    # Kiểm tra kỹ hơn: nếu có kết quả AI và position không rỗng
    if jd_requirements_ai and isinstance(jd_requirements_ai, dict):
        ai_position = jd_requirements_ai.get("position", "")
        # Nếu AI extract được position (không rỗng, không null)
        if ai_position and ai_position.strip() and ai_position.lower() != "null":
            target_position = ai_position.strip()
            required_years = jd_requirements_ai.get("years", 0)
            required_skills = jd_requirements_ai.get("skills", [])
            print(f"[JD-AI] ✓ Extract bằng AI - Position: '{target_position}', Years: {required_years}, Skills: {len(required_skills)}")
        else:
            # AI không extract được position, fallback về regex
            print(f"[JD-AI] ❌ AI không extract được position (got: '{ai_position}'), fallback về regex...")
            jd_requirements = extract_jd_requirements(jd_text)
            target_position = jd_requirements.get("position", "")
            required_years = jd_requirements.get("years", 0)
            required_skills = jd_requirements.get("skills", [])
            print(f"[JD-Regex] Fallback - Position: '{target_position}', Years: {required_years}, Skills: {len(required_skills)}")
    else:
        # AI không trả về kết quả, fallback về regex
        print(f"[JD-AI] ❌ AI không trả về kết quả (got: {jd_requirements_ai}), fallback về regex...")
        jd_requirements = extract_jd_requirements(jd_text)
        target_position = jd_requirements.get("position", "")
        required_years = jd_requirements.get("years", 0)
        required_skills = jd_requirements.get("skills", [])
        print(f"[JD-Regex] Fallback - Position: '{target_position}', Years: {required_years}, Skills: {len(required_skills)}")
    
    # Vị trí được lấy từ JD (mô tả công việc), không phải từ CV
    candidate_position = target_position or "(Không rõ)"
    print(f"[JD] Final candidate_position: '{candidate_position}'")

    # 5. Match
    match_result = match_cv_with_jd(
        candidate_skills, 
        required_skills,
        candidate_position=candidate_position,
        target_position=target_position,
        candidate_years=candidate_years,
        required_years=required_years
    )
    score = match_result.get("score", 0)

    # 6. Save DB - Nếu trùng email thì xóa bản ghi cũ và tạo mới
    db: Session = SessionLocal()
    try:
        # Kiểm tra xem có CV nào với email này chưa
        if email:
            existing_cv = db.query(CV).filter(CV.email == email).first()
            if existing_cv:
                # Xóa bản ghi cũ
                db.delete(existing_cv)
                db.commit()
                print(f"[DB] Đã xóa CV cũ với email: {email}")
        
        # Tạo CV mới
        cv = CV(
            name=name,
            email=email,
            phone=phone,
            date_of_birth=date_of_birth,
            address=address,
            social_links=json.dumps(social_links, ensure_ascii=False) if social_links else None,
            education=json.dumps(education, ensure_ascii=False) if education else None,

            candidate_position=candidate_position,
            candidate_years=candidate_years,
            candidate_skills=json.dumps(candidate_skills, ensure_ascii=False) if candidate_skills else None,

            target_position=target_position,
            required_years=required_years,
            required_skills=json.dumps(required_skills, ensure_ascii=False) if required_skills else None,

            summary=summary,
            experiences=json.dumps(experiences, ensure_ascii=False) if experiences else None,
            projects=json.dumps(projects, ensure_ascii=False) if projects else None,

            score=score
        )
        db.add(cv)
        db.commit()
        db.refresh(cv)
        message = "CV analyzed successfully"
        
        return {
            "id": cv.id,
            "name": cv.name,
            "candidate_position": cv.candidate_position,
            "score": cv.score,
            "message": message
        }
    except Exception as e:
        db.rollback()
        error_msg = str(e)
        print(f"[ERROR] Lỗi khi lưu CV vào database: {error_msg}")
        import traceback
        traceback.print_exc()
        # Kiểm tra nếu là lỗi database
        if "disk I/O error" in error_msg or "OperationalError" in error_msg:
            raise HTTPException(
                status_code=500,
                detail="Lỗi truy cập database. Vui lòng thử lại sau."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi lưu CV: {error_msg}"
        )
    finally:
        db.close()


# ================= LIST =================
@router.get("/list")
def list_cvs():
    """Lấy danh sách tất cả CV, sắp xếp theo điểm số"""
    db = SessionLocal()
    try:
        cvs = db.query(CV).order_by(CV.score.desc(), CV.id.desc()).all()
        
        result = []
        for cv in cvs:
            result.append({
                "id": cv.id,
                "name": cv.name or "(Không xác định)",
                "email": cv.email or "",
                "phone": cv.phone or "",
                "date_of_birth": cv.date_of_birth or None,
                "address": cv.address or None,
                "social_links": safe_json_loads(cv.social_links),
                "education": safe_json_loads(cv.education),
                "position": cv.candidate_position or "(Không rõ)",
                "candidate_position": cv.candidate_position or "(Không rõ)",
                "skills": safe_json_loads(cv.candidate_skills),
                "years_experience": cv.candidate_years or 0,
                "years": cv.candidate_years or 0,
                "summary": cv.summary or "",
                "experiences": safe_json_loads(cv.experiences),
                "projects": safe_json_loads(cv.projects),
                "score": float(cv.score) if cv.score else 0.0
            })
        
        return result
    except Exception as e:
        print(f"[ERROR] Lỗi khi lấy danh sách CV: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        # Trả về danh sách rỗng thay vì throw exception
        return []
    finally:
        db.close()


# ================= FILTER ADVANCED =================
@router.get("/filter-advanced")
def filter_advanced(
    position: str = "",
    min_years: int = 0,
    skill: str = ""
):
    db = SessionLocal()
    query = db.query(CV)

    if position:
        p = position.lower().strip()
        if p:
            # Tìm trong candidate_position hoặc target_position (vị trí từ JD)
            query = query.filter(
                or_(
                    CV.candidate_position.ilike(f"%{p}%"),
                    CV.target_position.ilike(f"%{p}%")
                )
            )

    if min_years and min_years > 0:
        query = query.filter(CV.candidate_years >= min_years)

    if skill:
        s = skill.lower().strip()
        if s:
            # Tìm trong candidate_skills (JSON string)
            query = query.filter(CV.candidate_skills.ilike(f"%{s}%"))

    try:
        cvs = query.order_by(CV.score.desc(), CV.id.desc()).all()
        
        result = []
        for cv in cvs:
            result.append({
                "id": cv.id,
                "name": cv.name or "(Không xác định)",
                "email": cv.email or "",
                "phone": cv.phone or "",
                "date_of_birth": cv.date_of_birth or None,
                "address": cv.address or None,
                "social_links": safe_json_loads(cv.social_links),
                "education": safe_json_loads(cv.education),
                "position": cv.candidate_position or "(Không rõ)",
                "candidate_position": cv.candidate_position or "(Không rõ)",
                "skills": safe_json_loads(cv.candidate_skills),
                "years_experience": cv.candidate_years or 0,
                "years": cv.candidate_years or 0,
                "summary": cv.summary or "",
                "experiences": safe_json_loads(cv.experiences),
                "projects": safe_json_loads(cv.projects),
                "score": float(cv.score) if cv.score else 0.0
            })
        
        return result
    finally:
        db.close()


# ================= SEARCH NATURAL LANGUAGE =================
@router.get("/search")
def search_cvs(query: str = ""):
    """
    Tìm kiếm CV bằng ngôn ngữ tự nhiên
    Ví dụ: "có 3 năm kn data engineer, biết aws"
    Hỗ trợ các pattern:
    - "có X năm kn/năm/years [position], biết/knows [skill]"
    - "X năm kinh nghiệm [position], [skill]"
    - "[position] với X năm, [skill]"
    """
    import re
    
    if not query:
        return []
    
    db = SessionLocal()
    query_obj = db.query(CV)
    
    query_lower = query.lower()
    
    # Trích xuất số năm kinh nghiệm - nhiều pattern hơn
    years_patterns = [
        r'có\s+(\d+)\s*(?:năm|years?|kn)',
        r'(\d+)\s*(?:năm|years?|kn)\s*(?:kinh\s+nghiệm|experience|kn)',
        r'(\d+)\s*(?:năm|years?)\s*(?:với|with)',
        r'(?:hơn|over|more\s+than)\s+(\d+)\s*(?:năm|years?)',
    ]
    
    min_years = 0
    for pattern in years_patterns:
        match = re.search(pattern, query_lower)
        if match:
            try:
                min_years = int(match.group(1))
                break
            except:
                continue
    
    # Trích xuất vị trí - mở rộng keywords với nhiều vị trí
    position_keywords = [
        # Business & Analysis
        "business analyst", "ba", "business analysis", "functional analyst",
        "data analyst", "data analysis", "business intelligence", "bi analyst",
        # Engineering
        "data engineer", "data engineering", "etl engineer", "big data engineer",
        "backend engineer", "backend developer", "server developer", "api developer",
        "frontend engineer", "frontend developer", "ui developer", "web developer",
        "fullstack", "full stack", "full-stack engineer", "full-stack developer",
        "ai engineer", "ml engineer", "machine learning engineer", "deep learning engineer",
        "devops engineer", "devops", "sre", "site reliability engineer",
        "software engineer", "software developer", "developer", "programmer",
        "mobile developer", "ios developer", "android developer",
        # Management
        "product manager", "pm", "product owner",
        "project manager", "project management", "scrum master",
        # Other
        "qa engineer", "qa", "quality assurance", "test engineer", "tester",
        "system analyst", "systems analyst", "it analyst",
    ]
    
    found_position = None
    # Ưu tiên match các keyword dài hơn trước (tránh match "analyst" khi tìm "business analyst")
    for pos in sorted(position_keywords, key=len, reverse=True):
        # Sử dụng word boundary để match chính xác hơn
        pattern = r'\b' + re.escape(pos) + r'\b'
        if re.search(pattern, query_lower):
            found_position = pos
            break
    
    # Trích xuất kỹ năng - mở rộng danh sách và tìm từ "biết", "knows", "có"
    skill_keywords = [
        # Cloud & Infrastructure
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins",
        # Programming Languages
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
        "php", "ruby", "swift", "kotlin", "scala", "r",
        # Web Frameworks
        "react", "vue", "angular", "nodejs", "next.js", "fastapi", "django", 
        "flask", "spring", "express", "nest.js",
        # Databases
        "sql", "mongodb", "postgresql", "mysql", "redis", "elasticsearch",
        "cassandra", "dynamodb",
        # Data & ML
        "spark", "hadoop", "kafka", "airflow", "machine learning", 
        "deep learning", "tensorflow", "pytorch", "pandas", "numpy",
        # Tools
        "git", "linux", "bash"
    ]
    
    found_skills = []
    
    # Pattern 1: Tìm skills sau các từ: "biết", "knows", "có", "có kinh nghiệm với"
    skill_patterns = [
        r'(?:biết|knows|know|sử dụng|sử dụng được|có kinh nghiệm với|có)\s+([a-z\s]+?)(?:,|\.|và|and|$)',
        r'([a-z\s]+?)(?:\s+(?:và|and)\s+)?(?:biết|knows)',
    ]
    
    for pattern in skill_patterns:
        matches = re.finditer(pattern, query_lower)
        for match in matches:
            skill_text = match.group(1).strip()
            # Tìm skill trong skill_text (ưu tiên match dài hơn trước)
            for skill in sorted(skill_keywords, key=len, reverse=True):
                if skill in skill_text and skill not in found_skills:
                    found_skills.append(skill)
                    break  # Chỉ lấy skill đầu tiên match trong đoạn text này
    
    # Pattern 2: Tìm trực tiếp trong query (nếu không tìm thấy bằng pattern)
    if not found_skills:
        # Ưu tiên match các skill dài hơn trước (tránh match "sql" trong "mysql")
        for skill in sorted(skill_keywords, key=len, reverse=True):
            # Sử dụng word boundary để tránh false positive
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, query_lower) and skill not in found_skills:
                found_skills.append(skill)
    
    # Áp dụng filter
    if min_years > 0:
        query_obj = query_obj.filter(CV.candidate_years >= min_years)
    
    if found_position:
        # Tìm kiếm linh hoạt: tìm trong position, skills, và cả experiences
        position_lower = found_position.lower()
        query_obj = query_obj.filter(
            or_(
                CV.candidate_position.ilike(f"%{position_lower}%"),
                CV.inferred_position.ilike(f"%{position_lower}%"),
                CV.candidate_skills.ilike(f"%{position_lower}%"),
                CV.experiences.ilike(f"%{position_lower}%"),
                CV.summary.ilike(f"%{position_lower}%")
            )
        )
    
    if found_skills:
        # Tìm CV có ít nhất một trong các skills
        from sqlalchemy import func
        conditions = []
        for skill in found_skills:
            conditions.append(CV.candidate_skills.ilike(f"%{skill}%"))
        if conditions:
            query_obj = query_obj.filter(or_(*conditions))
    
    try:
        cvs = query_obj.order_by(CV.score.desc(), CV.id.desc()).all()
        
        result = []
        for cv in cvs:
            result.append({
                "id": cv.id,
                "name": cv.name or "(Không xác định)",
                "email": cv.email or "",
                "phone": cv.phone or "",
                "date_of_birth": cv.date_of_birth or None,
                "address": cv.address or None,
                "social_links": safe_json_loads(cv.social_links),
                "education": safe_json_loads(cv.education),
                "position": cv.candidate_position or "(Không rõ)",
                "candidate_position": cv.candidate_position or "(Không rõ)",
                "skills": safe_json_loads(cv.candidate_skills),
                "years_experience": cv.candidate_years or 0,
                "years": cv.candidate_years or 0,
                "summary": cv.summary or "",
                "experiences": safe_json_loads(cv.experiences),
                "projects": safe_json_loads(cv.projects),
                "score": float(cv.score) if cv.score else 0.0
            })
        
        return result
    finally:
        db.close()
