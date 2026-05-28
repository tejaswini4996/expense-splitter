"""Settlement and payment routes"""
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import logging
from fastapi import APIRouter

from app.schemas import SettlementResponse, SettlementMarkPaid, UserBalance, GroupBalance
from app.models import User, Group, Expense, ExpenseShare, Settlement
from app.database import get_db
from app.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

class SettlementService:
    """Service to handle settlement calculations"""
    
    @staticmethod
    def calculate_group_balances(group_id: str, db: Session) -> dict:
        """
        Calculate who owes whom in a group.
        Returns: {user_id: balance} where positive = owed money, negative = owes money
        """
        balances = {}
        
        # Get all expenses in group
        expenses = db.query(Expense).filter(
            Expense.group_id == group_id,
            Expense.is_settled == False
        ).all()
        
        for expense in expenses:
            # Payer gets credit
            if expense.payer_id not in balances:
                balances[expense.payer_id] = 0
            balances[expense.payer_id] += expense.amount
            
            # Each share owner owes
            for share in expense.shares:
                if share.user_id not in balances:
                    balances[share.user_id] = 0
                balances[share.user_id] -= share.share_amount
        
        return balances
    
    @staticmethod
    def generate_settlements(group_id: str, db: Session) -> List[Settlement]:
        """
        Generate optimized settlements (who should pay whom).
        Uses greedy algorithm to minimize number of transactions.
        """
        balances = SettlementService.calculate_group_balances(group_id, db)
        settlements = []
        
        # Separate into creditors and debtors
        creditors = [(uid, bal) for uid, bal in balances.items() if bal > 0.01]
        debtors = [(uid, bal) for uid, bal in balances.items() if bal < -0.01]
        
        # Sort by amount (largest first)
        creditors.sort(key=lambda x: x[1], reverse=True)
        debtors.sort(key=lambda x: abs(x[1]), reverse=True)
        
        # Match debtors with creditors
        creditor_idx = 0
        debtor_idx = 0
        
        while creditor_idx < len(creditors) and debtor_idx < len(debtors):
            creditor_id, credit_amount = creditors[creditor_idx]
            debtor_id, debt_amount = debtors[debtor_idx]
            
            # Calculate settlement amount (minimum of what's owed)
            settlement_amount = min(credit_amount, -debt_amount)
            
            if settlement_amount > 0.01:
                settlement = Settlement(
                    group_id=group_id,
                    from_user_id=debtor_id,
                    to_user_id=creditor_id,
                    amount=round(settlement_amount, 2)
                )
                settlements.append(settlement)
                
                # Update balances
                creditors[creditor_idx] = (creditor_id, credit_amount - settlement_amount)
                debtors[debtor_idx] = (debtor_id, debt_amount + settlement_amount)
                
                # Move to next if current is settled
                if creditors[creditor_idx][1] <= 0.01:
                    creditor_idx += 1
                if abs(debtors[debtor_idx][1]) <= 0.01:
                    debtor_idx += 1
            else:
                break
        
        return settlements

@router.get("/group/{group_id}/balances", response_model=GroupBalance)
async def get_group_balances(
    group_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get balance summary for a group"""
    try:
        # Verify user is member
        user = db.query(User).filter(User.email == current_user['email']).first()
        group = db.query(Group).filter(Group.id == group_id).first()
        
        if not group or user not in group.members:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Calculate balances
        balances_dict = SettlementService.calculate_group_balances(group_id, db)
        
        # Get user details
        user_balances = []
        for user_id, balance in balances_dict.items():
            user_obj = db.query(User).filter(User.id == user_id).first()
            user_balances.append(UserBalance(
                user_id=user_id,
                username=user_obj.username,
                balance=round(balance, 2)
            ))
        
        # Get total expenses
        total_expenses = db.query(Expense).filter(
            Expense.group_id == group_id,
            Expense.is_settled == False
        ).all()
        total_amount = sum(e.amount for e in total_expenses)
        
        return GroupBalance(
            group_id=group_id,
            balances=user_balances,
            total_expenses=round(total_amount, 2),
            members_count=len(group.members),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get balances: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get balances"
        )

@router.post("/group/{group_id}/calculate", response_model=List[SettlementResponse])
async def calculate_settlements(
    group_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate settlements for a group"""
    try:
        # Verify user is member
        user = db.query(User).filter(User.email == current_user['email']).first()
        group = db.query(Group).filter(Group.id == group_id).first()
        
        if not group or user not in group.members:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Generate settlements
        settlements = SettlementService.generate_settlements(group_id, db)
        logger.info(f"Generated {len(settlements)} settlements for group {group_id}")
        
        return settlements
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate settlements: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate settlements"
        )

@router.post("/group/{group_id}/settle")
async def settle_group_expenses(
    group_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create settlement records for all unsettled expenses"""
    try:
        # Verify user is creator
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group or group.created_by != current_user['user_id']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only group creator can settle"
            )
        
        # Clear old settlements
        db.query(Settlement).filter(
            Settlement.group_id == group_id,
            Settlement.is_paid == False
        ).delete()
        
        # Generate and save new settlements
        settlements = SettlementService.generate_settlements(group_id, db)
        for settlement in settlements:
            db.add(settlement)
        
        # Mark expenses as settled
        db.query(Expense).filter(
            Expense.group_id == group_id,
            Expense.is_settled == False
        ).update({Expense.is_settled: True})
        
        db.commit()
        logger.info(f"Group {group_id} settled with {len(settlements)} transactions")
        
        return {
            "message": "Group settled successfully",
            "settlements_count": len(settlements),
            "settlements": [{
                "from": s.from_user_id,
                "to": s.to_user_id,
                "amount": s.amount
            } for s in settlements]
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to settle group: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to settle group"
        )

@router.get("/group/{group_id}", response_model=List[SettlementResponse])
async def get_group_settlements(
    group_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all settlements for a group"""
    try:
        # Verify user is member
        user = db.query(User).filter(User.email == current_user['email']).first()
        group = db.query(Group).filter(Group.id == group_id).first()
        
        if not group or user not in group.members:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        settlements = db.query(Settlement).filter(
            Settlement.group_id == group_id
        ).order_by(Settlement.created_at.desc()).all()
        
        return settlements
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get settlements: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get settlements"
        )

@router.post("/{settlement_id}/mark-paid")
async def mark_settlement_paid(
    settlement_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a settlement as paid"""
    try:
        settlement = db.query(Settlement).filter(Settlement.id == settlement_id).first()
        if not settlement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Settlement not found"
            )
        
        # Check if user is payer
        if settlement.from_user_id != current_user['user_id']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only debtor can mark as paid"
            )
        
        settlement.is_paid = True
        settlement.paid_at = datetime.utcnow()
        db.commit()
        logger.info(f"Settlement {settlement_id} marked as paid")
        
        return {"message": "Settlement marked as paid"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to mark settlement as paid: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark settlement as paid"
        )
