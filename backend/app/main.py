from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.api.endpoints import public
from app.config import settings
from app.core.database import engine
from app.core.rate_limit import rate_limiter

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("deception-orchestrator")


async def lifespan(app: FastAPI):
    settings.validate_runtime()
    yield
    await engine.dispose()


app = FastAPI(
    title="Deception Orchestrator",
    description="Agentic AI deception platform — honeypots, canary tokens, and adaptive engagement",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    if request.url.path == "/api/v1/auth/login" and request.method == "POST":
        if not rate_limiter.allowed(f"login:{client_ip}", limit=10, seconds=300):
            return JSONResponse(status_code=429, content={"detail": "Too many login attempts"})
    if request.url.path.startswith("/c/") and request.method == "GET":
        if not rate_limiter.allowed(f"canary:{client_ip}", limit=60, seconds=60):
            return JSONResponse(status_code=429, content={"detail": "Too many callback requests"})
    mutation = request.method in {"POST", "PUT", "PATCH", "DELETE"}
    if mutation and request.url.path.startswith("/api/v1/") and request.url.path != "/api/v1/auth/login":
        csrf_cookie = request.cookies.get("csrf_token")
        if not csrf_cookie or csrf_cookie != request.headers.get("x-csrf-token"):
            return JSONResponse(status_code=403, content={"detail": "CSRF validation failed"})
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return response

app.include_router(api_router, prefix="/api/v1")
app.include_router(public.router)


@app.get("/health")
async def health_check():
    return JSONResponse({"status": "ok"})
