"""Settlement routes"""
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
import logging

from app.schemas import SettlementResponse
from app.models import Settlement
from app.database import get_db
from app.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/{group_id}", response_model=list[SettlementResponse])
async def list_settlements(group_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """List settlements for a group"""
    try:
        settlements = db.query(Settlement).filter(Settlement.group_id == group_id).all()
        return settlements
    except Exception as e:
        logger.error(f"Failed to list settlements: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list settlements"
        )

@router.post("/{settlement_id}/mark-paid", status_code=status.HTTP_200_OK)
async def mark_settlement_paid(settlement_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Mark a settlement as paid"""
    try:
        settlement = db.query(Settlement).filter(Settlement.id == settlement_id).first()
        if not settlement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Settlement not found"
            )
        
        settlement.is_paid = True
        from datetime import datetime
        settlement.paid_at = datetime.utcnow()
        db.commit()
        logger.info(f"Settlement marked as paid: {settlement_id}")
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
