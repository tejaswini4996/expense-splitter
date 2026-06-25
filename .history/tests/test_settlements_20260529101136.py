"""Tests for settlement calculation and management"""
import pytest
from fastapi import status
from sqlalchemy.orm import Session

from app.models import Expense, ExpenseShare, Group, User, Settlement
from app.routes.settlements import SettlementService


class TestBalanceCalculation:
    """Test balance calculation logic"""
    
    def test_calculate_group_balances_equal_split(self, db: Session, test_group: Group, test_user: User, test_user_2: User, test_expense: Expense):
        """Test balance calculation with equal split"""
        balances = SettlementService.calculate_group_balances(test_group.id, db)
        
        # test_user paid 100, owes 50 -> balance = +50
        assert balances[test_user.id] == 50.0
        # test_user_2 owes 50 -> balance = -50
        assert balances[test_user_2.id] == -50.0


class TestSettlementGeneration:
    """Test settlement generation algorithm"""
    
    def test_generate_settlements_two_users(self, db: Session, test_group: Group, test_user: User, test_user_2: User):
        """Test settlement generation with two users"""
        # User 1 pays 100, split equally -> User 2 owes 50
        expense = Expense(
            group_id=test_group.id,
            payer_id=test_user.id,
            description="Shared expense",
            amount=100.0,
            category="food"
        )
        share1 = ExpenseShare(user_id=test_user.id, share_amount=50.0)
        share2 = ExpenseShare(user_id=test_user_2.id, share_amount=50.0)
        
        expense.shares.append(share1)
        expense.shares.append(share2)
        
        db.add(expense)
        db.commit()
        
        settlements = SettlementService.generate_settlements(test_group.id, db)
        
        assert len(settlements) == 1
        settlement = settlements[0]
        assert settlement.from_user_id == test_user_2.id
        assert settlement.to_user_id == test_user.id
        assert settlement.amount == 50.0


class TestSettlementAPI:
    """Test settlement API endpoints"""
    
    def test_get_group_balances(self, client, access_token: str, test_group: Group, test_expense: Expense):
        """Test getting group balances"""
        response = client.get(
            f"/api/v1/settlements/group/{test_group.id}/balances",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["group_id"] == test_group.id
        assert "balances" in data
    
    def test_calculate_settlements(self, client, access_token: str, test_group: Group, test_expense: Expense):
        """Test settlement calculation endpoint"""
        response = client.post(
            f"/api/v1/settlements/group/{test_group.id}/calculate",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
