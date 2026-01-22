import os
import shutil
import tempfile
import uuid

from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from server.database.handler import DatabaseHandler
from server.engine.handler import match_from_file

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Use IP address by default
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

# Task store
# task_id -> {"status": "pending"/"success"/"fail", "result": ..., "error": ...}
TASKS = {}  

# Thread pool for background processing
POOL = ThreadPoolExecutor(max_workers=4)

def process_audio(task_id: str, file_path: str):
    try:
        result = match_from_file(file_path, logging_enabled=False)
        TASKS[task_id]["status"] = "success"
        TASKS[task_id]["result"] = result
    except Exception as e:
        TASKS[task_id]["status"] = "fail"
        TASKS[task_id]["error"] = str(e)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@app.post("/match_file")
@limiter.limit("3/minute")
async def match_file(request: Request, file: UploadFile = File(...)):
    # Save temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        shutil.copyfileobj(file.file, tmp)
        temp_path = tmp.name

    task_id = str(uuid.uuid4())
    TASKS[task_id] = {"status": "pending"}

    # Submit task to thread pool
    POOL.submit(process_audio, task_id, temp_path)

    return {"task_id": task_id, "status": "pending"}


@app.get("/task_status/{task_id}")
@limiter.limit("30/minute")
async def task_status(request: Request, task_id: str):
    task = TASKS.get(task_id)
    if not task:
        return JSONResponse({"error": "Invalid task_id"}, status_code=404)

    return task

@app.get("/ping")
@limiter.limit("30/minute")
def home(request: Request):
    return {
        "msg": "spectra-api"
    }

@app.get("/health")
@limiter.limit("5/minute")
def health(request: Request):
    checks = {}

    # ThreadPool status
    checks["thread_pool"] = not POOL._shutdown

    # Filesystem write test
    try:
        with tempfile.NamedTemporaryFile(delete=True) as f:
            f.write(b"ping")
        checks["filesystem"] = True
    except Exception:
        checks["filesystem"] = False

    # Database check
    with DatabaseHandler() as db:
        checks["database"] = db.health_check()

    status = "ok" if all(checks.values()) else "degraded"

    return {
        "status": status,
        "service": "spectra-api",
        "checks": checks
    }
