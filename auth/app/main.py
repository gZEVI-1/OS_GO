# app/main.py
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.routers import auth
from app.database import init_db

app = FastAPI(
    title="Auth Service",
    description="FastAPI + Auth0 + 2FA Authentication",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение статических файлов
static_path = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_path, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Редирект на регистрацию по корневому пути
@app.get("/")
async def root():
    return FileResponse(os.path.join(static_path, "register.html"))



app.include_router(auth.router)

@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/health")
async def health_check():
    return {"status": "ok"}