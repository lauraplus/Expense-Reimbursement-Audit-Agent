export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

export type ExpenseCategory = "traffic_overtime_taxi" | "travel_hotel" | "team_building";

export type ReviewResult = {
  review_id: number;
  expense_id: string;
  decision: "suggested_pass" | "suggested_reject" | "human_review_required" | "agent_failed";
  risk_level: "low" | "medium" | "high";
  human_review_required: boolean;
  reasons: Array<{ issue: string; description: string; policy_id?: string | null; severity: string; action: string }>;
  policy_citations: Array<{ policy_id: string; title: string; text: string; version: string }>;
  tool_evidence: Array<{ tool: string; server: string; status: string; result_summary: string; latency_ms: number }>;
  audit_summary: string;
  status: string;
  model_version: string;
  policy_version: string;
  created_at: string;
};

export type Expense = {
  expense_id: string;
  employee_id: string;
  category: ExpenseCategory;
  amount_claimed: number;
  currency: string;
  expense_date: string;
  city?: string | null;
  team_id?: string | null;
  title: string;
  status: string;
  form_data: Record<string, unknown>;
  attachments: Array<{ attachment_id: number; fixture_id?: string | null; original_filename?: string | null }>;
  latest_review?: ReviewResult | null;
};

export type MockOptions = {
  employees: Array<{ employee_id: string; employee_name: string; department_name: string; team_id: string; level: string }>;
  teams: Array<{ team_id: string; team_name: string; base_city: string; team_size: number }>;
  receipt_fixtures: Array<{ fixture_id: string; category: ExpenseCategory; label: string }>;
};

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

export async function createExpense(payload: Record<string, unknown>, file?: File | null): Promise<Expense> {
  const form = new FormData();
  form.append("payload", JSON.stringify(payload));
  if (file) {
    form.append("file", file);
  }
  const response = await fetch(`${API_BASE}/api/expenses`, { method: "POST", body: form });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

export async function runAgentReview(expenseId: string): Promise<ReviewResult> {
  const response = await fetch(`${API_BASE}/api/expenses/${expenseId}/agent-review`, { method: "POST" });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

export async function sendFeedback(reviewId: number, finalDecision: "finance_confirmed" | "finance_overridden", reason = "") {
  const response = await fetch(`${API_BASE}/api/reviews/${reviewId}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ final_decision: finalDecision, operator_name: "财务审核员", correction_reason: reason })
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}
