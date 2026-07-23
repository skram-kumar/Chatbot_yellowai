from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.project import Project


class MessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"


class Message(Base, IDMixin, TimestampMixin):
    __tablename__ = "messages"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole, native_enum=False), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    project: Mapped["Project"] = relationship(back_populates="messages")
