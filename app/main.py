from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from app.config import CORS_ORIGINS
from app.database import Base, engine
from app import models  # noqa: F401
from app.routers import services
from app.routers import bookings
from app.routers import auth
from app.routers import admin  # <-- НОВОЕ


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Студия Ольги Шевалдиной — API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Базовые security-заголовки для всех ответов."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response

app.include_router(services.router)
app.include_router(bookings.router)
app.include_router(auth.router)
app.include_router(admin.router)  # <-- НОВОЕ


@app.get("/", tags=["system"])
def root():
    return {"service": "shevaldina-backend", "status": "ok", "docs": "/docs"}


@app.get("/health", tags=["system"])
def health():
    return {"status": "healthy"}


@app.get("/robots.txt", response_class=PlainTextResponse, tags=["seo"])
def robots():
    return (
        "User-agent: *\n"
        "Disallow: /api/\n"
        "Disallow: /admin/\n"
        "Disallow: /docs\n"
        "Disallow: /openapi.json\n"
    )