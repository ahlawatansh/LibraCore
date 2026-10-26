import os
import sqlite3
from datetime import datetime, date

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'library_lms.db')
SQL_DDL_PATH = os.path.join(BASE_DIR, 'database', '01_create_tables.sql')
SQL_DML_PATH = os.path.join(BASE_DIR, 'database', '02_insert_data.sql')
SQL_TRIGGERS_PATH = os.path.join(BASE_DIR, 'database', '07b_triggers_sqlite.sql')

# Business Rule Constants
FINE_RATE_PER_DAY = 5.00
UNPAID_FINE_BLOCK_THRESHOLD = 200.00
AUTO_SUSPEND_THRESHOLD = 500.00
AUTO_REACTIVATE_THRESHOLD = 200.00

LOAN_DAYS_MAP = {
    'Student': 14,
    'Faculty': 30,
    'Staff': 21
}

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON;')
    return conn

def initialize_database(force_recreate=False):
    if force_recreate and os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except Exception:
            pass

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='BOOK';")
    exists = cursor.fetchone()[0]

    if exists == 0 or force_recreate:
        with open(SQL_DDL_PATH, 'r', encoding='utf-8') as f:
            cursor.executescript(f.read())
        with open(SQL_DML_PATH, 'r', encoding='utf-8') as f:
            cursor.executescript(f.read())
        with open(SQL_TRIGGERS_PATH, 'r', encoding='utf-8') as f:
            cursor.executescript(f.read())
        conn.commit()

    conn.close()
    return True

# ----------------------------------------------------------------------------
# Catalog & Entity Getters
# ----------------------------------------------------------------------------
def get_all_books(search=None, range_filter=None, sort=None):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
    SELECT 
        b.book_id, b.isbn, b.title, b.author_id, b.category_id,
        a.first_name || ' ' || a.last_name AS author_name,
        c.category_name, c.category_code, c.shelf_zone,
        b.publisher, b.publish_date, b.edition, b.language,
        b.shelf_location, b.price, b.total_copies, b.available_copies,
        b.cover_url, b.added_on, b.status
    FROM BOOK b
    JOIN AUTHOR a ON b.author_id = a.author_id
    JOIN CATEGORY c ON b.category_id = c.category_id
    WHERE 1=1
    """
    params = []
    if search:
        search_like = f"%{search.strip()}%"
        query += " AND (b.title LIKE ? OR a.first_name LIKE ? OR a.last_name LIKE ? OR b.isbn LIKE ?)"
        params.extend([search_like, search_like, search_like, search_like])

    if range_filter:
        rf = range_filter.lower()
        if rf in ('7', 'last 7 days'):
            query += " AND b.added_on >= date('now', '-7 days')"
        elif rf in ('30', 'last 30 days'):
            query += " AND b.added_on >= date('now', '-30 days')"
        elif rf in ('90', 'last 90 days'):
            query += " AND b.added_on >= date('now', '-90 days')"
        elif rf in ('year', 'this year', '365'):
            query += " AND b.added_on >= date('now', '-365 days')"

    if sort == 'title_asc':
        query += " ORDER BY b.title ASC"
    elif sort == 'title_desc':
        query += " ORDER BY b.title DESC"
    elif sort == 'id_asc':
        query += " ORDER BY b.book_id ASC"
    elif sort == 'date_desc':
        query += " ORDER BY b.publish_date DESC"
    else:
        query += " ORDER BY b.book_id ASC"

    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_book_by_id(book_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 
        b.*, 
        a.first_name || ' ' || a.last_name AS author_name,
        c.category_name, c.shelf_zone
    FROM BOOK b
    JOIN AUTHOR a ON b.author_id = a.author_id
    JOIN CATEGORY c ON b.category_id = c.category_id
    WHERE b.book_id = ?;
    """, (book_id,))
    res = cursor.fetchone()
    if not res:
        conn.close()
        return None
    book_dict = dict(res)

    # Fetch active borrowers
    cursor.execute("""
    SELECT i.issue_id, m.member_id, m.member_code, m.first_name || ' ' || m.last_name AS member_name,
           i.issue_date, i.due_date,
           CASE WHEN i.due_date < date('now') THEN 1 ELSE 0 END AS is_overdue
    FROM ISSUE_TRANSACTION i
    JOIN MEMBER m ON i.member_id = m.member_id
    WHERE i.book_id = ? AND i.status = 'Issued'
    ORDER BY i.due_date ASC;
    """, (book_id,))
    book_dict['current_borrowers'] = [dict(r) for r in cursor.fetchall()]

    # Fetch waiting reservations
    cursor.execute("""
    SELECT r.reservation_id, r.member_id, m.member_code, m.first_name || ' ' || m.last_name AS member_name,
           r.reserved_on, r.expires_on, r.queue_position
    FROM RESERVATION r
    JOIN MEMBER m ON r.member_id = m.member_id
    WHERE r.book_id = ? AND r.status = 'Waiting'
    ORDER BY r.queue_position ASC;
    """, (book_id,))
    book_dict['reservations'] = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return book_dict

def get_all_members(search=None, type_filter=None):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
    SELECT 
        m.member_id, m.member_code, 
        m.first_name, m.last_name,
        m.first_name || ' ' || m.last_name AS full_name,
        m.email, m.phone, m.member_type, m.department,
        m.join_date, m.membership_expiry, m.max_books_allowed, m.status,
        (
            SELECT COUNT(*) 
            FROM ISSUE_TRANSACTION i 
            WHERE i.member_id = m.member_id AND i.status = 'Issued'
        ) AS current_loans,
        (
            SELECT COALESCE(SUM(fine_amount), 0.0) 
            FROM FINE f 
            WHERE f.member_id = m.member_id AND f.payment_status = 'Pending'
        ) AS pending_fines
    FROM MEMBER m
    WHERE 1=1
    """
    params = []
    if search:
        search_like = f"%{search.strip()}%"
        query += " AND (m.member_code LIKE ? OR m.first_name LIKE ? OR m.last_name LIKE ? OR m.email LIKE ?)"
        params.extend([search_like, search_like, search_like, search_like])

    if type_filter and type_filter.lower() != 'all':
        query += " AND LOWER(m.member_type) = LOWER(?)"
        params.append(type_filter.strip())

    query += " ORDER BY m.member_id ASC;"
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_member_by_id(member_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM MEMBER WHERE member_id = ?;", (member_id,))
    res = cursor.fetchone()
    conn.close()
    return dict(res) if res else None

def get_member_summary(member_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM MEMBER WHERE member_id = ?;", (member_id,))
    m_row = cursor.fetchone()
    if not m_row:
        conn.close()
        return None
    member = dict(m_row)

    # Active loans
    cursor.execute("""
    SELECT i.issue_id, b.book_id, b.title, b.isbn, i.issue_date, i.due_date,
           CASE WHEN i.due_date < date('now') THEN 1 ELSE 0 END AS is_overdue,
           CASE 
               WHEN i.due_date < date('now') 
               THEN CAST(julianday('now') - julianday(i.due_date) AS INTEGER) 
               ELSE 0 
           END AS days_overdue
    FROM ISSUE_TRANSACTION i
    JOIN BOOK b ON i.book_id = b.book_id
    WHERE i.member_id = ? AND i.status = 'Issued'
    ORDER BY i.due_date ASC;
    """, (member_id,))
    active_loans = [dict(r) for r in cursor.fetchall()]

    # Loan history (all)
    cursor.execute("""
    SELECT i.issue_id, b.title, i.issue_date, i.due_date, i.return_date, i.status
    FROM ISSUE_TRANSACTION i
    JOIN BOOK b ON i.book_id = b.book_id
    WHERE i.member_id = ?
    ORDER BY i.issue_date DESC;
    """, (member_id,))
    loan_history = [dict(r) for r in cursor.fetchall()]

    # Fines
    cursor.execute("""
    SELECT f.fine_id, f.issue_id, b.title, f.days_overdue, f.fine_amount,
           f.fine_date, f.payment_status, f.paid_on, f.payment_method, f.transaction_ref
    FROM FINE f
    JOIN ISSUE_TRANSACTION i ON f.issue_id = i.issue_id
    JOIN BOOK b ON i.book_id = b.book_id
    WHERE f.member_id = ?
    ORDER BY f.fine_id DESC;
    """, (member_id,))
    fines = [dict(r) for r in cursor.fetchall()]

    # Reservations
    cursor.execute("""
    SELECT r.reservation_id, b.title, r.reserved_on, r.expires_on, r.queue_position, r.status,
           b.available_copies
    FROM RESERVATION r
    JOIN BOOK b ON r.book_id = b.book_id
    WHERE r.member_id = ?
    ORDER BY r.reserved_on DESC;
    """, (member_id,))
    reservations = [dict(r) for r in cursor.fetchall()]

    conn.close()

    pending_fine_total = sum(f['fine_amount'] for f in fines if f['payment_status'] == 'Pending')
    paid_fine_total = sum(f['fine_amount'] for f in fines if f['payment_status'] == 'Paid')

    return {
        'member': member,
        'active_loans': active_loans,
        'loan_history': loan_history,
        'fines': fines,
        'reservations': reservations,
        'pending_fines': pending_fine_total,
        'paid_fines': paid_fine_total,
        'total_borrowed': len(loan_history)
    }

def get_all_authors():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT a.*, COUNT(b.book_id) AS titles_count
    FROM AUTHOR a
    LEFT JOIN BOOK b ON a.author_id = b.author_id
    GROUP BY a.author_id
    ORDER BY a.author_id ASC;
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_all_categories():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT c.*, COUNT(b.book_id) AS titles_count,
           COALESCE(SUM(b.total_copies), 0) AS total_volumes,
           COALESCE(SUM(b.available_copies), 0) AS available_volumes
    FROM CATEGORY c
    LEFT JOIN BOOK b ON c.category_id = b.category_id
    GROUP BY c.category_id
    ORDER BY c.category_id ASC;
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_all_librarians():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT l.*, COUNT(i.issue_id) AS transactions_processed
    FROM LIBRARIAN l
    LEFT JOIN ISSUE_TRANSACTION i ON l.librarian_id = i.librarian_id
    GROUP BY l.librarian_id
    ORDER BY l.librarian_id ASC;
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_all_issues(active_only=False):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
    SELECT 
        i.issue_id, i.book_id, b.title AS book_title, b.isbn,
        i.member_id, m.member_code, m.first_name || ' ' || m.last_name AS member_name,
        m.email AS member_email, m.phone AS member_phone, m.member_type,
        i.librarian_id, l.first_name || ' ' || l.last_name AS librarian_name,
        i.issue_date, i.due_date, i.return_date, i.status,
        CASE 
            WHEN i.return_date IS NULL AND i.due_date < date('now') THEN 1 
            ELSE 0 
        END AS is_overdue,
        CASE 
            WHEN i.return_date IS NULL AND i.due_date < date('now') 
            THEN CAST(julianday('now') - julianday(i.due_date) AS INTEGER)
            ELSE 0 
        END AS days_overdue
    FROM ISSUE_TRANSACTION i
    JOIN BOOK b ON i.book_id = b.book_id
    JOIN MEMBER m ON i.member_id = m.member_id
    JOIN LIBRARIAN l ON i.librarian_id = l.librarian_id
    """
    if active_only:
        query += " WHERE i.status = 'Issued' ORDER BY i.due_date ASC;"
    else:
        query += " ORDER BY i.issue_id DESC;"

    cursor.execute(query)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_all_reservations():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 
        r.reservation_id, r.book_id, b.title AS book_title, b.isbn, b.available_copies,
        r.member_id, m.member_code, m.first_name || ' ' || m.last_name AS member_name,
        m.email AS member_email, m.phone AS member_phone,
        r.reserved_on, r.expires_on, r.queue_position, r.status,
        CASE WHEN b.available_copies > 0 AND r.status = 'Waiting' THEN 1 ELSE 0 END AS ready_for_pickup
    FROM RESERVATION r
    JOIN BOOK b ON r.book_id = b.book_id
    JOIN MEMBER m ON r.member_id = m.member_id
    ORDER BY r.reservation_id DESC;
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_all_fines():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 
        f.fine_id, f.issue_id, b.title AS book_title,
        f.member_id, m.member_code, m.first_name || ' ' || m.last_name AS member_name,
        f.days_overdue, f.fine_amount, f.fine_date, f.payment_status,
        f.paid_on, f.payment_method, f.transaction_ref
    FROM FINE f
    JOIN ISSUE_TRANSACTION i ON f.issue_id = i.issue_id
    JOIN BOOK b ON i.book_id = b.book_id
    JOIN MEMBER m ON f.member_id = m.member_id
    ORDER BY f.fine_id DESC;
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

# ----------------------------------------------------------------------------
# Procedural Mirrors (Exact PL/SQL Logic in Python)
# ----------------------------------------------------------------------------
def get_loan_days_func(member_type):
    return LOAN_DAYS_MAP.get(str(member_type).capitalize(), 14)

def calculate_fine_func(issue_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT i.due_date, i.return_date, b.price
    FROM ISSUE_TRANSACTION i
    JOIN BOOK b ON i.book_id = b.book_id
    WHERE i.issue_id = ?;
    """, (issue_id,))
    res = cursor.fetchone()
    conn.close()
    if not res:
        return 0.0

    due_str, ret_str, price = res['due_date'], res['return_date'], float(res['price'])
    due_date = datetime.strptime(due_str, '%Y-%m-%d').date()

    if ret_str:
        ret_date = datetime.strptime(ret_str, '%Y-%m-%d').date()
    else:
        ret_date = date.today()

    days_late = (ret_date - due_date).days
    if days_late <= 0:
        return 0.0

    fine = min(days_late * FINE_RATE_PER_DAY, price)
    return round(fine, 2)

def get_member_pending_fine_func(member_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT COALESCE(SUM(fine_amount), 0.0)
    FROM FINE
    WHERE member_id = ? AND payment_status = 'Pending';
    """, (member_id,))
    total = cursor.fetchone()[0] or 0.0
    conn.close()
    return round(total, 2)

def issue_book_proc(book_id, member_id, librarian_id):
    """
    Mirrors Issue_Book_Proc.
    Validates member and book, verifies quotas and dues, inserts ISSUE_TRANSACTION.
    NOTE: Stock decrement is handled by the SQLite trigger trg_issue_decrement_stock.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 1. Validate Member
        cursor.execute("SELECT first_name || ' ' || last_name, member_type, status, membership_expiry, max_books_allowed FROM MEMBER WHERE member_id = ?;", (member_id,))
        m_res = cursor.fetchone()
        if not m_res:
            return (False, f"VALIDATION REJECTION: Member ID {member_id} does not exist in library registry.")
        m_name, m_type, m_status, m_expiry, m_max = m_res[0], m_res[1], m_res[2], m_res[3], int(m_res[4])

        if m_status != 'Active':
            return (False, f"VALIDATION REJECTION: Member {m_name} account is {m_status}. Circulation suspended.")

        exp_date = datetime.strptime(m_expiry, '%Y-%m-%d').date()
        if exp_date < date.today():
            return (False, f"VALIDATION REJECTION: Membership expired on {m_expiry}. Renewal required.")

        # 2. Check pending dues
        cursor.execute("SELECT COALESCE(SUM(fine_amount), 0.0) FROM FINE WHERE member_id = ? AND payment_status = 'Pending';", (member_id,))
        pending_fines = cursor.fetchone()[0] or 0.0
        if pending_fines > UNPAID_FINE_BLOCK_THRESHOLD:
            return (False, f"VALIDATION REJECTION: Member has outstanding pending fines of ₹{pending_fines:,.2f} (> ₹{UNPAID_FINE_BLOCK_THRESHOLD:,.2f} threshold).")

        # 3. Check active loan limit
        cursor.execute("SELECT COUNT(*) FROM ISSUE_TRANSACTION WHERE member_id = ? AND status = 'Issued';", (member_id,))
        active_loans = cursor.fetchone()[0]
        if active_loans >= m_max:
            return (False, f"VALIDATION REJECTION: Member quota full ({active_loans}/{m_max} books currently borrowed).")

        # 4. Check duplicate active copy
        cursor.execute("SELECT COUNT(*) FROM ISSUE_TRANSACTION WHERE member_id = ? AND book_id = ? AND status = 'Issued';", (member_id, book_id))
        if cursor.fetchone()[0] > 0:
            return (False, f"VALIDATION REJECTION: Member already holds an active copy of book #{book_id}.")

        # 5. Validate Book Catalog Entry & Stock
        cursor.execute("SELECT title, status, available_copies FROM BOOK WHERE book_id = ?;", (book_id,))
        b_res = cursor.fetchone()
        if not b_res:
            return (False, f"VALIDATION REJECTION: Book ID {book_id} not found in catalog.")
        b_title, b_status, b_avail = b_res[0], b_res[1], int(b_res[2])

        if b_status != 'Active':
            return (False, f"VALIDATION REJECTION: Book '{b_title}' is Archived and unavailable for checkout.")

        if b_avail <= 0:
            return (False, f"CIRCULATION REJECTION: Zero available copies for book '{b_title}'. Reservation advised.")

        # 6. Compute due date
        loan_days = get_loan_days_func(m_type)
        cursor.execute("SELECT COALESCE(MAX(issue_id), 5000) + 1 FROM ISSUE_TRANSACTION;")
        new_issue_id = cursor.fetchone()[0]

        # 7. Insert Issue record (Trigger trg_issue_decrement_stock will decrement available_copies)
        cursor.execute("""
        INSERT INTO ISSUE_TRANSACTION (issue_id, book_id, member_id, librarian_id, issue_date, due_date, return_date, status)
        VALUES (?, ?, ?, ?, DATE('now'), DATE('now', ?), NULL, 'Issued');
        """, (new_issue_id, book_id, member_id, librarian_id, f"+{loan_days} days"))

        # 8. Mark reservation as Fulfilled if patron was waiting
        cursor.execute("""
        UPDATE RESERVATION
        SET status = 'Fulfilled'
        WHERE book_id = ? AND member_id = ? AND status = 'Waiting';
        """, (book_id, member_id))

        conn.commit()
        return (True, f"SUCCESS: Issue #{new_issue_id} confirmed. Book '{b_title}' issued to {m_name}. Loan period: {loan_days} days.")
    except Exception as e:
        conn.rollback()
        return (False, f"TRANSACTION FAILED: {str(e)}")
    finally:
        conn.close()

def return_book_proc(issue_id, return_date_str=None):
    """
    Mirrors Return_Book_Proc.
    Marks issue as Returned, stock increment handled by trigger trg_return_increment_stock.
    Computes fines and generates FINE record if overdue.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        SELECT i.book_id, i.member_id, i.status, i.due_date, b.title, b.price,
               m.first_name || ' ' || m.last_name AS member_name
        FROM ISSUE_TRANSACTION i
        JOIN BOOK b ON i.book_id = b.book_id
        JOIN MEMBER m ON i.member_id = m.member_id
        WHERE i.issue_id = ?;
        """, (issue_id,))
        row = cursor.fetchone()
        if not row:
            return (False, f"VALIDATION REJECTION: Issue record #{issue_id} not found.")

        book_id, member_id, status = row['book_id'], row['member_id'], row['status']
        due_str, title, price, member_name = row['due_date'], row['title'], float(row['price']), row['member_name']

        if status == 'Returned':
            return (False, f"VALIDATION REJECTION: Issue #{issue_id} for '{title}' is already returned.")

        ret_date = datetime.strptime(return_date_str, '%Y-%m-%d').date() if return_date_str else date.today()
        due_date = datetime.strptime(due_str, '%Y-%m-%d').date()

        # Update ISSUE_TRANSACTION (Trigger trg_return_increment_stock will increment available_copies)
        cursor.execute("""
        UPDATE ISSUE_TRANSACTION
        SET return_date = ?, status = 'Returned'
        WHERE issue_id = ?;
        """, (ret_date.strftime('%Y-%m-%d'), issue_id))

        days_late = (ret_date - due_date).days
        msg = ""

        if days_late > 0:
            fine_amount = round(min(days_late * FINE_RATE_PER_DAY, price), 2)
            cursor.execute("SELECT COALESCE(MAX(fine_id), 7000) + 1 FROM FINE;")
            new_fine_id = cursor.fetchone()[0]

            cursor.execute("""
            INSERT INTO FINE (fine_id, issue_id, member_id, days_overdue, fine_amount, fine_date, payment_status)
            VALUES (?, ?, ?, ?, ?, DATE('now'), 'Pending');
            """, (new_fine_id, issue_id, member_id, days_late, fine_amount))

            msg = f"RETURN PROCESSED (LATE): Book '{title}' returned by {member_name}. Overdue by {days_late} days. Fine of ₹{fine_amount:,.2f} logged (Fine ID #{new_fine_id})."
        else:
            msg = f"RETURN PROCESSED (ON TIME): Book '{title}' returned successfully by {member_name}. No dues accrued."

        conn.commit()
        return (True, msg)
    except Exception as e:
        conn.rollback()
        return (False, f"RETURN TRANSACTION FAILED: {str(e)}")
    finally:
        conn.close()

def reserve_book_proc(book_id, member_id):
    """
    Mirrors Reserve_Book_Proc.
    Enforces that reservations are only placed on out-of-stock titles (available_copies = 0).
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check Book stock
        cursor.execute("SELECT title, available_copies FROM BOOK WHERE book_id = ?;", (book_id,))
        b_res = cursor.fetchone()
        if not b_res:
            return (False, f"VALIDATION REJECTION: Book ID {book_id} does not exist.")
        title, avail = b_res[0], int(b_res[1])

        if avail > 0:
            return (False, f"RESERVATION REJECTION: Book '{title}' has {avail} copy available. Direct checkout permitted.")

        # Check Member
        cursor.execute("SELECT first_name || ' ' || last_name, status FROM MEMBER WHERE member_id = ?;", (member_id,))
        m_res = cursor.fetchone()
        if not m_res:
            return (False, f"VALIDATION REJECTION: Member ID {member_id} not found.")
        member_name, m_status = m_res[0], m_res[1]

        if m_status != 'Active':
            return (False, f"RESERVATION REJECTION: Member account is {m_status}.")

        # Check existing active reservation
        cursor.execute("SELECT COUNT(*) FROM RESERVATION WHERE book_id = ? AND member_id = ? AND status = 'Waiting';", (book_id, member_id))
        if cursor.fetchone()[0] > 0:
            return (False, f"RESERVATION REJECTION: Member {member_name} already has an active waitlist reservation for '{title}'.")

        # Check active borrowed copy
        cursor.execute("SELECT COUNT(*) FROM ISSUE_TRANSACTION WHERE book_id = ? AND member_id = ? AND status = 'Issued';", (book_id, member_id))
        if cursor.fetchone()[0] > 0:
            return (False, f"RESERVATION REJECTION: Member {member_name} currently holds a loaned copy of this book.")

        # Next queue position
        cursor.execute("SELECT COALESCE(MAX(queue_position), 0) + 1 FROM RESERVATION WHERE book_id = ? AND status = 'Waiting';", (book_id,))
        next_pos = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(MAX(reservation_id), 6000) + 1 FROM RESERVATION;")
        new_res_id = cursor.fetchone()[0]

        cursor.execute("""
        INSERT INTO RESERVATION (reservation_id, book_id, member_id, reserved_on, expires_on, queue_position, status)
        VALUES (?, ?, ?, DATE('now'), DATE('now', '+7 days'), ?, 'Waiting');
        """, (new_res_id, book_id, member_id, next_pos))

        conn.commit()
        return (True, f"RESERVATION CONFIRMED: Reservation #{new_res_id} placed for '{title}'. Member: {member_name}. Queue Position: #{next_pos}. Valid for 7 days.")
    except Exception as e:
        conn.rollback()
        return (False, f"RESERVATION FAILED: {str(e)}")
    finally:
        conn.close()

def pay_fine_proc(fine_id, payment_method, transaction_ref=None):
    """
    Mirrors Pay_Fine_Proc.
    Validates pending status, marks Paid, and triggers member auto-reactivation if dues drop <= 200.
    """
    valid_methods = ('UPI', 'Cash', 'Credit Card', 'Debit Card', 'Net Banking')
    if payment_method not in valid_methods:
        return (False, f"PAYMENT REJECTION: Invalid payment method '{payment_method}'. Allowed: {', '.join(valid_methods)}")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        SELECT f.fine_amount, f.payment_status, f.member_id, m.first_name || ' ' || m.last_name AS member_name
        FROM FINE f
        JOIN MEMBER m ON f.member_id = m.member_id
        WHERE f.fine_id = ?;
        """, (fine_id,))
        row = cursor.fetchone()
        if not row:
            return (False, f"PAYMENT REJECTION: Fine record #{fine_id} does not exist.")

        fine_amt, status, member_id, member_name = float(row['fine_amount']), row['payment_status'], row['member_id'], row['member_name']

        if status in ('Paid', 'Waived'):
            return (False, f"PAYMENT REJECTION: Fine #{fine_id} has already been settled ({status}).")

        if not transaction_ref:
            transaction_ref = f"TXN_LIB_{datetime.now().strftime('%Y%m%d%H%M%S')}_{fine_id}"

        # Check unique txn ref
        cursor.execute("SELECT COUNT(*) FROM FINE WHERE transaction_ref = ?;", (transaction_ref,))
        if cursor.fetchone()[0] > 0:
            return (False, f"PAYMENT REJECTION: Duplicate transaction reference '{transaction_ref}'.")

        # Update FINE (Trigger trg_fine_paid_reactivate will reactivate member if pending dues <= 200)
        cursor.execute("""
        UPDATE FINE
        SET payment_status = 'Paid',
            paid_on = DATE('now'),
            payment_method = ?,
            transaction_ref = ?
        WHERE fine_id = ?;
        """, (payment_method, transaction_ref, fine_id))

        conn.commit()
        return (True, f"RECEIPT ISSUED: Fine #{fine_id} of ₹{fine_amt:,.2f} settled by {member_name} via {payment_method}. Voucher: {transaction_ref}")
    except Exception as e:
        conn.rollback()
        return (False, f"PAYMENT FAILED: {str(e)}")
    finally:
        conn.close()

# ----------------------------------------------------------------------------
# Cursor Implementations
# ----------------------------------------------------------------------------
def generate_overdue_report_cursor():
    """
    Python implementation of Overdue_Report_Cursor.
    Traverses active overdue loans, categorizes risk severity, and aggregates dues.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT i.issue_id,
           m.member_id,
           m.member_code,
           m.first_name || ' ' || m.last_name AS member_name,
           m.email,
           m.phone,
           m.member_type,
           b.book_id,
           b.title AS book_title,
           b.price AS book_price,
           i.issue_date,
           i.due_date,
           CAST(julianday('now') - julianday(i.due_date) AS INTEGER) AS days_late
    FROM ISSUE_TRANSACTION i
    JOIN MEMBER m ON i.member_id = m.member_id
    JOIN BOOK b ON i.book_id = b.book_id
    WHERE i.return_date IS NULL AND i.due_date < date('now')
    ORDER BY days_late DESC;
    """)

    records = []
    total_projected = 0.0
    minor_count = 0
    serious_count = 0
    critical_count = 0

    for r in cursor.fetchall():
        row = dict(r)
        days = row['days_late']
        price = float(row['book_price'])
        fine = min(days * FINE_RATE_PER_DAY, price)
        total_projected += fine

        if days <= 7:
            severity = "Minor Overdue"
            minor_count += 1
        elif days <= 30:
            severity = "Serious Overdue"
            serious_count += 1
        else:
            severity = "Critical Overdue"
            critical_count += 1

        row['projected_fine'] = round(fine, 2)
        row['severity'] = severity
        records.append(row)

    conn.close()
    summary = {
        'total_overdue': len(records),
        'minor_count': minor_count,
        'serious_count': serious_count,
        'critical_count': critical_count,
        'total_projected_fine': round(total_projected, 2)
    }
    return records, summary

def generate_member_activity_cursor():
    """
    Python implementation of Member_Activity_Cursor.
    Iterates through patron records to analyze circulation velocity and dues.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT m.member_id,
           m.member_code,
           m.first_name || ' ' || m.last_name AS full_name,
           m.member_type,
           m.department,
           m.status,
           COUNT(i.issue_id) AS total_loans,
           SUM(CASE WHEN i.status = 'Issued' THEN 1 ELSE 0 END) AS active_loans,
           SUM(CASE WHEN i.status = 'Returned' THEN 1 ELSE 0 END) AS returned_loans,
           COALESCE(f.pending_amount, 0.0) AS pending_fines
    FROM MEMBER m
    LEFT JOIN ISSUE_TRANSACTION i ON m.member_id = i.member_id
    LEFT JOIN (
        SELECT member_id, SUM(fine_amount) AS pending_amount
        FROM FINE
        WHERE payment_status = 'Pending'
        GROUP BY member_id
    ) f ON m.member_id = f.member_id
    GROUP BY m.member_id, m.member_code, m.first_name, m.last_name, m.member_type, m.department, m.status, f.pending_amount
    ORDER BY total_loans DESC, pending_fines DESC;
    """)

    records = []
    power_count = 0
    regular_count = 0
    inactive_count = 0

    for r in cursor.fetchall():
        row = dict(r)
        loans = row['total_loans']
        if loans >= 4:
            tier = 'Power Reader'
            power_count += 1
        elif loans >= 1:
            tier = 'Regular Reader'
            regular_count += 1
        else:
            tier = 'Inactive Patron'
            inactive_count += 1

        row['tier'] = tier
        row['active_loans'] = row['active_loans'] or 0
        row['returned_loans'] = row['returned_loans'] or 0
        records.append(row)

    conn.close()
    summary = {
        'total_members': len(records),
        'power_readers': power_count,
        'regular_readers': regular_count,
        'inactive_patrons': inactive_count
    }
    return records, summary

# ----------------------------------------------------------------------------
# Master Data CRUD Handlers
# ----------------------------------------------------------------------------
def add_book(isbn, title, author_id, category_id, publisher, publish_date, edition, language, shelf_location, price, total_copies, cover_url=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COALESCE(MAX(book_id), 1000) + 1 FROM BOOK;")
        new_id = cursor.fetchone()[0]
        if not cover_url:
            clean_isbn = isbn.replace('-', '').strip()
            cover_url = f"https://covers.openlibrary.org/b/isbn/{clean_isbn}-M.jpg"

        cursor.execute("""
        INSERT INTO BOOK (
            book_id, isbn, title, author_id, category_id, publisher, publish_date,
            edition, language, shelf_location, price, total_copies, available_copies,
            cover_url, added_on, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, DATE('now'), 'Active');
        """, (new_id, isbn, title, author_id, category_id, publisher, publish_date,
              edition or '1st', language or 'English', shelf_location, price, total_copies, total_copies, cover_url))
        conn.commit()
        return (True, f"SUCCESS: Book #{new_id} '{title}' cataloged successfully.")
    except Exception as e:
        conn.rollback()
        return (False, f"FAILED TO ADD BOOK: {str(e)}")
    finally:
        conn.close()

def update_book(book_id, title, author_id, category_id, publisher, publish_date, edition, language, shelf_location, price, total_copies, status):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT total_copies, available_copies FROM BOOK WHERE book_id = ?;", (book_id,))
        cur_row = cursor.fetchone()
        if not cur_row:
            return (False, f"Book ID {book_id} not found.")

        old_tot, old_avail = cur_row[0], cur_row[1]
        borrowed = old_tot - old_avail
        if total_copies < borrowed:
            return (False, f"Cannot reduce total copies ({total_copies}) below currently borrowed copies ({borrowed}).")

        new_avail = total_copies - borrowed

        cursor.execute("""
        UPDATE BOOK
        SET title = ?, author_id = ?, category_id = ?, publisher = ?, publish_date = ?,
            edition = ?, language = ?, shelf_location = ?, price = ?, total_copies = ?,
            available_copies = ?, status = ?
        WHERE book_id = ?;
        """, (title, author_id, category_id, publisher, publish_date, edition, language,
              shelf_location, price, total_copies, new_avail, status, book_id))
        conn.commit()
        return (True, f"SUCCESS: Book #{book_id} '{title}' updated successfully.")
    except Exception as e:
        conn.rollback()
        return (False, f"UPDATE FAILED: {str(e)}")
    finally:
        conn.close()

def delete_book(book_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM BOOK WHERE book_id = ?;", (book_id,))
        conn.commit()
        return (True, f"SUCCESS: Book #{book_id} deleted from catalog.")
    except Exception as e:
        conn.rollback()
        return (False, f"DELETE FAILED: Restricted due to foreign key references in circulation loans/reservations. ({str(e)})")
    finally:
        conn.close()

def bulk_delete_books(book_ids):
    conn = get_connection()
    cursor = conn.cursor()
    deleted_count = 0
    errors = []
    try:
        for bid in book_ids:
            try:
                cursor.execute("DELETE FROM BOOK WHERE book_id = ?;", (bid,))
                deleted_count += 1
            except Exception as e:
                errors.append(f"Book #{bid}: {str(e)}")
        conn.commit()
        msg = f"Processed bulk deletion: {deleted_count} books deleted."
        if errors:
            msg += f" {len(errors)} failed due to active constraints."
        return (True, msg)
    except Exception as e:
        conn.rollback()
        return (False, f"BULK DELETE ABORTED: {str(e)}")
    finally:
        conn.close()

def register_member(member_code, first_name, last_name, email, phone, member_type, department, join_date=None, membership_expiry=None, max_books_allowed=3):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COALESCE(MAX(member_id), 2000) + 1 FROM MEMBER;")
        new_id = cursor.fetchone()[0]
        j_date = join_date or date.today().strftime('%Y-%m-%d')
        if not membership_expiry:
            expiry_date = date.today().replace(year=date.today().year + (2 if member_type == 'Faculty' else 1)).strftime('%Y-%m-%d')
        else:
            expiry_date = membership_expiry

        cursor.execute("""
        INSERT INTO MEMBER (
            member_id, member_code, first_name, last_name, email, phone,
            member_type, department, join_date, membership_expiry, max_books_allowed, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Active');
        """, (new_id, member_code, first_name, last_name, email, phone, member_type, department, j_date, expiry_date, max_books_allowed))
        conn.commit()
        return (True, f"SUCCESS: Member #{new_id} ({member_code}) registered successfully.")
    except Exception as e:
        conn.rollback()
        return (False, f"MEMBER REGISTRATION FAILED: {str(e)}")
    finally:
        conn.close()

def update_member_status(member_id, new_status):
    if new_status not in ('Active', 'Suspended', 'Expired'):
        return (False, "Invalid status.")
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE MEMBER SET status = ? WHERE member_id = ?;", (new_status, member_id))
        conn.commit()
        return (True, f"Member #{member_id} status updated to '{new_status}'.")
    except Exception as e:
        conn.rollback()
        return (False, f"STATUS UPDATE FAILED: {str(e)}")
    finally:
        conn.close()

def delete_member(member_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM MEMBER WHERE member_id = ?;", (member_id,))
        conn.commit()
        return (True, f"Member #{member_id} record deleted.")
    except Exception as e:
        conn.rollback()
        return (False, f"DELETE FAILED: Restricted by existing loan records or unsettled fines. ({str(e)})")
    finally:
        conn.close()

def add_author(first_name, last_name, email, nationality, birth_year):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COALESCE(MAX(author_id), 200) + 1 FROM AUTHOR;")
        new_id = cursor.fetchone()[0]
        cursor.execute("""
        INSERT INTO AUTHOR (author_id, first_name, last_name, email, nationality, birth_year)
        VALUES (?, ?, ?, ?, ?, ?);
        """, (new_id, first_name, last_name, email, nationality, birth_year))
        conn.commit()
        return (True, f"Author #{new_id} '{first_name} {last_name}' registered.")
    except Exception as e:
        conn.rollback()
        return (False, f"FAILED TO ADD AUTHOR: {str(e)}")
    finally:
        conn.close()

def add_category(category_name, category_code, shelf_zone, description):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COALESCE(MAX(category_id), 100) + 1 FROM CATEGORY;")
        new_id = cursor.fetchone()[0]
        cursor.execute("""
        INSERT INTO CATEGORY (category_id, category_name, category_code, shelf_zone, description)
        VALUES (?, ?, ?, ?, ?);
        """, (new_id, category_name, category_code, shelf_zone, description))
        conn.commit()
        return (True, f"Category #{new_id} '{category_name}' added.")
    except Exception as e:
        conn.rollback()
        return (False, f"FAILED TO ADD CATEGORY: {str(e)}")
    finally:
        conn.close()

def add_librarian(first_name, last_name, email, phone, hire_date, designation, salary, shift):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COALESCE(MAX(librarian_id), 300) + 1 FROM LIBRARIAN;")
        new_id = cursor.fetchone()[0]
        cursor.execute("""
        INSERT INTO LIBRARIAN (librarian_id, first_name, last_name, email, phone, hire_date, designation, salary, shift)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (new_id, first_name, last_name, email, phone, hire_date or date.today().strftime('%Y-%m-%d'), designation, salary, shift))
        conn.commit()
        return (True, f"Librarian #{new_id} '{first_name} {last_name}' onboarded.")
    except Exception as e:
        conn.rollback()
        return (False, f"FAILED TO ADD LIBRARIAN: {str(e)}")
    finally:
        conn.close()

def cancel_reservation(reservation_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE RESERVATION SET status = 'Cancelled' WHERE reservation_id = ?;", (reservation_id,))
        conn.commit()
        return (True, f"Reservation #{reservation_id} marked as Cancelled.")
    except Exception as e:
        conn.rollback()
        return (False, f"CANCELLATION FAILED: {str(e)}")
    finally:
        conn.close()
