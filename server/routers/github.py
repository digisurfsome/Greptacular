"""
GitHub Integration Router
==========================
Endpoints for GitHub token validation, repo creation, and settings.
"""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from server.services.github_integration import (
    create_empty_repo,
    create_repo_from_template,
    slugify_repo_name,
    validate_github_token,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/github", tags=["github"])


class TokenValidateRequest(BaseModel):
    token: str


class TokenValidateResponse(BaseModel):
    login: str
    name: str
    avatar_url: str


class CreateRepoRequest(BaseModel):
    token: str
    repo_name: str
    private: bool = True
    description: str = ""
    template_owner: str | None = None
    template_repo: str | None = None


class CreateRepoResponse(BaseModel):
    status: str
    repo_url: str
    clone_url: str
    full_name: str
    private: bool


@router.post("/validate-token", response_model=TokenValidateResponse)
async def validate_token(req: TokenValidateRequest):
    """Validate a GitHub Personal Access Token."""
    try:
        user_info = await validate_github_token(req.token)
        return TokenValidateResponse(**user_info)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("GitHub token validation failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to validate token")


@router.post("/create-repo", response_model=CreateRepoResponse)
async def create_repo(req: CreateRepoRequest):
    """Create a new GitHub repository, optionally from a template."""
    repo_name = slugify_repo_name(req.repo_name)

    try:
        if req.template_owner and req.template_repo:
            result = await create_repo_from_template(
                token=req.token,
                template_owner=req.template_owner,
                template_repo=req.template_repo,
                new_repo_name=repo_name,
                private=req.private,
                description=req.description,
            )
        else:
            result = await create_empty_repo(
                token=req.token,
                repo_name=repo_name,
                private=req.private,
                description=req.description,
            )

        return CreateRepoResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error("GitHub repo creation failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create repository")
