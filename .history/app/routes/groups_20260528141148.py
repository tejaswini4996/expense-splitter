"""Group management routes"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List

import logging

from app.schemas import GroupCreate, GroupUpdate, GroupResponse, GroupDetailResponse
from app.models import User, Group, GroupMember
from app.database import get_db
from app.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_data: GroupCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new group"""
    try:
        # Get current user
        user = db.query(User).filter(User.email == current_user['email']).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        # Create group
        new_group = Group(
            name=group_data.name,
            description=group_data.description,
            created_by=user.id,
            currency=group_data.currency
        )
        
        # Add creator as member
        new_group.members.append(user)
        
        # Add other members if provided
        if group_data.member_ids:
            other_members = db.query(User).filter(User.id.in_(group_data.member_ids)).all()
            new_group.members.extend(other_members)
        
        db.add(new_group)
        db.commit()
        db.refresh(new_group)
        logger.info(f"Group created: {new_group.id} by {user.email}")
        
        return new_group
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create group: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create group"
        )

@router.get("/", response_model=List[GroupResponse])
async def list_user_groups(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all groups for current user"""
    try:
        user = db.query(User).filter(User.email == current_user['email']).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        groups = db.query(Group).filter(Group.members.contains(user)).all()
        return groups
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list groups: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list groups"
        )

@router.get("/{group_id}", response_model=GroupDetailResponse)
async def get_group(
    group_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get group details"""
    try:
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found"
            )
        
        # Check if user is member
        user = db.query(User).filter(User.email == current_user['email']).first()
        if user not in group.members:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this group"
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

@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: str,
    group_data: GroupUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update group"""
    try:
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found"
            )
        
        # Check if user is creator
        if group.created_by != current_user['user_id']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only group creator can update"
            )
        
        # Update fields
        if group_data.name:
            group.name = group_data.name
        if group_data.description is not None:
            group.description = group_data.description
        if group_data.currency:
            group.currency = group_data.currency
        
        db.commit()
        db.refresh(group)
        logger.info(f"Group updated: {group_id}")
        
        return group
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update group: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update group"
        )

@router.post("/{group_id}/members/{user_id}")
async def add_member_to_group(
    group_id: str,
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add member to group"""
    try:
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found"
            )
        
        # Check if user is creator
        if group.created_by != current_user['user_id']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only group creator can add members"
            )
        
        member = db.query(User).filter(User.id == user_id).first()
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if member in group.members:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member"
            )
        
        group.members.append(member)
        db.commit()
        logger.info(f"User {user_id} added to group {group_id}")
        
        return {"message": "Member added successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to add member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add member"
        )
