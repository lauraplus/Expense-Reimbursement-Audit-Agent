from backend.app.services.rules import RuleContext, RuleEngine


def test_traffic_premium_without_approval_rejects():
    ctx = RuleContext(
        expense_id="EXP-1",
        category="traffic_overtime_taxi",
        amount_claimed=68,
        city="北京",
        team_id="T-RD-A",
        form_data={},
        ocr={"low_confidence": False, "normalized": {"actual_amount": 68, "ride_time": "22:30", "ride_type": "专车"}},
    )
    blockers, review = RuleEngine().evaluate(ctx)
    assert not review
    assert any(issue.issue == "premium_ride_without_manager_approval" for issue in blockers)


def test_hotel_amount_mismatch_rejects():
    ctx = RuleContext(
        expense_id="EXP-2",
        category="travel_hotel",
        amount_claimed=500,
        city="杭州",
        team_id="T-SALES-HZ",
        form_data={"hotel_city": "杭州"},
        ocr={"low_confidence": False, "normalized": {"total_amount": 550, "room_rate": 550}},
        employee={"level": "P5"},
    )
    blockers, _ = RuleEngine().evaluate(ctx)
    assert any(issue.issue == "hotel_amount_mismatch" for issue in blockers)


def test_team_building_cross_city_requires_vp():
    ctx = RuleContext(
        expense_id="EXP-3",
        category="team_building",
        amount_claimed=4500,
        city="三亚",
        team_id="T-PROD-A",
        form_data={"activity_city": "三亚", "participants_count": 12},
        ocr={"low_confidence": False, "normalized": {"total_amount": 4500, "participants_count": 12}},
        team={"base_city": "北京"},
        budget={"remaining_amount": 18000},
    )
    blockers, review = RuleEngine().evaluate(ctx)
    assert not review
    assert any(issue.issue == "cross_city_team_building_without_vp_approval" for issue in blockers)
