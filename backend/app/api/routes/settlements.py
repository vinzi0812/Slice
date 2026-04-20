from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_db, get_current_user
from app.db.models import Group, Settlement, SettlementStatus, User, UserGroupMapping
from app.schemas.settlement import SettlementCreate, SettlementResponse
from app.services.financials import recompute_group_financials

router = APIRouter()


@router.post("/", response_model=SettlementResponse)
def create_settlement(
    payload: SettlementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new settlement to settle up debts between users in a group."""
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Settlement amount must be greater than zero")
    if payload.from_user_id == payload.to_user_id:
        raise HTTPException(status_code=400, detail="Cannot settle with yourself")

    # Check if current user is in the group
    group = (
        db.query(Group)
        .join(UserGroupMapping, UserGroupMapping.group_id == Group.id)
        .filter(
            Group.id == payload.group_id,
            UserGroupMapping.user_id == current_user.id,
            UserGroupMapping.is_active.is_(True),
        )
        .first()
    )
    if not group:
        raise HTTPException(status_code=404, detail="Group not found or you are not a member")

    # Check if from_user and to_user are active members
    member_ids = {mapping.user_id for mapping in group.members if mapping.is_active}
    if payload.from_user_id not in member_ids:
        raise HTTPException(status_code=400, detail="From user is not an active member of the group")
    if payload.to_user_id not in member_ids:
        raise HTTPException(status_code=400, detail="To user is not an active member of the group")

    # Create settlement
    settlement = Settlement(
        group_id=payload.group_id,
        from_user_id=payload.from_user_id,
        to_user_id=payload.to_user_id,
        amount=payload.amount,
        settled_date=payload.settled_date or datetime.now(UTC),
        status=SettlementStatus.settled,
    )
    db.add(settlement)
    db.flush()

    # Recompute financials
    recompute_group_financials(db, payload.group_id)

    db.commit()
    db.refresh(settlement)

    return SettlementResponse.model_validate(settlement)


@router.get("/group/{group_id}", response_model=list[SettlementResponse])
def list_group_settlements(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all settlements for a specific group the current user belongs to."""
    group = (
        db.query(Group)
        .join(UserGroupMapping, UserGroupMapping.group_id == Group.id)
        .filter(
            Group.id == group_id,
            UserGroupMapping.user_id == current_user.id,
            UserGroupMapping.is_active.is_(True),
        )
        .first()
    )
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    settlements = db.query(Settlement).filter(Settlement.group_id == group_id).all()
    return [SettlementResponse.model_validate(s) for s in settlements]
