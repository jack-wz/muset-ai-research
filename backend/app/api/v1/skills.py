"""
Skills Management API Endpoints

This module provides API endpoints for managing Claude Skills packages.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.config import SkillPackage
from app.models.user import User
from app.services.skill_loader import SkillLoader

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize skill loader
skill_loader = SkillLoader()


# Pydantic schemas
class SkillPackageResponse(BaseModel):
    """Schema for skill package response."""

    id: int
    name: str
    version: str
    provider: str
    description: str = ""
    instructions: str = ""
    default_enabled: bool
    active: bool = False
    required_resources: List[str]
    exposed_tools: List[str]
    created_at: str
    updated_at: str

    class Config:
        """Pydantic config."""

        from_attributes = True


class SkillPackageListResponse(BaseModel):
    """Schema for skill package list response."""

    skills: List[SkillPackageResponse]
    total: int


class SkillActionRequest(BaseModel):
    """Schema for skill action request."""

    action: str = Field(..., description="Action to perform (activate, deactivate)")


class ActiveSkillsResponse(BaseModel):
    """Schema for active skills response."""

    skills: List[str]
    instructions: str


@router.get("/", response_model=SkillPackageListResponse)
async def list_skills(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SkillPackageListResponse:
    """
    List all skill packages.

    Returns:
        List of skill packages
    """
    try:
        result = await db.execute(select(SkillPackage))
        skills = result.scalars().all()

        # Check if skills are active
        active_skills_map = {
            name: data.get("active", False)
            for name, data in skill_loader.active_skills.items()
        }

        skill_responses = []
        for skill in skills:
            response = SkillPackageResponse(
                id=skill.id,
                name=skill.name,
                version=skill.version,
                provider=skill.provider,
                description=skill.instructions[:200] if skill.instructions else "",
                instructions=skill.instructions,
                default_enabled=skill.default_enabled,
                active=active_skills_map.get(skill.name, False),
                required_resources=skill.required_resources or [],
                exposed_tools=skill.exposed_tools or [],
                created_at=str(skill.created_at),
                updated_at=str(skill.updated_at),
            )
            skill_responses.append(response)

        return SkillPackageListResponse(skills=skill_responses, total=len(skill_responses))

    except Exception as e:
        logger.error(f"Failed to list skills: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list skills: {str(e)}",
        )


@router.post("/upload", response_model=SkillPackageResponse, status_code=status.HTTP_201_CREATED)
async def upload_skill(
    file: UploadFile = File(..., description="Skill package zip file"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SkillPackageResponse:
    """
    Upload a new skill package.

    Args:
        file: Skill package zip file
        db: Database session
        current_user: Current user

    Returns:
        Created skill package
    """
    try:
        # Validate file type
        if not file.filename or not file.filename.endswith(".zip"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only .zip files are supported",
            )

        # Save uploaded file temporarily
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        try:
            # Load skill
            skill_data = await skill_loader.load_skill(temp_path)

            # Check if skill already exists
            result = await db.execute(
                select(SkillPackage).where(SkillPackage.name == skill_data["name"])
            )
            existing_skill = result.scalar_one_or_none()

            if existing_skill:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Skill {skill_data['name']} already exists",
                )

            # Create skill package record
            skill_package = SkillPackage(
                name=skill_data["name"],
                version=skill_data["version"],
                provider=skill_data["provider"],
                manifest_path=skill_data["directory"],
                instructions=skill_data["instructions"],
                default_enabled=False,
                required_resources=skill_data["metadata"].get("resources", []),
                exposed_tools=skill_data["metadata"].get("tools", []),
            )

            db.add(skill_package)
            await db.commit()
            await db.refresh(skill_package)

            return SkillPackageResponse(
                id=skill_package.id,
                name=skill_package.name,
                version=skill_package.version,
                provider=skill_package.provider,
                description=skill_package.instructions[:200] if skill_package.instructions else "",
                instructions=skill_package.instructions,
                default_enabled=skill_package.default_enabled,
                active=False,
                required_resources=skill_package.required_resources or [],
                exposed_tools=skill_package.exposed_tools or [],
                created_at=str(skill_package.created_at),
                updated_at=str(skill_package.updated_at),
            )

        finally:
            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload skill: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to upload skill: {str(e)}",
        )


@router.get("/{skill_id}", response_model=SkillPackageResponse)
async def get_skill(
    skill_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SkillPackageResponse:
    """
    Get skill package by ID.

    Args:
        skill_id: Skill package ID
        db: Database session
        current_user: Current user

    Returns:
        Skill package details
    """
    try:
        result = await db.execute(select(SkillPackage).where(SkillPackage.id == skill_id))
        skill = result.scalar_one_or_none()

        if not skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill {skill_id} not found",
            )

        active = skill.name in skill_loader.active_skills and skill_loader.active_skills[
            skill.name
        ].get("active", False)

        return SkillPackageResponse(
            id=skill.id,
            name=skill.name,
            version=skill.version,
            provider=skill.provider,
            description=skill.instructions[:200] if skill.instructions else "",
            instructions=skill.instructions,
            default_enabled=skill.default_enabled,
            active=active,
            required_resources=skill.required_resources or [],
            exposed_tools=skill.exposed_tools or [],
            created_at=str(skill.created_at),
            updated_at=str(skill.updated_at),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get skill: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get skill: {str(e)}",
        )


@router.post("/{skill_id}/action", response_model=SkillPackageResponse)
async def perform_skill_action(
    skill_id: int,
    action_request: SkillActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SkillPackageResponse:
    """
    Perform action on skill (activate, deactivate).

    Args:
        skill_id: Skill package ID
        action_request: Action to perform
        db: Database session
        current_user: Current user

    Returns:
        Updated skill package
    """
    try:
        result = await db.execute(select(SkillPackage).where(SkillPackage.id == skill_id))
        skill = result.scalar_one_or_none()

        if not skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill {skill_id} not found",
            )

        if action_request.action == "activate":
            await skill_loader.activate_skill(skill.name)
        elif action_request.action == "deactivate":
            await skill_loader.deactivate_skill(skill.name)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action: {action_request.action}",
            )

        active = skill.name in skill_loader.active_skills and skill_loader.active_skills[
            skill.name
        ].get("active", False)

        return SkillPackageResponse(
            id=skill.id,
            name=skill.name,
            version=skill.version,
            provider=skill.provider,
            description=skill.instructions[:200] if skill.instructions else "",
            instructions=skill.instructions,
            default_enabled=skill.default_enabled,
            active=active,
            required_resources=skill.required_resources or [],
            exposed_tools=skill.exposed_tools or [],
            created_at=str(skill.created_at),
            updated_at=str(skill.updated_at),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to perform skill action: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform action: {str(e)}",
        )


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete skill package.

    Args:
        skill_id: Skill package ID
        db: Database session
        current_user: Current user
    """
    try:
        result = await db.execute(select(SkillPackage).where(SkillPackage.id == skill_id))
        skill = result.scalar_one_or_none()

        if not skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill {skill_id} not found",
            )

        # Deactivate if active
        if skill.name in skill_loader.active_skills:
            await skill_loader.deactivate_skill(skill.name)

        # Delete from database
        await db.delete(skill)
        await db.commit()

        # Delete skill directory
        from pathlib import Path
        import shutil

        skill_dir = Path(skill.manifest_path)
        if skill_dir.exists():
            shutil.rmtree(skill_dir, ignore_errors=True)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete skill: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete skill: {str(e)}",
        )


@router.get("/active/instructions", response_model=ActiveSkillsResponse)
async def get_active_instructions(
    current_user: User = Depends(get_current_user),
) -> ActiveSkillsResponse:
    """
    Get combined instructions from all active skills.

    Args:
        current_user: Current user

    Returns:
        Active skills and their combined instructions
    """
    try:
        instructions = skill_loader.get_active_instructions()
        active_skills = [
            skill["name"]
            for skill in skill_loader.get_active_skills()
        ]

        return ActiveSkillsResponse(
            skills=active_skills,
            instructions=instructions,
        )

    except Exception as e:
        logger.error(f"Failed to get active instructions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active instructions: {str(e)}",
        )
