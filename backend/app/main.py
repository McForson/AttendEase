
from fastapi import FastAPI

app = FastAPI(
    title="AttendEase API",
    description="University Attendance Management System",
    version="1.0.0"
)


@app.get("/")
async def root():
    return {
        "message": "Welcome to AttendEase API",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy"
    }
