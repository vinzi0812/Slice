from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Enum, func
from sqlalchemy.orm import relationship
from .database import Base
import enum

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    phone_number = Column(String, nullable=True)
    profile_picture = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    groups = relationship("Group", back_populates="created_by_user")
    group_memberships = relationship("UserGroupMapping", back_populates="user")
    expenses_paid = relationship("Expense", back_populates="paid_by_user")
    expense_splits = relationship("ExpenseSplit", back_populates="user")
    settlements_from = relationship("Settlement", foreign_keys="Settlement.from_user_id", back_populates="from_user")
    settlements_to = relationship("Settlement", foreign_keys="Settlement.to_user_id", back_populates="to_user")


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    simplified_debts = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    created_by_user = relationship("User", back_populates="groups")
    members = relationship("UserGroupMapping", back_populates="group")
    expenses = relationship("Expense", back_populates="group")
    settlements = relationship("Settlement", back_populates="group")
    balances = relationship("UserGroupBalance", back_populates="group")


class UserGroupMapping(Base):
    __tablename__ = "user_group_mapping"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    joined_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="group_memberships")
    group = relationship("Group", back_populates="members")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"))
    paid_by = Column(Integer, ForeignKey("users.id"))
    description = Column(String)
    amount = Column(Float)
    expense_type = Column(String)  # petrol, food, movie, games, etc.
    expense_date = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())

    # Relationships
    group = relationship("Group", back_populates="expenses")
    paid_by_user = relationship("User", back_populates="expenses_paid")
    splits = relationship("ExpenseSplit", back_populates="expense", cascade="all, delete-orphan")


class SplitType(str, enum.Enum):
    equal = "equal"
    percentage = "percentage"
    custom = "custom"


class ExpenseType(str, enum.Enum):
    petrol = "petrol"
    food = "food"
    movie = "movie"
    games = "games"
    groceries = "groceries"
    entertainment = "entertainment"
    utilities = "utilities"
    other = "other"


class ExpenseSplit(Base):
    __tablename__ = "expense_splits"

    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    amount_owed = Column(Float)
    split_type = Column(Enum(SplitType), default=SplitType.equal)
    split_value = Column(Float, nullable=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    expense = relationship("Expense", back_populates="splits")
    user = relationship("User", back_populates="expense_splits")


class SettlementStatus(str, enum.Enum):
    pending = "pending"
    settled = "settled"
    cancelled = "cancelled"


class Settlement(Base):
    __tablename__ = "settlements"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"))
    from_user_id = Column(Integer, ForeignKey("users.id"))
    to_user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    settled_date = Column(DateTime, nullable=True)
    status = Column(Enum(SettlementStatus), default=SettlementStatus.pending)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    group = relationship("Group", back_populates="settlements")
    from_user = relationship("User", foreign_keys="Settlement.from_user_id", back_populates="settlements_from")
    to_user = relationship("User", foreign_keys="Settlement.to_user_id", back_populates="settlements_to")


class UserGroupBalance(Base):
    __tablename__ = "user_group_balances"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    balance = Column(Float, default=0.0)  # Positive = owed money, Negative = owes money
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User")
    group = relationship("Group", back_populates="balances")

