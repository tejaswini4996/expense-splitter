"""Analytics and insights routes"""
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging
from fastapi import APIRouter

from app.schemas import GroupAnalytics, ExpenseByCategory
from app.models import User, Group, Expense, ExpenseCategory, Settlement
from app.database import get_db
from app.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/group/{group_id}", response_model=GroupAnalytics)
async def get_group_analytics(
    group_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analytics for a group"""
    try:
        # Verify user is member
        user = db.query(User).filter(User.email == current_user['email']).first()
        group = db.query(Group).filter(Group.id == group_id).first()
        
        if not group or user not in group.members:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get all expenses
        all_expenses = db.query(Expense).filter(Expense.group_id == group_id).all()
        settled_expenses = db.query(Expense).filter(
            Expense.group_id == group_id,
            Expense.is_settled == True
        ).all()
        
        total_expenses = sum(e.amount for e in all_expenses)
        total_settled = sum(e.amount for e in settled_expenses)
        pending_amount = total_expenses - total_settled
        
        # Get expenses by category
        category_stats = {}
        for expense in all_expenses:
            cat = expense.category.value
            if cat not in category_stats:
                category_stats[cat] = {"amount": 0, "count": 0}
            category_stats[cat]["amount"] += expense.amount
            category_stats[cat]["count"] += 1
        
        by_category = []
        for cat, stats in category_stats.items():
            percentage = (stats["amount"] / total_expenses * 100) if total_expenses > 0 else 0
            by_category.append(ExpenseByCategory(
                category=cat,
                total_amount=round(stats["amount"], 2),
                count=stats["count"],
                percentage=round(percentage, 2)
            ))
        
        return GroupAnalytics(
            group_id=group_id,
            total_expenses=round(total_expenses, 2),
            total_settled=round(total_settled, 2),
            pending_amount=round(pending_amount, 2),
            member_count=len(group.members),
            expense_count=len(all_expenses),
            by_category=by_category
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get analytics"
        )

@router.get("/user/summary")
async def get_user_summary(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's overall expense summary"""
    try:
        user = db.query(User).filter(User.email == current_user['email']).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get all groups
        groups = db.query(Group).filter(Group.members.contains(user)).all()
        
        total_spent = 0  # Amount user paid
        total_owes = 0   # Amount user owes
        
        for group in groups:
            # Amount paid
            paid = db.query(func.sum(Expense.amount)).filter(
                Expense.group_id == group.id,
                Expense.payer_id == user.id
            ).scalar() or 0
            total_spent += paid
            
            # Amount owes (sum of shares)
            from app.models import ExpenseShare
            owes = db.query(func.sum(ExpenseShare.share_amount)).filter(
                ExpenseShare.user_id == user.id
            ).scalar() or 0
            total_owes += owes
        
        return {
            "user_id": user.id,
            "username": user.username,
            "total_spent": round(total_spent, 2),
            "total_owes": round(total_owes, 2),
            "balance": round(total_spent - total_owes, 2),  # Positive = owed money
            "groups_count": len(groups)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user summary"
        )
