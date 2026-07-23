from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.message import Message
    from app.models.prompt import Prompt
    from app.models.user import User


class Project(Base, IDMixin, TimestampMixin):
    __tablename__ = "projects"

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    owner: Mapped["User"] = relationship(back_populates="projects")
    prompts: Mapped[list["Prompt"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    messages: Mapped[list["Message"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
