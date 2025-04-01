from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging
from logging.config import dictConfig
import uvicorn 
from fastapi.middleware.cors import CORSMiddleware

from .routers import operators
from api.database import connect_db, disconnect_db



logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Handles setup (like DB connection) before app starts and teardown after app stops
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to DB
    logger.info("Application startup...")
    await connect_db()
    yield # Application runs here
    # Shutdown: Disconnect from DB
    logger.info("Application shutdown...")
    await disconnect_db()
# ---

app = FastAPI(
    title="Intuitive Care ANS API",
    description="API for accessing and searching ANS Operator Data",
    version="1.0.0",
    lifespan=lifespan 
)

origins = [
    "http://localhost:5173", 
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET"], # Allow all methods (GET, POST, etc.)
    allow_headers=["*"], 
)

# Include routers
app.include_router(operators.router)

# Simple root endpoint
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Intuitive Care ANS API"}

# --- Optional: Allow running with `python -m services.api.main` ---
# Note: For production, use a proper ASGI server like uvicorn directly:
# uvicorn services.api.main:app --reload --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    # This is primarily for simple local testing/running.
    # Production deployments should use uvicorn/gunicorn directly.
    uvicorn.run(app, host="0.0.0.0", port=8000)