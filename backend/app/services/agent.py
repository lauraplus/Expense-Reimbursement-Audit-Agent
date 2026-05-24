from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from ..models import Attachment, Expense, ReviewRun
from .mcp_clients import MCPResult, MockMCPGateway
from .ocr import OCRService
from .rules import RuleContext, RuleEngine, RuleIssue


class ControlledExpenseAgent:
    def __init__(self, db: Session):
        self.db = db
        self.mcp = MockMCPGateway(db)
        self.ocr = OCRService()
        self.rules = RuleEngine()

    def review(self, expense_id: str) -> ReviewRun:
        expense = self.db.get(Expense, expense_id)
        if not expense:
            raise ValueError(f"Expense not found: {expense_id}")
        expense.status = "agent_reviewing"
        self.db.flush()
        trace: list[dict[str, Any]] = []
        evidence: list[dict[str, Any]] = []
        citations: list[dict[str, Any]] = []
        try:
            form_data = json.loads(expense.form_data_json or "{}")
            employee = self._call("hr", "query_employee_profile", {"employee_id": expense.employee_id}, trace, evidence).data
            team_id = expense.team_id or employee.get("team_id")
            team = {}
            budget = {}
            if team_id:
                team = self._call("hr", "query_team_info", {"team_id": team_id}, trace, evidence).data
            manager_approvals = self._call(
                "approval",
                "query_approval_records",
                {
                    "expense_id": expense.expense_id,
                    "employee_id": expense.employee_id,
                    "team_id": team_id,
                    "approval_type": "department_manager",
                },
                trace,
                evidence,
            ).data.get("records", [])
            vp_approvals = self._call(
                "approval",
                "query_approval_records",
                {
                    "expense_id": expense.expense_id,
                    "employee_id": expense.employee_id,
                    "team_id": team_id,
                    "approval_type": "vp",
                },
                trace,
                evidence,
            ).data.get("records", [])
            if expense.category == "team_building" and team_id:
                budget = self._call("budget", "query_budget_balance", {"team_id": team_id, "category": "team_building"}, trace, evidence).data
            policy = self._call(
                "policy",
                "search_expense_policy",
                {"category": expense.category, "query": self._policy_query(expense.category, form_data)},
                trace,
                evidence,
            ).data
            citations = self._policy_citations(policy)
            attachment = self._primary_attachment(expense)
            ocr_result = self.ocr.parse_receipt_image(
                category=expense.category,
                fixture_id=attachment.fixture_id if attachment else None,
                file_path=attachment.file_path if attachment else None,
            )
            evidence.append(
                {
                    "server": "receipt",
                    "tool": "parse_receipt_image",
                    "status": "error" if ocr_result.get("error_code") else "ok",
                    "result_summary": self._ocr_summary(ocr_result),
                    "latency_ms": 0,
                }
            )
            trace.append({"step": "parse_receipt_image", "observation": self._ocr_summary(ocr_result)})
            ctx = RuleContext(
                expense_id=expense.expense_id,
                category=expense.category,
                amount_claimed=expense.amount_claimed,
                city=expense.city,
                team_id=team_id,
                form_data=form_data,
                ocr=ocr_result,
                employee=employee,
                team=team,
                budget=budget,
                manager_approvals=manager_approvals,
                vp_approvals=vp_approvals,
            )
            blockers, review_issues = self.rules.evaluate(ctx)
            decision = self._decision(blockers, review_issues)
            risk_level = self._risk_level(blockers, review_issues)
            reasons = [self._issue_dict(issue) for issue in [*blockers, *review_issues]]
            audit_summary = self._audit_summary(expense, decision, blockers, review_issues, citations)
        except Exception as exc:  # pragma: no cover - defensive request boundary
            decision = "agent_failed"
            risk_level = "high"
            reasons = [{"issue": "agent_failed", "description": f"Agent 初审失败：{exc}", "severity": "high", "action": "review"}]
            audit_summary = f"Agent 初审失败：{exc}"
            citations = []
            expense.status = "agent_failed"
        else:
            expense.status = decision
        review = ReviewRun(
            expense_id=expense.expense_id,
            status=expense.status,
            decision=decision,
            risk_level=risk_level,
            human_review_required=decision in {"human_review_required", "agent_failed"},
            reasons_json=json.dumps(reasons, ensure_ascii=False),
            policy_citations_json=json.dumps(citations, ensure_ascii=False),
            tool_evidence_json=json.dumps(evidence, ensure_ascii=False),
            trace_json=json.dumps(trace, ensure_ascii=False),
            audit_summary=audit_summary,
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review

    def _call(self, server: str, tool: str, arguments: dict[str, Any], trace: list[dict[str, Any]], evidence: list[dict[str, Any]]) -> MCPResult:
        trace.append({"step": "tool_call", "server": server, "tool": tool, "arguments": arguments})
        result = self.mcp.call_tool(server, tool, arguments)
        trace.append({"step": "tool_observation", "server": server, "tool": tool, "status": result.status, "summary": result.result_summary})
        evidence.append(result.evidence())
        return result

    def _primary_attachment(self, expense: Expense) -> Attachment | None:
        return expense.attachments[0] if expense.attachments else None

    def _policy_query(self, category: str, form_data: dict[str, Any]) -> str:
        if category == "traffic_overtime_taxi":
            return "加班打车 车型 标准 金额 时间"
        if category == "travel_hotel":
            return f"{form_data.get('hotel_city', '')} 住宿标准 职级 金额"
        return "团建 跨城 预算 人均 VP 审批"

    def _policy_citations(self, policy_result: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {"policy_id": item["policy_id"], "title": item["title"], "text": item["text"], "version": item["version"]}
            for item in policy_result.get("results", [])
        ]

    def _decision(self, blockers: list[RuleIssue], review_issues: list[RuleIssue]) -> str:
        if review_issues:
            return "human_review_required"
        if blockers:
            return "suggested_reject"
        return "suggested_pass"

    def _risk_level(self, blockers: list[RuleIssue], review_issues: list[RuleIssue]) -> str:
        severities = {issue.severity for issue in [*blockers, *review_issues]}
        if "high" in severities:
            return "high"
        if "medium" in severities:
            return "medium"
        return "low"

    def _issue_dict(self, issue: RuleIssue) -> dict[str, Any]:
        return {
            "issue": issue.issue,
            "description": issue.description,
            "policy_id": issue.policy_id,
            "severity": issue.severity,
            "action": issue.action,
        }

    def _audit_summary(self, expense: Expense, decision: str, blockers: list[RuleIssue], review_issues: list[RuleIssue], citations: list[dict[str, Any]]) -> str:
        if decision == "suggested_pass":
            return f"单据 {expense.expense_id} 未发现确定性违规，建议通过。已引用 {len(citations)} 条政策并完成必要工具查询。"
        issue_text = "；".join(issue.description for issue in [*blockers, *review_issues]) or "需要人工确认"
        label = "需人工复核" if decision == "human_review_required" else "建议驳回"
        return f"单据 {expense.expense_id} {label}：{issue_text}"

    def _ocr_summary(self, ocr_result: dict[str, Any]) -> str:
        if ocr_result.get("error_code"):
            return ocr_result["error_message"]
        normalized = ocr_result.get("normalized", {})
        return f"OCR 置信度 {ocr_result.get('confidence', 0):.2f}，结构化字段：{json.dumps(normalized, ensure_ascii=False)}"
