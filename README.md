# 📊 Nexus Data Analytics

Nexus Data Analytics is a full-stack, powerful data analytics and visualization platform that allows users to instantly generate beautiful charts from uploaded datasets and execute AI-powered queries against remote databases using natural language.

## ✨ Features

* **File Analysis**: Safely parse `.csv`, `.xls`, and `.xlsx` files using Pandas. Handle corrupted files, missing values, and dirty strings automatically.
* **Dynamic Visualization**: Generate Bar, Line, Scatter, Histogram, and Pie charts using `seaborn` and `matplotlib`.
* **Database AI Analysis**: Connect to remote databases directly and type queries in natural language! The system automatically infers your database schema and uses Google Gemini to translate your request into a valid SQL or MongoDB Aggregation Pipeline.
* **Database Agnostic**: Natively supports PostgreSQL, MySQL, SQL Server, Oracle, and **MongoDB** (NoSQL).
* **Test Connections**: Securely test database credentials before running intensive AI queries.
* **Auto-Cleanup**: The server automatically manages space by clearing temporary datasets on page refresh.
* **Dark Mode UI**: A stunning, premium aesthetic built with pure HTML/CSS/JS (no bulky frontend frameworks).

## 🚀 Tech Stack

* **Backend**: FastAPI, Python 3.11+
* **Data Processing & Connections**: Pandas, OpenPyXL, SQLAlchemy, PyMongo
* **AI Engine**: Google Generative AI (`gemini-pro`)
* **Data Visualization**: Seaborn, Matplotlib
* **Frontend**: Vanilla HTML5, CSS3, JavaScript

---

## 💻 Running the App Locally

### 1. Prerequisites

Ensure you have Python 3.11+ installed on your system. You will also need a Google Gemini API Key if you want to use the Database AI Analysis feature.

### 2. Install Dependencies

Navigate to the root directory and install all required backend packages:

```bash
pip install -r backend/requirements.txt
```

### 3. Start the Server

Start the FastAPI server using Uvicorn:

```bash
cd backend
uvicorn main:app --reload
```

By default, the application will be hosted at `http://127.0.0.1:8000`. Simply open this URL in your browser!

---

## ☁️ Deployment (Render)

This application is fully configured for a 1-click free deployment on [Render](https://render.com/).

1. Create a **New Web Service** and connect this repository.
2. **Build Command**: `pip install -r backend/requirements.txt`
3. **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. Make sure to set an Environment Variable `PYTHON_VERSION` to `3.11.8` (or newer).

Once deployed, the FastAPI backend will automatically serve both the API endpoints and the static frontend UI.
