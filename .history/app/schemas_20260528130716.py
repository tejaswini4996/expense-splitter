"""Pydantic Schemas for request/response validation"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import List, Optional
from enum import Enum

class ExpenseCategory(str, Enum):
    FOOD = "food"
    TRANSPORT = "transport"
    ACCOMMODATION = "accommodation"
    ENTERTAINMENT = "entertainment"
    UTILITIES = "utilities"
    SHOPPING = "shopping"
    HEALTH = "health"
    OTHER = "other"

# ============ User Schemas ============

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============ Group Schemas ============

class GroupBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    currency: str = Field(default="USD", min_length=3, max_length=3)

class GroupCreate(GroupBase):
    member_ids: Optional[List[str]] = []

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    currency: Optional[str] = None

class GroupResponse(GroupBase):
    id: str
    created_by: str
    is_active: bool
    members: List[UserResponse]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class GroupDetailResponse(GroupResponse):
    expenses: Optional[List['ExpenseResponse']] = []
    settlements: Optional[List['SettlementResponse']] = []

# ============ Expense Schemas ============

class ExpenseShare(BaseModel):
    user_id: str
    share_amount: float = Field(..., gt=0)

class ExpenseBase(BaseModel):
    description: str = Field(..., min_length=1, max_length=255)
    amount: float = Field(..., gt=0)
    category: ExpenseCategory = ExpenseCategory.OTHER
    notes: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    group_id: str
    expense_date: Optional[datetime] = None
    shares: List[ExpenseShare]  # Who this expense is split among
    
    @field_validator('shares')
    @classmethod
    def validate_shares(cls, v: List[ExpenseShare], info):
        if not v:
            raise ValueError('Expense must have at least one share')
        total_share = sum(share.share_amount for share in v)
        amount = info.data.get('amount', 0)
        if abs(total_share - amount) > 0.01:  # Allow small floating point difference
            raise ValueError(f'Shares sum ({total_share}) must equal amount ({amount})')
        return v

class ExpenseResponse(ExpenseBase):
    id: str
    group_id: str
    payer_id: str
    expense_date: datetime
    is_settled: bool
    created_at: datetime
    updated_at: datetime
    shares: List['ExpenseShareResponse']
    
    class Config:
        from_attributes = True

class ExpenseShareResponse(BaseModel):
    id: str
    user_id: str
    share_amount: float
    
    class Config:
        from_attributes = True

# ============ Settlement Schemas ============

class SettlementCreate(BaseModel):
    from_user_id: str
    to_user_id: str
    amount: float = Field(..., gt=0)

class SettlementMarkPaid(BaseModel):
    settlement_id: str

class SettlementResponse(BaseModel):
    id: str
    group_id: str
    from_user_id: str
    to_user_id: str
    amount: float
    is_paid: bool
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SettlementDetailResponse(SettlementResponse):
    from_user: UserResponse
    to_user: UserResponse

# ============ Group Balance Schemas ============

class UserBalance(BaseModel):
    user_id: str
    username: str
    balance: float  # Positive = owed money, Negative = owes money

class GroupBalance(BaseModel):
    group_id: str
    balances: List[UserBalance]
    total_expenses: float
    members_count: int

# ============ Analytics Schemas ============

class ExpenseByCategory(BaseModel):
    category: ExpenseCategory
    total_amount: float
    count: int
    percentage: float

class GroupAnalytics(BaseModel):
    group_id: str
    total_expenses: float
    total_settled: float
    pending_amount: float
    member_count: int
    expense_count: int
    by_category: List[ExpenseByCategory]

# ============ Auth Schemas ============

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
"""Pydantic Schemas for request/response validation"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import List, Optional
from enum import Enum

class ExpenseCategory(str, Enum):
    FOOD = "food"
    TRANSPORT = "transport"
    ACCOMMODATION = "accommodation"
    ENTERTAINMENT = "entertainment"
    UTILITIES = "utilities"
    SHOPPING = "shopping"
    HEALTH = "health"
    OTHER = "other"

# ============ User Schemas ============

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============ Group Schemas ============

class GroupBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    currency: str = Field(default="USD", min_length=3, max_length=3)

class GroupCreate(GroupBase):
    member_ids: Optional[List[str]] = []

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    currency: Optional[str] = None

class GroupResponse(GroupBase):
    id: str
    created_by: str
    is_active: bool
    members: List[UserResponse]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class GroupDetailResponse(GroupResponse):
    expenses: Optional[List['ExpenseResponse']] = []
    settlements: Optional[List['SettlementResponse']] = []

# ============ Expense Schemas ============

class ExpenseShareCreate(BaseModel):
    user_id: str
    share_amount: float = Field(..., gt=0)

class ExpenseBase(BaseModel):
    description: str = Field(..., min_length=1, max_length=255)
    amount: float = Field(..., gt=0)
    category: ExpenseCategory = ExpenseCategory.OTHER
    notes: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    group_id: str
    expense_date: Optional[datetime] = None
    shares: List[ExpenseShareCreate]  # Who this expense is split among
    
    @field_validator('shares')
    @classmethod
    def validate_shares(cls, v: List[ExpenseShareCreate], info):
        if not v:
            raise ValueError('Expense must have at least one share')
        total_share = sum(share.share_amount for share in v)
        amount = info.data.get('amount', 0)
        if abs(total_share - amount) > 0.01:  # Allow small floating point difference
            raise ValueError(f'Shares sum ({total_share}) must equal amount ({amount})')
        return v

class ExpenseResponse(ExpenseBase):
    id: str
    group_id: str
    payer_id: str
    expense_date: datetime
    is_settled: bool
    created_at: datetime
    updated_at: datetime
    shares: List['ExpenseShareResponse']
    
    class Config:
        from_attributes = True

class ExpenseShareResponse(BaseModel):
    id: str
    user_id: str
    share_amount: float
    
    class Config:
        from_attributes = True

# ============ Settlement Schemas ============

class SettlementCreate(BaseModel):
    from_user_id: str
    to_user_id: str
    amount: float = Field(..., gt=0)

class SettlementMarkPaid(BaseModel):
    settlement_id: str

class SettlementResponse(BaseModel):
    id: str
    group_id: str
    from_user_id: str
    to_user_id: str
    amount: float
    is_paid: bool
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SettlementDetailResponse(SettlementResponse):
    from_user: UserResponse
    to_user: UserResponse

# ============ Group Balance Schemas ============

class UserBalance(BaseModel):
    user_id: str
    username: str
    balance: float  # Positive = owed money, Negative = owes money

class GroupBalance(BaseModel):
    group_id: str
    balances: List[UserBalance]
    total_expenses: float
    members_count: int

# ============ Analytics Schemas ============

class ExpenseByCategory(BaseModel):
    category: str
    total_amount: float
    count: int
    percentage: float

class GroupAnalytics(BaseModel):
    group_id: str
    total_expenses: float
    total_settled: float
    pending_amount: float
    member_count: int
    expense_count: int
    by_category: List[ExpenseByCategory]

# ============ Auth Schemas ============

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[str] = None

# Update forward references
GroupDetailResponse.model_rebuild()
ExpenseResponse.model_rebuild()
ExpenseShareResponse.model_rebuild()
class TokenData(BaseModel):
    email: Optional[str] = None

# Update forward references
GroupDetailResponse.model_rebuild()
ExpenseResponse.model_rebuild()
ExpenseShareResponse.model_rebuild()