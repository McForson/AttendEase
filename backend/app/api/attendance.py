from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models import User, UserRole, Course, AttendanceSession, Attendance, Enrollment
from app.schemas.attendance import ( AttendanceSessionCreate, AttendanceSessionResponse, AttendanceMarkResponse)
from app.core.permissions import require_role


router = APIRouter(
    prefix="/attendance",
    tags=["Attendance"]
)


@router.post(
    "/sessions",
    response_model=AttendanceSessionResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_attendance_session(
    session_data: AttendanceSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.LECTURER)
    )
):
    # Check whether the course exists
    result = await db.execute(
        select(Course).where(
            Course.id == session_data.course_id
        )
    )

    course = result.scalar_one_or_none()

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # Check whether this lecturer teaches the course
    if course.lecturer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this course"
        )

    # Check whether expiry time is in the future
    now = datetime.now(timezone.utc)

    if session_data.expires_at.tzinfo is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Expiry time must include a timezone"
        )

    if session_data.expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expiry time must be in the future"
        )

    # Create the attendance session
    new_session = AttendanceSession(
        course_id=course.id,
        lecturer_id=current_user.id,
        title=session_data.title,
        expires_at=session_data.expires_at
    )

    # Save to database
    db.add(new_session)

    await db.commit()
    await db.refresh(new_session)

    return new_session




@router.get(
    "/sessions",
    response_model=list[AttendanceSessionResponse]
)
async def get_my_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.LECTURER)
    )
):
    result = await db.execute(
        select(AttendanceSession)
        .where(
            AttendanceSession.lecturer_id == current_user.id
        )
        .order_by(AttendanceSession.started_at.desc())
    )

    sessions = result.scalars().all()

    return sessions




@router.patch(
    "/sessions/{session_id}/close",
    response_model=AttendanceSessionResponse
)
async def close_attendance_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.LECTURER)
    )
):
    # Find the attendance session
    result = await db.execute(
        select(AttendanceSession).where(
            AttendanceSession.id == session_id
        )
    )

    attendance_session = result.scalar_one_or_none()

    if attendance_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance session not found"
        )

    # Verify that the lecturer owns this session
    if attendance_session.lecturer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot close another lecturer's session"
        )

    # Close the session
    attendance_session.is_active = False

    await db.commit()
    await db.refresh(attendance_session)

    return attendance_session




@router.post(
    "/sessions/{session_id}/mark",
    response_model=AttendanceMarkResponse,
    status_code=status.HTTP_201_CREATED
)
async def mark_attendance(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.STUDENT)
    )
):
    result = await db.execute(
        select(AttendanceSession).where(
            AttendanceSession.id == session_id
        )
    )

    attendance_session = result.scalar_one_or_none()

    if attendance_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance session not found"
        )


    if not attendance_session.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This attendance session is closed"
        )

    now = datetime.now(timezone.utc)

    if attendance_session.expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This attendance session has expired"
        )


    result = await db.execute(
        select(Enrollment).where(
            Enrollment.student_id == current_user.id,
            Enrollment.course_id == attendance_session.course_id
        )
    )

    enrollment = result.scalar_one_or_none()

    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this course"
        )


    result = await db.execute(
        select(Attendance).where(
            Attendance.session_id == attendance_session.id,
            Attendance.student_id == current_user.id
        )
    )

    existing_attendance = result.scalar_one_or_none()

    if existing_attendance is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already marked attendance for this session"
        )


    new_attendance = Attendance(
        session_id=attendance_session.id,
        student_id=current_user.id,
        status="PRESENT"
    )

    db.add(new_attendance)

    await db.commit()

    await db.refresh(new_attendance)

    return new_attendance