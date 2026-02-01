from sqlalchemy import Column, Integer, String, Text, Float
from app.models.database import Base

class CV(Base):
    __tablename__ = "cvs"

    id = Column(Integer, primary_key=True, index=True)

    # ===== THÔNG TIN ỨNG VIÊN =====
    name = Column(String)
    email = Column(String)
    phone = Column(String)
    date_of_birth = Column(String)              # Ngày tháng năm sinh
    address = Column(Text)                      # Địa chỉ
    social_links = Column(Text)                 # JSON - Link mạng xã hội
    education = Column(Text)                    # JSON - Học vấn

    # Vị trí & kinh nghiệm
    candidate_position = Column(String)        # ghi trong CV (Data Engineer…)
    inferred_position = Column(String)          # suy luận từ skill
    candidate_years = Column(Integer)

    # Dữ liệu bóc tách
    candidate_skills = Column(Text)             # JSON
    summary = Column(Text)                      # Giới thiệu bản thân
    experiences = Column(Text)                  # JSON - Kinh nghiệm (WORK EXPERIENCE)
    projects = Column(Text)                     # JSON - Dự án (PROJECTS)

    # ===== YÊU CẦU TUYỂN (JD) =====
    target_position = Column(String)
    required_years = Column(Integer)
    required_skills = Column(Text)              # JSON

    # ===== KẾT QUẢ ĐÁNH GIÁ =====
    score = Column(Float)
