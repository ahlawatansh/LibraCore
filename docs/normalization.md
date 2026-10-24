# LibraCore — Normalization & Relational Design Justification

**Course:** BCSE302P – Database Systems Lab  
**Institution:** Vellore Institute of Technology (VIT)  

---

## 1. Functional Dependencies (FDs) Analysis

Let the schema relation attributes be defined as follows:

### 1. CATEGORY
- `category_id → {category_name, category_code, shelf_zone, description}`
- `category_name → {category_id, category_code, shelf_zone, description}`
- `category_code → {category_id, category_name, shelf_zone, description}`
- **Candidate Keys:** `category_id`, `category_name`, `category_code`.
- **Primary Key:** `category_id`.

### 2. AUTHOR
- `author_id → {first_name, last_name, email, nationality, birth_year}`
- `email → {author_id, first_name, last_name, nationality, birth_year}`
- **Candidate Keys:** `author_id`, `email`.
- **Primary Key:** `author_id`.

### 3. LIBRARIAN
- `librarian_id → {first_name, last_name, email, phone, hire_date, designation, salary, shift}`
- `email → {librarian_id, first_name, last_name, phone, hire_date, designation, salary, shift}`
- `phone → {librarian_id, first_name, last_name, email, hire_date, designation, salary, shift}`
- **Candidate Keys:** `librarian_id`, `email`, `phone`.
- **Primary Key:** `librarian_id`.

### 4. BOOK
- `book_id → {isbn, title, author_id, category_id, publisher, publish_date, edition, language, shelf_location, price, total_copies, available_copies, cover_url, added_on, status}`
- `isbn → {book_id, title, author_id, category_id, publisher, publish_date, edition, language, shelf_location, price, total_copies, available_copies, cover_url, added_on, status}`
- **Candidate Keys:** `book_id`, `isbn`.
- **Primary Key:** `book_id`.

### 5. MEMBER
- `member_id → {member_code, first_name, last_name, email, phone, member_type, department, join_date, membership_expiry, max_books_allowed, status}`
- `member_code → {member_id, first_name, last_name, email, phone, member_type, department, join_date, membership_expiry, max_books_allowed, status}`
- `email → {member_id, member_code, first_name, last_name, phone, member_type, department, join_date, membership_expiry, max_books_allowed, status}`
- `phone → {member_id, member_code, first_name, last_name, email, member_type, department, join_date, membership_expiry, max_books_allowed, status}`
- **Candidate Keys:** `member_id`, `member_code`, `email`, `phone`.
- **Primary Key:** `member_id`.

### 6. ISSUE_TRANSACTION
- `issue_id → {book_id, member_id, librarian_id, issue_date, due_date, return_date, status}`
- **Candidate Key:** `issue_id`.
- **Primary Key:** `issue_id`.

### 7. RESERVATION
- `reservation_id → {book_id, member_id, reserved_on, expires_on, queue_position, status}`
- `{book_id, member_id, reserved_on} → {reservation_id, expires_on, queue_position, status}`
- **Candidate Keys:** `reservation_id`, `{book_id, member_id, reserved_on}`.
- **Primary Key:** `reservation_id`.

### 8. FINE
- `fine_id → {issue_id, member_id, days_overdue, fine_amount, fine_date, payment_status, paid_on, payment_method, transaction_ref}`
- `issue_id → {fine_id, member_id, days_overdue, fine_amount, fine_date, payment_status, paid_on, payment_method, transaction_ref}`
- `transaction_ref → {fine_id, issue_id, member_id, days_overdue, fine_amount, fine_date, payment_status, paid_on, payment_method}` (when not null)
- **Candidate Keys:** `fine_id`, `issue_id`.
- **Primary Key:** `fine_id`.

---

## 2. Normalization Steps

### First Normal Form (1NF)
1. **Atomicity:** All attributes contain single atomic values (no repeating groups or multi-valued attributes like multiple phone numbers or author arrays).
2. **Explicit Primary Keys:** Every table is uniquely identifiable by an unambiguous integer primary key.
3. **Domain Integrity:** Strict constraints ensure valid values across domain sets (e.g. member types, statuses).

### Second Normal Form (2NF)
1. **Elimination of Partial Dependencies:** In all 8 tables, every non-prime attribute is fully functionally dependent on the entire primary key.
2. Since all primary keys except composite candidate keys are single-attribute integer identifiers, no partial functional dependencies exist:
   $$\forall (X \to Y), \quad X \text{ is not a proper subset of any candidate key.}$$

### Third Normal Form (3NF)
1. **Elimination of Transitive Dependencies:** No non-prime attribute is transitively dependent on the primary key via another non-prime attribute:
   $$\forall (X \to Y), \quad X \text{ is a superkey OR } Y \text{ is a prime attribute.}$$
2. Examples of Transitive Dependency prevention:
   - Category names and shelf zones are maintained in `CATEGORY` rather than duplicated inside `BOOK`.
   - Author biographical details are stored in `AUTHOR`, preventing modification anomalies in `BOOK`.
   - Member departments and contact details are stored in `MEMBER`, referencing issues via foreign keys.
   - Staff designation and shift schedules reside in `LIBRARIAN`, preventing update anomalies on checkout logs.

---

## 3. Controlled Denormalization Justification

### Attribute: `BOOK.available_copies`
- **Strict Normalized Form:** In pure 3NF, the available stock can theoretically be derived dynamically via:
  $$\text{available\_copies} = \text{total\_copies} - \sum [\text{ISSUE\_TRANSACTION.status} = \text{'Issued'}]$$
- **Engine Performance & ACID Justification:**
  1. **High-Frequency Read Throughput:** The catalog table is queried hundreds of times per minute by patrons browsing titles, searching by author, and filtering categories. Calculating an aggregate `COUNT(*)` over a potentially million-row `ISSUE_TRANSACTION` table on every catalog read introduces unacceptable $O(N)$ query latency.
  2. **Race-Condition & Over-Issue Prevention:** Storing `available_copies` on the `BOOK` record allows atomic row-level locking and instantaneous trigger validation (`trg_prevent_issue_no_stock`).
  3. **Strict Invariant Maintenance via Triggers:** The integrity of this column is safeguarded through native database triggers (`trg_issue_decrement_stock` and `trg_return_increment_stock`), ensuring zero divergence between stored state and transactional reality.
