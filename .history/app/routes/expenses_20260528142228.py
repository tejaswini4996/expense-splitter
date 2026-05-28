"""Expense management routes"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from fastapi import APIRouter

from datetime import datetime, timedelta
import logging

from app.schemas import ExpenseCreate, ExpenseResponse, ExpenseCategory
from app.models import User, Group, Expense, ExpenseShare
from app.database import get_db
from app.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    expense_data: ExpenseCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new expense"""
    try:
        # Get current user
        user = db.query(User).filter(User.email == current_user['email']).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        # Get group
        group = db.query(Group).filter(Group.id == expense_data.group_id).first()
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found"
            )
        
        # Check if user is member
        if user not in group.members:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this group"
            )
        
        # Create expense
        new_expense = Expense(
            group_id=expense_data.group_id,
            payer_id=user.id,
            description=expense_data.description,
            amount=expense_data.amount,
            category=expense_data.category,
            expense_date=expense_data.expense_date or datetime.utcnow(),
            notes=expense_data.notes
        )
        
        # Add shares
        for share in expense_data.shares:
            share_user = db.query(User).filter(User.id == share.user_id).first()
            if not share_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User {share.user_id} not found"
                )
            
            expense_share = ExpenseShare(
                expense_id=new_expense.id,
                user_id=share.user_id,
                share_amount=share.share_amount
            )
            new_expense.shares.append(expense_share)
        
        db.add(new_expense)
        db.commit()
        db.refresh(new_expense)
        logger.info(f"Expense created: {new_expense.id} in group {group.id}")
        
        return new_expense
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create expense: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create expense"
        )

@router.get("/group/{group_id}", response_model=List[ExpenseResponse])
async def get_group_expenses(
    group_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """Get all expenses in a group"""
    try:
        # Verify user is member
        user = db.query(User).filter(User.email == current_user['email']).first()
        group = db.query(Group).filter(Group.id == group_id).first()
        
        if not group or user not in group.members:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        expenses = db.query(Expense).filter(
            Expense.group_id == group_id
        ).order_by(Expense.expense_date.desc()).offset(skip).limit(limit).all()
        
        return expenses
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get expenses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get expenses"
        )

@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get expense details"""
    try:
        expense = db.query(Expense).filter(Expense.id == expense_id).first()
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found"
            )
        
        # Check if user is member of group
        user = db.query(User).filter(User.email == current_user['email']).first()
        if user not in expense.group.members:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return expense
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get expense: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get expense"
        )

@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an expense (only by payer)"""
    try:
        expense = db.query(Expense).filter(Expense.id == expense_id).first()
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found"
            )
        
        # Check if user is payer
        if expense.payer_id != current_user['user_id']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only payer can delete expense"
            )
        
        db.delete(expense)
        db.commit()
        logger.info(f"Expense deleted: {expense_id}")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete expense: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete expense"
        )
