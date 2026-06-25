"""Expense routes"""
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
import logging

from app.schemas import ExpenseCreate, ExpenseResponse
from app.models import Expense, ExpenseShare
from app.database import get_db
from app.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(expense_data: ExpenseCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new expense"""
    try:
        new_expense = Expense(
            group_id=expense_data.group_id,
            payer_id=current_user['user_id'],
            description=expense_data.description,
            amount=expense_data.amount,
            category=expense_data.category,
            notes=expense_data.notes,
            expense_date=expense_data.expense_date
        )
        db.add(new_expense)
        db.flush()
        
        # Add expense shares
        for share in expense_data.shares:
            expense_share = ExpenseShare(
                expense_id=new_expense.id,
                user_id=share.user_id,
                share_amount=share.share_amount
            )
            db.add(expense_share)
        
        db.commit()
        db.refresh(new_expense)
        logger.info(f"Expense created: {new_expense.id}")
        return new_expense
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create expense: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create expense"
        )

@router.get("/{group_id}", response_model=list[ExpenseResponse])
async def list_expenses(group_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """List expenses for a group"""
    try:
        expenses = db.query(Expense).filter(Expense.group_id == group_id).all()
        return expenses
    except Exception as e:
        logger.error(f"Failed to list expenses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list expenses"
        )
