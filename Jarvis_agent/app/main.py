from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from app.core.config import settings
from app.core.logger import logger
from app.memory.database import init_db
from app.api.routes_chat import router as chat_router
from app.api.routes_sessions import router as sessions_router
from app.api.routes_memory import router as memory_router
from app.api.routes_documents import router as documents_router
from app.api.routes_system import router as system_router
from app.api.routes_tts import router as tts_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}...")
    settings.ensure_directories()
    init_db()
    logger.info("Storage, memory tables, and file directories ready.")
    yield
    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="JARVIS — Modular Personal AI Assistant Backend API",
    lifespan=lifespan
)

# CORS Middleware with configurable origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global sanitized error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Check server logs for details."}
    )


# Include API routers
app.include_router(system_router)
app.include_router(chat_router)
app.include_router(sessions_router)
app.include_router(memory_router)
app.include_router(documents_router)
app.include_router(tts_router)

# Serve HUD Frontend
INDEX_FILE = Path(__file__).resolve().parent.parent / "index.html"

@app.get("/", include_in_schema=False)
async def serve_index():
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE)
    return {"message": f"{settings.APP_NAME} v{settings.APP_VERSION} is operational"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG
    )
