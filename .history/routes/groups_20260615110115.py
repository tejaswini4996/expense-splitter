"""Group routes"""
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
import logging

from app.schemas import GroupCreate, GroupResponse, GroupDetailResponse
from app.models import Group, User
from app.database import get_db
from app.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(group_data: GroupCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new group"""
    try:
        new_group = Group(
            name=group_data.name,
            description=group_data.description,
            created_by=current_user['user_id'],
            currency=group_data.currency
        )
        db.add(new_group)
        db.commit()
        db.refresh(new_group)
        logger.info(f"Group created: {new_group.id}")
        return new_group
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create group: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create group"
        )

@router.get("/", response_model=list[GroupResponse])
async def list_groups(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """List user's groups"""
    try:
        groups = db.query(Group).filter(Group.is_active == True).all()
        return groups
    except Exception as e:
        logger.error(f"Failed to list groups: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list groups"
        )

@router.get("/{group_id}", response_model=GroupDetailResponse)
async def get_group(group_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get group details"""
    try:
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found"
            )
        return group
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get group: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get group"
        )
