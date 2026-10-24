# LibraCore — Relational Database Schema Data Dictionary

**Course:** BCSE302P – Database Systems Lab  
**Institution:** Vellore Institute of Technology (VIT)  
**Database Engine:** SQLite 3 (ACID, Foreign Keys Enforced, Native Triggers)  
**Emulation & Architecture:** Oracle PL/SQL Specification  

---

## 1. Relational Entities Summary

| # | Entity Name | Primary Key | Description |
|---|---|---|---|
| 1 | `CATEGORY` | `category_id` | Subject classification, DDC genres, and shelf zones |
| 2 | `AUTHOR` | `author_id` | Book creators, bio information, and nationalities |
| 3 | `LIBRARIAN` | `librarian_id` | Circulation staff, administrators, and shift schedules |
| 4 | `BOOK` | `book_id` | Catalog titles, ISBNs, prices, shelf locations, and copies |
| 5 | `MEMBER` | `member_id` | Registered library patrons (Students, Faculty, Staff) |
| 6 | `ISSUE_TRANSACTION` | `issue_id` | Book circulation checkout, due dates, and return records |
| 7 | `RESERVATION` | `reservation_id` | FIFO waitlist queues for out-of-stock titles |
| 8 | `FINE` | `fine_id` | Late return penalty ledgers, dues, and payment vouchers |

---

## 2. Detailed Data Dictionary

### Table 1: `CATEGORY`
| Column | Data Type | Size | Constraints | Description |
|---|---|---|---|---|
| `category_id` | INTEGER | - | PRIMARY KEY | Unique classification identifier (101+) |
| `category_name` | VARCHAR | 80 | NOT NULL, UNIQUE | Human-readable genre/subject name |
| `category_code` | VARCHAR | 10 | NOT NULL, UNIQUE | Standard abbreviation (e.g., CS-AI, DB-SYS) |
| `shelf_zone` | VARCHAR | 20 | NOT NULL | Physical library wing/zone (Zone A to J) |
| `description` | VARCHAR | 200 | DEFAULT 'General collection' | Scope of collection |

### Table 2: `AUTHOR`
| Column | Data Type | Size | Constraints | Description |
|---|---|---|---|---|
| `author_id` | INTEGER | - | PRIMARY KEY | Unique author sequence identifier (201+) |
| `first_name` | VARCHAR | 50 | NOT NULL | Author forename |
| `last_name` | VARCHAR | 50 | NOT NULL | Author surname |
| `email` | VARCHAR | 100 | UNIQUE | Author academic/professional email |
| `nationality` | VARCHAR | 50 | NOT NULL, DEFAULT 'Indian' | Author citizenship |
| `birth_year` | INTEGER | - | CHECK (birth_year BETWEEN 1500 AND 2010) | Historical birth year |

### Table 3: `LIBRARIAN`
| Column | Data Type | Size | Constraints | Description |
|---|---|---|---|---|
| `librarian_id` | INTEGER | - | PRIMARY KEY | Staff personnel identifier (301+) |
| `first_name` | VARCHAR | 50 | NOT NULL | Staff given name |
| `last_name` | VARCHAR | 50 | NOT NULL | Staff family name |
| `email` | VARCHAR | 100 | NOT NULL, UNIQUE | Institutional email |
| `phone` | VARCHAR | 20 | NOT NULL, UNIQUE | Contact telephone number |
| `hire_date` | DATE | - | NOT NULL | Date appointed to library |
| `designation` | VARCHAR | 50 | NOT NULL, CHECK IN ('Head Librarian','Assistant Librarian','Library Clerk','Admin') | Official library rank |
| `salary` | DECIMAL | 10,2 | NOT NULL, CHECK (salary >= 20000) | Monthly compensation ledger |
| `shift` | VARCHAR | 20 | NOT NULL, DEFAULT 'Morning', CHECK IN ('Morning','Evening') | Operational duty shift |

### Table 4: `BOOK`
| Column | Data Type | Size | Constraints | Description |
|---|---|---|---|---|
| `book_id` | INTEGER | - | PRIMARY KEY | Unique catalog title identifier (1001+) |
| `isbn` | VARCHAR | 20 | NOT NULL, UNIQUE | International Standard Book Number |
| `title` | VARCHAR | 150 | NOT NULL | Title of the volume |
| `author_id` | INTEGER | - | NOT NULL, FK → AUTHOR | Author foreign key reference |
| `category_id` | INTEGER | - | NOT NULL, FK → CATEGORY | Subject classification foreign key |
| `publisher` | VARCHAR | 100 | NOT NULL | Publishing house |
| `publish_date` | DATE | - | NOT NULL | Original publication date |
| `edition` | VARCHAR | 20 | DEFAULT '1st' | Edition string |
| `language` | VARCHAR | 30 | DEFAULT 'English' | Publication language |
| `shelf_location` | VARCHAR | 30 | NOT NULL | Physical rack and row (e.g. A-01-04) |
| `price` | DECIMAL | 8,2 | NOT NULL, CHECK (price > 0) | Book replacement cost (INR) |
| `total_copies` | INTEGER | - | NOT NULL, DEFAULT 1, CHECK (total_copies >= 1) | Total copies owned |
| `available_copies` | INTEGER | - | NOT NULL, CHECK (available_copies >= 0 AND available_copies <= total_copies) | Copies currently in stock |
| `cover_url` | VARCHAR | 300 | NULL | Remote URL to book cover graphic |
| `added_on` | DATE | - | NOT NULL, DEFAULT CURRENT_DATE | Date cataloged into LMS |
| `status` | VARCHAR | 20 | NOT NULL, DEFAULT 'Active', CHECK IN ('Active','Archived') | Title circulation status |

### Table 5: `MEMBER`
| Column | Data Type | Size | Constraints | Description |
|---|---|---|---|---|
| `member_id` | INTEGER | - | PRIMARY KEY | Patron primary key (2001+) |
| `member_code` | VARCHAR | 20 | NOT NULL, UNIQUE | University Registration / Employee ID |
| `first_name` | VARCHAR | 50 | NOT NULL | Patron forename |
| `last_name` | VARCHAR | 50 | NOT NULL | Patron surname |
| `email` | VARCHAR | 100 | NOT NULL, UNIQUE | Institutional email |
| `phone` | VARCHAR | 20 | NOT NULL, UNIQUE | Mobile contact number |
| `member_type` | VARCHAR | 20 | NOT NULL, CHECK IN ('Student','Faculty','Staff') | Institutional category |
| `department` | VARCHAR | 60 | NOT NULL | Departmental affiliation |
| `join_date` | DATE | - | NOT NULL | Membership inception date |
| `membership_expiry` | DATE | - | NOT NULL | Expiry date of library privileges |
| `max_books_allowed` | INTEGER | - | NOT NULL, DEFAULT 3, CHECK BETWEEN 1 AND 10 | Max simultaneous loan quota |
| `status` | VARCHAR | 20 | NOT NULL, DEFAULT 'Active', CHECK IN ('Active','Suspended','Expired') | Circulation eligibility state |

### Table 6: `ISSUE_TRANSACTION`
| Column | Data Type | Size | Constraints | Description |
|---|---|---|---|---|
| `issue_id` | INTEGER | - | PRIMARY KEY | Circulation transaction ID (5001+) |
| `book_id` | INTEGER | - | NOT NULL, FK → BOOK | Loaned volume reference |
| `member_id` | INTEGER | - | NOT NULL, FK → MEMBER | Borrower patron reference |
| `librarian_id` | INTEGER | - | NOT NULL, FK → LIBRARIAN | Approving staff reference |
| `issue_date` | DATE | - | NOT NULL, DEFAULT CURRENT_DATE | Date book was checked out |
| `due_date` | DATE | - | NOT NULL, CHECK (due_date > issue_date) | Date book must be returned |
| `return_date` | DATE | - | NULL, CHECK (return_date IS NULL OR return_date >= issue_date) | Actual check-in date |
| `status` | VARCHAR | 20 | NOT NULL, DEFAULT 'Issued', CHECK IN ('Issued','Returned','Lost') | Transaction lifecycle state |

### Table 7: `RESERVATION`
| Column | Data Type | Size | Constraints | Description |
|---|---|---|---|---|
| `reservation_id` | INTEGER | - | PRIMARY KEY | Waitlist ticket ID (6001+) |
| `book_id` | INTEGER | - | NOT NULL, FK → BOOK | Out-of-stock book reference |
| `member_id` | INTEGER | - | NOT NULL, FK → MEMBER | Requesting patron reference |
| `reserved_on` | DATE | - | NOT NULL, DEFAULT CURRENT_DATE | Date reservation was logged |
| `expires_on` | DATE | - | NOT NULL | Hold release expiration date |
| `queue_position` | INTEGER | - | NOT NULL, CHECK (queue_position > 0) | FIFO queue placement |
| `status` | VARCHAR | 20 | NOT NULL, DEFAULT 'Waiting', CHECK IN ('Waiting','Fulfilled','Cancelled','Expired') | Waitlist resolution state |

### Table 8: `FINE`
| Column | Data Type | Size | Constraints | Description |
|---|---|---|---|---|
| `fine_id` | INTEGER | - | PRIMARY KEY | Penalty voucher ID (7001+) |
| `issue_id` | INTEGER | - | NOT NULL, UNIQUE, FK → ISSUE_TRANSACTION | Reference to overdue loan |
| `member_id` | INTEGER | - | NOT NULL, FK → MEMBER | Patron liable for fee |
| `days_overdue` | INTEGER | - | NOT NULL, CHECK (days_overdue > 0) | Days elapsed past due date |
| `fine_amount` | DECIMAL | 8,2 | NOT NULL, CHECK (fine_amount > 0) | Computed penalty (capped at book price) |
| `fine_date` | DATE | - | NOT NULL, DEFAULT CURRENT_DATE | Date fine was assessed |
| `payment_status` | VARCHAR | 20 | NOT NULL, DEFAULT 'Pending', CHECK IN ('Pending','Paid','Waived') | Settlement status |
| `paid_on` | DATE | - | NULL | Date payment was settled |
| `payment_method` | VARCHAR | 30 | NULL, CHECK IN ('UPI','Cash','Credit Card','Debit Card','Net Banking') | Payment gateway channel |
| `transaction_ref` | VARCHAR | 50 | UNIQUE, NULL | Bank/gateway voucher code |
