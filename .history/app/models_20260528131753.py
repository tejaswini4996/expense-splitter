"""Database Models"""
from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey, Boolean, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from enum import Enum
from app.database import Base

class ExpenseCategory(str, Enum):
    """Expense categories"""
    FOOD = "food"
    TRANSPORT = "transport"
    ACCOMMODATION = "accommodation"
    ENTERTAINMENT = "entertainment"
    UTILITIES = "utilities"
    SHOPPING = "shopping"
    HEALTH = "health"
    OTHER = "other"

class User(Base):
    """User Model"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(255))
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    groups = relationship("Group", secondary="group_members", back_populates="members")
    expenses = relationship("Expense", back_populates="payer", foreign_keys="Expense.payer_id")
    expense_shares = relationship("ExpenseShare", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"

class Group(Base):
    """Group Model for shared expenses"""
    __tablename__ = "groups"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    currency = Column(String(3), default="USD")  # ISO 4217 currency code
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    members = relationship("User", secondary="group_members", back_populates="groups")
    expenses = relationship("Expense", back_populates="group", cascade="all, delete-orphan")
    settlements = relationship("Settlement", back_populates="group", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Group(id={self.id}, name={self.name}, created_by={self.created_by})>"

class GroupMember(Base):
    """Group Members Association Table"""
    __tablename__ = "group_members"
    
    group_id = Column(String(36), ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class Expense(Base):
    """Expense Model"""
    __tablename__ = "expenses"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = Column(String(36), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    payer_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    description = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)  # Total amount paid
    category = Column(SQLEnum(ExpenseCategory), default=ExpenseCategory.OTHER)
    expense_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    receipt_url = Column(String(255))
    notes = Column(Text)
    is_settled = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    group = relationship("Group", back_populates="expenses")
    payer = relationship("User", back_populates="expenses", foreign_keys=[payer_id])
    shares = relationship("ExpenseShare", back_populates="expense", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Expense(id={self.id}, group_id={self.group_id}, amount={self.amount})>"

class ExpenseShare(Base):
    """Expense Share Model - Who owes what for each expense"""
    __tablename__ = "expense_shares"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    expense_id = Column(String(36), ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    share_amount = Column(Float, nullable=False)  # Amount this user owes for this expense
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    expense = relationship("Expense", back_populates="shares")
    user = relationship("User", back_populates="expense_shares")
    
    def __repr__(self):
        return f"<ExpenseShare(id={self.id}, expense_id={self.expense_id}, user_id={self.user_id}, amount={self.share_amount})>"

class Settlement(Base):
    """Settlement Model - Who should pay whom"""
    __tablename__ = "settlements"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = Column(String(36), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    from_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)  # Debtor
    to_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)    # Creditor
    amount = Column(Float, nullable=False)
    is_paid = Column(Boolean, default=False, index=True)
    paid_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    group = relationship("Group", back_populates="settlements")
    
    def __repr__(self):
        return f"<Settlement(id={self.id}, from={self.from_user_id}, to={self.to_user_id}, amount={self.amount})>"

class TransactionLog(Base):
    """Transaction Log for audit trail"""
    __tablename__ = "transaction_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String(100), nullable=False)  # "expense_created", "settlement_paid", etc.
    resource_type = Column(String(50))  # "expense", "settlement", etc.
    resource_id = Column(String(36))
    details = Column(Text)  # JSON details
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<TransactionLog(id={self.id}, user_id={self.user_id}, action={self.action})>"