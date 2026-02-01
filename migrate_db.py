"""
Script để migrate database - thêm các cột mới vào bảng CV
Chạy script này nếu bạn đã có database cũ và muốn thêm các trường mới
"""
import os
import sqlite3
import sys
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_PATH = Path("ai_recruitment.db")

# Nếu database chưa tồn tại, bỏ qua migration (sẽ được tạo bởi Base.metadata.create_all)
if not DB_PATH.exists():
    print("Database chua ton tai. Database se duoc tao tu dong khi chay app.")
    exit(0)

print("Dang kiem tra va cap nhat database...")

try:
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Kiểm tra xem bảng có tồn tại không
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cvs'")
    if not cursor.fetchone():
        print("Bang 'cvs' chua ton tai. Database se duoc tao tu dong.")
        conn.close()
        exit(0)
    
    # Kiểm tra các cột hiện có
    cursor.execute("PRAGMA table_info(cvs)")
    columns = [row[1] for row in cursor.fetchall()]
except sqlite3.Error as e:
    print(f"LOI: Khong the ket noi database: {e}")
    exit(0)

# Thêm các cột mới nếu chưa có
new_columns = {
    "date_of_birth": "TEXT",
    "address": "TEXT",
    "social_links": "TEXT",
    "education": "TEXT"
}

for col_name, col_type in new_columns.items():
    if col_name not in columns:
        print(f"Dang them cot: {col_name}")
        try:
            cursor.execute(f"ALTER TABLE cvs ADD COLUMN {col_name} {col_type}")
            print(f"OK: Da them cot {col_name}")
        except Exception as e:
            print(f"LOI: Khi them cot {col_name}: {e}")
    else:
        print(f"OK: Cot {col_name} da ton tai")

conn.commit()
conn.close()

print("\nOK: Migration hoan tat!")