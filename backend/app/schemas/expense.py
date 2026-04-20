from datetime import datetime

from pydantic import BaseModel, Field


class ExpenseContributionCreate(BaseModel):
    user_id: int
    amount_paid: float


class ExpenseSplitCreate(BaseModel):
    user_id: int
    amount_owed: float


class ExpenseCreate(BaseModel):
    group_id: int
    description: str
    expense_type: str = "other"
    expense_date: datetime
    paid_by: list[ExpenseContributionCreate] = Field(default_factory=list)
    split_by: list[ExpenseSplitCreate] = Field(default_factory=list)


class ExpenseContributionResponse(ExpenseContributionCreate):
    id: int

    class Config:
        from_attributes = True


class ExpenseSplitResponse(ExpenseSplitCreate):
    id: int
    split_type: str
    split_value: float | None = None

    class Config:
        from_attributes = True


class ExpenseResponse(BaseModel):
    id: int
    group_id: int
    description: str
    amount: float
    expense_type: str
    expense_date: datetime
    created_at: datetime
    paid_by: list[ExpenseContributionResponse]
    split_by: list[ExpenseSplitResponse]

