from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.api.cv_upload import router as cv_router
from app.models.database import engine, Base

app = FastAPI(
    title="AI Recruitment System",
    version="1.0"
)

# ✅ CORS – BẮT BUỘC
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả origins khi serve cùng origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Tạo bảng DB
Base.metadata.create_all(bind=engine)

# ✅ Router API - phải đặt trước static files
# Router đã có prefix="/cv" trong định nghĩa, không cần thêm prefix nữa
app.include_router(cv_router)

# ✅ Serve static files từ frontend
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    # Serve frontend HTML files
    @app.get("/")
    @app.head("/")
    async def index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
    
    @app.get("/list.html")
    async def list_page():
        return FileResponse(os.path.join(frontend_dir, "list.html"))
    
    @app.get("/index.html")
    async def index_page():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
    
    # Serve các file static cụ thể - không dùng catch-all để tránh conflict với API routes
    @app.get("/app.js")
    async def serve_app_js():
        return FileResponse(os.path.join(frontend_dir, "app.js"))
    
    @app.get("/styles.css")
    async def serve_styles_css():
        return FileResponse(os.path.join(frontend_dir, "styles.css"))
    
    @app.get("/favicon.ico")
    async def serve_favicon():
        favicon_path = os.path.join(frontend_dir, "favicon.ico")
        if os.path.exists(favicon_path):
            return FileResponse(favicon_path)
        from fastapi import HTTPException
        raise HTTPException(status_code=404)
else:
    @app.get("/")
    def root():
        return {"message": "AI Recruitment API is running"}
