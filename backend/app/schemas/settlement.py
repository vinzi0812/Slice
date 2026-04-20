from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SettlementCreate(BaseModel):
    group_id: int
    from_user_id: int
    to_user_id: int
    amount: float
    settled_date: datetime | None = None


class SettlementResponse(BaseModel):
    id: int
    group_id: int
    from_user_id: int
    to_user_id: int
    amount: float
    settled_date: datetime | None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
