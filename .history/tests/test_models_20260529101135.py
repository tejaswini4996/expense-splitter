"""Tests for database models"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import User, Group, Expense, ExpenseShare, Settlement
from app.security import SecurityUtils


class TestUserModel:
    """Test User model"""
    
    def test_create_user(self, db: Session):
        """Test creating user"""
        user = User(
            email="newuser@example.com",
            username="newuser",
            full_name="New User",
            hashed_password=SecurityUtils.hash_password("password123")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.is_active == True


class TestGroupModel:
    """Test Group model"""
    
    def test_create_group(self, db: Session, test_user: User):
        """Test creating group"""
        group = Group(
            name="Test Group",
            description="Test description",
            created_by=test_user.id,
            currency="USD"
        )
        db.add(group)
        db.commit()
        db.refresh(group)
        
        assert group.id is not None
        assert group.name == "Test Group"
        assert group.currency == "USD"


class TestExpenseModel:
    """Test Expense model"""
    
    def test_create_expense(self, db: Session, test_group: Group, test_user: User):
        """Test creating expense"""
        expense = Expense(
            group_id=test_group.id,
            payer_id=test_user.id,
            description="Test expense",
            amount=100.0,
            category="food"
        )
        db.add(expense)
        db.commit()
        db.refresh(expense)
        
        assert expense.id is not None
        assert expense.amount == 100.0
        assert expense.is_settled == False
"""Tests for database models"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import User, Group, Expense, ExpenseShare, Settlement
from app.security import SecurityUtils


class TestUserModel:
    """Test User model"""
    
    def test_create_user(self, db: Session):
        """Test creating user"""
        user = User(
            email="newuser@example.com",
            username="newuser",
            full_name="New User",
            hashed_password=SecurityUtils.hash_password("password123")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.is_active == True


class TestGroupModel:
    """Test Group model"""
    
    def test_create_group(self, db: Session, test_user: User):
        """Test creating group"""
        group = Group(
            name="Test Group",
            description="Test description",
            created_by=test_user.id,
            currency="USD"
        )
        db.add(group)
        db.commit()
        db.refresh(group)
        
        assert group.id is not None
        assert group.name == "Test Group"
        assert group.currency == "USD"


class TestExpenseModel:
    """Test Expense model"""
    
    def test_create_expense(self, db: Session, test_group: Group, test_user: User):
        """Test creating expense"""
        expense = Expense(
            group_id=test_group.id,
            payer_id=test_user.id,
            description="Test expense",
            amount=100.0,
            category="food"
        )
        db.add(expense)
        db.commit()
        db.refresh(expense)
        
        assert expense.id is not None
        assert expense.amount == 100.0
        assert expense.is_settled == False
