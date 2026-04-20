from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from math import isclose

from sqlalchemy.orm import Session

from app.db.models import (
    Expense,
    Group,
    GroupDebt,
    Settlement,
    SettlementStatus,
    UserGroupBalance,
)

AMOUNT_TOLERANCE = 0.01


@dataclass
class SimplifiedTransfer:
    from_user_id: int
    to_user_id: int
    amount: float


def round_currency(value: float) -> float:
    rounded = round(value + 1e-9, 2)
    return 0.0 if isclose(rounded, 0.0, abs_tol=AMOUNT_TOLERANCE) else rounded


def get_group_member_ids(group: Group) -> list[int]:
    return sorted(mapping.user_id for mapping in group.members if mapping.is_active)


def compute_expense_nets(group: Group) -> dict[int, float]:
    net_by_user = {user_id: 0.0 for user_id in get_group_member_ids(group)}

    for expense in group.expenses:
        for contribution in expense.contributions:
            net_by_user.setdefault(contribution.user_id, 0.0)
            net_by_user[contribution.user_id] += contribution.amount_paid

        for split in expense.splits:
            net_by_user.setdefault(split.user_id, 0.0)
            net_by_user[split.user_id] -= split.amount_owed

    return {user_id: round_currency(amount) for user_id, amount in net_by_user.items()}


def compute_raw_group_debts(group: Group) -> dict[tuple[int, int], float]:
    debt_map: dict[tuple[int, int], float] = defaultdict(float)

    for expense in group.expenses:
        total_paid = sum(contribution.amount_paid for contribution in expense.contributions)
        if isclose(total_paid, 0.0, abs_tol=AMOUNT_TOLERANCE):
            continue

        for split in expense.splits:
            if isclose(split.amount_owed, 0.0, abs_tol=AMOUNT_TOLERANCE):
                continue

            for contribution in expense.contributions:
                if isclose(contribution.amount_paid, 0.0, abs_tol=AMOUNT_TOLERANCE):
                    continue

                if split.user_id == contribution.user_id:
                    continue

                pair_amount = split.amount_owed * (contribution.amount_paid / total_paid)
                debt_map[(split.user_id, contribution.user_id)] += pair_amount

    for settlement in group.settlements:
        if settlement.status != SettlementStatus.settled:
            continue
        debt_map[(settlement.from_user_id, settlement.to_user_id)] -= settlement.amount

    normalized = normalize_pairwise_debts(debt_map)
    return {
        key: value
        for key, value in normalized.items()
        if not isclose(value, 0.0, abs_tol=AMOUNT_TOLERANCE)
    }


def normalize_pairwise_debts(
    debt_map: dict[tuple[int, int], float],
) -> dict[tuple[int, int], float]:
    normalized: dict[tuple[int, int], float] = {}
    visited_pairs: set[tuple[int, int]] = set()

    for debtor_id, creditor_id in debt_map:
        if debtor_id == creditor_id:
            continue

        canonical = tuple(sorted((debtor_id, creditor_id)))
        if canonical in visited_pairs:
            continue
        visited_pairs.add(canonical)

        forward_amount = debt_map.get((debtor_id, creditor_id), 0.0)
        reverse_amount = debt_map.get((creditor_id, debtor_id), 0.0)
        net_amount = round_currency(forward_amount - reverse_amount)

        if isclose(net_amount, 0.0, abs_tol=AMOUNT_TOLERANCE):
            continue

        if net_amount > 0:
            normalized[(debtor_id, creditor_id)] = net_amount
        else:
            normalized[(creditor_id, debtor_id)] = abs(net_amount)

    return normalized


def apply_settlements_to_nets(
    net_by_user: dict[int, float],
    settlements: list[Settlement],
) -> dict[int, float]:
    adjusted = dict(net_by_user)

    for settlement in settlements:
        if settlement.status != SettlementStatus.settled:
            continue
        adjusted.setdefault(settlement.from_user_id, 0.0)
        adjusted.setdefault(settlement.to_user_id, 0.0)
        adjusted[settlement.from_user_id] += settlement.amount
        adjusted[settlement.to_user_id] -= settlement.amount

    return {user_id: round_currency(amount) for user_id, amount in adjusted.items()}


def compute_simplified_transfers(group: Group) -> list[SimplifiedTransfer]:
    adjusted_nets = apply_settlements_to_nets(compute_expense_nets(group), list(group.settlements))

    creditors = [
        [user_id, amount]
        for user_id, amount in sorted(adjusted_nets.items())
        if amount > AMOUNT_TOLERANCE
    ]
    debtors = [
        [user_id, abs(amount)]
        for user_id, amount in sorted(adjusted_nets.items())
        if amount < -AMOUNT_TOLERANCE
    ]

    transfers: list[SimplifiedTransfer] = []
    creditor_index = 0
    debtor_index = 0

    while debtor_index < len(debtors) and creditor_index < len(creditors):
        debtor_id, amount_owed = debtors[debtor_index]
        creditor_id, amount_receivable = creditors[creditor_index]

        transfer_amount = round_currency(min(amount_owed, amount_receivable))
        if isclose(transfer_amount, 0.0, abs_tol=AMOUNT_TOLERANCE):
            break

        transfers.append(
            SimplifiedTransfer(
                from_user_id=debtor_id,
                to_user_id=creditor_id,
                amount=transfer_amount,
            )
        )

        debtors[debtor_index][1] = round_currency(amount_owed - transfer_amount)
        creditors[creditor_index][1] = round_currency(amount_receivable - transfer_amount)

        if debtors[debtor_index][1] <= AMOUNT_TOLERANCE:
            debtor_index += 1
        if creditors[creditor_index][1] <= AMOUNT_TOLERANCE:
            creditor_index += 1

    return transfers


def recompute_group_financials(db: Session, group_id: int) -> list[SimplifiedTransfer]:
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise ValueError(f"Group {group_id} not found")

    member_ids = get_group_member_ids(group)
    net_by_user = apply_settlements_to_nets(compute_expense_nets(group), list(group.settlements))

    existing_balances = {
        balance.user_id: balance
        for balance in db.query(UserGroupBalance).filter(UserGroupBalance.group_id == group_id).all()
    }
    for user_id in member_ids:
        balance = existing_balances.get(user_id)
        if balance is None:
            balance = UserGroupBalance(group_id=group_id, user_id=user_id, balance=0.0)
            db.add(balance)
            existing_balances[user_id] = balance
        balance.balance = round_currency(net_by_user.get(user_id, 0.0))

    for user_id, balance in existing_balances.items():
        if user_id not in member_ids:
            db.delete(balance)

    existing_debts = db.query(GroupDebt).filter(GroupDebt.group_id == group_id).all()
    for debt in existing_debts:
        db.delete(debt)

    simplified_transfers: list[SimplifiedTransfer] = []
    if group.simplified_debts:
        simplified_transfers = compute_simplified_transfers(group)
    else:
        for (from_user_id, to_user_id), amount in compute_raw_group_debts(group).items():
            db.add(
                GroupDebt(
                    group_id=group_id,
                    from_user_id=from_user_id,
                    to_user_id=to_user_id,
                    amount=round_currency(amount),
                )
            )

    db.flush()
    return simplified_transfers
