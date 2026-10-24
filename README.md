<div align="center">

# LibraCore — Library Management System

**A relational academic library administration platform featuring catalog inventory tracking, circulation checkout/returns, patron quotas, automated overdue fine calculation, and an interactive SQL query inspection engine.**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57.svg?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![HTML5](https://img.shields.io/badge/HTML5-E34F26.svg?logo=html5&logoColor=white)](https://html.spec.whatwg.org/)
[![CSS3](https://img.shields.io/badge/CSS3-1572B6.svg?logo=css3&logoColor=white)](https://www.w3.org/Style/CSS/)
[![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-F7DF1E.svg?logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)

### 📚 BCSE302P – Database Systems Lab Project (VIT)

</div>

---

## What it is

**LibraCore** is a full-stack library administration and database management platform built to replace outdated university book management systems with a high-performance, single-screen workspace. It combines circulation desk operations (book loans, returns, waitlist reservations, fine settlements) with an active relational database engine that enables administrators and educators to inspect table schemas, execute pre-compiled analytical SQL queries with sub-millisecond execution telemetry, and manage institutional borrowing records with strict relational integrity.

The frontend is reconstructed from the ground up to match the modern Spik dashboard design system (`ui_reference.png`) with Poppins typography, rounded container cards, elevated floating selected rows, and real-time database state change tracking.

---

## Key Features

- **Catalog & Inventory Administration** — Browse, search, filter, and paginate catalog volumes by title, author, category, or ISBN. Track physical shelf locations, replacement prices, and live available stock versus total copies.
- **Patron Management & Quota Limits** — Manage student, faculty, and staff patrons with designated borrowing quotas (Students: 3, Faculty: 8, Staff: 5) and auto-suspension triggers when unpaid dues exceed institutional thresholds.
- **Circulation Desk (Check-Out & Check-In)** — Issue books with loan duration policies computed dynamically by patron category (Student: 14 days, Faculty: 30 days, Staff: 21 days). Check in returned books with automated overdue fine calculation (`Calculate_Fine_Func`).
- **Waitlist Reservations** — Enforce FIFO waitlist queues when high-demand titles reach 0 available copies. When a copy is checked in, patrons with waiting holds are highlighted for one-click fulfillment.
- **Fine Ledger & Remittance** — Track overdue fees assessed at ₹5/day late (strictly capped at the book's replacement price). Settle dues via UPI, Cash, Cards, or Net Banking with unique voucher tracking and automatic patron reactivation.
- **Explicit Database Cursors** — Execute `Overdue_Report_Cursor` to audit overdue loans by severity tier (Minor, Serious, Critical) and `Member_Activity_Cursor` to rank patrons by reading frequency.
- **Real-Time Telemetry & Flow Engine** — Live 5-stage telemetry drawer displaying the exact operational journey: **User Operation → SQL/PL-SQL → DB Processing → State Change → Result**, logging SQL statements, affected tables, and execution timing in milliseconds.
- **SQL Query Engine & Schema Explorer** — Explore all 8 normalized tables with live column specifications, primary keys, and foreign keys. Execute 18 categorized SQL queries covering multi-table INNER JOINs, GROUP BY aggregations, HAVING filters, correlated subqueries, set operations, and date velocity trends.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Semantic HTML5, Vanilla JavaScript (ES6+), Custom Design System (CSS3), Chart.js |
| **Backend** | Python 3, Flask, Werkzeug, Gunicorn |
| **Database** | SQLite3 (ACID-compliant, Foreign Key Enforcement, Strict Native Triggers) |
| **PL/SQL Lab Spec** | Oracle PL/SQL Syntax (`04_procedures.sql`, `05_functions.sql`, `06_cursor.sql`, `07_triggers.sql`) |
| **Typography** | Google Fonts: Poppins (300, 400, 500, 600, 700) |
| **Reference Design** | Modern Spik UI Dashboard (`ui_reference.png`) |

---

## Project Structure

```text
LibraCore/
├── application/
│   ├── templates/
│   │   └── index.html             # Single-screen dashboard UI (replicated to reference)
│   ├── static/
│   │   └── ui_reference.png       # Original visual reference image
│   ├── app.py                     # Interactive CLI administration console
│   ├── db_manager.py              # SQLite connection, DDL/DML, and Python PL/SQL mirrors
│   ├── demo_runner.py             # 8 End-to-end ACID transaction test suite
│   ├── query_runner.py            # 18 Pre-compiled SQL queries with ASCII tables
│   └── server.py                  # Flask REST API server and telemetry logger
├── database/
│   ├── 01_create_tables.sql       # 8 Relational tables DDL with strict integrity constraints
│   ├── 02_insert_data.sql         # 125+ Benchmark seed records
│   ├── 03_queries.sql             # 18 Analytical SQL queries
│   ├── 04_procedures.sql          # Oracle PL/SQL procedures (4)
│   ├── 05_functions.sql           # Oracle PL/SQL functions (3)
│   ├── 06_cursor.sql              # Oracle PL/SQL explicit cursors (2)
│   ├── 07_triggers.sql            # Oracle PL/SQL triggers (6)
│   ├── 07b_triggers_sqlite.sql    # Native SQLite triggers (6)
│   ├── 08_demo_transactions.sql   # 8 Real-world ACID transaction sequences
│   └── library_lms.db             # Active SQLite database file
├── docs/
│   ├── er_diagram.mmd             # Mermaid ER diagram
│   ├── er_diagram.svg             # Vector SVG ER diagram
│   ├── relational_schema.md       # Comprehensive schema report and data dictionary
│   ├── normalization.md           # Functional dependencies, 1NF-3NF proofs, denormalization
│   └── rubric_mapping.md          # Non-negotiable lab rubric checklist and mapping
├── README.md                      # Project documentation and guide
└── requirements.txt               # Dependencies (Flask, Werkzeug, gunicorn)
```

---

## Domain Mapping (CampusCore → LibraCore)

| CampusCore Entity | LibraCore Entity | Primary Responsibility |
|---|---|---|
| `DEPARTMENT` | **`CATEGORY`** | Subject classification, DDC genres, shelf zones |
| `FACULTY` | **`AUTHOR`** | Book creators and biographical metadata |
| `COURSE` | **`BOOK`** | Catalog titles, pricing, shelf coordinates, stock |
| `STUDENT` | **`MEMBER`** | Registered patrons (Student, Faculty, Staff) |
| `COURSE_OFFERING` | **`LIBRARIAN`** | Circulation desk personnel and duty shifts |
| `ENROLLMENT` | **`ISSUE_TRANSACTION`** | Active and historical circulation loans |
| `EXAM_RESULT` | **`RESERVATION`** | Waitlist queue for out-of-stock titles |
| `FEE_PAYMENT` | **`FINE`** | Overdue fine ledgers and payment settlements |
| `Enroll_Student_Proc` | `Issue_Book_Proc` | Validates eligibility and processes checkout |
| `Record_Exam_Result_Proc` | `Return_Book_Proc` | Checks in book and assesses overdue fines |
| `Process_Fee_Payment_Proc` | `Pay_Fine_Proc` | Records fee settlement and reactivates patron |
| `Calculate_Student_GPA_Func`| `Calculate_Fine_Func` | Capped late fee computation (₹5/day) |
| `Calculate_Pending_Fee_Func`| `Get_Member_Pending_Fine_Func` | Aggregates unpaid patron fines |
| `Generate_Academic_Report_Cursor` | `Overdue_Report_Cursor` | Audits overdue loans by risk severity |

---

## Relational Schema (8 Tables)

1. **`CATEGORY`** (`category_id` PK, `category_name` UK, `category_code` UK, `shelf_zone`, `description`)
2. **`AUTHOR`** (`author_id` PK, `first_name`, `last_name`, `email` UK, `nationality`, `birth_year`)
3. **`LIBRARIAN`** (`librarian_id` PK, `first_name`, `last_name`, `email` UK, `phone` UK, `hire_date`, `designation`, `salary`, `shift`)
4. **`BOOK`** (`book_id` PK, `isbn` UK, `title`, `author_id` FK, `category_id` FK, `publisher`, `publish_date`, `edition`, `language`, `shelf_location`, `price`, `total_copies`, `available_copies`, `cover_url`, `added_on`, `status`)
5. **`MEMBER`** (`member_id` PK, `member_code` UK, `first_name`, `last_name`, `email` UK, `phone` UK, `member_type`, `department`, `join_date`, `membership_expiry`, `max_books_allowed`, `status`)
6. **`ISSUE_TRANSACTION`** (`issue_id` PK, `book_id` FK, `member_id` FK, `librarian_id` FK, `issue_date`, `due_date`, `return_date`, `status`)
7. **`RESERVATION`** (`reservation_id` PK, `book_id` FK, `member_id` FK, `reserved_on`, `expires_on`, `queue_position`, `status`)
8. **`FINE`** (`fine_id` PK, `issue_id` UK/FK, `member_id` FK, `days_overdue`, `fine_amount`, `fine_date`, `payment_status`, `paid_on`, `payment_method`, `transaction_ref` UK)

---

## REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/stats` | Summary statistics (books, members, active loans, overdue, pending fines) |
| `GET` | `/api/meta` | Author, Category, and Librarian metadata for dropdowns |
| `GET` | `/api/tables/<table_name>` | Full rows and column metadata from any of the 8 tables |
| `GET` | `/api/books` | Paginated books with search, sort, and date range filters |
| `GET` | `/api/books/<id>` | Comprehensive book details, active borrowers, and waitlist queue |
| `POST` | `/api/books` | Catalog a new book |
| `PUT` | `/api/books/<id>` | Update catalog attributes, shelf location, and copy stock |
| `DELETE` | `/api/books/<id>` | Delete a book (guarded by `ON DELETE RESTRICT`) |
| `DELETE` | `/api/books/bulk` | Bulk delete multiple selected catalog titles |
| `GET` | `/api/members` | Patron directory with search and type filters |
| `GET` | `/api/members/<id>/summary`| Patron profile with active loans, history, and unpaid fines |
| `POST` | `/api/members/add` | Register a new patron into the library |
| `PUT` | `/api/members/<id>` | Update patron status (Active, Suspended, Expired) |
| `POST` | `/api/issue` | Checkout a book (`Issue_Book_Proc` + trigger stock decrement) |
| `POST` | `/api/return` | Check in a book (`Return_Book_Proc` + fine assessment) |
| `POST` | `/api/reserve` | Place a waitlist hold on an out-of-stock title (`Reserve_Book_Proc`) |
| `POST` | `/api/reservations/<id>/cancel`| Cancel a pending reservation |
| `POST` | `/api/fines/pay` | Settle an overdue fine (`Pay_Fine_Proc` + patron reactivation) |
| `GET` | `/api/cursor/overdue` | Execute explicit cursor auditing overdue loans by severity |
| `GET` | `/api/cursor/activity` | Execute explicit cursor auditing patron engagement tiers |
| `GET` | `/api/queries` | List all 18 pre-compiled analytical SQL queries |
| `GET` | `/api/queries/<id>` | Execute a pre-compiled SQL query and return execution metrics |
| `POST` | `/api/execute_raw_sql` | Execute safe read-only SQL queries (`SELECT` only) |
| `GET` | `/api/demo_transactions`| Run all 8 ACID transactions with verified assertions |
| `POST` | `/api/reset_db` | Drop and re-seed database with benchmark records and triggers |
| `GET` | `/api/telemetry` | Retrieve real-time 5-stage execution activity logs |

---

## Architectural Improvements & Fixes Over CampusCore

1. **Elimination of Double-Counting Bug:** In CampusCore, `Enroll_Student_Proc` manually incremented seats while the database trigger also incremented seats, causing duplicate counts. In LibraCore, stored procedures and Python mirrors **never modify `available_copies` directly**; stock adjustments are handled **exclusively by database triggers** (`trg_issue_decrement_stock` and `trg_return_increment_stock`).
2. **Native SQLite Triggers:** In addition to the Oracle PL/SQL specification files required for lab review, a dedicated `07b_triggers_sqlite.sql` script creates real, active triggers inside SQLite that fire during runtime operations.
3. **Strict SQL Console Security:** The raw query execution endpoint enforces strict validation, rejecting all mutations (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`) and permitting only `SELECT`, `PRAGMA`, and `EXPLAIN` read operations.
4. **Resolved Dead References:** Replaced dead diagram directories and missing assets with actual vector SVG diagrams (`docs/er_diagram.svg`), Mermaid source (`docs/er_diagram.mmd`), and real UI reference assets.

---

## How to Run

### 1. Installation
Ensure Python 3.10+ is installed:
```bash
cd LibraCore
pip install -r requirements.txt
```

### 2. Launch the Web Application
```bash
python application/server.py
```
Open your browser to: **`http://localhost:5001`**

### 3. Run the CLI Console
For terminal-based library administration:
```bash
python application/app.py
```

### 4. Execute the 18 Analytical SQL Queries
```bash
python application/query_runner.py
```

### 5. Run the 8 ACID Real-World Transaction Tests
```bash
python application/demo_runner.py
```
Asserts that checkout decrements stock by **exactly 1**, returns increment stock by **exactly 1**, out-of-stock loans abort, and fine payments auto-reactivate patrons.
