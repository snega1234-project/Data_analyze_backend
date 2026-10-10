import os
import sys
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Ensure the backend directory is in the system path so it can find analytics.py universally
sys.path.append(os.path.dirname(__file__))
from analytics import DataAnalyzer

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

app_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app")
# Ensure the directory exists before mounting
os.makedirs(app_dir, exist_ok=True)
app.mount("/", StaticFiles(directory=app_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
