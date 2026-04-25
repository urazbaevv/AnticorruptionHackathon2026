from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
from agents import run_anticorruption_analysis

app = FastAPI(title="Anticorruption AI Agent API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

# Ensure data dir exists
os.makedirs(DATA_DIR, exist_ok=True)

class Settings(BaseModel):
    api_key: str

class AnalyzeRequest(BaseModel):
    document_text: str

@app.get("/api/settings")
async def get_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            # Mask key for frontend, or just return it if we trust the local user
            return {"api_key": data.get("api_key", "")}
    return {"api_key": ""}

@app.post("/api/settings")
async def save_settings(settings: Settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump({"api_key": settings.api_key}, f)
    return {"status": "success", "message": "Settings saved successfully"}

@app.post("/api/analyze")
async def analyze_document(req: AnalyzeRequest):
    # Get API key
    api_key = ""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            api_key = data.get("api_key", "")
            
    if not api_key:
        raise HTTPException(status_code=400, detail="API Key is missing. Please set it in Settings.")
        
    try:
        results = await run_anticorruption_analysis(req.document_text, api_key)
        return {"status": "success", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve static files (Frontend)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
