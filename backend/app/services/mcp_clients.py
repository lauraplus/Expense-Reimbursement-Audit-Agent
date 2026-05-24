from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..models import ApprovalRecord, Budget, Employee, HistoricalClaim, PolicyChunk, Team


@dataclass
class MCPResult:
    server: str
    tool: str
    status: str
    data: dict[str, Any]
    result_summary: str
    latency_ms: int

    def evidence(self) -> dict[str, Any]:
        return {
            "server": self.server,
            "tool": self.tool,
            "status": self.status,
            "result_summary": self.result_summary,
            "latency_ms": self.latency_ms,
        }


class MockMCPGateway:
    """A JSON-RPC-like mock MCP tool gateway backed by SQLite.

    The Agent only calls tools through this gateway. Replacing a mock tool with a
    real MCP server later requires preserving the tool name and schemas.
    """

    def __init__(self, db: Session):
        self.db = db

    def call_tool(self, server: str, tool: str, arguments: dict[str, Any]) -> MCPResult:
        start = time.perf_counter()
        try:
            data = self._dispatch(server, tool, arguments)
            status = "ok"
            summary = self._summarize(tool, data)
        except Exception as exc:  # pragma: no cover - defensive tool boundary
            data = {"error": str(exc), "error_code": "MOCK_MCP_TOOL_ERROR"}
            status = "error"
            summary = str(exc)
        latency_ms = int((time.perf_counter() - start) * 1000)
        return MCPResult(server=server, tool=tool, status=status, data=data, result_summary=summary, latency_ms=latency_ms)

    def _dispatch(self, server: str, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if server == "hr" and tool == "query_employee_profile":
            employee = self.db.get(Employee, arguments["employee_id"])
            if not employee:
                return {"found": False}
            return {
                "found": True,
                "employee_id": employee.employee_id,
                "employee_name": employee.employee_name,
                "department_id": employee.department_id,
                "department_name": employee.department_name,
                "team_id": employee.team_id,
                "level": employee.level,
                "cost_center": employee.cost_center,
                "manager_id": employee.manager_id,
                "vp_id": employee.vp_id,
            }
        if server == "hr" and tool == "query_team_info":
            team = self.db.get(Team, arguments["team_id"])
            if not team:
                return {"found": False}
            return {
                "found": True,
                "team_id": team.team_id,
                "team_name": team.team_name,
                "department_id": team.department_id,
                "base_city": team.base_city,
                "base_location": team.base_location,
                "team_size": team.team_size,
                "owner_id": team.owner_id,
            }
        if server == "budget" and tool == "query_budget_balance":
            budget = (
                self.db.query(Budget)
                .filter(Budget.team_id == arguments["team_id"], Budget.category == arguments["category"])
                .first()
            )
            if not budget:
                return {"found": False}
            remaining = budget.annual_budget - budget.used_amount - budget.frozen_amount
            return {
                "found": True,
                "budget_id": budget.budget_id,
                "team_id": budget.team_id,
                "category": budget.category,
                "period": budget.period,
                "annual_budget": budget.annual_budget,
                "used_amount": budget.used_amount,
                "frozen_amount": budget.frozen_amount,
                "remaining_amount": remaining,
            }
        if server == "approval" and tool == "query_approval_records":
            query = self.db.query(ApprovalRecord)
            expense_id = arguments.get("expense_id")
            employee_id = arguments.get("employee_id")
            team_id = arguments.get("team_id")
            approval_type = arguments.get("approval_type")
            if expense_id:
                query = query.filter(ApprovalRecord.expense_id == expense_id)
            else:
                filters = []
                if employee_id:
                    filters.append(ApprovalRecord.employee_id == employee_id)
                if team_id:
                    filters.append(ApprovalRecord.team_id == team_id)
                if filters:
                    query = query.filter(or_(*filters))
            if approval_type:
                query = query.filter(ApprovalRecord.approval_type == approval_type)
            records = query.all()
            return {
                "found": bool(records),
                "records": [
                    {
                        "approval_id": r.approval_id,
                        "expense_id": r.expense_id,
                        "approval_type": r.approval_type,
                        "approver_id": r.approver_id,
                        "approved_at": r.approved_at,
                        "summary": r.summary,
                    }
                    for r in records
                ],
            }
        if server == "policy" and tool == "search_expense_policy":
            category = arguments.get("category")
            query = (arguments.get("query") or "").lower()
            chunks_query = self.db.query(PolicyChunk)
            if category:
                chunks_query = chunks_query.filter(PolicyChunk.category == category)
            chunks = chunks_query.all()
            ranked = []
            for chunk in chunks:
                haystack = f"{chunk.policy_id} {chunk.title} {chunk.text}".lower()
                score = sum(1 for token in query.replace("/", " ").split() if token and token in haystack)
                if score or not query:
                    ranked.append((score, chunk))
            ranked.sort(key=lambda item: item[0], reverse=True)
            results = [
                {
                    "policy_id": chunk.policy_id,
                    "version": chunk.version,
                    "category": chunk.category,
                    "title": chunk.title,
                    "text": chunk.text,
                    "effective_from": chunk.effective_from,
                    "effective_to": chunk.effective_to,
                    "score": score,
                }
                for score, chunk in ranked[:5]
            ]
            return {"found": bool(results), "results": results}
        if server == "expense" and tool == "check_duplicate_claim":
            claims = (
                self.db.query(HistoricalClaim)
                .filter(HistoricalClaim.employee_id == arguments["employee_id"], HistoricalClaim.category == arguments["category"])
                .all()
            )
            fingerprint = arguments.get("fingerprint")
            matches = [c for c in claims if fingerprint and c.fingerprint == fingerprint]
            return {
                "found": bool(matches),
                "matches": [
                    {"claim_id": c.claim_id, "amount": c.amount, "expense_date": c.expense_date, "fingerprint": c.fingerprint}
                    for c in matches
                ],
            }
        raise ValueError(f"Unknown mock MCP tool: {server}.{tool}")

    def _summarize(self, tool: str, data: dict[str, Any]) -> str:
        if not data.get("found", True):
            return "未查询到匹配数据"
        if tool == "query_employee_profile":
            return f"{data['employee_name']}，{data['department_name']}，职级 {data['level']}"
        if tool == "query_team_info":
            return f"{data['team_name']} base 地为 {data['base_city']}，团队人数 {data['team_size']}"
        if tool == "query_budget_balance":
            return f"年度预算 {data['annual_budget']}，已用 {data['used_amount']}，冻结 {data['frozen_amount']}，剩余 {data['remaining_amount']}"
        if tool == "query_approval_records":
            return f"查询到 {len(data['records'])} 条审批记录" if data["records"] else "未查询到审批记录"
        if tool == "search_expense_policy":
            return "命中政策：" + "、".join(item["policy_id"] for item in data["results"])
        if tool == "check_duplicate_claim":
            return f"疑似重复报销 {len(data['matches'])} 条" if data["matches"] else "未发现重复报销"
        return json.dumps(data, ensure_ascii=False)[:120]
