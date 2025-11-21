<div align="center">

# 🤖 SQL Database Agent From Scratch

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Gemini](https://img.shields.io/badge/LLM-Gemini%202.5%20Flash-orange.svg)

*A lightweight ReAct-based agent that interprets natural language queries and interacts with SQL databases*

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Tools](#%EF%B8%8F-available-tools) • [Example](#-example-run-with-trace)

</div>

---

## 📋 Purpose

This project implements a complete SQL database agent **from scratch** without using any agent frameworks (no LangChain, no LangGraph, no external agent libraries). The agent uses the **ReAct (Reasoning + Acting)** pattern to:

- 🔍 Explore database schemas automatically
- 💬 Answer natural language questions about data
- 🛡️ Execute safe, read-only SQL queries
- 📝 Provide full reasoning traces for every decision

## ✨ Features

- **🔄 ReAct Loop**: Complete Thought → Action → Observation → Answer cycle
- **🔒 Read-Only Safety**: Only `SELECT` queries allowed (no mutations)
- **🗺️ Schema Discovery**: Automatic table exploration and description
- **⏱️ Rate Limit Handling**: Automatic retry with exponential backoff
- **🚨 Error Recovery**: Graceful handling of missing tables and invalid queries
- **📊 Auditable Traces**: Step-by-step reasoning logs

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/veershah04/Vizuara-NL-SQL-Project.git
cd Vizuara-NL-SQL-Project
```

### 2. Install Dependencies

```bash
pip install google-generativeai
```

### 3. Configure API Key

Get your Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey) and set it in the code files:

```python
GEMINI_API_KEY = "GEMINI_API_KEY"
```

## 💻 Usage

### Single Query Mode

Run a single natural language query:

```bash
python single_query.py "What is the total amount of all orders?"
```

### Test Suite Mode

Execute all 6 comprehensive test cases:

```bash
python test_agent.py
```

**Test cases include:**
- Schema discovery
- Simple counts
- Aggregations
- Filtering queries
- Error recovery
- Complex queries

## 🛠️ Available Tools

The agent has access to three tools for database interaction:

| Tool | Arguments | Returns | Description |
|------|-----------|---------|-------------|
| `list_tables` | None | List of table names | Lists all tables in the database |
| `describe_table` | `table_name` (str) | Schema and row count | Shows columns, data types, and row count |
| `query_database` | `query` (str) | Formatted results | Executes SELECT queries only (max 100 rows) |

## 📖 Example Run with Trace

```
Using model: gemini-2.5-flash
✓ Agent ready!

============================================================
NEW QUERY: How many customers are in the database?
============================================================

STEP 1
THOUGHT: I need to find what tables are available first
ACTION: list_tables{}
OBSERVATION: Available tables: customers, orders

STEP 2
THOUGHT: Let me check the customers table schema
ACTION: describe_table{"table_name": "customers"}
OBSERVATION: Table: customers
Columns:
  - id (INTEGER)
  - name (TEXT)
  - email (TEXT)
  - age (INTEGER)
  - city (TEXT)
Row count: 5

STEP 3
THOUGHT: Now I can count the customers
ACTION: query_database{"query": "SELECT COUNT(*) FROM customers"}
OBSERVATION: Columns: COUNT(*)
Returned 1 row(s):
  1. (5,)

FINAL ANSWER: There are 5 customers in the database.
```

## 📁 Project Structure

```
sql-database-agent/
├── agent.py              # Main agent implementation (~330 lines)
├── sample.db             # Sample SQLite database
├── single_query.py       # Single query runner
├── test_agent.py         # Test suite (6 comprehensive tests)
├── agent_log.txt         # Agent execution logs
├── test_log.txt          # Test execution logs
└── README.md             # This file
```

## ⚙️ Technical Specifications

- **LLM**: Google Gemini 2.5 Flash
- **Database**: SQLite (read-only connection)
- **Max Steps**: 10 per query (configurable)
- **Row Limit**: 100 rows per query (auto-enforced)
- **Lines of Code**: ~330 (excluding comments and docstrings)
- **Dependencies**: `google-generativeai` only

## 🔐 Safety Features

- ✅ SQL validation (blocks `INSERT`/`UPDATE`/`DELETE`/`DROP`/`ALTER`/`CREATE`)
- ✅ Automatic `LIMIT` clause for unbounded queries
- ✅ Read-only database connection
- ✅ Graceful error handling for syntax errors
- ✅ Maximum step limit protection (prevents infinite loops)

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

---
