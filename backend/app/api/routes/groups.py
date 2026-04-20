import random

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.models import Group, User, UserGroupMapping
from app.core.auth import get_db, get_current_user
from app.schemas.group import GroupCreate, GroupDetailResponse, GroupSummaryResponse

SAMPLE_GROUPS = [
    ("Goa Escape", "Trip costs for the long-weekend beach run."),
    ("Flat 4B", "Monthly apartment rent, groceries, and utilities."),
    ("Friday Lunch Crew", "Office lunch bills and quick settlements."),
    ("Road Trip North", "Fuel, snacks, tolls, and stay split-ups."),
    ("Birthday House Party", "Decor, drinks, food, and surprise gifts."),
]

router = APIRouter()

def serialize_group(group: Group) -> dict:
    active_members = [mapping.user for mapping in group.members if mapping.is_active]
    return {
        "id": group.id,
        "name": group.name,
        "description": group.description,
        "simplified_debts": group.simplified_debts,
        "created_by": group.created_by,
        "created_at": group.created_at,
        "member_count": len(active_members),
        "members": [
            {
                "id": member.id,
                "name": member.name,
                "email": member.email,
                "username": member.username,
            }
            for member in active_members
        ],
    }


def ensure_group_membership(group_id: int, member_ids: set[int], db: Session) -> None:
    existing_member_ids = {
        mapping.user_id
        for mapping in db.query(UserGroupMapping)
        .filter(UserGroupMapping.group_id == group_id, UserGroupMapping.is_active.is_(True))
        .all()
    }
    for member_id in member_ids:
        if member_id in existing_member_ids:
            continue
        db.add(UserGroupMapping(user_id=member_id, group_id=group_id, is_active=True))


@router.get("/", response_model=list[GroupSummaryResponse])
def list_groups(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List all groups"""
    groups = (
        db.query(Group)
        .join(UserGroupMapping, UserGroupMapping.group_id == Group.id)
        .filter(UserGroupMapping.user_id == current_user.id, UserGroupMapping.is_active.is_(True))
        .order_by(Group.created_at.desc())
        .all()
    )
    return [
        {
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "simplified_debts": group.simplified_debts,
            "created_by": group.created_by,
            "created_at": group.created_at,
            "member_count": len([mapping for mapping in group.members if mapping.is_active]),
        }
        for group in groups
    ]

@router.post("/", response_model=GroupDetailResponse)
def create_group(payload: GroupCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create a new group"""
    member_ids = set(payload.member_ids)
    member_ids.add(current_user.id)
    users = db.query(User).filter(User.id.in_(member_ids)).all()
    if len(users) != len(member_ids):
        raise HTTPException(status_code=400, detail="One or more member IDs are invalid")

    group = Group(
        name=payload.name,
        description=payload.description,
        created_by=current_user.id,
        simplified_debts=payload.simplified_debts,
    )
    db.add(group)
    db.flush()

    ensure_group_membership(group.id, member_ids, db)
    db.commit()
    db.refresh(group)
    return serialize_group(group)

@router.post("/sample-data", response_model=list[GroupDetailResponse])
def create_sample_groups(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create sample groups with a random number of members."""
    users = db.query(User).order_by(User.id).all()
    if len(users) < 2:
        raise HTTPException(status_code=400, detail="At least two users are required to create sample groups")

    seeded_groups: list[Group] = []
    for index, (name, description) in enumerate(SAMPLE_GROUPS):
        group = db.query(Group).filter(Group.name == name).first()
        if group is None:
            group = Group(
                name=name,
                description=description,
                created_by=current_user.id,
                simplified_debts=bool(index % 2),
            )
            db.add(group)
            db.flush()

        member_count = random.randint(2, min(len(users), 5))
        member_ids = {current_user.id}
        candidate_ids = [user.id for user in users if user.id != current_user.id]
        member_ids.update(random.sample(candidate_ids, k=max(1, member_count - 1)))
        ensure_group_membership(group.id, member_ids, db)
        seeded_groups.append(group)

    db.commit()
    for group in seeded_groups:
        db.refresh(group)
    return [serialize_group(group) for group in seeded_groups]


@router.get("/{group_id}", response_model=GroupDetailResponse)
def get_group(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get group by ID"""
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
    return serialize_group(group)
