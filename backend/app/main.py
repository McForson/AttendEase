
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from sqlalchemy.exc import SQLAlchemyError
from app.db.session import get_db
from app.api.auth import router as auth_router
from app.api.courses import router as courses_router
from app.api.enrollment import router as enrollments_router
from app.api.attendance import router as attendance_router

app = FastAPI(
    title="AttendEase API",
    description="Attendance Management System",
    version="1.0.0"
)


app.include_router(auth_router, prefix="/api")

app.include_router(
    courses_router,
    prefix="/api"
)

app.include_router(
    enrollments_router,
    prefix="/api"
)

app.include_router(
    attendance_router,
    prefix="/api"
)


@app.get("/")
async def root():
    return {
        "message": "Welcome to AttendEase API",
        "status": "running"
    }


@app.get("/health/db")
async def database_health(
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(text("SELECT 1"))

        return {
            "database": "connected",
            "result": result.scalar_one()
        }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed"
        )
