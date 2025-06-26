from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import os
import json
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Refrigerator Diagnosis API",
    description="FastAPI backend for refrigerator troubleshooting and diagnosis",
    version="1.0.0"
)

# CORS configuration - load from cors-config.json if available
try:
    cors_config_path = os.path.join(os.path.dirname(__file__), "cors-config.json")
    with open(cors_config_path, "r") as f:
        cors_config = json.load(f)
        allowed_origins = cors_config.get("allowed_origins", ["*"])
except FileNotFoundError:
    allowed_origins = ["*"]
    logger.info("cors-config.json not found, using default CORS settings")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint (early)
@app.get("/")
async def root():
    return {"message": "Refrigerator Diagnosis API", "version": "1.0.0", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Import routers with error handling
try:
    from api.process_s3_video import router as refrigerator_router
    app.include_router(refrigerator_router, prefix="/api")
    logger.info("✅ Successfully loaded process_s3_video router")
except Exception as e:
    logger.error(f"❌ Failed to load process_s3_video router: {e}")

try:
    from api.upload import router as upload_router
    app.include_router(upload_router, prefix="/api")
    logger.info("✅ Successfully loaded upload router")
except Exception as e:
    logger.error(f"❌ Failed to load upload router: {e}")

try:
    from api.history import router as history_router
    app.include_router(history_router, prefix="/api")
    logger.info("✅ Successfully loaded history router")
except Exception as e:
    logger.error(f"❌ Failed to load history router: {e}")

try:
    from api.chat_router import router as chat_router
    app.include_router(chat_router, prefix="/api")
    logger.info("✅ Successfully loaded chat router")
except Exception as e:
    logger.error(f"❌ Failed to load chat router: {e}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    ) 