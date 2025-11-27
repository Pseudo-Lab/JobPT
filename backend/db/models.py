from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship, mapped_column, Mapped
from datetime import datetime
from zoneinfo import ZoneInfo

from .database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(ZoneInfo("Asia/Seoul")),
        nullable=False
    )

    resumes: Mapped[list["Resume"]] = relationship("Resume", back_populates="user")

class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.user_id"))
    pdf_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(ZoneInfo("Asia/Seoul")),
        nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="resumes")
