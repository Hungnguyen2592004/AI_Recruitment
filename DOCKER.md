# Docker Setup Guide

Hướng dẫn chạy ứng dụng AI Recruitment với Docker.

## Yêu cầu

- Docker
- Docker Compose

## Cấu trúc Docker

- **App**: FastAPI chạy trên port 8000 (bao gồm cả backend và frontend)
- **Database**: SQLite (file được mount vào container)

## Cách chạy

### 1. Development Mode

```bash
# Build và chạy containers
docker-compose up --build

# Chạy ở background
docker-compose up -d --build

# Xem logs
docker-compose logs -f

# Dừng containers
docker-compose down
```

## Truy cập ứng dụng

- **Web App**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Volumes

- `./uploads` - Thư mục chứa CV đã upload
- `./ai_recruitment.db` - Database file (SQLite)
- `./data` - Thư mục data (production)

## Troubleshooting

### 1. Lỗi port đã được sử dụng

Nếu port 8000 đã được sử dụng, sửa trong `docker-compose.yml`:

```yaml
ports:
  - "8001:8000"  # Thay đổi port
```

### 2. Lỗi permission

Trên Linux/Mac, có thể cần fix permission:

```bash
sudo chown -R $USER:$USER uploads/
sudo chmod -R 755 uploads/
```

### 3. Rebuild containers

```bash
# Xóa containers và images cũ
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### 4. Xem logs

```bash
# Tất cả services
docker-compose logs -f

# Chỉ app service
docker-compose logs -f app
```

### 5. Vào container để debug

```bash
# Vào app container
docker-compose exec app bash
```

## Environment Variables

Có thể thêm environment variables trong `docker-compose.yml`:

```yaml
environment:
  - DATABASE_URL=sqlite:///./ai_recruitment.db
  - DEBUG=True
```

## Health Checks

Container có health check tự động:
- App: Kiểm tra endpoint `/`

Xem status:
```bash
docker-compose ps
```