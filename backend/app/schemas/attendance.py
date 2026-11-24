from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class AttendanceSessionCreate(BaseModel):
    course_id: int = Field(gt=0)

    title: str = Field(
        min_length=3,
        max_length=150
    )

    expires_at: datetime


class AttendanceSessionResponse(BaseModel):
    id: int
    course_id: int
    lecturer_id: int
    title: str
    started_at: datetime
    expires_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)



class AttendanceMarkResponse(BaseModel):
    id: int
    session_id: int
    student_id: int
    marked_at: datetime
    status: str

    model_config = ConfigDict(from_attributes=True)