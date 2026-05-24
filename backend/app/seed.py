from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from .config import MOCK_DIR
from .database import Base, engine
from .models import (
    ApprovalRecord,
    Attachment,
    Budget,
    Employee,
    Expense,
    HistoricalClaim,
    PolicyChunk,
    PolicyRule,
    Team,
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def seed_if_empty(db: Session) -> None:
    if db.query(Employee).first():
        return
    seed_master_data(db)
    seed_policies(db)
    seed_demo_expenses(db)
    db.commit()


def seed_master_data(db: Session) -> None:
    for item in load_json(MOCK_DIR / "master-data" / "employees.json"):
        db.merge(Employee(**item))
    for item in load_json(MOCK_DIR / "master-data" / "teams.json"):
        db.merge(Team(**item))
    for item in load_json(MOCK_DIR / "master-data" / "budgets.json"):
        db.merge(Budget(**item))
    for item in load_json(MOCK_DIR / "master-data" / "approvals.json"):
        db.merge(ApprovalRecord(**item))
    for item in load_json(MOCK_DIR / "master-data" / "historical_claims.json"):
        db.merge(HistoricalClaim(**item))


def seed_policies(db: Session) -> None:
    for item in load_json(MOCK_DIR / "policies" / "policy_chunks.json"):
        db.merge(PolicyChunk(**item))
    for item in load_json(MOCK_DIR / "policies" / "policy_rules.json"):
        rule_id = item["rule_id"]
        db.merge(
            PolicyRule(
                rule_id=rule_id,
                category=item["category"],
                policy_id=item["policy_id"],
                payload_json=json.dumps(item, ensure_ascii=False),
            )
        )


def seed_demo_expenses(db: Session) -> None:
    for file_name in ("traffic.json", "travel_hotel.json", "team_building.json"):
        for item in load_json(MOCK_DIR / "expenses" / file_name):
            expense = Expense(
                expense_id=item["expense_id"],
                employee_id=item["employee_id"],
                category=item["category"],
                amount_claimed=item["amount_claimed"],
                currency=item["currency"],
                expense_date=item["expense_date"],
                city=item.get("city"),
                team_id=item.get("team_id"),
                title=item.get("title") or item.get("form_data", {}).get("title", ""),
                form_data_json=json.dumps(item.get("form_data", {}), ensure_ascii=False),
            )
            db.merge(expense)
            db.flush()
            existing = db.query(Attachment).filter(Attachment.expense_id == item["expense_id"]).first()
            if not existing:
                db.add(
                    Attachment(
                        expense_id=item["expense_id"],
                        attachment_type="receipt_image",
                        fixture_id=item.get("attachment_fixture_id"),
                    )
                )
