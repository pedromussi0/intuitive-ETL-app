from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging
from logging.config import dictConfig
import uvicorn 


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

# Create FastAPI app instance with lifespan manager
app = FastAPI(
    title="Intuitive Care ANS API",
    description="API for accessing and searching ANS Operator Data",
    version="1.0.0",
    lifespan=lifespan # Use the lifespan context manager
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