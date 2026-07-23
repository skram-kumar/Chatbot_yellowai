from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_owned_project
from app.models.project import Project
from app.models.prompt import Prompt
from app.schemas.prompt import PromptCreate, PromptRead, PromptUpdate

router = APIRouter(prefix="/projects/{project_id}/prompts", tags=["prompts"])


async def _get_project_prompt(prompt_id: int, project: Project, db: AsyncSession) -> Prompt:
    prompt = await db.get(Prompt, prompt_id)
    if prompt is None or prompt.project_id != project.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")
    return prompt


@router.post("", response_model=PromptRead, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    payload: PromptCreate,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> Prompt:
    prompt = Prompt(project_id=project.id, content=payload.content)
    db.add(prompt)
    await db.commit()
    await db.refresh(prompt)
    return prompt


@router.get("", response_model=list[PromptRead])
async def list_prompts(
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> list[Prompt]:
    result = await db.scalars(select(Prompt).where(Prompt.project_id == project.id))
    return list(result.all())


@router.patch("/{prompt_id}", response_model=PromptRead)
async def update_prompt(
    prompt_id: int,
    payload: PromptUpdate,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> Prompt:
    prompt = await _get_project_prompt(prompt_id, project, db)
    prompt.content = payload.content
    await db.commit()
    await db.refresh(prompt)
    return prompt


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(
    prompt_id: int,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> None:
    prompt = await _get_project_prompt(prompt_id, project, db)
    await db.delete(prompt)
    await db.commit()
