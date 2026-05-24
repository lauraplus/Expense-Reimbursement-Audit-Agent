"use client";

import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  BadgeCheck,
  Building2,
  CalendarDays,
  Check,
  ChevronRight,
  FileSearch,
  Hotel,
  Loader2,
  MapPin,
  ReceiptText,
  Route,
  Send,
  ShieldCheck,
  Users
} from "lucide-react";
import {
  Expense,
  ExpenseCategory,
  MockOptions,
  ReviewResult,
  apiGet,
  createExpense,
  runAgentReview,
  sendFeedback
} from "../lib/api";

const categoryMeta: Record<ExpenseCategory, { label: string; icon: React.ReactNode; hint: string }> = {
  traffic_overtime_taxi: {
    label: "交通",
    icon: <Route size={18} />,
    hint: "加班打车，核验金额、车型和打车时间"
  },
  travel_hotel: {
    label: "差旅住宿",
    icon: <Hotel size={18} />,
    hint: "核验账单金额、城市住宿标准和审批"
  },
  team_building: {
    label: "团建",
    icon: <Users size={18} />,
    hint: "核验 base 地、跨城审批、预算和人均标准"
  }
};

const decisionCopy: Record<string, { label: string; className: string; icon: React.ReactNode }> = {
  suggested_pass: { label: "建议通过", className: "bg-teal-50 text-teal-800 border-teal-200", icon: <BadgeCheck size={18} /> },
  suggested_reject: { label: "建议驳回", className: "bg-rose-50 text-rose-800 border-rose-200", icon: <AlertTriangle size={18} /> },
  human_review_required: { label: "需人工复核", className: "bg-amber-50 text-amber-900 border-amber-200", icon: <FileSearch size={18} /> },
  agent_failed: { label: "初审失败", className: "bg-slate-100 text-slate-700 border-slate-300", icon: <AlertTriangle size={18} /> }
};

export default function Page() {
  const [options, setOptions] = useState<MockOptions | null>(null);
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [category, setCategory] = useState<ExpenseCategory>("traffic_overtime_taxi");
  const [employeeId, setEmployeeId] = useState("E1003");
  const [teamId, setTeamId] = useState("T-RD-A");
  const [amount, setAmount] = useState("68");
  const [city, setCity] = useState("北京");
  const [expenseDate, setExpenseDate] = useState("2026-05-24");
  const [fixtureId, setFixtureId] = useState("receipt_taxi_fast_68");
  const [file, setFile] = useState<File | null>(null);
  const [participants, setParticipants] = useState("12");
  const [hotelCity, setHotelCity] = useState("杭州");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [activeExpense, setActiveExpense] = useState<Expense | null>(null);
  const [activeReview, setActiveReview] = useState<ReviewResult | null>(null);
  const [feedbackReason, setFeedbackReason] = useState("");

  useEffect(() => {
    Promise.all([apiGet<MockOptions>("/api/mock/options"), apiGet<Expense[]>("/api/expenses")])
      .then(([mockOptions, expenseList]) => {
        setOptions(mockOptions);
        setExpenses(expenseList);
      })
      .catch((error) => setMessage(error.message));
  }, []);

  const fixtureOptions = useMemo(() => {
    return options?.receipt_fixtures.filter((item) => item.category === category) ?? [];
  }, [options, category]);

  useEffect(() => {
    const first = fixtureOptions[0]?.fixture_id;
    if (first && !fixtureOptions.some((item) => item.fixture_id === fixtureId)) {
      setFixtureId(first);
    }
  }, [category, fixtureOptions, fixtureId]);

  function applyCategory(next: ExpenseCategory) {
    setCategory(next);
    if (next === "traffic_overtime_taxi") {
      setEmployeeId("E1003");
      setTeamId("T-RD-A");
      setAmount("68");
      setCity("北京");
    }
    if (next === "travel_hotel") {
      setEmployeeId("E1004");
      setTeamId("T-SALES-HZ");
      setAmount("500");
      setCity("杭州");
      setHotelCity("杭州");
    }
    if (next === "team_building") {
      setEmployeeId("E1001");
      setTeamId("T-PROD-A");
      setAmount("8500");
      setCity("三亚");
      setParticipants("12");
    }
  }

  async function submit() {
    setBusy(true);
    setMessage("");
    setActiveReview(null);
    try {
      const formData = buildFormData();
      const expense = await createExpense(
        {
          employee_id: employeeId,
          category,
          amount_claimed: Number(amount),
          currency: "CNY",
          expense_date: expenseDate,
          city: category === "travel_hotel" ? hotelCity : city,
          team_id: teamId,
          title: categoryMeta[category].label,
          form_data: formData,
          attachment_fixture_id: file ? null : fixtureId
        },
        file
      );
      setActiveExpense(expense);
      const review = await runAgentReview(expense.expense_id);
      setActiveReview(review);
      const latest = await apiGet<Expense>(`/api/expenses/${expense.expense_id}`);
      setActiveExpense(latest);
      const list = await apiGet<Expense[]>("/api/expenses");
      setExpenses(list);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "提交失败");
    } finally {
      setBusy(false);
    }
  }

  function buildFormData() {
    if (category === "traffic_overtime_taxi") {
      return { title: "加班打车", ride_reason: "项目上线支持" };
    }
    if (category === "travel_hotel") {
      return { title: "差旅住宿", hotel_city: hotelCity, check_in: "2026-05-14", check_out: "2026-05-15" };
    }
    return { title: "团队团建", activity_city: city, participants_count: Number(participants), activity_date: expenseDate };
  }

  async function handleFeedback(finalDecision: "finance_confirmed" | "finance_overridden") {
    if (!activeReview) return;
    setBusy(true);
    try {
      await sendFeedback(activeReview.review_id, finalDecision, feedbackReason);
      const latest = activeExpense ? await apiGet<Expense>(`/api/expenses/${activeExpense.expense_id}`) : null;
      setActiveExpense(latest);
      const list = await apiGet<Expense[]>("/api/expenses");
      setExpenses(list);
      setMessage(finalDecision === "finance_confirmed" ? "财务已确认 Agent 初审结果。" : "财务修正已留存到反馈库。");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "反馈提交失败");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-7xl flex-col gap-5 px-5 py-5 lg:px-8">
      <header className="flex flex-col justify-between gap-4 border-b border-line pb-4 md:flex-row md:items-center">
        <div>
          <p className="text-sm font-semibold text-teal">Expense Review Agent MVP</p>
          <h1 className="mt-1 text-2xl font-bold text-ink md:text-3xl">报销智能初审工作台</h1>
        </div>
        <div className="grid grid-cols-3 gap-2 text-sm">
          <Metric label="Mock 单据" value={String(expenses.length)} />
          <Metric label="MCP 工具" value="6" />
          <Metric label="状态闭环" value="已接入" />
        </div>
      </header>

      <section className="grid gap-5 lg:grid-cols-[minmax(0,1.05fr)_minmax(360px,0.95fr)]">
        <div className="rounded-lg border border-line bg-panel p-4 shadow-soft">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-bold text-ink">员工提交</h2>
              <p className="text-sm text-muted">提交后自动触发 Agent 初审，结果进入财务确认流。</p>
            </div>
            <ShieldCheck className="text-teal" size={24} />
          </div>

          <div className="mt-4 grid gap-2 sm:grid-cols-3">
            {(Object.keys(categoryMeta) as ExpenseCategory[]).map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => applyCategory(item)}
                className={`focus-ring flex min-h-20 flex-col justify-between rounded-lg border p-3 text-left transition ${
                  category === item ? "border-teal bg-teal-50 text-teal-900" : "border-line bg-white hover:border-teal/50"
                }`}
              >
                <span className="flex items-center gap-2 font-semibold">
                  {categoryMeta[item].icon}
                  {categoryMeta[item].label}
                </span>
                <span className="text-xs leading-5 text-muted">{categoryMeta[item].hint}</span>
              </button>
            ))}
          </div>

          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <Field label="报销人" icon={<Building2 size={16} />}>
              <select className="input" value={employeeId} onChange={(event) => setEmployeeId(event.target.value)}>
                {options?.employees.map((employee) => (
                  <option key={employee.employee_id} value={employee.employee_id}>
                    {employee.employee_name} / {employee.department_name} / {employee.level}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="团队" icon={<Users size={16} />}>
              <select className="input" value={teamId} onChange={(event) => setTeamId(event.target.value)}>
                {options?.teams.map((team) => (
                  <option key={team.team_id} value={team.team_id}>
                    {team.team_name} / {team.base_city} / {team.team_size}人
                  </option>
                ))}
              </select>
            </Field>
            <Field label="申报金额" icon={<ReceiptText size={16} />}>
              <input className="input" value={amount} onChange={(event) => setAmount(event.target.value)} inputMode="decimal" />
            </Field>
            <Field label="发生日期" icon={<CalendarDays size={16} />}>
              <input className="input" type="date" value={expenseDate} onChange={(event) => setExpenseDate(event.target.value)} />
            </Field>
            {category !== "travel_hotel" ? (
              <Field label={category === "team_building" ? "活动城市" : "发生城市"} icon={<MapPin size={16} />}>
                <input className="input" value={city} onChange={(event) => setCity(event.target.value)} />
              </Field>
            ) : (
              <Field label="出差城市" icon={<MapPin size={16} />}>
                <input className="input" value={hotelCity} onChange={(event) => setHotelCity(event.target.value)} />
              </Field>
            )}
            {category === "team_building" && (
              <Field label="参与人数" icon={<Users size={16} />}>
                <input className="input" value={participants} onChange={(event) => setParticipants(event.target.value)} inputMode="numeric" />
              </Field>
            )}
            <Field label="演示票据样例" icon={<ReceiptText size={16} />}>
              <select className="input" value={fixtureId} onChange={(event) => setFixtureId(event.target.value)} disabled={Boolean(file)}>
                {fixtureOptions.map((fixture) => (
                  <option key={fixture.fixture_id} value={fixture.fixture_id}>
                    {fixture.fixture_id}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="上传真实票据" icon={<FileSearch size={16} />}>
              <input className="file-input" type="file" accept="image/*,.pdf" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
            </Field>
          </div>

          <div className="mt-5 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={submit}
              disabled={busy || !options}
              className="focus-ring inline-flex min-h-11 items-center gap-2 rounded-lg bg-ink px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
            >
              {busy ? <Loader2 className="animate-spin" size={18} /> : <Send size={18} />}
              提交并初审
            </button>
            <p className="text-sm text-muted">真实上传会调用 OCR 适配器；不上传时使用留存的 mock OCR 结果。</p>
          </div>
          {message && <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">{message}</div>}
        </div>

        <ReviewPanel review={activeReview ?? activeExpense?.latest_review ?? null} busy={busy} />
      </section>

      {activeReview && (
        <section className="rounded-lg border border-line bg-panel p-4 shadow-soft">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="text-lg font-bold text-ink">财务确认</h2>
              <p className="text-sm text-muted">确认或修正都会写入反馈表，保留最终人工责任边界。</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button className="secondary-button" type="button" onClick={() => handleFeedback("finance_confirmed")} disabled={busy}>
                <Check size={17} />
                确认结果
              </button>
              <button className="danger-button" type="button" onClick={() => handleFeedback("finance_overridden")} disabled={busy}>
                <AlertTriangle size={17} />
                修正结果
              </button>
            </div>
          </div>
          <textarea
            className="mt-3 min-h-20 w-full rounded-lg border border-line px-3 py-2 text-sm focus:border-teal focus:outline-none"
            placeholder="修正原因，例如：员工有线下 VP 特批，当前 mock 审批库未覆盖。"
            value={feedbackReason}
            onChange={(event) => setFeedbackReason(event.target.value)}
          />
        </section>
      )}

      <section className="rounded-lg border border-line bg-panel shadow-soft">
        <div className="flex items-center justify-between border-b border-line px-4 py-3">
          <h2 className="text-lg font-bold text-ink">近期单据</h2>
          <span className="text-sm text-muted">SQLite seeded + 本次提交</span>
        </div>
        <div className="max-h-80 overflow-auto">
          <table className="w-full min-w-[760px] border-collapse text-sm">
            <thead className="sticky top-0 bg-slate-50 text-left text-xs uppercase tracking-wide text-muted">
              <tr>
                <th className="px-4 py-3">单号</th>
                <th className="px-4 py-3">类目</th>
                <th className="px-4 py-3">员工</th>
                <th className="px-4 py-3">金额</th>
                <th className="px-4 py-3">状态</th>
                <th className="px-4 py-3">操作</th>
              </tr>
            </thead>
            <tbody>
              {expenses.slice(0, 30).map((expense) => (
                <tr key={expense.expense_id} className="border-t border-line">
                  <td className="px-4 py-3 font-mono text-xs">{expense.expense_id}</td>
                  <td className="px-4 py-3">{categoryMeta[expense.category]?.label ?? expense.category}</td>
                  <td className="px-4 py-3">{expense.employee_id}</td>
                  <td className="px-4 py-3">{expense.amount_claimed.toFixed(2)} 元</td>
                  <td className="px-4 py-3">{statusPill(expense.status)}</td>
                  <td className="px-4 py-3">
                    <button
                      className="inline-flex items-center gap-1 text-sm font-semibold text-teal hover:text-teal-900"
                      type="button"
                      onClick={async () => {
                        const latest = await apiGet<Expense>(`/api/expenses/${expense.expense_id}`);
                        setActiveExpense(latest);
                        setActiveReview(latest.latest_review ?? null);
                      }}
                    >
                      查看
                      <ChevronRight size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-line bg-white px-3 py-2 text-right">
      <div className="text-lg font-bold text-ink">{value}</div>
      <div className="text-xs text-muted">{label}</div>
    </div>
  );
}

function Field({ label, icon, children }: { label: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 flex items-center gap-1.5 text-sm font-semibold text-ink">
        {icon}
        {label}
      </span>
      {children}
    </label>
  );
}

function ReviewPanel({ review, busy }: { review: ReviewResult | null; busy: boolean }) {
  if (busy && !review) {
    return (
      <div className="flex min-h-[480px] items-center justify-center rounded-lg border border-line bg-panel p-6 shadow-soft">
        <div className="text-center">
          <Loader2 className="mx-auto animate-spin text-teal" size={34} />
          <p className="mt-3 font-semibold text-ink">Agent 正在收集证据</p>
          <p className="mt-1 text-sm text-muted">MCP 工具、OCR、规则引擎和政策检索正在串起来。</p>
        </div>
      </div>
    );
  }
  if (!review) {
    return (
      <div className="flex min-h-[480px] items-center justify-center rounded-lg border border-dashed border-line bg-white/70 p-6">
        <div className="max-w-sm text-center">
          <ReceiptText className="mx-auto text-muted" size={34} />
          <p className="mt-3 font-semibold text-ink">提交一笔报销后查看初审结果</p>
          <p className="mt-1 text-sm leading-6 text-muted">结果会包含建议结论、政策依据、工具证据和可审计摘要。</p>
        </div>
      </div>
    );
  }
  const decision = decisionCopy[review.decision] ?? decisionCopy.agent_failed;
  return (
    <div className="rounded-lg border border-line bg-panel p-4 shadow-soft">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-ink">Agent 初审结果</h2>
          <p className="mt-1 text-sm text-muted">{review.expense_id}</p>
        </div>
        <span className={`inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-bold ${decision.className}`}>
          {decision.icon}
          {decision.label}
        </span>
      </div>
      <p className="mt-4 rounded-lg bg-slate-50 p-3 text-sm leading-6 text-ink">{review.audit_summary}</p>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <Metric label="风险等级" value={review.risk_level} />
        <Metric label="政策版本" value={review.policy_version} />
        <Metric label="人工复核" value={review.human_review_required ? "是" : "否"} />
      </div>

      <Section title="风险原因">
        {review.reasons.length === 0 ? (
          <p className="text-sm text-muted">未发现确定性违规或强制复核项。</p>
        ) : (
          review.reasons.map((reason) => (
            <div key={`${reason.issue}-${reason.description}`} className="rounded-lg border border-line p-3">
              <div className="flex items-center justify-between gap-2">
                <span className="font-semibold text-ink">{reason.issue}</span>
                <span className="text-xs font-semibold text-muted">{reason.policy_id ?? "策略"}</span>
              </div>
              <p className="mt-1 text-sm leading-6 text-muted">{reason.description}</p>
            </div>
          ))
        )}
      </Section>

      <Section title="工具证据">
        <div className="space-y-2">
          {review.tool_evidence.map((item, index) => (
            <div key={`${item.server}-${item.tool}-${index}`} className="rounded-lg border border-line p-3">
              <div className="flex items-center justify-between gap-2 text-sm">
                <span className="font-semibold text-ink">
                  {item.server}.{item.tool}
                </span>
                <span className={item.status === "ok" ? "text-teal" : "text-rose"}>{item.status}</span>
              </div>
              <p className="mt-1 text-sm leading-6 text-muted">{item.result_summary}</p>
            </div>
          ))}
        </div>
      </Section>

      <Section title="政策依据">
        <div className="space-y-2">
          {review.policy_citations.slice(0, 4).map((item) => (
            <details key={item.policy_id} className="rounded-lg border border-line p-3">
              <summary className="cursor-pointer text-sm font-semibold text-ink">
                {item.policy_id} / {item.title}
              </summary>
              <p className="mt-2 text-sm leading-6 text-muted">{item.text}</p>
            </details>
          ))}
        </div>
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mt-4">
      <h3 className="mb-2 text-sm font-bold text-ink">{title}</h3>
      {children}
    </div>
  );
}

function statusPill(status: string) {
  const classes: Record<string, string> = {
    suggested_pass: "bg-teal-50 text-teal-800 border-teal-200",
    suggested_reject: "bg-rose-50 text-rose-800 border-rose-200",
    human_review_required: "bg-amber-50 text-amber-900 border-amber-200",
    submitted: "bg-slate-50 text-slate-700 border-slate-200",
    finance_confirmed: "bg-teal-100 text-teal-900 border-teal-200",
    finance_overridden: "bg-purple-50 text-purple-900 border-purple-200"
  };
  return <span className={`rounded-md border px-2 py-1 text-xs font-semibold ${classes[status] ?? classes.submitted}`}>{status}</span>;
}
