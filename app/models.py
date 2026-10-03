"""Relational data model for users, assessments, plans, feedback and progress."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    """Return the current UTC time without timezone information."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(300), nullable=False)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    profile: Mapped["Profile | None"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    assessment: Mapped["FitnessAssessment | None"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    plans: Mapped[list["WorkoutPlan"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="WorkoutPlan.created_at.desc()",
    )
    progress: Mapped[list["ProgressRecord"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="ProgressRecord.recorded_at.desc()",
    )


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    age: Mapped[int | None] = mapped_column(Integer)
    height_cm: Mapped[float | None] = mapped_column(Float)
    weight_kg: Mapped[float | None] = mapped_column(Float)
    goal: Mapped[str | None] = mapped_column(String(40))
    activity_level: Mapped[str | None] = mapped_column(String(30))
    intensity: Mapped[str | None] = mapped_column(String(20))
    location: Mapped[str | None] = mapped_column(String(30))
    equipment: Mapped[str | None] = mapped_column(Text)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    days_per_week: Mapped[int | None] = mapped_column(Integer)
    dietary_preference: Mapped[str | None] = mapped_column(String(40))
    allergies: Mapped[str | None] = mapped_column(Text)
    sleep_hours: Mapped[float | None] = mapped_column(Float)
    rest_preference: Mapped[str | None] = mapped_column(String(30))
    exercise_preferences: Mapped[str | None] = mapped_column(Text)
    limitations: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="profile")


class FitnessAssessment(Base):
    __tablename__ = "fitness_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    experience: Mapped[str] = mapped_column(String(30), nullable=False)
    activity_level: Mapped[str] = mapped_column(String(30), nullable=False)
    preferred_time: Mapped[str | None] = mapped_column(String(30))
    recovery_preference: Mapped[str | None] = mapped_column(String(30))
    exercise_preferences: Mapped[str | None] = mapped_column(Text)
    limitations: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="assessment")


class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    goal: Mapped[str] = mapped_column(String(40), nullable=False)
    intensity: Mapped[str] = mapped_column(String(20), nullable=False)
    original_plan: Mapped[str] = mapped_column(Text, nullable=False)
    updated_plan: Mapped[str | None] = mapped_column(Text)
    feedback: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)

    user: Mapped["User"] = relationship(back_populates="plans")
    completions: Mapped[list["WorkoutDayCompletion"]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="WorkoutDayCompletion.day",
    )
    feedback_items: Mapped[list["PlanFeedback"]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="PlanFeedback.created_at",
    )

    @property
    def is_updated(self) -> bool:
        return self.updated_plan is not None


class PlanFeedback(Base):
    __tablename__ = "plan_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("workout_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    feedback: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str | None] = mapped_column(String(30))
    energy: Mapped[str | None] = mapped_column(String(30))
    preferences: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow,
        nullable=False,
    )

    plan: Mapped["WorkoutPlan"] = relationship(back_populates="feedback_items")


class ProgressRecord(Base):
    __tablename__ = "progress_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    weight_kg: Mapped[float | None] = mapped_column(Float)
    workout_completion: Mapped[int | None] = mapped_column(Integer)
    energy: Mapped[str | None] = mapped_column(String(30))
    difficulty: Mapped[str | None] = mapped_column(String(30))
    notes: Mapped[str | None] = mapped_column(Text)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow,
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="progress")


class WorkoutDayCompletion(Base):
    __tablename__ = "workout_day_completions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("workout_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    day: Mapped[int] = mapped_column(Integer, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    plan: Mapped["WorkoutPlan"] = relationship(back_populates="completions")
