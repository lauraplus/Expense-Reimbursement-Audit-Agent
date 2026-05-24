# 报销智能初审 Agent MVP

一个可本地演示的企业报销智能初审系统，覆盖交通（加班打车）、差旅住宿、团建三类场景。系统使用 Next.js 前端、FastAPI 后端、SQLite 留存数据，并通过模拟 MCP 工具层查询 HR、预算、政策、审批和历史报销数据。

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

- `frontend/`：员工提交页和初审结果展示
- `backend/`：FastAPI、SQLite、受控 Agent、规则引擎、OCR 适配器、模拟 MCP 工具
- `mock/`：政策、员工、团队、预算、审批、历史报销、票据 OCR、benchmark 标签
- `scripts/`：mock 数据生成和评估脚本

## Agent 职责边界

Agent 只输出初审建议，不直接完成最终审批、付款或预算扣减。财务人员可在页面中确认或修正 Agent 结果，反馈会留存在数据库中，供后续分析和优化。
