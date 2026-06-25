"""Tests for expense management routes"""
import pytest
from fastapi import status

from app.models import Expense, Group, User


class TestExpenseCreation:
    """Test expense creation"""
    
    def test_create_expense_success(self, client, access_token: str, test_group: Group, test_user: User, test_user_2: User):
        """Test successful expense creation"""
        response = client.post(
            "/api/v1/expenses/",
            json={
                "group_id": test_group.id,
                "description": "Restaurant dinner",
                "amount": 120.0,
                "category": "food",
                "shares": [
                    {"user_id": test_user.id, "share_amount": 60.0},
                    {"user_id": test_user_2.id, "share_amount": 60.0}
                ]
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["description"] == "Restaurant dinner"
        assert data["amount"] == 120.0
        assert len(data["shares"]) == 2
    
    def test_create_expense_invalid_shares_sum(self, client, access_token: str, test_group: Group, test_user: User, test_user_2: User):
        """Test creating expense with shares that don't sum to amount"""
        response = client.post(
            "/api/v1/expenses/",
            json={
                "group_id": test_group.id,
                "description": "Wrong split",
                "amount": 100.0,
                "category": "food",
                "shares": [
                    {"user_id": test_user.id, "share_amount": 50.0},
                    {"user_id": test_user_2.id, "share_amount": 40.0}
                ]
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_expense_no_token(self, client, test_group: Group):
        """Test creating expense without token"""
        response = client.post(
            "/api/v1/expenses/",
            json={
                "group_id": test_group.id,
                "description": "Unauthorized",
                "amount": 100.0,
                "category": "food",
                "shares": []
            }
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestExpenseRetrieval:
    """Test expense retrieval"""
    
    def test_get_group_expenses(self, client, access_token: str, test_group: Group, test_expense: Expense):
        """Test getting expenses from group"""
        response = client.get(
            f"/api/v1/expenses/group/{test_group.id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
    
    def test_get_expense_details(self, client, access_token: str, test_expense: Expense):
        """Test getting expense details"""
        response = client.get(
            f"/api/v1/expenses/{test_expense.id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_expense.id
        assert data["amount"] == 100.0
    
    def test_get_expense_not_found(self, client, access_token: str):
        """Test getting nonexistent expense"""
        response = client.get(
            "/api/v1/expenses/nonexistent-id",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
