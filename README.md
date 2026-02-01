# AI Recruitment System

Hệ thống tuyển dụng sử dụng AI để phân tích CV và tìm kiếm ứng viên phù hợp.

## Tính năng

### 1. Trích xuất thông tin từ CV
Hệ thống tự động trích xuất các trường dữ liệu sau từ CV:
- ✅ Họ tên
- ✅ Email
- ✅ Số điện thoại
- ✅ Ngày tháng năm sinh
- ✅ Địa chỉ
- ✅ Giới thiệu bản thân
- ✅ Link mạng xã hội (LinkedIn, GitHub, Facebook, etc.)
- ✅ Học vấn
- ✅ Kinh nghiệm (WORK EXPERIENCE)
- ✅ Kỹ năng (Skills)
- ✅ Dự án (PROJECTS)

### 2. Tìm kiếm ứng viên
- **Tìm kiếm ngôn ngữ tự nhiên**: Hỗ trợ tìm kiếm bằng câu tự nhiên như "3 năm kn data engineer, biết aws"
- **Lọc nâng cao**: Lọc theo vị trí, số năm kinh nghiệm, kỹ năng

### 3. Giao diện người dùng
- Upload CV và mô tả công việc
- Xem danh sách ứng viên
- Xem chi tiết CV đầy đủ
- Tìm kiếm và lọc ứng viên

## Cài đặt

### Cách 1: Docker (Khuyến nghị)

1. Build và chạy containers:
```bash
docker-compose up --build
```

Hoặc sử dụng Makefile:
```bash
make build
make up
```

2. Truy cập ứng dụng:
- Frontend: http://localhost
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

Xem thêm hướng dẫn chi tiết trong [DOCKER.md](DOCKER.md)

### Cách 2: Local Development

1. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

2. Chạy server:
```bash
uvicorn app.main:app --reload
```

3. Mở frontend:
- Mở file `frontend/index.html` trong trình duyệt
- Hoặc sử dụng Live Server (VS Code extension)

## Lưu ý về Database

Nếu bạn đã có database cũ, cần xóa file `ai_recruitment.db` để tạo lại với schema mới (có thêm các trường: date_of_birth, address, social_links, education).

Hoặc chạy script migration:
```python
# Xóa database cũ và tạo mới
import os
if os.path.exists("ai_recruitment.db"):
    os.remove("ai_recruitment.db")

from app.models.database import engine, Base
Base.metadata.create_all(bind=engine)
```

## API Endpoints

- `POST /cv/analyze` - Phân tích CV và lưu vào database
- `GET /cv/list` - Lấy danh sách tất cả CV
- `GET /cv/filter-advanced` - Lọc CV theo tiêu chí
- `GET /cv/search?query=...` - Tìm kiếm CV bằng ngôn ngữ tự nhiên

## Cấu trúc dự án

```
ai_recruitment/
├── app/
│   ├── api/
│   │   └── cv_upload.py      # API endpoints
│   ├── models/
│   │   ├── cv_model.py        # CV database model
│   │   └── database.py        # Database configuration
│   ├── services/
│   │   ├── cv_reader.py       # Đọc file CV (PDF, DOCX)
│   │   ├── cv_extractor.py   # Trích xuất thông tin từ CV
│   │   ├── cv_parser.py       # Parse CV text
│   │   ├── cv_matcher.py      # So khớp CV với JD
│   │   └── position_infer.py  # Suy luận vị trí từ skills
│   └── main.py                # FastAPI app
├── frontend/
│   ├── index.html             # Trang upload CV
│   ├── list.html              # Trang danh sách CV
│   ├── app.js                 # JavaScript logic
│   └── styles.css             # CSS styles
└── uploads/                   # Thư mục lưu CV đã upload