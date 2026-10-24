-- ============================================================================
-- LibraCore — Library Management System
-- Database Systems Lab (BCSE302P) — Relational Schema Definition
-- 8 Normalized Tables with Primary, Foreign Keys, and Strict Integrity Constraints
-- ============================================================================

DROP TABLE IF EXISTS FINE;
DROP TABLE IF EXISTS RESERVATION;
DROP TABLE IF EXISTS ISSUE_TRANSACTION;
DROP TABLE IF EXISTS BOOK;
DROP TABLE IF EXISTS MEMBER;
DROP TABLE IF EXISTS LIBRARIAN;
DROP TABLE IF EXISTS AUTHOR;
DROP TABLE IF EXISTS CATEGORY;

-- 1. CATEGORY: Subject genres, classifications, and library zone mapping
CREATE TABLE CATEGORY (
    category_id     INTEGER PRIMARY KEY,
    category_name   VARCHAR(80)  NOT NULL UNIQUE,
    category_code   VARCHAR(10)  NOT NULL UNIQUE,
    shelf_zone      VARCHAR(20)  NOT NULL,
    description     VARCHAR(200) DEFAULT 'General collection'
);

-- 2. AUTHOR: Book creators and literary information
CREATE TABLE AUTHOR (
    author_id       INTEGER PRIMARY KEY,
    first_name      VARCHAR(50)  NOT NULL,
    last_name       VARCHAR(50)  NOT NULL,
    email           VARCHAR(100) UNIQUE,
    nationality     VARCHAR(50)  NOT NULL DEFAULT 'Indian',
    birth_year      INTEGER      CHECK (birth_year BETWEEN 1500 AND 2010)
);

-- 3. LIBRARIAN: Library circulation and administrative personnel
CREATE TABLE LIBRARIAN (
    librarian_id    INTEGER PRIMARY KEY,
    first_name      VARCHAR(50)  NOT NULL,
    last_name       VARCHAR(50)  NOT NULL,
    email           VARCHAR(100) NOT NULL UNIQUE,
    phone           VARCHAR(20)  NOT NULL UNIQUE,
    hire_date       DATE         NOT NULL,
    designation     VARCHAR(50)  NOT NULL CHECK (designation IN ('Head Librarian', 'Assistant Librarian', 'Library Clerk', 'Admin')),
    salary          DECIMAL(10,2) NOT NULL CHECK (salary >= 20000),
    shift           VARCHAR(20)  NOT NULL DEFAULT 'Morning' CHECK (shift IN ('Morning', 'Evening'))
);

-- 4. BOOK: Catalog titles, metadata, pricing, shelf locations, and stock counts
CREATE TABLE BOOK (
    book_id          INTEGER PRIMARY KEY,
    isbn             VARCHAR(20)   NOT NULL UNIQUE,
    title            VARCHAR(150)  NOT NULL,
    author_id        INTEGER       NOT NULL,
    category_id      INTEGER       NOT NULL,
    publisher        VARCHAR(100)  NOT NULL,
    publish_date     DATE          NOT NULL,
    edition          VARCHAR(20)   DEFAULT '1st',
    language         VARCHAR(30)   DEFAULT 'English',
    shelf_location   VARCHAR(30)   NOT NULL,
    price            DECIMAL(8,2)  NOT NULL CHECK (price > 0),
    total_copies     INTEGER       NOT NULL DEFAULT 1 CHECK (total_copies >= 1),
    available_copies INTEGER       NOT NULL CHECK (available_copies >= 0 AND available_copies <= total_copies),
    cover_url        VARCHAR(300),
    added_on         DATE          NOT NULL DEFAULT CURRENT_DATE,
    status           VARCHAR(20)   NOT NULL DEFAULT 'Active' CHECK (status IN ('Active', 'Archived')),
    FOREIGN KEY (author_id)   REFERENCES AUTHOR(author_id)     ON DELETE RESTRICT,
    FOREIGN KEY (category_id) REFERENCES CATEGORY(category_id) ON DELETE RESTRICT
);

-- 5. MEMBER: Registered library patrons (Students, Faculty, Staff)
CREATE TABLE MEMBER (
    member_id          INTEGER PRIMARY KEY,
    member_code        VARCHAR(20)  NOT NULL UNIQUE,
    first_name         VARCHAR(50)  NOT NULL,
    last_name          VARCHAR(50)  NOT NULL,
    email              VARCHAR(100) NOT NULL UNIQUE,
    phone              VARCHAR(20)  NOT NULL UNIQUE,
    member_type        VARCHAR(20)  NOT NULL CHECK (member_type IN ('Student', 'Faculty', 'Staff')),
    department         VARCHAR(60)  NOT NULL,
    join_date          DATE         NOT NULL,
    membership_expiry  DATE         NOT NULL,
    max_books_allowed  INTEGER      NOT NULL DEFAULT 3 CHECK (max_books_allowed BETWEEN 1 AND 10),
    status             VARCHAR(20)  NOT NULL DEFAULT 'Active' CHECK (status IN ('Active', 'Suspended', 'Expired'))
);

-- 6. ISSUE_TRANSACTION: Circulation loans of books to members
CREATE TABLE ISSUE_TRANSACTION (
    issue_id        INTEGER PRIMARY KEY,
    book_id         INTEGER     NOT NULL,
    member_id       INTEGER     NOT NULL,
    librarian_id    INTEGER     NOT NULL,
    issue_date      DATE        NOT NULL DEFAULT CURRENT_DATE,
    due_date        DATE        NOT NULL CHECK (due_date > issue_date),
    return_date     DATE        NULL CHECK (return_date IS NULL OR return_date >= issue_date),
    status          VARCHAR(20) NOT NULL DEFAULT 'Issued' CHECK (status IN ('Issued', 'Returned', 'Lost')),
    FOREIGN KEY (book_id)      REFERENCES BOOK(book_id)           ON DELETE RESTRICT,
    FOREIGN KEY (member_id)    REFERENCES MEMBER(member_id)       ON DELETE RESTRICT,
    FOREIGN KEY (librarian_id) REFERENCES LIBRARIAN(librarian_id) ON DELETE RESTRICT
);

-- 7. RESERVATION: Waiting queue for out-of-stock titles
CREATE TABLE RESERVATION (
    reservation_id  INTEGER PRIMARY KEY,
    book_id         INTEGER     NOT NULL,
    member_id       INTEGER     NOT NULL,
    reserved_on     DATE        NOT NULL DEFAULT CURRENT_DATE,
    expires_on      DATE        NOT NULL,
    queue_position  INTEGER     NOT NULL CHECK (queue_position > 0),
    status          VARCHAR(20) NOT NULL DEFAULT 'Waiting' CHECK (status IN ('Waiting', 'Fulfilled', 'Cancelled', 'Expired')),
    UNIQUE(book_id, member_id, reserved_on),
    FOREIGN KEY (book_id)   REFERENCES BOOK(book_id)     ON DELETE RESTRICT,
    FOREIGN KEY (member_id) REFERENCES MEMBER(member_id) ON DELETE RESTRICT
);

-- 8. FINE: Penalties for overdue loans and fee remittance records
CREATE TABLE FINE (
    fine_id         INTEGER PRIMARY KEY,
    issue_id        INTEGER       NOT NULL UNIQUE,
    member_id       INTEGER       NOT NULL,
    days_overdue    INTEGER       NOT NULL CHECK (days_overdue > 0),
    fine_amount     DECIMAL(8,2)  NOT NULL CHECK (fine_amount > 0),
    fine_date       DATE          NOT NULL DEFAULT CURRENT_DATE,
    payment_status  VARCHAR(20)   NOT NULL DEFAULT 'Pending' CHECK (payment_status IN ('Pending', 'Paid', 'Waived')),
    paid_on         DATE          NULL,
    payment_method  VARCHAR(30)   NULL CHECK (payment_method IN ('UPI', 'Cash', 'Credit Card', 'Debit Card', 'Net Banking')),
    transaction_ref VARCHAR(50)   UNIQUE NULL,
    FOREIGN KEY (issue_id)  REFERENCES ISSUE_TRANSACTION(issue_id) ON DELETE RESTRICT,
    FOREIGN KEY (member_id) REFERENCES MEMBER(member_id)           ON DELETE RESTRICT
);
