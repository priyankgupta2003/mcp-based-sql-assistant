# MCP BASED SQL ASSISTANT
MCP (Model Context Protocol) BASED SQL ASSISTANT. It converts natural language to SQL, executes via an MCP server against SQLite, and renders results in Streamlit.

## Included (MCP-only)
- app_mcp.py — Streamlit UI
- agent_mcp.py — LangGraph agent (schema → generate → optimize → execute)
- mcp_client.py — MCP stdio client (auto-starts server)
- mcp_server.py — MCP server exposing get_schema, list_tables, query_database
- sql_optimizer.py — SQL optimization and analysis
- requirements.txt — dependencies
- .env — set OPENAI_API_KEY (and optionally DB_URL for future use)
- sales.db — SQLite database (created by setup_db.py)
- setup_db.py — one-time DB initialization

## Prerequisites
- Python 3.10+
- OpenAI API key

## Setup
1) Create and activate a virtual environment

Windows PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
macOS/Linux:
```bash
python -m venv .venv
source .venv/bin/activate
```

2) Install dependencies
```bash
pip install -r requirements.txt
```

3) Configure environment
Create .env in project root:
```bash
OPENAI_API_KEY="OPEN-API-KEY"
# Optional (future multi-DB)
# DB_URL="sqlite:///sales.db"
```

4) Initialize database (first run only)
```bash
python setup_db.py
```

## Run (MCP version)
If streamlit is not on PATH, use python -m.

Windows PowerShell:
```powershell
python -m streamlit run app_mcp.py --server.address 0.0.0.0 --server.port 8501
```
macOS/Linux:
```bash
python -m streamlit run app_mcp.py --server.address 0.0.0.0 --server.port 8501
```
Open http://localhost:8501 in your browser.

Notes:
- The MCP client auto-starts the MCP server via stdio; no separate process to manage.
- The MCP server defaults to SQLite at sales.db in the project root.

## How it works
1) User enters a question in app_mcp.py.
2) agent_mcp.py runs nodes: get_schema → generate_sql → optimize_sql → execute_sql.
3) mcp_client.py calls MCP tools in mcp_server.py.
4) sql_optimizer.py improves SQL and provides analysis.
5) UI displays original/optimized SQL, results, and analysis.

## UI overview
- Button: Generate & Optimize SQL
- Tabs:
  - Queries: original vs optimized SQL
  - Results: execution output
  - Analysis: optimizer details and query analysis

## Troubleshooting
- Streamlit not found:
  - Use: python -m streamlit run app_mcp.py
  - Ensure venv is activated
- Missing OpenAI key:
  - Set OPENAI_API_KEY in .env and restart
- Database missing/empty:
  - Run: python setup_db.py
- MCP errors:
  - Ensure mcp and pydantic are installed (from requirements.txt)
  - Check console logs; client auto-starts the server

## Deployment
Ship at minimum:
- app_mcp.py, agent_mcp.py, mcp_client.py, mcp_server.py, sql_optimizer.py
- requirements.txt, .env (or environment variables), sales.db (or setup_db.py)

Example run step:
```bash
pip install -r requirements.txt
python setup_db.py  # if DB not persisted
python -m streamlit run app_mcp.py --server.address 0.0.0.0 --server.port 8501
```

Env vars:
- OPENAI_API_KEY — required
- DB_URL — optional (server currently uses sales.db by default)

Security:
- Do not commit .env; use a secret manager in production.

---
Built with LangGraph, LangChain, MCP, Streamlit, and SQLite.
