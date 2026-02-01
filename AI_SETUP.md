# Hướng dẫn cấu hình AI Extraction

## Tổng quan

Hệ thống hỗ trợ sử dụng AI (OpenAI GPT hoặc Anthropic Claude) để phân tích CV chính xác hơn so với regex thông thường.

## Cách sử dụng

### 1. Lấy API Key

#### OpenAI:
1. Đăng ký tại: https://platform.openai.com/
2. Tạo API key tại: https://platform.openai.com/api-keys
3. Copy API key

#### Anthropic Claude:
1. Đăng ký tại: https://console.anthropic.com/
2. Tạo API key tại: https://console.anthropic.com/settings/keys
3. Copy API key

### 2. Cấu hình

#### Cách 1: Sử dụng file .env (khuyến nghị)

1. Tạo file `.env` trong thư mục gốc:
```bash
USE_AI_EXTRACTION=true
OPENAI_API_KEY=sk-your-key-here
AI_PROVIDER=openai
```

Hoặc với Anthropic:
```bash
USE_AI_EXTRACTION=true
ANTHROPIC_API_KEY=sk-ant-your-key-here
AI_PROVIDER=anthropic
```

2. Docker Compose sẽ tự động load biến môi trường từ `.env`

#### Cách 2: Set biến môi trường trực tiếp

**Windows (PowerShell):**
```powershell
$env:USE_AI_EXTRACTION="true"
$env:OPENAI_API_KEY="sk-your-key-here"
$env:AI_PROVIDER="openai"
```

**Linux/Mac:**
```bash
export USE_AI_EXTRACTION=true
export OPENAI_API_KEY=sk-your-key-here
export AI_PROVIDER=openai
```

#### Cách 3: Sửa docker-compose.yml

Thêm vào section `environment` của backend:
```yaml
environment:
  - USE_AI_EXTRACTION=true
  - OPENAI_API_KEY=sk-your-key-here
  - AI_PROVIDER=openai
```

### 3. Khởi động lại

```bash
docker-compose down
docker-compose up -d
```

## Các tùy chọn

- `USE_AI_EXTRACTION`: `true` để bật AI, `false` để dùng regex (mặc định)
- `OPENAI_API_KEY`: API key của OpenAI
- `ANTHROPIC_API_KEY`: API key của Anthropic
- `AI_PROVIDER`: `openai` hoặc `anthropic` (mặc định: `openai`)

## Lưu ý

1. **Chi phí**: Sử dụng AI API sẽ tốn phí. OpenAI GPT-4o-mini rẻ hơn GPT-4.
2. **Fallback**: Nếu AI không trả về kết quả, hệ thống sẽ tự động fallback về regex.
3. **Bảo mật**: Không commit file `.env` chứa API key lên Git.
4. **Performance**: AI chậm hơn regex nhưng chính xác hơn nhiều.

## So sánh

| Tính năng | Regex | AI |
|-----------|-------|-----|
| Tốc độ | ⚡⚡⚡ Nhanh | 🐢 Chậm hơn |
| Độ chính xác | ⭐⭐ Trung bình | ⭐⭐⭐⭐⭐ Rất cao |
| Chi phí | 💰 Miễn phí | 💰💰 Có phí |
| Xử lý format lạ | ❌ Kém | ✅ Tốt |

## Troubleshooting

1. **Lỗi "OpenAI library not installed"**:
   ```bash
   pip install openai
   ```

2. **Lỗi "Anthropic library not installed"**:
   ```bash
   pip install anthropic
   ```

3. **AI không hoạt động**: Kiểm tra:
   - `USE_AI_EXTRACTION=true`
   - API key đúng
   - Có internet để gọi API
   - API key còn hạn
