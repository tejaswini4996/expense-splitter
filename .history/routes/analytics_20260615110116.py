"""Analytics routes"""
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
import logging

from app.schemas import GroupAnalytics
from app.models import Expense, Settlement
from app.database import get_db
from app.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/{group_id}", response_model=GroupAnalytics)
async def get_group_analytics(group_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get analytics for a group"""
    try:
        expenses = db.query(Expense).filter(Expense.group_id == group_id).all()
        settlements = db.query(Settlement).filter(Settlement.group_id == group_id).all()
        
        total_expenses = sum(e.amount for e in expenses)
        total_settled = sum(s.amount for s in settlements if s.is_paid)
        pending_amount = total_expenses - total_settled
        
        return {
            "group_id": group_id,
            "total_expenses": total_expenses,
            "total_settled": total_settled,
            "pending_amount": pending_amount,
            "member_count": 0,
            "expense_count": len(expenses),
            "by_category": []
        }
    except Exception as e:
        logger.error(f"Failed to get analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get analytics"
        )
