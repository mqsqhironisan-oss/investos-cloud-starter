
from fastapi import FastAPI, Response
from fastapi.responses import PlainTextResponse
from pathlib import Path
import subprocess
import os

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "out"

app = FastAPI(title="InvestOS Cloud Starter")

@app.get("/health", response_class=PlainTextResponse)
def health():
    return "ok"

@app.get("/out/{name}")
def get_out(name: str):
    p = OUT / name
    if not p.exists():
        return Response(status_code=404, content="not found")
    media = "text/csv" if name.endswith(".csv") else "text/plain"
    return Response(content=p.read_bytes(), media_type=media)

@app.post("/run/weekly")
def run_weekly():
    # Runs weekly pipeline synchronously
    cmd = ["python", str(BASE/"src"/"pipeline_weekly.py")]
    proc = subprocess.run(cmd, cwd=str(BASE), capture_output=True, text=True)
    if proc.returncode != 0:
        return Response(status_code=500, content=f"error\n{proc.stdout}\n{proc.stderr}")
    return {"status": "ok", "stdout": proc.stdout[-4000:]}

