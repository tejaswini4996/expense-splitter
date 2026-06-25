"""Tests for analytics endpoints"""
import pytest
from fastapi import status
from sqlalchemy.orm import Session

from app.models import Expense, ExpenseShare, Group, User


class TestGroupAnalytics:
    """Test group analytics"""
    
    def test_get_group_analytics(self, client, access_token: str, test_group: Group, test_expense: Expense):
        """Test getting group analytics"""
        response = client.get(
            f"/api/v1/analytics/group/{test_group.id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["group_id"] == test_group.id
        assert data["total_expenses"] == 100.0
        assert "by_category" in data
    
    def test_get_analytics_access_denied(self, client, access_token: str, test_user_3: User, db: Session):
        """Test accessing analytics for group user is not member of"""
        # Create exclusive group
        group = Group(
            name="Exclusive",
            created_by=test_user_3.id,
            currency="USD"
        )
        group.members.append(test_user_3)
        db.add(group)
        db.commit()
        
        response = client.get(
            f"/api/v1/analytics/group/{group.id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUserAnalytics:
    """Test user analytics"""
    
    def test_get_user_summary(self, client, access_token: str, test_user: User, test_group: Group, test_expense: Expense):
        """Test getting user financial summary"""
        response = client.get(
            "/api/v1/analytics/user/summary",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == test_user.id
        assert "total_spent" in data
        assert "total_owes" in data
        assert "balance" in data
