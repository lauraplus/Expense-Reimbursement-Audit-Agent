from __future__ import annotations

import json
import shutil
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .config import MOCK_DIR, UPLOAD_DIR
from .database import SessionLocal, get_db
from .models import Attachment, Expense, Feedback, ReviewRun
from .schemas import ExpenseCreate, ExpenseOut, FeedbackCreate, FeedbackOut, ReviewResult
from .seed import init_db, seed_if_empty
from .services.agent import ControlledExpenseAgent


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    with SessionLocal() as db:
        seed_if_empty(db)
    yield


app = FastAPI(title="Expense Review Agent MVP", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/mock/options")
def mock_options(db: Session = Depends(get_db)) -> dict[str, object]:
    from .models import Employee, Team

    receipts = json.loads((MOCK_DIR / "receipts" / "ocr_results.json").read_text(encoding="utf-8"))
    return {
        "employees": [
            {
                "employee_id": e.employee_id,
                "employee_name": e.employee_name,
                "department_name": e.department_name,
                "team_id": e.team_id,
                "level": e.level,
            }
            for e in db.query(Employee).all()
        ],
        "teams": [
            {"team_id": t.team_id, "team_name": t.team_name, "base_city": t.base_city, "team_size": t.team_size}
            for t in db.query(Team).all()
        ],
        "receipt_fixtures": [
            {"fixture_id": fixture_id, "category": item["category"], "label": f"{item['category']} / {fixture_id}"}
            for fixture_id, item in receipts.items()
        ],
    }


@app.get("/api/expenses")
def list_expenses(db: Session = Depends(get_db)) -> list[ExpenseOut]:
    expenses = db.query(Expense).order_by(Expense.created_at.desc()).limit(80).all()
    return [expense_to_out(expense) for expense in expenses]


@app.post("/api/expenses", response_model=ExpenseOut)
async def create_expense(
    payload: str = Form(...),
    file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
) -> ExpenseOut:
    try:
        data = ExpenseCreate.model_validate_json(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {exc}") from exc
    expense_id = f"EXP-{uuid.uuid4().hex[:10].upper()}"
    expense = Expense(
        expense_id=expense_id,
        employee_id=data.employee_id,
        category=data.category,
        amount_claimed=data.amount_claimed,
        currency=data.currency,
        expense_date=data.expense_date,
        city=data.city,
        team_id=data.team_id,
        title=data.title or data.form_data.get("title", ""),
        form_data_json=json.dumps(data.form_data, ensure_ascii=False),
        status="submitted",
    )
    db.add(expense)
    db.flush()
    file_path = None
    original_filename = None
    if file and file.filename:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        suffix = Path(file.filename).suffix or ".bin"
        target = UPLOAD_DIR / f"{expense_id}{suffix}"
        with target.open("wb") as out:
            shutil.copyfileobj(file.file, out)
        file_path = str(target)
        original_filename = file.filename
    db.add(
        Attachment(
            expense_id=expense_id,
            attachment_type="receipt_image",
            file_path=file_path,
            fixture_id=data.attachment_fixture_id if not file_path else None,
            original_filename=original_filename,
        )
    )
    db.commit()
    db.refresh(expense)
    return expense_to_out(expense)


@app.get("/api/expenses/{expense_id}", response_model=ExpenseOut)
def get_expense(expense_id: str, db: Session = Depends(get_db)) -> ExpenseOut:
    expense = db.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense_to_out(expense)


@app.post("/api/expenses/{expense_id}/agent-review", response_model=ReviewResult)
def agent_review(expense_id: str, db: Session = Depends(get_db)) -> ReviewResult:
    expense = db.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    review = ControlledExpenseAgent(db).review(expense_id)
    return review_to_out(review)


@app.post("/api/reviews/{review_id}/feedback", response_model=FeedbackOut)
def create_feedback(review_id: int, payload: FeedbackCreate, db: Session = Depends(get_db)) -> FeedbackOut:
    review = db.get(ReviewRun, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    feedback = Feedback(
        review_id=review_id,
        final_decision=payload.final_decision,
        operator_name=payload.operator_name,
        correction_reason=payload.correction_reason,
    )
    review.expense.status = payload.final_decision
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return FeedbackOut(
        feedback_id=feedback.feedback_id,
        review_id=feedback.review_id,
        final_decision=feedback.final_decision,
        operator_name=feedback.operator_name,
        correction_reason=feedback.correction_reason,
        created_at=feedback.created_at.isoformat(),
    )


def expense_to_out(expense: Expense) -> ExpenseOut:
    latest = sorted(expense.review_runs, key=lambda r: r.created_at, reverse=True)[0] if expense.review_runs else None
    return ExpenseOut(
        expense_id=expense.expense_id,
        employee_id=expense.employee_id,
        category=expense.category,
        amount_claimed=expense.amount_claimed,
        currency=expense.currency,
        expense_date=expense.expense_date,
        city=expense.city,
        team_id=expense.team_id,
        title=expense.title,
        status=expense.status,
        form_data=json.loads(expense.form_data_json or "{}"),
        attachments=[
            {
                "attachment_id": a.attachment_id,
                "attachment_type": a.attachment_type,
                "file_path": a.file_path,
                "fixture_id": a.fixture_id,
                "original_filename": a.original_filename,
            }
            for a in expense.attachments
        ],
        latest_review=review_to_out(latest) if latest else None,
    )


def review_to_out(review: ReviewRun) -> ReviewResult:
    return ReviewResult(
        review_id=review.review_id,
        expense_id=review.expense_id,
        decision=review.decision,
        risk_level=review.risk_level,
        human_review_required=review.human_review_required,
        reasons=json.loads(review.reasons_json or "[]"),
        policy_citations=json.loads(review.policy_citations_json or "[]"),
        tool_evidence=json.loads(review.tool_evidence_json or "[]"),
        audit_summary=review.audit_summary,
        status=review.status,
        model_version=review.model_version,
        policy_version=review.policy_version,
        created_at=review.created_at.isoformat(),
    )
