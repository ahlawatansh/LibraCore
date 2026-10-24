import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_manager import get_connection, initialize_database

QUERIES = [
    {
        'id': 'Q1',
        'title': 'Recent Catalog Additions (WHERE + ORDER BY)',
        'sql': """
            SELECT book_id, isbn, title, publisher, publish_date, price, added_on
            FROM BOOK
            WHERE added_on >= date('now', '-30 days') AND status = 'Active'
            ORDER BY added_on DESC, title ASC;
        """
    },
    {
        'id': 'Q2',
        'title': 'Books with Author Details (Two-Table INNER JOIN)',
        'sql': """
            SELECT b.book_id, b.isbn, b.title, 
                   a.first_name || ' ' || a.last_name AS author_name,
                   a.nationality, b.shelf_location, b.price
            FROM BOOK b
            INNER JOIN AUTHOR a ON b.author_id = a.author_id
            ORDER BY a.last_name ASC, b.title ASC;
        """
    },
    {
        'id': 'Q3',
        'title': 'Catalog Classification Matrix (Three-Table INNER JOIN)',
        'sql': """
            SELECT b.book_id, b.title, 
                   a.first_name || ' ' || a.last_name AS author_name,
                   c.category_name, c.shelf_zone, b.shelf_location,
                   b.available_copies || ' / ' || b.total_copies AS stock_ratio
            FROM BOOK b
            INNER JOIN AUTHOR a ON b.author_id = a.author_id
            INNER JOIN CATEGORY c ON b.category_id = c.category_id
            ORDER BY c.shelf_zone ASC, b.title ASC;
        """
    },
    {
        'id': 'Q4',
        'title': 'Circulation Audit Trail (Four-Table INNER JOIN)',
        'sql': """
            SELECT i.issue_id, m.member_code, 
                   m.first_name || ' ' || m.last_name AS member_name,
                   b.title AS book_title,
                   l.first_name || ' ' || l.last_name AS issued_by_librarian,
                   i.issue_date, i.due_date, i.return_date, i.status
            FROM ISSUE_TRANSACTION i
            INNER JOIN MEMBER m ON i.member_id = m.member_id
            INNER JOIN BOOK b ON i.book_id = b.book_id
            INNER JOIN LIBRARIAN l ON i.librarian_id = l.librarian_id
            ORDER BY i.issue_date DESC;
        """
    },
    {
        'id': 'Q5',
        'title': 'Uncirculated Catalog Inventory (LEFT JOIN for Zero Issues)',
        'sql': """
            SELECT b.book_id, b.isbn, b.title, c.category_name, b.total_copies, b.price
            FROM BOOK b
            INNER JOIN CATEGORY c ON b.category_id = c.category_id
            LEFT JOIN ISSUE_TRANSACTION i ON b.book_id = i.book_id
            WHERE i.issue_id IS NULL
            ORDER BY b.book_id ASC;
        """
    },
    {
        'id': 'Q6',
        'title': 'Subject Collection Metrics (GROUP BY + COUNT + SUM + AVG)',
        'sql': """
            SELECT c.category_id, c.category_name, c.shelf_zone,
                   COUNT(b.book_id) AS title_count,
                   COALESCE(SUM(b.total_copies), 0) AS total_volumes,
                   COALESCE(SUM(b.available_copies), 0) AS available_volumes,
                   ROUND(AVG(b.price), 2) AS avg_title_price
            FROM CATEGORY c
            LEFT JOIN BOOK b ON c.category_id = b.category_id
            GROUP BY c.category_id, c.category_name, c.shelf_zone
            ORDER BY total_volumes DESC;
        """
    },
    {
        'id': 'Q7',
        'title': 'Prolific Authors with Multiple Titles (GROUP BY + HAVING >= 2)',
        'sql': """
            SELECT a.author_id, a.first_name || ' ' || a.last_name AS author_name,
                   a.nationality,
                   COUNT(b.book_id) AS total_books_cataloged,
                   ROUND(AVG(b.price), 2) AS avg_book_price
            FROM AUTHOR a
            INNER JOIN BOOK b ON a.author_id = b.author_id
            GROUP BY a.author_id, a.first_name, a.last_name, a.nationality
            HAVING COUNT(b.book_id) >= 2
            ORDER BY total_books_cataloged DESC, author_name ASC;
        """
    },
    {
        'id': 'Q8',
        'title': 'Revenue Breakdown by Payment Channel (AVG, MIN, MAX, SUM)',
        'sql': """
            SELECT COALESCE(payment_method, 'Unpaid') AS channel,
                   COUNT(fine_id) AS transaction_count,
                   ROUND(SUM(fine_amount), 2) AS total_collected,
                   ROUND(AVG(fine_amount), 2) AS avg_fine,
                   MIN(fine_amount) AS min_fine,
                   MAX(fine_amount) AS max_fine
            FROM FINE
            GROUP BY payment_method
            ORDER BY total_collected DESC;
        """
    },
    {
        'id': 'Q9',
        'title': 'Top-5 Most Borrowed Titles (Aggregation + LIMIT)',
        'sql': """
            SELECT b.book_id, b.title, 
                   a.first_name || ' ' || a.last_name AS author_name,
                   c.category_name,
                   COUNT(i.issue_id) AS total_times_borrowed,
                   b.available_copies || ' / ' || b.total_copies AS current_stock
            FROM BOOK b
            INNER JOIN AUTHOR a ON b.author_id = a.author_id
            INNER JOIN CATEGORY c ON b.category_id = c.category_id
            INNER JOIN ISSUE_TRANSACTION i ON b.book_id = i.book_id
            GROUP BY b.book_id, b.title, a.first_name, a.last_name, c.category_name, b.available_copies, b.total_copies
            ORDER BY total_times_borrowed DESC
            LIMIT 5;
        """
    },
    {
        'id': 'Q10',
        'title': 'Active Overdue Loans with Contact Details (Date Arithmetic)',
        'sql': """
            SELECT i.issue_id, b.title, m.member_code,
                   m.first_name || ' ' || m.last_name AS borrower_name,
                   m.email, m.phone, m.member_type,
                   i.issue_date, i.due_date,
                   CAST(julianday('now') - julianday(i.due_date) AS INTEGER) AS days_late,
                   CAST(julianday('now') - julianday(i.due_date) AS INTEGER) * 5.00 AS accrued_fine_estimate
            FROM ISSUE_TRANSACTION i
            INNER JOIN BOOK b ON i.book_id = b.book_id
            INNER JOIN MEMBER m ON i.member_id = m.member_id
            WHERE i.return_date IS NULL AND i.due_date < date('now')
            ORDER BY days_late DESC;
        """
    },
    {
        'id': 'Q11',
        'title': 'Member Outstanding Fines Ledger (SUM + CASE Statement)',
        'sql': """
            SELECT m.member_id, m.member_code, 
                   m.first_name || ' ' || m.last_name AS member_name,
                   m.member_type, m.status AS member_status,
                   COALESCE(SUM(CASE WHEN f.payment_status = 'Pending' THEN f.fine_amount ELSE 0 END), 0.0) AS pending_fines,
                   COALESCE(SUM(CASE WHEN f.payment_status = 'Paid' THEN f.fine_amount ELSE 0 END), 0.0) AS settled_fines,
                   CASE 
                       WHEN COALESCE(SUM(CASE WHEN f.payment_status = 'Pending' THEN f.fine_amount ELSE 0 END), 0.0) > 200.00 THEN 'Borrowing Blocked'
                       WHEN COALESCE(SUM(CASE WHEN f.payment_status = 'Pending' THEN f.fine_amount ELSE 0 END), 0.0) > 0.00 THEN 'Dues Pending'
                       ELSE 'Good Standing'
                   END AS account_standing
            FROM MEMBER m
            LEFT JOIN FINE f ON m.member_id = f.member_id
            GROUP BY m.member_id, m.member_code, m.first_name, m.last_name, m.member_type, m.status
            HAVING pending_fines > 0
            ORDER BY pending_fines DESC;
        """
    },
    {
        'id': 'Q12',
        'title': 'Highest Priced Catalog Volume (Nested Subquery with MAX)',
        'sql': """
            SELECT b.book_id, b.isbn, b.title, 
                   a.first_name || ' ' || a.last_name AS author_name,
                   c.category_name, b.price
            FROM BOOK b
            INNER JOIN AUTHOR a ON b.author_id = a.author_id
            INNER JOIN CATEGORY c ON b.category_id = c.category_id
            WHERE b.price = (
                SELECT MAX(price) FROM BOOK
            );
        """
    },
    {
        'id': 'Q13',
        'title': 'High Circulation Patrons Exceeding Peer Group Average (Correlated Subquery)',
        'sql': """
            SELECT m.member_id, m.member_code, 
                   m.first_name || ' ' || m.last_name AS member_name,
                   m.member_type, m.department,
                   COUNT(i.issue_id) AS total_borrowed
            FROM MEMBER m
            INNER JOIN ISSUE_TRANSACTION i ON m.member_id = i.member_id
            GROUP BY m.member_id, m.member_code, m.first_name, m.last_name, m.member_type, m.department
            HAVING COUNT(i.issue_id) > (
                SELECT AVG(inner_cnt)
                FROM (
                    SELECT COUNT(inner_i.issue_id) AS inner_cnt
                    FROM MEMBER inner_m
                    LEFT JOIN ISSUE_TRANSACTION inner_i ON inner_m.member_id = inner_i.member_id
                    WHERE inner_m.member_type = m.member_type
                    GROUP BY inner_m.member_id
                )
            )
            ORDER BY total_borrowed DESC;
        """
    },
    {
        'id': 'Q14',
        'title': 'Books in Technical Zones (Subquery with IN)',
        'sql': """
            SELECT b.book_id, b.title, b.shelf_location, b.price, c.category_name, c.shelf_zone
            FROM BOOK b
            INNER JOIN CATEGORY c ON b.category_id = c.category_id
            WHERE b.category_id IN (
                SELECT category_id 
                FROM CATEGORY 
                WHERE shelf_zone IN ('Zone A', 'Zone B', 'Zone C')
            )
            ORDER BY b.price DESC;
        """
    },
    {
        'id': 'Q15',
        'title': 'Catalog Titles Free of Waitlist Reservations (Subquery with NOT EXISTS)',
        'sql': """
            SELECT b.book_id, b.title, b.available_copies, b.total_copies, c.category_name
            FROM BOOK b
            INNER JOIN CATEGORY c ON b.category_id = c.category_id
            WHERE b.available_copies > 0
              AND NOT EXISTS (
                  SELECT 1 
                  FROM RESERVATION r 
                  WHERE r.book_id = b.book_id AND r.status = 'Waiting'
              )
            ORDER BY b.available_copies DESC;
        """
    },
    {
        'id': 'Q16',
        'title': 'All Engaged Patrons (Set Operation: UNION of Borrowers & Reservists)',
        'sql': """
            SELECT m.member_id, m.member_code, m.first_name || ' ' || m.last_name AS patron_name, 'Loan Recipient' AS engagement_type
            FROM MEMBER m
            WHERE m.member_id IN (SELECT DISTINCT member_id FROM ISSUE_TRANSACTION)
            UNION
            SELECT m.member_id, m.member_code, m.first_name || ' ' || m.last_name AS patron_name, 'Waitlist Subscriber' AS engagement_type
            FROM MEMBER m
            WHERE m.member_id IN (SELECT DISTINCT member_id FROM RESERVATION WHERE status = 'Waiting')
            ORDER BY member_code ASC;
        """
    },
    {
        'id': 'Q17',
        'title': 'Unutilized Registered Members (Set Operation: EXCEPT / NOT IN Equivalent)',
        'sql': """
            SELECT m.member_id, m.member_code, 
                   m.first_name || ' ' || m.last_name AS member_name,
                   m.member_type, m.department, m.join_date
            FROM MEMBER m
            WHERE m.status = 'Active'
              AND m.member_id NOT IN (
                  SELECT DISTINCT member_id FROM ISSUE_TRANSACTION
              )
            ORDER BY m.join_date ASC;
        """
    },
    {
        'id': 'Q18',
        'title': 'Monthly Circulation Velocity & Duration Trend (Date Functions + Aggregation)',
        'sql': """
            SELECT strftime('%Y-%m', issue_date) AS circulation_month,
                   COUNT(issue_id) AS total_loans_issued,
                   COUNT(return_date) AS total_returns_processed,
                   ROUND(AVG(
                       CASE 
                           WHEN return_date IS NOT NULL 
                           THEN julianday(return_date) - julianday(issue_date) 
                           ELSE NULL 
                       END
                   ), 1) AS avg_days_held
            FROM ISSUE_TRANSACTION
            GROUP BY strftime('%Y-%m', issue_date)
            ORDER BY circulation_month DESC;
        """
    }
]

def run_all_queries():
    initialize_database()
    conn = get_connection()
    cursor = conn.cursor()
    print('\n' + '=' * 80)
    print('          LIBRACORE — 18 RELATIONAL SQL QUERIES EXECUTION ENGINE')
    print('=' * 80)

    for item in QUERIES:
        print(f"\n[{item['id']}] {item['title']}")
        print('-' * 80)
        try:
            cursor.execute(item['sql'].strip())
            rows = cursor.fetchall()
            headers = [desc[0] for desc in cursor.description]
            table_data = [[r[h] for h in headers] for r in rows]

            col_widths = [
                max(len(str(h)), max((len(str(row[i])) for row in table_data), default=0))
                for i, h in enumerate(headers)
            ]
            header_line = ' | '.join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
            separator = '-+-'.join('-' * col_widths[i] for i in range(len(headers)))
            print(header_line)
            print(separator)
            for row in table_data:
                print(' | '.join(str(val).ljust(col_widths[i]) for i, val in enumerate(row)))
            print(f"Total Rows: {len(rows)}")
        except Exception as e:
            print(f"Execution Error: {e}")

    conn.close()
    print('\n' + '=' * 80)
    print(' Completed execution of all 18 SQL queries.')
    print('=' * 80 + '\n')

if __name__ == '__main__':
    run_all_queries()
