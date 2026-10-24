# LibraCore — Evaluation Rubric Mapping & Verification Checklist

**Course:** BCSE302P – Database Systems Lab  
**Lab Review:** Review 1, 2, and 3 Comprehensive Submission  
**Institution:** Vellore Institute of Technology (VIT)  

---

## Non-Negotiable Lab Checklist & File Verification

| # | Requirement | Required Count / Target | Implemented In LibraCore | File Location & Line References | Status |
|---|---|---|---|---|:---:|
| **1** | 6–8 Related Tables with PK + FK | 6–8 tables (target 8) | **8 Fully Normalized Tables** (`CATEGORY`, `AUTHOR`, `LIBRARIAN`, `BOOK`, `MEMBER`, `ISSUE_TRANSACTION`, `RESERVATION`, `FINE`) | `database/01_create_tables.sql` (Lines 14–112) | **PASS** |
| **2** | Constraints: NOT NULL, UNIQUE, CHECK, DEFAULT | All 4 types across many columns | NOT NULL (45+ cols), UNIQUE (12 keys), CHECK (14 range/domain rules), DEFAULT (8 default values) | `database/01_create_tables.sql` (Throughout DDL) | **PASS** |
| **3** | ≥ 10 Meaningful Records per Table | ≥ 10 rows (aim 12–25) | **125+ Total Records** (10 Categories, 15 Authors, 6 Librarians, 25 Books, 20 Members, 46 Issues, 12 Reservations, 12 Fines) | `database/02_insert_data.sql` (Lines 11–180) | **PASS** |
| **4** | ER Diagram + Relational Schema | Mermaid, SVG, markdown report | Mermaid `.mmd` definition, vector `.svg`, comprehensive schema markdown, and normalization analysis | `docs/er_diagram.mmd`, `docs/er_diagram.svg`, `docs/relational_schema.md`, `docs/normalization.md` | **PASS** |
| **5** | ≥ 15 Complex SQL Queries | ≥ 15 queries (write 18) | **18 Analytical Queries** covering Joins (2, 3, 4 table), LEFT JOIN, GROUP BY/HAVING, Aggregations, Nested/Correlated Subqueries, IN/NOT EXISTS, UNION/EXCEPT, and Trends | `database/03_queries.sql` (Queries Q1 to Q18), `application/query_runner.py` | **PASS** |
| **6** | ≥ 2 Procedures + ≥ 2 Functions | ≥ 2 procs + ≥ 2 funcs (write 4 + 3) | **4 Procedures** (`Issue_Book_Proc`, `Return_Book_Proc`, `Reserve_Book_Proc`, `Pay_Fine_Proc`) + **3 Functions** (`Calculate_Fine_Func`, `Get_Member_Pending_Fine_Func`, `Get_Loan_Days_Func`) | `database/04_procedures.sql` (Lines 10–270), `database/05_functions.sql` (Lines 10–75) | **PASS** |
| **7** | ≥ 1 Explicit Cursor | ≥ 1 cursor (write 2) | **2 Explicit Cursors** (`Overdue_Report_Cursor`, `Member_Activity_Cursor`) with record processing and summary totals | `database/06_cursor.sql` (Lines 10–135) | **PASS** |
| **8** | ≥ 2 Database Triggers | ≥ 2 triggers (write 5) | **6 Oracle Triggers + 6 Native SQLite Triggers** (`trg_issue_decrement_stock`, `trg_return_increment_stock`, `trg_prevent_issue_no_stock`, `trg_block_inactive_member`, `trg_fine_suspend_member`, `trg_fine_paid_reactivate`) | `database/07_triggers.sql`, `database/07b_triggers_sqlite.sql` | **PASS** |
| **9** | INSERT / UPDATE / DELETE Demonstrated | Full CRUD in DB + UI | Demonstrated across Books, Members, Issues, Returns, Reservations, and Fines with FK RESTRICT error handling | `database/08_demo_transactions.sql`, `application/server.py`, UI modals | **PASS** |
| **10** | Database Connectivity from App | Python DB API / SQLite3 | Native SQLite3 connection with `PRAGMA foreign_keys = ON;` and commit/rollback transactions | `application/db_manager.py` (Lines 22–35) | **PASS** |
| **11** | End-to-End System Flow | User Op → SQL/PL-SQL → DB Processing → State Change → Result | Live Telemetry Drawer tracking action type, raw SQL, tables touched, delta change, and execution time in ms | `application/server.py` (`log_telemetry`), `application/templates/index.html` | **PASS** |
| **12** | ≥ 5 Real-World Transactions Demonstrated | ≥ 5 (write 8) | **8 End-to-End ACID Transactions** automated in test runner and UI viva button with zero double counting assertions | `database/08_demo_transactions.sql`, `application/demo_runner.py` | **PASS** |
| **13** | Every Component Connected to App | No isolated scripts | Every Procedure, Function, Cursor, and Trigger is mapped to UI actions and REST endpoints | UI Modals & Buttons → Flask Endpoints → Python DB Manager → Triggers / SQLite | **PASS** |

---

## Component-to-UI Action Mapping Table

| SQL / PL-SQL Component | Type | Python Mirror | Triggered by UI Action | REST Endpoint |
|---|---|---|---|---|
| `Issue_Book_Proc` | Procedure | `issue_book_proc` | Clicking "Confirm Checkout" in Issue Modal or Book Detail Drawer | `POST /api/issue` |
| `Return_Book_Proc` | Procedure | `return_book_proc` | Clicking "Return" button on active loan card or row | `POST /api/return` |
| `Reserve_Book_Proc` | Procedure | `reserve_book_proc` | Clicking "Join Waitlist" on out-of-stock book | `POST /api/reserve` |
| `Pay_Fine_Proc` | Procedure | `pay_fine_proc` | Clicking "Pay" button on outstanding fine row | `POST /api/fines/pay` |
| `Calculate_Fine_Func` | Function | `calculate_fine_func` | Automatically invoked upon book check-in | Internal during Return |
| `Get_Member_Pending_Fine_Func` | Function | `get_member_pending_fine_func` | Evaluated during loan checkout eligibility check | Internal during Issue |
| `Get_Loan_Days_Func` | Function | `get_loan_days_func` | Displayed live in checkout modal loan policy preview | `GET /api/meta` / Issue |
| `Overdue_Report_Cursor` | Cursor | `generate_overdue_report_cursor` | Reports view button "Run Overdue Audit Cursor" | `GET /api/cursor/overdue` |
| `Member_Activity_Cursor` | Cursor | `generate_member_activity_cursor` | Reports view button "Run Patron Engagement Cursor" | `GET /api/cursor/activity` |
| `trg_issue_decrement_stock` | Trigger | Native Trigger | Fires after INSERT on `ISSUE_TRANSACTION` | Automatically in DB |
| `trg_return_increment_stock` | Trigger | Native Trigger | Fires after UPDATE of return_date on `ISSUE_TRANSACTION` | Automatically in DB |
| `trg_prevent_issue_no_stock` | Trigger | Native Trigger | Fires before INSERT on `ISSUE_TRANSACTION` if stock = 0 | Automatically in DB |
| `trg_block_inactive_member` | Trigger | Native Trigger | Fires before INSERT on `ISSUE_TRANSACTION` if status != 'Active' | Automatically in DB |
| `trg_fine_suspend_member` | Trigger | Native Trigger | Fires after INSERT on `FINE` if pending > ₹500 | Automatically in DB |
| `trg_fine_paid_reactivate` | Trigger | Native Trigger | Fires after UPDATE on `FINE` when pending dues drop ≤ ₹200 | Automatically in DB |
