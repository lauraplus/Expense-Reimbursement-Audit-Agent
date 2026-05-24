from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Employee(Base):
    __tablename__ = "employees"

    employee_id: Mapped[str] = mapped_column(String, primary_key=True)
    employee_name: Mapped[str] = mapped_column(String, nullable=False)
    department_id: Mapped[str] = mapped_column(String, nullable=False)
    department_name: Mapped[str] = mapped_column(String, nullable=False)
    team_id: Mapped[str] = mapped_column(String, nullable=False)
    level: Mapped[str] = mapped_column(String, nullable=False)
    cost_center: Mapped[str] = mapped_column(String, nullable=False)
    manager_id: Mapped[str] = mapped_column(String, nullable=False)
    vp_id: Mapped[str] = mapped_column(String, nullable=False)


class Team(Base):
    __tablename__ = "teams"

    team_id: Mapped[str] = mapped_column(String, primary_key=True)
    team_name: Mapped[str] = mapped_column(String, nullable=False)
    department_id: Mapped[str] = mapped_column(String, nullable=False)
    base_city: Mapped[str] = mapped_column(String, nullable=False)
    base_location: Mapped[str] = mapped_column(String, nullable=False)
    team_size: Mapped[int] = mapped_column(Integer, nullable=False)
    owner_id: Mapped[str] = mapped_column(String, nullable=False)


class Budget(Base):
    __tablename__ = "budgets"

    budget_id: Mapped[str] = mapped_column(String, primary_key=True)
    team_id: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    period: Mapped[str] = mapped_column(String, nullable=False)
    annual_budget: Mapped[float] = mapped_column(Float, nullable=False)
    used_amount: Mapped[float] = mapped_column(Float, nullable=False)
    frozen_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0)


class ApprovalRecord(Base):
    __tablename__ = "approval_records"

    approval_id: Mapped[str] = mapped_column(String, primary_key=True)
    expense_id: Mapped[str | None] = mapped_column(String, nullable=True)
    employee_id: Mapped[str | None] = mapped_column(String, nullable=True)
    team_id: Mapped[str | None] = mapped_column(String, nullable=True)
    approval_type: Mapped[str] = mapped_column(String, nullable=False)
    approver_id: Mapped[str] = mapped_column(String, nullable=False)
    approved_at: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)


class HistoricalClaim(Base):
    __tablename__ = "historical_claims"

    claim_id: Mapped[str] = mapped_column(String, primary_key=True)
    employee_id: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    expense_date: Mapped[str] = mapped_column(String, nullable=False)
    fingerprint: Mapped[str] = mapped_column(String, nullable=False)


class PolicyChunk(Base):
    __tablename__ = "policy_chunks"

    policy_id: Mapped[str] = mapped_column(String, primary_key=True)
    version: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    effective_from: Mapped[str] = mapped_column(String, nullable=False)
    effective_to: Mapped[str | None] = mapped_column(String, nullable=True)


class PolicyRule(Base):
    __tablename__ = "policy_rules"

    rule_id: Mapped[str] = mapped_column(String, primary_key=True)
    category: Mapped[str] = mapped_column(String, nullable=False)
    policy_id: Mapped[str] = mapped_column(String, nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)


class Expense(Base):
    __tablename__ = "expenses"

    expense_id: Mapped[str] = mapped_column(String, primary_key=True)
    employee_id: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    amount_claimed: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False, default="CNY")
    expense_date: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str | None] = mapped_column(String, nullable=True)
    team_id: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False, default="")
    status: Mapped[str] = mapped_column(String, nullable=False, default="submitted")
    form_data_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    attachments: Mapped[list["Attachment"]] = relationship(back_populates="expense", cascade="all, delete-orphan")
    review_runs: Mapped[list["ReviewRun"]] = relationship(back_populates="expense", cascade="all, delete-orphan")


class Attachment(Base):
    __tablename__ = "attachments"

    attachment_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    expense_id: Mapped[str] = mapped_column(ForeignKey("expenses.expense_id"), nullable=False)
    attachment_type: Mapped[str] = mapped_column(String, nullable=False, default="receipt_image")
    file_path: Mapped[str | None] = mapped_column(String, nullable=True)
    fixture_id: Mapped[str | None] = mapped_column(String, nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String, nullable=True)

    expense: Mapped[Expense] = relationship(back_populates="attachments")


class ReviewRun(Base):
    __tablename__ = "review_runs"

    review_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    expense_id: Mapped[str] = mapped_column(ForeignKey("expenses.expense_id"), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    decision: Mapped[str] = mapped_column(String, nullable=False)
    risk_level: Mapped[str] = mapped_column(String, nullable=False)
    human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reasons_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    policy_citations_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    tool_evidence_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    trace_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    audit_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    model_version: Mapped[str] = mapped_column(String, nullable=False, default="local-controlled-agent-v1")
    policy_version: Mapped[str] = mapped_column(String, nullable=False, default="2026.01")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    expense: Mapped[Expense] = relationship(back_populates="review_runs")
    feedback: Mapped[list["Feedback"]] = relationship(back_populates="review", cascade="all, delete-orphan")


class Feedback(Base):
    __tablename__ = "feedback"

    feedback_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_id: Mapped[int] = mapped_column(ForeignKey("review_runs.review_id"), nullable=False)
    final_decision: Mapped[str] = mapped_column(String, nullable=False)
    operator_name: Mapped[str] = mapped_column(String, nullable=False)
    correction_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    review: Mapped[ReviewRun] = relationship(back_populates="feedback")
