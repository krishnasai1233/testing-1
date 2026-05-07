from utils import init_env
init_env()
from fastapi import FastAPI,APIRouter, Request
from fastapi.responses import PlainTextResponse
from router import process_webhook, start_worker_thread
from fastapi.middleware.cors import CORSMiddleware
from models.gitlab_webhook import GitLabWebhookPayload 
import json
import uvicorn
import sys
import os
from contextlib import asynccontextmanager

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_worker_thread()   
    yield

app = FastAPI(
    root_path="/user/rohith_palani/vscode/proxy/10000",
    lifespan=lifespan
)
# app = FastAPI(lifespan=lifespan)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["x-activityid", "x-sources"],
)

@app.get("/api/v0/health")
async def health_check(request: Request) -> PlainTextResponse:
    # health check, return a 200 OK with "OK" message.
    return PlainTextResponse("OK")

@app.post("/api/webhook")
async def handle_webhook(payload: GitLabWebhookPayload):
    result = process_webhook(payload.model_dump())
    logger.info("Input Payload captured for the Documentation trigger: %s",payload)
    return {"status": "MR is being processed for documentation", "result": result}

@app.get("/")
def ping():
    return "Welcome to Release Notes Agent Back-end API"


# ─── Runner ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    HOST = (
        "0.0.0.0"  
    )
    PORT = 10000
    uvicorn.run("main:app", host=HOST, port=PORT, reload=False, timeout_keep_alive=300)
