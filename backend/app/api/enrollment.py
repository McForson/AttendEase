from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models import User, UserRole, Course, Enrollment
from app.schemas.enrollment import EnrollmentResponse, EnrolledStudentResponse
from app.core.permissions import require_role


router = APIRouter(
    prefix="/enrollments",
    tags=["Enrollments"]
)




@router.post(
    "/{course_id}",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED
)
async def enroll_in_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.STUDENT)
    )
):
    # Check whether the course exists
    result = await db.execute(
        select(Course).where(Course.id == course_id)
    )

    course = result.scalar_one_or_none()

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # Check whether the student is already enrolled
    result = await db.execute(
        select(Enrollment).where(
            Enrollment.student_id == current_user.id,
            Enrollment.course_id == course_id
        )
    )

    existing_enrollment = result.scalar_one_or_none()

    if existing_enrollment:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are already enrolled in this course"
        )

    # Create the enrollment
    new_enrollment = Enrollment(
        student_id=current_user.id,
        course_id=course_id
    )

    db.add(new_enrollment)

    await db.commit()
    await db.refresh(new_enrollment)

    return new_enrollment





@router.get(
    "/course/{course_id}/students",
    response_model=list[EnrolledStudentResponse]
)
async def get_course_students(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.ADMIN, UserRole.LECTURER)
    )
):
    result = await db.execute(
        select(User)
        .join(
            Enrollment,
            Enrollment.student_id == User.id
        )
        .where(Enrollment.course_id == course_id)
        .where(User.role == UserRole.STUDENT)
    )

    students = result.scalars().all()

    return students


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def withdraw_from_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.STUDENT)
    )
):
    result = await db.execute(
        select(Enrollment).where(
            Enrollment.student_id == current_user.id,
            Enrollment.course_id == course_id
        )
    )

    enrollment = result.scalar_one_or_none()

    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not enrolled in this course"
        )

    await db.delete(enrollment)
    await db.commit()

    return None