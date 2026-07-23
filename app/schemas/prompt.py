from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PromptCreate(BaseModel):
    content: str = Field(min_length=1)


class PromptUpdate(BaseModel):
    content: str = Field(min_length=1)


class PromptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    content: str
    created_at: datetime
