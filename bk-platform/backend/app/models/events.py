from sqlalchemy import Integer, ForeignKey, DateTime, func, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base

class SearchQuery(Base):
    __tablename__ = "search_queries"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    query: Mapped[str]
    timestamp: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

class UserActivity(Base):
    __tablename__ = "user_activities"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(64))
    resource_id: Mapped[int | None]
    timestamp: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
