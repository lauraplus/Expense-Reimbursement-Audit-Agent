from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


ExpenseCategory = Literal["traffic_overtime_taxi", "travel_hotel", "team_building"]
Decision = Literal["suggested_pass", "suggested_reject", "human_review_required", "agent_failed"]


class ExpenseCreate(BaseModel):
    employee_id: str
    category: ExpenseCategory
    amount_claimed: float = Field(gt=0)
    currency: str = "CNY"
    expense_date: str
    city: str | None = None
    team_id: str | None = None
    title: str = ""
    form_data: dict[str, Any] = Field(default_factory=dict)
    attachment_fixture_id: str | None = None


class FeedbackCreate(BaseModel):
    final_decision: Literal["finance_confirmed", "finance_overridden"]
    operator_name: str = "财务审核员"
    correction_reason: str = ""


class ToolEvidence(BaseModel):
    tool: str
    server: str
    status: str
    result_summary: str
    latency_ms: int


class ReviewResult(BaseModel):
    review_id: int
    expense_id: str
    decision: Decision
    risk_level: Literal["low", "medium", "high"]
    human_review_required: bool
    reasons: list[dict[str, Any]]
    policy_citations: list[dict[str, Any]]
    tool_evidence: list[ToolEvidence]
    audit_summary: str
    status: str
    model_version: str
    policy_version: str
    created_at: str


class AttachmentOut(BaseModel):
    attachment_id: int
    attachment_type: str
    file_path: str | None
    fixture_id: str | None
    original_filename: str | None


class ExpenseOut(BaseModel):
    expense_id: str
    employee_id: str
    category: str
    amount_claimed: float
    currency: str
    expense_date: str
    city: str | None
    team_id: str | None
    title: str
    status: str
    form_data: dict[str, Any]
    attachments: list[AttachmentOut]
    latest_review: ReviewResult | None = None


class FeedbackOut(BaseModel):
    feedback_id: int
    review_id: int
    final_decision: str
    operator_name: str
    correction_reason: str
    created_at: str
