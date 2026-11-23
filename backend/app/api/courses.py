
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models import User, UserRole, Course
from app.schemas.course import CourseCreate, CourseResponse
from app.core.permissions import require_role
from app.core.dependencies import get_current_user

from app.schemas.course import (CourseCreate, CourseResponse, CourseUpdate)
from app.schemas.course import (CourseCreate, CourseResponse,CourseUpdate,CourseLecturerAssign)

router = APIRouter(
    prefix="/courses",
    tags=["Courses"]
)


@router.post(
    "/",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_course(
    course_data: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.ADMIN)
    )
):
    # Check whether the course code already exists
    result = await db.execute(
        select(Course).where(
            Course.course_code == course_data.course_code
        )
    )

    existing_course = result.scalar_one_or_none()

    if existing_course:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Course code already exists"
        )

    # Create the course
    new_course = Course(
        course_code=course_data.course_code,
        title=course_data.title,
        description=course_data.description,
        credit_hours=course_data.credit_hours
    )

    # Save the course
    db.add(new_course)
    await db.commit()
    await db.refresh(new_course)

    return new_course



@router.get(
    "/",
    response_model=list[CourseResponse]
)
async def get_courses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Course).order_by(Course.course_code)
    )

    courses = result.scalars().all()

    return courses



@router.get(
    "/{course_id}",
    response_model=CourseResponse
)
async def get_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Course).where(Course.id == course_id)
    )

    course = result.scalar_one_or_none()

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    return course



@router.put(
    "/{course_id}",
    response_model=CourseResponse
)
async def update_course(
    course_id: int,
    course_data: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.ADMIN)
    )
):
    result = await db.execute(
        select(Course).where(Course.id == course_id)
    )

    course = result.scalar_one_or_none()

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    update_data = course_data.model_dump(exclude_unset=True)

    if "course_code" in update_data:
        existing_result = await db.execute(
            select(Course).where(
                Course.course_code == update_data["course_code"],
                Course.id != course_id
            )
        )

        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Course code already exists"
            )

    for field, value in update_data.items():
        setattr(course, field, value)

    await db.commit()
    await db.refresh(course)

    return course




@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.ADMIN)
    )
):
    result = await db.execute(
        select(Course).where(Course.id == course_id)
    )

    course = result.scalar_one_or_none()

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    await db.delete(course)
    await db.commit()

    return None



@router.put(
    "/{course_id}/lecturer",
    response_model=CourseResponse
)
async def assign_lecturer(
    course_id: int,
    assignment: CourseLecturerAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.ADMIN)
    )
):
    # Check whether the course exists
    course_result = await db.execute(
        select(Course).where(Course.id == course_id)
    )

    course = course_result.scalar_one_or_none()

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # Check whether the user exists
    lecturer_result = await db.execute(
        select(User).where(
            User.id == assignment.lecturer_id
        )
    )

    lecturer = lecturer_result.scalar_one_or_none()

    if lecturer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check whether the user is actually a lecturer
    if lecturer.role != UserRole.LECTURER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected user is not a lecturer"
        )

    # Assign the lecturer to the course
    course.lecturer_id = lecturer.id

    await db.commit()
    await db.refresh(course)

    return course