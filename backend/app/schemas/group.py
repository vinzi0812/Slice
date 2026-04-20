from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    simplified_debts: bool = False
    member_ids: list[int] = Field(default_factory=list)


class GroupMemberResponse(BaseModel):
    id: int
    name: str
    email: str
    username: Optional[str] = None

    class Config:
        from_attributes = True


class GroupSummaryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    simplified_debts: bool
    created_by: int
    created_at: datetime
    member_count: int


class GroupDetailResponse(GroupSummaryResponse):
    members: list[GroupMemberResponse]
