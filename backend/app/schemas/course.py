
from pydantic import BaseModel, Field, ConfigDict


class CourseCreate(BaseModel):
    course_code: str = Field(
        min_length=3,
        max_length=20
    )

    title: str = Field(
        min_length=3,
        max_length=150
    )

    description: str | None = None

    credit_hours: int = Field(
        gt=0,
        le=10
    )


class CourseResponse(BaseModel):
    id: int
    course_code: str
    title: str
    description: str | None
    credit_hours: int
    lecturer_id: int | None

    model_config = ConfigDict(from_attributes=True)




class CourseUpdate(BaseModel):
    course_code: str | None = Field(
        default=None,
        min_length=3,
        max_length=20
    )

    title: str | None = Field(
        default=None,
        min_length=3,
        max_length=150
    )

    description: str | None = None

    credit_hours: int | None = Field(
        default=None,
        gt=0,
        le=10
    )



class CourseLecturerAssign(BaseModel):
    lecturer_id: int = Field(gt=0)
