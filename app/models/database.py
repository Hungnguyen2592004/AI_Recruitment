from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

import os
from pathlib import Path

# Tạo thư mục data nếu chưa có
data_dir = Path("./data")
data_dir.mkdir(exist_ok=True)

DATABASE_URL = "sqlite:///./data/ai_recruitment.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()
