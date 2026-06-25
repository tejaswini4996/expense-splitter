"""Pytest configuration and fixtures"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os

from app.main import app
from app.database import Base, get_db
from app.models import User, Group, Expense, ExpenseShare, Settlement
from app.security import SecurityUtils

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def db() -> Session:
    """Database session fixture"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def test_user(db: Session) -> User:
    """Create test user"""
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password=SecurityUtils.hash_password("test_password_123")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_user_2(db: Session) -> User:
    """Create second test user"""
    user = User(
        email="test2@example.com",
        username="testuser2",
        full_name="Test User 2",
        hashed_password=SecurityUtils.hash_password("test_password_123")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_user_3(db: Session) -> User:
    """Create third test user"""
    user = User(
        email="test3@example.com",
        username="testuser3",
        full_name="Test User 3",
        hashed_password=SecurityUtils.hash_password("test_password_123")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def access_token(test_user: User) -> str:
    """Create JWT access token for test user"""
    from datetime import timedelta
    token = SecurityUtils.create_access_token(
        data={"sub": test_user.email, "user_id": test_user.id},
        expires_delta=timedelta(hours=1)
    )
    return token


@pytest.fixture
def test_group(db: Session, test_user: User, test_user_2: User) -> Group:
    """Create test group"""
    group = Group(
        name="Test Group",
        description="Test group description",
        created_by=test_user.id,
        currency="USD"
    )
    group.members.append(test_user)
    group.members.append(test_user_2)
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


@pytest.fixture
def test_expense(db: Session, test_group: Group, test_user: User, test_user_2: User) -> Expense:
    """Create test expense"""
    expense = Expense(
        group_id=test_group.id,
        payer_id=test_user.id,
        description="Test Expense",
        amount=100.0,
        category="food"
    )
    
    # Add shares
    share1 = ExpenseShare(
        expense_id=expense.id,
        user_id=test_user.id,
        share_amount=50.0
    )
    share2 = ExpenseShare(
        expense_id=expense.id,
        user_id=test_user_2.id,
        share_amount=50.0
    )
    
    db.add(expense)
    db.add(share1)
    db.add(share2)
    db.commit()
    db.refresh(expense)
    return expense
