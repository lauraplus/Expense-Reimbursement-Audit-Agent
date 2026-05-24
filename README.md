# 报销智能初审 Agent MVP

搭建面向企业报销场景的智能初审 Agent，自动理解报销场景、按需检索政策条款、自主调用关联系统完成合规判定，并通过 Human-in-the-Loop 保留财务最终确认责任。

关键词：ReAct Agent、Agentic RAG、MCP Tool Use、Skill、向量检索、Human-in-the-Loop。

## 项目能力

1. **受控 Agent 审核引擎**：Agent 接收报销单后，根据报销类目路由到对应审核 Skill，通过工具调用、政策检索和规则引擎输出带政策依据的初审结论。
2. **MCP 模拟工具调用**：通过统一工具层模拟 HR、预算、政策、审批、报销历史和票据解析等系统，Agent 根据报销类型选择不同工具组合。
3. **政策知识库 RAG**：将费控政策按条款粒度留存，审核结论引用具体政策编号；政策更新可通过刷新知识库完成。
4. **Skill 封装审核经验**：将交通、差旅住宿、团建三类高频报销审核要点封装为可维护的自然语言/结构化指引。
5. **人机协同与审计**：Agent 输出建议通过、建议驳回或需人工复核；财务人员可确认或修正结果，系统留存工具证据、政策依据和反馈记录。

## 安全说明

OCR 凭证只通过环境变量读取，不写入代码、mock 数据或数据库：

- `ALIBABA_CLOUD_ACCESS_KEY_ID`
- `ALIBABA_CLOUD_ACCESS_KEY_SECRET`

如果曾经在对话、文档或截图中暴露过真实密钥，建议在云控制台轮换。

## 快速启动

1. 生成 mock 数据：

   ```powershell
   & "C:\Users\frank\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\generate_mock_data.py
   ```

2. 安装后端依赖并启动：

   ```powershell
   & "C:\Users\frank\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pip install -r backend\requirements.txt
   & "C:\Users\frank\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m uvicorn backend.app.main:app --reload --port 8000
   ```

3. 安装前端依赖并启动：

   ```powershell
   cd frontend
   npm.cmd install
   npm.cmd run dev
   ```

4. 打开：

   - 前端：http://localhost:3000
   - 后端健康检查：http://localhost:8000/api/health

## 目录

- `frontend/`：员工提交页、Agent 初审结果展示、财务确认/修正入口
- `backend/`：FastAPI、SQLite、受控 Agent、规则引擎、OCR 适配器、模拟 MCP 工具
- `mock/`：政策、员工、团队、预算、审批、历史报销、票据 OCR、benchmark 标签
- `scripts/`：mock 数据生成和评估脚本

## Agent 职责边界

Agent 只输出初审建议，不直接完成最终审批、付款或预算扣减。财务人员可在页面中确认或修正 Agent 结果，反馈会留存在数据库中，供后续分析和优化。
