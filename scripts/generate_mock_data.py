from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MOCK = ROOT / "mock"


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_svg(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    y = 70
    text_nodes = []
    for line in lines:
        text_nodes.append(f'<text x="36" y="{y}" font-size="24" fill="#253047">{line}</text>')
        y += 42
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="560" viewBox="0 0 900 560">
  <rect width="900" height="560" rx="18" fill="#f8fafc"/>
  <rect x="24" y="24" width="852" height="512" rx="14" fill="#ffffff" stroke="#d8dee9" stroke-width="2"/>
  <text x="36" y="48" font-size="28" font-weight="700" fill="#111827">{title}</text>
  {''.join(text_nodes)}
</svg>
'''
    path.write_text(svg, encoding="utf-8")


def policies() -> None:
    chunks = [
        {
            "policy_id": "TRAFFIC-2.1",
            "version": "2026.01",
            "category": "traffic_overtime_taxi",
            "title": "加班打车时间要求",
            "text": "员工因工作需要在 21:00 后离开办公地，可申请加班打车报销。21:00 前产生的通勤费用原则上不予报销，特殊情况需直属主管审批。",
            "effective_from": "2026-01-01",
            "effective_to": None,
        },
        {
            "policy_id": "TRAFFIC-2.3",
            "version": "2026.01",
            "category": "traffic_overtime_taxi",
            "title": "加班打车车型标准",
            "text": "加班打车报销仅限快车、拼车、出租车。专车、商务车等高等级车型需附部门主管审批记录。",
            "effective_from": "2026-01-01",
            "effective_to": None,
        },
        {
            "policy_id": "TRAFFIC-2.5",
            "version": "2026.01",
            "category": "traffic_overtime_taxi",
            "title": "交通票据金额一致性",
            "text": "员工申报金额应与打车凭证实际支付金额一致；金额不一致时，应退回补充说明或转人工复核。",
            "effective_from": "2026-01-01",
            "effective_to": None,
        },
        {
            "policy_id": "HOTEL-6.2",
            "version": "2026.01",
            "category": "travel_hotel",
            "title": "住宿城市与职级标准",
            "text": "杭州、成都、南京、武汉等新一线城市，P5 及以下员工住宿标准上限为 500 元/晚，P6-P7 上限为 650 元/晚，P8 及以上上限为 800 元/晚。",
            "effective_from": "2026-01-01",
            "effective_to": None,
        },
        {
            "policy_id": "HOTEL-6.4",
            "version": "2026.01",
            "category": "travel_hotel",
            "title": "住宿超标审批",
            "text": "因会议、展会、旺季等原因导致住宿超标的，应在报销时附直属主管审批；超标超过 20% 的，还需部门 VP 审批。",
            "effective_from": "2026-01-01",
            "effective_to": None,
        },
        {
            "policy_id": "HOTEL-6.5",
            "version": "2026.01",
            "category": "travel_hotel",
            "title": "住宿账单一致性",
            "text": "住宿报销单填写金额、入住天数和酒店账单应一致。账单解析金额与申报金额不一致时，不得自动通过。",
            "effective_from": "2026-01-01",
            "effective_to": None,
        },
        {
            "policy_id": "TEAM-3.1",
            "version": "2026.01",
            "category": "team_building",
            "title": "团建预算与人均标准",
            "text": "团队团建报销应在年度团建预算余额内，单次活动人均金额原则上不超过 800 元。",
            "effective_from": "2026-01-01",
            "effective_to": None,
        },
        {
            "policy_id": "TEAM-3.2.1",
            "version": "2026.01",
            "category": "team_building",
            "title": "跨城团建审批",
            "text": "活动地点与团队 base 地不一致时，属于跨城团建。跨城团建需提前获得 VP 级审批，并在报销时附审批记录。",
            "effective_from": "2026-01-01",
            "effective_to": None,
        },
        {
            "policy_id": "TEAM-3.4",
            "version": "2026.01",
            "category": "team_building",
            "title": "团建参与人数",
            "text": "团建参与人数应与团队实际人数或活动签到记录匹配。参与人数异常时，应转人工复核。",
            "effective_from": "2026-01-01",
            "effective_to": None,
        },
    ]
    rules = [
        {"rule_id": "R-TRAFFIC-TIME", "category": "traffic_overtime_taxi", "policy_id": "TRAFFIC-2.1", "field": "ride_time", "operator": "after_or_equal", "value": "21:00", "severity": "medium"},
        {"rule_id": "R-TRAFFIC-RIDE-TYPE", "category": "traffic_overtime_taxi", "policy_id": "TRAFFIC-2.3", "field": "ride_type", "allowed_values": ["快车", "拼车", "出租车"], "exception_approval": "department_manager", "severity": "high"},
        {"rule_id": "R-TRAFFIC-AMOUNT", "category": "traffic_overtime_taxi", "policy_id": "TRAFFIC-2.5", "field": "actual_amount", "operator": "equals_claimed", "severity": "high"},
        {"rule_id": "R-HOTEL-P5-NEW-TIER", "category": "travel_hotel", "policy_id": "HOTEL-6.2", "city": "杭州", "employee_level_max": "P5", "limit_amount": 500, "unit": "CNY/night", "severity": "high"},
        {"rule_id": "R-HOTEL-P6-NEW-TIER", "category": "travel_hotel", "policy_id": "HOTEL-6.2", "city": "杭州", "employee_level_min": "P6", "employee_level_max": "P7", "limit_amount": 650, "unit": "CNY/night", "severity": "medium"},
        {"rule_id": "R-HOTEL-AMOUNT", "category": "travel_hotel", "policy_id": "HOTEL-6.5", "field": "total_amount", "operator": "equals_claimed", "severity": "high"},
        {"rule_id": "R-TEAM-PER-CAPITA", "category": "team_building", "policy_id": "TEAM-3.1", "field": "per_capita_amount", "operator": "less_or_equal", "value": 800, "severity": "medium"},
        {"rule_id": "R-TEAM-CROSS-CITY", "category": "team_building", "policy_id": "TEAM-3.2.1", "field": "activity_city", "operator": "same_as_base_city", "exception_approval": "vp", "severity": "high"},
        {"rule_id": "R-TEAM-BUDGET", "category": "team_building", "policy_id": "TEAM-3.1", "field": "budget_remaining", "operator": "greater_or_equal_claimed", "severity": "high"},
    ]
    skills = {
        "traffic_overtime_taxi": [
            "解析打车截图，提取实际金额、车型、出发地、目的地和打车时间。",
            "比对申报金额与截图金额。",
            "检查打车时间是否满足加班打车条件。",
            "检查车型是否需要主管审批。",
        ],
        "travel_hotel": [
            "解析酒店账单，提取酒店名称、单晚房费、入住天数和总额。",
            "比对申报金额与账单总额。",
            "查询员工职级并匹配城市住宿标准。",
            "如超标，检查主管或 VP 审批记录。",
        ],
        "team_building": [
            "查询团队 base 地和团队人数。",
            "判断活动地点是否跨城。",
            "查询预算余额与已使用金额。",
            "计算人均金额并检查是否超过标准。",
            "跨城或超标场景检查 VP 审批。",
        ],
    }
    write_json(MOCK / "policies" / "policy_chunks.json", chunks)
    write_json(MOCK / "policies" / "policy_rules.json", rules)
    write_json(MOCK / "policies" / "skills.json", skills)


def master_data() -> None:
    employees = [
        {"employee_id": "E1001", "employee_name": "张三", "department_id": "D-PRODUCT", "department_name": "产品部", "team_id": "T-PROD-A", "level": "P6", "cost_center": "CC-PD-001", "manager_id": "E9001", "vp_id": "E9901"},
        {"employee_id": "E1002", "employee_name": "李四", "department_id": "D-RD", "department_name": "研发部", "team_id": "T-RD-A", "level": "P5", "cost_center": "CC-RD-001", "manager_id": "E9002", "vp_id": "E9902"},
        {"employee_id": "E1003", "employee_name": "王五", "department_id": "D-RD", "department_name": "研发部", "team_id": "T-RD-A", "level": "P5", "cost_center": "CC-RD-001", "manager_id": "E9002", "vp_id": "E9902"},
        {"employee_id": "E1004", "employee_name": "赵六", "department_id": "D-SALES", "department_name": "销售部", "team_id": "T-SALES-HZ", "level": "P5", "cost_center": "CC-SL-001", "manager_id": "E9003", "vp_id": "E9903"},
        {"employee_id": "E1005", "employee_name": "钱七", "department_id": "D-SALES", "department_name": "销售部", "team_id": "T-SALES-HZ", "level": "P7", "cost_center": "CC-SL-001", "manager_id": "E9003", "vp_id": "E9903"},
        {"employee_id": "E1006", "employee_name": "孙八", "department_id": "D-HR", "department_name": "人力资源部", "team_id": "T-HR-BJ", "level": "P6", "cost_center": "CC-HR-001", "manager_id": "E9004", "vp_id": "E9904"},
        {"employee_id": "E1007", "employee_name": "周九", "department_id": "D-PRODUCT", "department_name": "产品部", "team_id": "T-PROD-A", "level": "P5", "cost_center": "CC-PD-001", "manager_id": "E9001", "vp_id": "E9901"},
        {"employee_id": "E1008", "employee_name": "吴十", "department_id": "D-FIN", "department_name": "财务部", "team_id": "T-FIN-BJ", "level": "P6", "cost_center": "CC-FN-001", "manager_id": "E9005", "vp_id": "E9905"},
    ]
    teams = [
        {"team_id": "T-PROD-A", "team_name": "产品部 A 组", "department_id": "D-PRODUCT", "base_city": "北京", "base_location": "北京望京", "team_size": 12, "owner_id": "E9001"},
        {"team_id": "T-RD-A", "team_name": "研发部 A 组", "department_id": "D-RD", "base_city": "北京", "base_location": "北京中关村", "team_size": 18, "owner_id": "E9002"},
        {"team_id": "T-SALES-HZ", "team_name": "销售杭州组", "department_id": "D-SALES", "base_city": "杭州", "base_location": "杭州滨江", "team_size": 10, "owner_id": "E9003"},
        {"team_id": "T-HR-BJ", "team_name": "人力北京组", "department_id": "D-HR", "base_city": "北京", "base_location": "北京望京", "team_size": 8, "owner_id": "E9004"},
        {"team_id": "T-FIN-BJ", "team_name": "财务北京组", "department_id": "D-FIN", "base_city": "北京", "base_location": "北京望京", "team_size": 9, "owner_id": "E9005"},
    ]
    budgets = [
        {"budget_id": "B-PROD-A-TEAM-2026", "team_id": "T-PROD-A", "category": "team_building", "period": "2026", "annual_budget": 50000, "used_amount": 32000, "frozen_amount": 0},
        {"budget_id": "B-RD-A-TEAM-2026", "team_id": "T-RD-A", "category": "team_building", "period": "2026", "annual_budget": 72000, "used_amount": 66400, "frozen_amount": 0},
        {"budget_id": "B-SALES-HZ-TEAM-2026", "team_id": "T-SALES-HZ", "category": "team_building", "period": "2026", "annual_budget": 42000, "used_amount": 20000, "frozen_amount": 0},
        {"budget_id": "B-HR-BJ-TEAM-2026", "team_id": "T-HR-BJ", "category": "team_building", "period": "2026", "annual_budget": 32000, "used_amount": 12000, "frozen_amount": 0},
    ]
    approvals = [
        {"approval_id": "APR-001", "expense_id": "EXP-TRAFFIC-006", "employee_id": "E1003", "team_id": "T-RD-A", "approval_type": "department_manager", "approver_id": "E9002", "approved_at": "2026-05-20T20:10:00", "summary": "项目上线当日允许专车回家"},
        {"approval_id": "APR-002", "expense_id": "EXP-HOTEL-006", "employee_id": "E1004", "team_id": "T-SALES-HZ", "approval_type": "department_manager", "approver_id": "E9003", "approved_at": "2026-05-16T09:30:00", "summary": "展会期间酒店价格上涨，允许小幅超标"},
        {"approval_id": "APR-003", "expense_id": "EXP-TEAM-006", "employee_id": "E1001", "team_id": "T-PROD-A", "approval_type": "vp", "approver_id": "E9901", "approved_at": "2026-05-18T11:00:00", "summary": "产品部跨城团建已提前审批"},
        {"approval_id": "APR-004", "expense_id": "EXP-HOTEL-014", "employee_id": "E1005", "team_id": "T-SALES-HZ", "approval_type": "vp", "approver_id": "E9903", "approved_at": "2026-04-22T14:20:00", "summary": "高峰期客户会议酒店超标审批"},
    ]
    historical = [
        {"claim_id": "H-001", "employee_id": "E1003", "category": "traffic_overtime_taxi", "amount": 62, "expense_date": "2026-05-02", "fingerprint": "taxi-E1003-20260502-62"},
        {"claim_id": "H-002", "employee_id": "E1004", "category": "travel_hotel", "amount": 500, "expense_date": "2026-04-12", "fingerprint": "hotel-E1004-hangzhou-20260412"},
        {"claim_id": "H-003", "employee_id": "E1001", "category": "team_building", "amount": 8200, "expense_date": "2026-03-18", "fingerprint": "team-T-PROD-A-20260318"},
    ]
    write_json(MOCK / "master-data" / "employees.json", employees)
    write_json(MOCK / "master-data" / "teams.json", teams)
    write_json(MOCK / "master-data" / "budgets.json", budgets)
    write_json(MOCK / "master-data" / "approvals.json", approvals)
    write_json(MOCK / "master-data" / "historical_claims.json", historical)


def receipts() -> None:
    records: dict[str, dict[str, object]] = {}
    fixtures = [
        ("receipt_taxi_fast_68", "traffic_overtime_taxi", "加班打车凭证", ["出发地：望京SOHO", "目的地：天通苑", "车型：快车", "支付金额：68.00 元", "打车时间：22:30"], {"from_location": "望京SOHO", "to_location": "天通苑", "ride_type": "快车", "actual_amount": 68, "ride_time": "22:30", "confidence": 0.96}),
        ("receipt_taxi_premium_68", "traffic_overtime_taxi", "加班打车凭证", ["出发地：望京SOHO", "目的地：天通苑", "车型：专车", "支付金额：68.00 元", "打车时间：22:30"], {"from_location": "望京SOHO", "to_location": "天通苑", "ride_type": "专车", "actual_amount": 68, "ride_time": "22:30", "confidence": 0.95}),
        ("receipt_taxi_early_52", "traffic_overtime_taxi", "打车凭证", ["出发地：中关村", "目的地：回龙观", "车型：快车", "支付金额：52.00 元", "打车时间：20:15"], {"from_location": "中关村", "to_location": "回龙观", "ride_type": "快车", "actual_amount": 52, "ride_time": "20:15", "confidence": 0.94}),
        ("receipt_taxi_mismatch_88", "traffic_overtime_taxi", "加班打车凭证", ["出发地：望京SOHO", "目的地：通州北苑", "车型：快车", "支付金额：88.00 元", "打车时间：22:05"], {"from_location": "望京SOHO", "to_location": "通州北苑", "ride_type": "快车", "actual_amount": 88, "ride_time": "22:05", "confidence": 0.97}),
        ("receipt_taxi_low_conf", "traffic_overtime_taxi", "模糊打车截图", ["出发地：识别不清", "目的地：识别不清", "车型：快车", "支付金额：64.00 元", "打车时间：22:10"], {"from_location": None, "to_location": None, "ride_type": "快车", "actual_amount": 64, "ride_time": "22:10", "confidence": 0.62}),
        ("receipt_hotel_hz_500", "travel_hotel", "酒店住宿账单", ["酒店：杭州云栖酒店", "房费：500.00 元/晚", "入住：1 晚", "总额：500.00 元"], {"hotel_name": "杭州云栖酒店", "room_rate": 500, "nights": 1, "total_amount": 500, "confidence": 0.96}),
        ("receipt_hotel_hz_550", "travel_hotel", "酒店住宿账单", ["酒店：杭州星河酒店", "房费：550.00 元/晚", "入住：1 晚", "总额：550.00 元"], {"hotel_name": "杭州星河酒店", "room_rate": 550, "nights": 1, "total_amount": 550, "confidence": 0.97}),
        ("receipt_hotel_hz_650", "travel_hotel", "酒店住宿账单", ["酒店：杭州国际酒店", "房费：650.00 元/晚", "入住：1 晚", "总额：650.00 元"], {"hotel_name": "杭州国际酒店", "room_rate": 650, "nights": 1, "total_amount": 650, "confidence": 0.94}),
        ("receipt_hotel_hz_780", "travel_hotel", "酒店住宿账单", ["酒店：杭州会展中心酒店", "房费：780.00 元/晚", "入住：1 晚", "总额：780.00 元"], {"hotel_name": "杭州会展中心酒店", "room_rate": 780, "nights": 1, "total_amount": 780, "confidence": 0.94}),
        ("receipt_hotel_low_conf", "travel_hotel", "模糊酒店账单", ["酒店：识别不清", "房费：? 元/晚", "入住：1 晚", "总额：500.00 元"], {"hotel_name": None, "room_rate": None, "nights": 1, "total_amount": 500, "confidence": 0.58}),
        ("receipt_team_8500", "team_building", "团建消费凭证", ["商户：三亚海岸餐厅", "项目：团队活动餐饮", "人数：12 人", "金额：8500.00 元"], {"merchant": "三亚海岸餐厅", "participants_count": 12, "total_amount": 8500, "confidence": 0.93}),
        ("receipt_team_7200", "team_building", "团建消费凭证", ["商户：北京融合餐厅", "项目：团队聚餐", "人数：12 人", "金额：7200.00 元"], {"merchant": "北京融合餐厅", "participants_count": 12, "total_amount": 7200, "confidence": 0.94}),
        ("receipt_team_10800", "team_building", "团建消费凭证", ["商户：杭州湖滨餐厅", "项目：团队活动", "人数：10 人", "金额：10800.00 元"], {"merchant": "杭州湖滨餐厅", "participants_count": 10, "total_amount": 10800, "confidence": 0.95}),
        ("receipt_team_budget_9000", "team_building", "团建消费凭证", ["商户：北京创意厨房", "项目：团队活动", "人数：18 人", "金额：9000.00 元"], {"merchant": "北京创意厨房", "participants_count": 18, "total_amount": 9000, "confidence": 0.95}),
        ("receipt_team_low_conf", "team_building", "模糊团建凭证", ["商户：识别不清", "项目：团队活动", "人数：? 人", "金额：6000.00 元"], {"merchant": None, "participants_count": None, "total_amount": 6000, "confidence": 0.55}),
    ]
    for fixture_id, category, title, lines, normalized in fixtures:
        write_svg(MOCK / "receipts" / "images" / f"{fixture_id}.svg", title, lines)
        records[fixture_id] = {
            "fixture_id": fixture_id,
            "category": category,
            "image_path": f"mock/receipts/images/{fixture_id}.svg",
            "raw_text": "\n".join(lines),
            "normalized": normalized,
            "provider": "mock_fixture",
        }
    write_json(MOCK / "receipts" / "ocr_results.json", records)


def expense_record(idx: int, category: str, employee_id: str, amount: float, fixture: str, city: str | None, team_id: str | None, form_data: dict[str, object], expected: str, reasons: list[str]) -> dict[str, object]:
    day = date(2026, 5, 1) + timedelta(days=idx % 24)
    return {
        "expense_id": f"EXP-{category.upper().replace('_', '-')}-{idx:03d}",
        "employee_id": employee_id,
        "category": category,
        "amount_claimed": amount,
        "currency": "CNY",
        "expense_date": day.isoformat(),
        "city": city,
        "team_id": team_id,
        "title": form_data.get("title", ""),
        "form_data": form_data,
        "attachment_fixture_id": fixture,
        "expected_decision": expected,
        "expected_reasons": reasons,
    }


def expenses_and_benchmark() -> None:
    traffic = []
    hotel = []
    team = []
    labels = {}
    traffic_patterns = [
        ("E1003", 68, "receipt_taxi_fast_68", "suggested_pass", []),
        ("E1003", 68, "receipt_taxi_premium_68", "suggested_reject", ["专车缺少主管审批"]),
        ("E1002", 52, "receipt_taxi_early_52", "suggested_reject", ["打车时间早于 21:00"]),
        ("E1003", 68, "receipt_taxi_mismatch_88", "suggested_reject", ["申报金额与票据金额不一致"]),
        ("E1002", 64, "receipt_taxi_low_conf", "human_review_required", ["OCR 置信度低"]),
        ("E1003", 68, "receipt_taxi_premium_68", "suggested_pass", ["有主管审批"]),
    ]
    for i in range(1, 21):
        employee, amount, fixture, decision, reasons = traffic_patterns[(i - 1) % len(traffic_patterns)]
        expense_id = "EXP-TRAFFIC-006" if i == 6 else None
        record = expense_record(
            i,
            "traffic_overtime_taxi",
            employee,
            amount,
            fixture,
            "北京",
            "T-RD-A",
            {"title": "加班打车", "ride_reason": "项目上线支持"},
            decision,
            reasons,
        )
        if expense_id:
            record["expense_id"] = expense_id
        traffic.append(record)
        labels[record["expense_id"]] = {"decision": decision, "reasons": reasons, "policy_ids": ["TRAFFIC-2.1", "TRAFFIC-2.3", "TRAFFIC-2.5"]}
    hotel_patterns = [
        ("E1004", 500, "receipt_hotel_hz_500", "杭州", "suggested_pass", []),
        ("E1004", 500, "receipt_hotel_hz_550", "杭州", "suggested_reject", ["申报金额与账单金额不一致", "P5 住宿超标"]),
        ("E1005", 650, "receipt_hotel_hz_650", "杭州", "suggested_pass", []),
        ("E1004", 780, "receipt_hotel_hz_780", "杭州", "human_review_required", ["超标超过 20%"]),
        ("E1004", 500, "receipt_hotel_low_conf", "杭州", "human_review_required", ["OCR 置信度低"]),
        ("E1004", 550, "receipt_hotel_hz_550", "杭州", "suggested_pass", ["小幅超标有主管审批"]),
    ]
    for i in range(1, 21):
        employee, amount, fixture, city, decision, reasons = hotel_patterns[(i - 1) % len(hotel_patterns)]
        expense_id = "EXP-HOTEL-006" if i == 6 else None
        record = expense_record(
            i,
            "travel_hotel",
            employee,
            amount,
            fixture,
            city,
            "T-SALES-HZ",
            {"title": "差旅住宿", "hotel_city": city, "check_in": "2026-05-14", "check_out": "2026-05-15"},
            decision,
            reasons,
        )
        if expense_id:
            record["expense_id"] = expense_id
        hotel.append(record)
        labels[record["expense_id"]] = {"decision": decision, "reasons": reasons, "policy_ids": ["HOTEL-6.2", "HOTEL-6.4", "HOTEL-6.5"]}
    team_patterns = [
        ("E1001", 7200, "receipt_team_7200", "北京", "T-PROD-A", 12, "suggested_pass", []),
        ("E1001", 8500, "receipt_team_8500", "三亚", "T-PROD-A", 12, "suggested_reject", ["跨城团建缺少 VP 审批"]),
        ("E1001", 10800, "receipt_team_10800", "杭州", "T-PROD-A", 12, "human_review_required", ["高金额强制人工复核", "人均超标"]),
        ("E1003", 9000, "receipt_team_budget_9000", "北京", "T-RD-A", 18, "human_review_required", ["预算余额不足"]),
        ("E1001", 6000, "receipt_team_low_conf", "北京", "T-PROD-A", 12, "human_review_required", ["OCR 置信度低"]),
        ("E1001", 8500, "receipt_team_8500", "三亚", "T-PROD-A", 12, "human_review_required", ["跨城团建有 VP 审批但金额超 5000"]),
    ]
    for i in range(1, 21):
        employee, amount, fixture, city, team_id, participants, decision, reasons = team_patterns[(i - 1) % len(team_patterns)]
        expense_id = "EXP-TEAM-006" if i == 6 else None
        record = expense_record(
            i,
            "team_building",
            employee,
            amount,
            fixture,
            city,
            team_id,
            {"title": "团队团建", "activity_city": city, "participants_count": participants, "activity_date": "2026-05-20"},
            decision,
            reasons,
        )
        if expense_id:
            record["expense_id"] = expense_id
        team.append(record)
        labels[record["expense_id"]] = {"decision": decision, "reasons": reasons, "policy_ids": ["TEAM-3.1", "TEAM-3.2.1", "TEAM-3.4"]}
    write_json(MOCK / "expenses" / "traffic.json", traffic)
    write_json(MOCK / "expenses" / "travel_hotel.json", hotel)
    write_json(MOCK / "expenses" / "team_building.json", team)
    write_json(MOCK / "benchmark" / "labels.json", labels)


def main() -> None:
    policies()
    master_data()
    receipts()
    expenses_and_benchmark()
    print(f"Mock data generated under {MOCK}")


if __name__ == "__main__":
    main()
