<!-- 


## Live Demo

Clone and run locally — instructions below.

### Screenshots

**Main Interface**
<img width="1690" height="922" alt="query_pilot_ss1_demo" src="https://github.com/user-attachments/assets/3672584a-9071-4824-ae9c-2d1182a15bbd" />


**SQL Transparency — See Exactly What Ran**

<img width="1918" height="967" alt="query_pilot_ss2" src="https://github.com/user-attachments/assets/25cffb8f-a8e1-4f76-a0a9-558b694e77bc" />


**Complex Query — Revenue by Cuisine**

<img width="1872" height="927" alt="query_pilot_ss3" src="https://github.com/user-attachments/assets/61493689-0d28-481f-97dc-bedecb0df099" />


---
-->



# QueryPilot 📊 — Natural Language to SQL Agent

> Ask questions about any database in plain English.
> Get instant answers backed by real SQL.
> Your data never leaves your machine.

**Demo Video:** [Watch on LinkedIn](https://linkedin.com/in/mohd-sami-dev) | **GitHub:** [github.com/Sami21234/text-to-sql-agent](https://github.com/Sami21234/text-to-sql-agent)

---

## The Problem

Data lives in databases. Insights require SQL.
Most people cannot write SQL.

A marketing manager wants to know which city has the most 
orders this month. A finance analyst needs revenue by cuisine 
type. An operations lead wants cancellation rates by restaurant.

Today they either wait for a data engineer, learn SQL 
themselves, or make decisions without data.

QueryPilot eliminates that bottleneck.

---

## Your Data Is Safe - Here Is Why

This is the most important thing to understand about QueryPilot.

**Everything runs locally on your machine.**

- Mistral 7B runs through Ollama on your own hardware
- Your database file never leaves your computer
- No queries are sent to any cloud API
- No third party ever sees your data
- Suitable for sensitive domains — HR records, financial data, medical information, legal documents

This is fundamentally different from tools like ChatGPT with 
Code Interpreter or cloud-based analytics platforms. Those 
services process your data on their servers. QueryPilot 
processes everything on yours.

---

## What It Does

Upload any SQLite database. Ask questions in plain English.
Get answers backed by real SQL with full transparency.

| You ask | QueryPilot does |
|---|---|
| "Which customer spent the most?" | Inspects schema → generates JOIN query → executes → explains |
| "What % of orders were cancelled?" | Writes CASE WHEN percentage query → shows result |
| "Top cuisine by revenue?" | Groups by cuisine, sums totals, ranks results |
| "What is the total salary by department?" | Detects HR schema → generates relevant query |

---

## Key Features

**Dynamic Database Upload**
Upload any SQLite .db file. The system automatically detects
all tables, columns, primary keys, foreign keys, and 
relationships. No configuration needed.

**Auto-Generated Sample Questions**
After upload, Mistral analyzes your schema and generates 10 
relevant analytical questions specific to your database. 
Different database = different questions.

**SQL Transparency**
Every answer shows the exact SQL query that ran. Business 
users can verify logic, auditors can trace results, analysts 
can adapt queries for custom reports.

**Query History with CSV Export**
Every query is tracked in the session. Re-run any previous 
question with one click. Export any result set to CSV 
for further analysis in Excel or other tools.

**Security Layer**
Only SELECT queries execute. DROP, DELETE, UPDATE, INSERT 
are blocked at the code level before reaching the database 
regardless of what the LLM generates.

**Complete Privacy**
No internet connection required after setup. Everything 
runs locally. Your data never leaves your machine.

---

## When To Use QueryPilot vs RAG

**Use QueryPilot (SQL) when:**
Your data is structured and relational. Questions require 
exact numeric aggregation, rankings, counts, or comparisons. 
Example: "Show me total sales revenue by region for Q2."

**Use RAG when:**
Your data is unstructured text. Questions require semantic 
understanding and context retrieval. Example: "How do I reset 
my router if the power light is blinking?" — the answer lives 
in a manual, not a database table.

Same AI engineering stack. Different data types. Different tools.

---

## Screenshots

### Food Delivery Analytics
<img width="1872" height="927" alt="query_pilot_ss3" src="https://github.com/user-attachments/assets/61493689-0d28-481f-97dc-bedecb0df099" />

<!-- ### Dynamic HR Database Upload
![HR Database](screenshots/hr_upload.png) -->

### SQL Transparency Panel
<img width="1918" height="967" alt="query_pilot_ss2" src="https://github.com/user-attachments/assets/25cffb8f-a8e1-4f76-a0a9-558b694e77bc" />

<!-- ### Auto-Generated Schema Questions
![Schema Questions](screenshots/schema_questions.png) -->

---

## How It Works
<div align="centre">

  ```text

  User uploads SQLite database
              ↓
  PRAGMA inspection — tables, columns, PKs, FKs, row counts
              ↓
  Ambiguous column detection — auto-generates disambiguation rules
              ↓
  Schema-aware prompt generated — no hardcoding
              ↓
  User asks question in plain English
              ↓
  Input validation — length check, injection pattern detection
              ↓
  LLM (Mistral 7B) generates raw SQL from schema prompt
              ↓
  clean_sql() strips markdown and multiple statements
              ↓
  Safety check — SELECT-only guard blocks destructive queries
              ↓
  SQLite executes the query
              ↓
  LLM formats raw result as natural language answer
              ↓
  Answer + SQL + CSV export displayed in UI
              ↓
  Query saved to session history
  ```
</div>

---

## Tech Stack

| Component | Technology |
|---|---|
| LLM | Mistral 7B via Ollama (fully local) |
| Schema Inspection | SQLite PRAGMA statements |
| SQL Execution | SQLite + LangChain SQLDatabase |
| Safety Layer | SELECT-only guard + keyword blocklist |
| Backend API | FastAPI |
| Frontend | HTML, CSS, Vanilla JavaScript |
| Database | SQLite (any .db file) |

**Total API cost: $0**
**Data privacy: Everything runs locally**

---

## Installation

**Step 1 — Clone**
```bash
git clone https://github.com/Sami21234/text-to-sql-agent.git
cd text-to-sql-agent
```

**Step 2 — Virtual environment**
```bash
python -m venv venv
venv\Scripts\activate
```

**Step 3 — Install dependencies**
```bash
pip install -r requirements.txt
```

**Step 4 — Create demo database**
```bash
python backend/create_db.py
```

**Step 5 — Pull Mistral and start Ollama**
```bash
ollama pull mistral
ollama serve
```

**Step 6 — Start QueryPilot**
```bash
python backend/main.py
```

**Step 7 — Open browser**

http://localhost:8000


---

## Usage

**With demo database:**
Start asking questions immediately using the sample chips.

**With your own database:**
1. Click "Choose File" or drag and drop your .db file
2. Wait for schema detection and question generation
3. Ask any question about your data

**Keyboard shortcut:**
Press Enter to submit a question without clicking Ask.

---

## Project Structure

text-to-sql-agent/<br>
│<br>
├── backend/<br>
│ ├── create_db.py # Creates and seeds SQLite database<br>
│ ├── database.py # Connection manager<br>
│ ├── schema_inspector.py # PRAGMA-based schema detection<br>
│ ├── safety.py # SQL guardrails and input validation<br>
│ ├── agent.py # Two-step NL-to-SQL pipeline<br>
│ └── main.py # FastAPI REST API<br>
│<br>
├── frontend/<br>
│ ├── index.html # Analytics interface<br>
│ ├── style.css # Dark theme<br>
│ └── app.js # Frontend logic with polling<br>
│<br>
├── backend/<br>
│ └── uploads/ # Upload SQLite databases<br>
├── requirements.txt<br>
└── README.md

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | /health | Server status |
| POST | /upload-db | Upload SQLite database |
| GET | /db-info | Current schema details |
| POST | /ask | Submit a natural language question |
| GET | /sample-questions | Get schema-aware suggestions |
| GET | /history | Session query history |
| GET | /export/{id} | Download query result as CSV |
| DELETE | /reset | Return to demo database |

---

## Key Engineering Decisions

**Why auto-generate prompt rules from schema?**
Hardcoded prompt rules break when the schema changes or a 
new database is uploaded. Schema inspection via SQLite PRAGMA 
generates precise rules — foreign key paths, ambiguous column 
disambiguation, table row counts — automatically from the 
actual database structure. Different database = different rules 
= fewer hallucinations.

**Why two-step pipeline instead of ReAct agent loop?**
Mistral 7B in a ReAct loop produces inconsistent output — 
markdown formatting, multiple statements, wrong aggregation 
functions. Separating SQL generation from answer formatting 
gives each step a single responsibility and produces reliable 
output. One prompt asks for SQL only. Another prompt explains 
the result.

**Why clean_sql() in addition to prompt rules?**
Defense in depth. Prompt rules reduce bad output. clean_sql() 
catches what slips through. Relying on only one layer for 
structured output safety is insufficient for production.

**Why SQLite instead of MySQL or PostgreSQL?**
Zero infrastructure. One file. Portable. The SQL logic is 
directly transferable to MySQL or PostgreSQL in production. 
For a local privacy-first tool, SQLite is the correct choice.

**Why local LLM instead of GPT-4 API?**
Privacy. A tool that processes sensitive business data — 
HR records, financial data, customer information — must never 
send that data to a third party server. Mistral 7B via Ollama 
runs entirely on your hardware. GPT-4 sends every query and 
every result to OpenAI's servers. For enterprise use cases 
that is a compliance violation.

---

## Known Limitations

- Complex statistical queries (median, correlation, 
  percentile) may produce incorrect results with Mistral 7B — 
  these require multi-step calculation that smaller local 
  models handle inconsistently
- Generated sample questions may include questions the 
  database cannot answer if the schema lacks certain data 
  patterns
- File upload uses server-side storage — uploaded databases 
  are deleted on server restart in the current implementation
- SQLite only — MySQL and PostgreSQL support is on the roadmap

---

## Roadmap

- PostgreSQL and MySQL connection string support
- Persistent uploaded database storage
- Multi-turn conversation memory for follow-up questions
- Chart generation from query results
- Query bookmarking and sharing

---

## What I Learned

**RAG and SQL solve different problems.**
RAG retrieves meaning from unstructured text. SQL retrieves 
facts from structured data. Both use LLMs for generation. 
Knowing which tool fits which problem is the real engineering 
skill.

**Schema-aware prompting eliminates most hallucinations.**
The single biggest improvement to SQL generation quality was 
injecting the exact foreign key map into the prompt. The LLM 
stopped guessing column names and started using real ones.

**Separate concerns in LLM pipelines.**
One prompt doing too many things fails. Two focused prompts 
succeed. Generate SQL in one step. Explain results in another.

**Defense in depth for LLM output.**
Prompt rules reduce bad output. clean_sql() catches 
formatting. safety.py blocks destructive keywords. Three 
layers catch what one layer misses.

---

## Author

Built by Mohd Sami
GitHub: [Sami21234](https://github.com/Sami21234)
LinkedIn: [mohd-sami-dev](https://linkedin.com/in/mohd-sami-dev)

---

## License

MIT License

---

## Acknowledgements

- [LangChain](https://langchain.com) for SQL database utilities
- [Ollama](https://ollama.ai) for local LLM runtime
- [SQLite](https://sqlite.org) for zero-config database engine
- [FastAPI](https://fastapi.tiangolo.com) for the REST API

