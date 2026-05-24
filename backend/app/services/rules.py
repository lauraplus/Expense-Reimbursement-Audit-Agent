from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..config import settings


@dataclass
class RuleIssue:
    issue: str
    description: str
    policy_id: str | None = None
    severity: str = "medium"
    action: str = "reject"


@dataclass
class RuleContext:
    expense_id: str
    category: str
    amount_claimed: float
    city: str | None
    team_id: str | None
    form_data: dict[str, Any]
    ocr: dict[str, Any]
    employee: dict[str, Any] = field(default_factory=dict)
    team: dict[str, Any] = field(default_factory=dict)
    budget: dict[str, Any] = field(default_factory=dict)
    manager_approvals: list[dict[str, Any]] = field(default_factory=list)
    vp_approvals: list[dict[str, Any]] = field(default_factory=list)


class RuleEngine:
    def evaluate(self, ctx: RuleContext) -> tuple[list[RuleIssue], list[RuleIssue]]:
        blockers: list[RuleIssue] = []
        review: list[RuleIssue] = []
        if ctx.amount_claimed > settings.high_amount_review_threshold:
            review.append(
                RuleIssue(
                    issue="high_amount_requires_human_review",
                    description=f"单笔金额 {ctx.amount_claimed:.2f} 元超过 {settings.high_amount_review_threshold:.0f} 元，按策略强制转人工复核。",
                    severity="high",
                    action="review",
                )
            )
        if ctx.ocr.get("error_code"):
            review.append(RuleIssue("ocr_failed", ctx.ocr["error_message"], severity="high", action="review"))
            return blockers, review
        if ctx.ocr.get("low_confidence"):
            review.append(
                RuleIssue(
                    issue="ocr_low_confidence",
                    description=f"OCR 置信度 {ctx.ocr.get('confidence', 0):.2f} 低于阈值 {settings.ocr_min_confidence:.2f}。",
                    severity="high",
                    action="review",
                )
            )
        if ctx.category == "traffic_overtime_taxi":
            self._traffic(ctx, blockers, review)
        elif ctx.category == "travel_hotel":
            self._hotel(ctx, blockers, review)
        elif ctx.category == "team_building":
            self._team_building(ctx, blockers, review)
        return blockers, review

    def _traffic(self, ctx: RuleContext, blockers: list[RuleIssue], review: list[RuleIssue]) -> None:
        normalized = ctx.ocr.get("normalized", {})
        actual_amount = normalized.get("actual_amount")
        if actual_amount is None:
            review.append(RuleIssue("traffic_amount_missing", "OCR 未识别到打车实际金额。", "TRAFFIC-2.5", "high", "review"))
        elif abs(float(actual_amount) - ctx.amount_claimed) > 0.01:
            blockers.append(
                RuleIssue(
                    "traffic_amount_mismatch",
                    f"申报金额 {ctx.amount_claimed:.2f} 元与打车凭证金额 {float(actual_amount):.2f} 元不一致。",
                    "TRAFFIC-2.5",
                    "high",
                )
            )
        ride_time = normalized.get("ride_time")
        if not ride_time:
            review.append(RuleIssue("traffic_time_missing", "OCR 未识别到打车时间。", "TRAFFIC-2.1", "medium", "review"))
        elif ride_time < "21:00":
            blockers.append(RuleIssue("traffic_time_too_early", f"打车时间 {ride_time} 早于加班打车可报销时间 21:00。", "TRAFFIC-2.1", "medium"))
        ride_type = normalized.get("ride_type")
        if not ride_type:
            review.append(RuleIssue("traffic_ride_type_missing", "OCR 未识别到车型。", "TRAFFIC-2.3", "medium", "review"))
        elif ride_type not in {"快车", "拼车", "出租车"} and not ctx.manager_approvals:
            blockers.append(RuleIssue("premium_ride_without_manager_approval", f"车型为{ride_type}，但未查询到部门主管审批。", "TRAFFIC-2.3", "high"))

    def _hotel(self, ctx: RuleContext, blockers: list[RuleIssue], review: list[RuleIssue]) -> None:
        normalized = ctx.ocr.get("normalized", {})
        total_amount = normalized.get("total_amount")
        if total_amount is None:
            review.append(RuleIssue("hotel_total_missing", "OCR 未识别到酒店账单总额。", "HOTEL-6.5", "high", "review"))
        elif abs(float(total_amount) - ctx.amount_claimed) > 0.01:
            blockers.append(
                RuleIssue("hotel_amount_mismatch", f"申报金额 {ctx.amount_claimed:.2f} 元与酒店账单总额 {float(total_amount):.2f} 元不一致。", "HOTEL-6.5", "high")
            )
        room_rate = normalized.get("room_rate")
        level = ctx.employee.get("level")
        city = ctx.city or ctx.form_data.get("hotel_city")
        limit = self._hotel_limit(city=city, level=level)
        if room_rate is None:
            review.append(RuleIssue("hotel_room_rate_missing", "OCR 未识别到单晚房费。", "HOTEL-6.2", "medium", "review"))
            return
        if limit is None:
            review.append(RuleIssue("hotel_policy_missing", f"未找到城市 {city}、职级 {level} 对应住宿标准。", "HOTEL-6.2", "medium", "review"))
            return
        over_rate = (float(room_rate) - limit) / limit
        if float(room_rate) > limit:
            if over_rate > 0.2:
                if not ctx.vp_approvals:
                    review.append(RuleIssue("hotel_over_limit_more_than_20_percent", f"房费 {float(room_rate):.2f} 元/晚超过标准 {limit:.2f} 元/晚 20% 以上，需 VP 审批并转人工复核。", "HOTEL-6.4", "high", "review"))
            elif not ctx.manager_approvals:
                blockers.append(RuleIssue("hotel_over_limit_without_manager_approval", f"房费 {float(room_rate):.2f} 元/晚超过 {city}{level} 标准 {limit:.2f} 元/晚，未查询到主管审批。", "HOTEL-6.4", "high"))

    def _team_building(self, ctx: RuleContext, blockers: list[RuleIssue], review: list[RuleIssue]) -> None:
        normalized = ctx.ocr.get("normalized", {})
        activity_city = ctx.form_data.get("activity_city") or ctx.city
        base_city = ctx.team.get("base_city")
        if not base_city:
            review.append(RuleIssue("team_base_missing", "未查询到团队 base 地。", "TEAM-3.4", "high", "review"))
        elif activity_city and activity_city != base_city and not ctx.vp_approvals:
            blockers.append(RuleIssue("cross_city_team_building_without_vp_approval", f"活动地点 {activity_city} 与团队 base 地 {base_city} 不一致，未查询到 VP 审批。", "TEAM-3.2.1", "high"))
        participants = ctx.form_data.get("participants_count") or normalized.get("participants_count")
        if not participants:
            review.append(RuleIssue("participants_missing", "未获得团建参与人数，无法计算人均金额。", "TEAM-3.4", "medium", "review"))
        else:
            per_capita = ctx.amount_claimed / float(participants)
            if per_capita > 800:
                review.append(RuleIssue("team_building_per_capita_over_limit", f"人均金额 {per_capita:.2f} 元超过 800 元标准。", "TEAM-3.1", "medium", "review"))
        remaining = ctx.budget.get("remaining_amount")
        if remaining is None:
            review.append(RuleIssue("budget_missing", "未查询到团队团建预算。", "TEAM-3.1", "high", "review"))
        elif float(remaining) < ctx.amount_claimed:
            review.append(RuleIssue("budget_insufficient", f"预算剩余 {float(remaining):.2f} 元，低于申报金额 {ctx.amount_claimed:.2f} 元。", "TEAM-3.1", "high", "review"))

    def _hotel_limit(self, *, city: str | None, level: str | None) -> float | None:
        if not city or not level:
            return None
        if city == "杭州":
            try:
                numeric_level = int(level.replace("P", ""))
            except ValueError:
                return None
            if numeric_level <= 5:
                return 500
            if 6 <= numeric_level <= 7:
                return 650
            return 800
        return 500
