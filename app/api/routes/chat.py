from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_owned_project
from app.models.message import Message, MessageRole
from app.models.project import Project
from app.models.prompt import Prompt
from app.schemas.message import MessageCreate, MessageRead
from app.services.llm import LLMServiceError, get_chat_completion

router = APIRouter(prefix="/projects/{project_id}/chat", tags=["chat"])


@router.get("", response_model=list[MessageRead])
async def get_chat_history(
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> list[Message]:
    result = await db.scalars(
        select(Message).where(Message.project_id == project.id).order_by(Message.created_at)
    )
    return list(result.all())


@router.post("", response_model=list[MessageRead], status_code=status.HTTP_201_CREATED)
async def send_chat_message(
    payload: MessageCreate,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> list[Message]:
    # Most recently edited prompt is treated as the project's active system prompt.
    prompt = await db.scalar(
        select(Prompt)
        .where(Prompt.project_id == project.id)
        .order_by(Prompt.created_at.desc())
        .limit(1)
    )
    system_prompt = prompt.content if prompt is not None else ""

    history = list(
        await db.scalars(
            select(Message).where(Message.project_id == project.id).order_by(Message.created_at)
        )
    )

    user_message = Message(project_id=project.id, role=MessageRole.user, content=payload.content)
    db.add(user_message)
    await db.commit()
    await db.refresh(user_message)

    conversation = [{"role": m.role.value, "content": m.content} for m in history]
    conversation.append({"role": "user", "content": payload.content})

    try:
        reply_content = await get_chat_completion(system_prompt, conversation)
    except LLMServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    assistant_message = Message(
        project_id=project.id, role=MessageRole.assistant, content=reply_content
    )
    db.add(assistant_message)
    await db.commit()
    await db.refresh(assistant_message)

    return [user_message, assistant_message]
