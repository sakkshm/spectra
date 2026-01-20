import os
import shutil
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from server.engine.handler import match_from_file

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory task store
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
async def match_file(file: UploadFile = File(...)):
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
async def task_status(task_id: str):
    task = TASKS.get(task_id)
    if not task:
        return JSONResponse({"error": "Invalid task_id"}, status_code=404)

    return task
