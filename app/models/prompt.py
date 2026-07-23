from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.project import Project


class Prompt(Base, IDMixin, TimestampMixin):
    __tablename__ = "prompts"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    project: Mapped["Project"] = relationship(back_populates="prompts")
