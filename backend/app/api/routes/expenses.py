from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.auth import get_db, get_current_user
from app.db.models import Expense, ExpenseContribution, ExpenseSplit, Group, User, UserGroupMapping
from app.services.financials import recompute_group_financials
from app.schemas.expense import ExpenseCreate, ExpenseResponse

router = APIRouter()

AMOUNT_TOLERANCE = 0.01


def serialize_expense(expense: Expense) -> dict:
    return {
        "id": expense.id,
        "group_id": expense.group_id,
        "description": expense.description,
        "amount": expense.amount,
        "expense_type": expense.expense_type,
        "expense_date": expense.expense_date,
        "created_at": expense.created_at,
        "paid_by": [
            {
                "id": contribution.id,
                "user_id": contribution.user_id,
                "amount_paid": contribution.amount_paid,
            }
            for contribution in expense.contributions
        ],
        "split_by": [
            {
                "id": split.id,
                "user_id": split.user_id,
                "amount_owed": split.amount_owed,
                "split_type": split.split_type.value if hasattr(split.split_type, "value") else split.split_type,
                "split_value": split.split_value,
            }
            for split in expense.splits
        ],
    }

@router.get("/", response_model=list[ExpenseResponse])
def list_expenses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List all expenses"""
    expenses = (
        db.query(Expense)
        .join(Group, Group.id == Expense.group_id)
        .join(UserGroupMapping, UserGroupMapping.group_id == Group.id)
        .filter(
            UserGroupMapping.user_id == current_user.id,
            UserGroupMapping.is_active.is_(True),
        )
        .order_by(Expense.expense_date.desc(), Expense.created_at.desc())
        .all()
    )
    return [serialize_expense(expense) for expense in expenses]


@router.get("/group/{group_id}", response_model=list[ExpenseResponse])
def list_group_expenses(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all expenses for a specific group the current user belongs to."""
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

    expenses = (
        db.query(Expense)
        .filter(Expense.group_id == group_id)
        .order_by(Expense.expense_date.desc(), Expense.created_at.desc())
        .all()
    )
    return [serialize_expense(expense) for expense in expenses]

@router.post("/", response_model=ExpenseResponse)
def create_expense(
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new expense"""
    if not payload.paid_by:
        raise HTTPException(status_code=400, detail="At least one payer entry is required")
    if not payload.split_by:
        raise HTTPException(status_code=400, detail="At least one split entry is required")

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
        raise HTTPException(status_code=404, detail="Group not found")

    contributor_ids = [entry.user_id for entry in payload.paid_by]
    debtor_ids = [entry.user_id for entry in payload.split_by]
    all_user_ids = set(contributor_ids + debtor_ids)

    active_member_ids = {
        mapping.user_id for mapping in group.members if mapping.is_active
    }
    invalid_member_ids = sorted(all_user_ids - active_member_ids)
    if invalid_member_ids:
        raise HTTPException(
            status_code=400,
            detail=f"These users are not active members of the group: {invalid_member_ids}",
        )

    if len(contributor_ids) != len(set(contributor_ids)):
        raise HTTPException(status_code=400, detail="Duplicate payers are not allowed")
    if len(debtor_ids) != len(set(debtor_ids)):
        raise HTTPException(status_code=400, detail="Duplicate split members are not allowed")

    total_paid = round(sum(entry.amount_paid for entry in payload.paid_by), 2)
    total_owed = round(sum(entry.amount_owed for entry in payload.split_by), 2)

    if any(entry.amount_paid <= 0 for entry in payload.paid_by):
        raise HTTPException(status_code=400, detail="All payer amounts must be greater than zero")
    if any(entry.amount_owed < 0 for entry in payload.split_by):
        raise HTTPException(status_code=400, detail="Split amounts cannot be negative")
    if abs(total_paid - total_owed) > AMOUNT_TOLERANCE:
        raise HTTPException(
            status_code=400,
            detail="Total paid amount must match total split amount",
        )

    expense = Expense(
        group_id=payload.group_id,
        description=payload.description.strip(),
        amount=total_paid,
        expense_type=payload.expense_type,
        expense_date=payload.expense_date,
    )
    db.add(expense)
    db.flush()

    contributions = [
        ExpenseContribution(
            expense_id=expense.id,
            user_id=entry.user_id,
            amount_paid=entry.amount_paid,
        )
        for entry in payload.paid_by
    ]
    splits = [
        ExpenseSplit(
            expense_id=expense.id,
            user_id=entry.user_id,
            amount_owed=entry.amount_owed,
            split_type="custom",
            split_value=entry.amount_owed,
        )
        for entry in payload.split_by
    ]

    db.add_all(contributions)
    db.add_all(splits)
    recompute_group_financials(db, payload.group_id)
    db.commit()
    db.refresh(expense)

    return serialize_expense(expense)

@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(expense_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get expense by ID"""
    expense = (
        db.query(Expense)
        .join(Group, Group.id == Expense.group_id)
        .join(UserGroupMapping, UserGroupMapping.group_id == Group.id)
        .filter(
            Expense.id == expense_id,
            UserGroupMapping.user_id == current_user.id,
            UserGroupMapping.is_active.is_(True),
        )
        .first()
    )
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return serialize_expense(expense)
