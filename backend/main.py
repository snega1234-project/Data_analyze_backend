import os
import sys
from pydantic import BaseModel
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Ensure the backend directory is in the system path so it can find analytics.py universally
sys.path.append(os.path.dirname(__file__))
from analytics import DataAnalyzer
from db_query import execute_nl_query

app = FastAPI(title="Data Analytics API")

# Add CORS middleware to allow the frontend to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/api/cleanup")
async def cleanup_uploads():
    try:
        for filename in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        return {"message": "Uploads cleaned successfully"}
    except Exception as e:
        return {"error": str(e)}

class TestConnectionRequest(BaseModel):
    db_type: str
    connection_string: str

@app.post("/api/test_connection")
async def test_connection(req: TestConnectionRequest):
    try:
        if req.db_type.lower() == "mongodb":
            import pymongo
            client = pymongo.MongoClient(req.connection_string, serverSelectionTimeoutMS=5000)
            client.admin.command('ping')
        elif req.db_type.lower() == "sqlite" or req.connection_string.strip().lower().startswith("sqlite"):
            return {"status": "error", "message": "SQLite is a local database and cannot be tested here."}
        else:
            from sqlalchemy import create_engine
            engine = create_engine(req.connection_string)
            with engine.connect() as conn:
                pass
        return {"status": "success", "message": "Connection successful!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
        
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        analyzer = DataAnalyzer(file_path)
        columns = analyzer.get_columns()
        rows, cols = analyzer.df.shape
        return {"filename": file.filename, "columns": columns, "row_count": rows, "column_count": cols}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/visualize")
async def visualize(
    filename: str = Form(...),
    chart_type: str = Form(...),
    x_field: str = Form(...),
    y_field: str = Form(None)
):
    if y_field == "":
        y_field = None

    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found. Please upload again.")
        
    try:
        analyzer = DataAnalyzer(file_path)
        image_data = analyzer.generate_chart(chart_type, x_field, y_field)
        return {"image": image_data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/db_query")
async def db_query(
    db_type: str = Form(...),
    connection_string: str = Form(...),
    api_key: str = Form(...),
    query: str = Form(...)
):
    try:
        result = execute_nl_query(db_type, connection_string, api_key, query)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

app_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app")
# Ensure the directory exists before mounting
os.makedirs(app_dir, exist_ok=True)
app.mount("/", StaticFiles(directory=app_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
