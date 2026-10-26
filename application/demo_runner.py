import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_manager import (
    initialize_database, get_connection,
    issue_book_proc, return_book_proc, reserve_book_proc, pay_fine_proc,
    calculate_fine_func, get_member_pending_fine_func,
    generate_overdue_report_cursor, generate_member_activity_cursor,
    delete_book, cancel_reservation
)

def run_all_transactions():
    initialize_database(force_recreate=True)
    print('\n' + '=' * 80)
    print('          LIBRACORE — 8 REAL-WORLD ACID TRANSACTIONS DEMO')
    print('=' * 80)

    # ------------------------------------------------------------------------
    # DEMO 1: Issue Book Successfully (Stock Decrements by Exactly 1)
    # ------------------------------------------------------------------------
    print('\n--- [1/8] Issue Book Successfully (Stock Decrements by Exactly 1) ---')
    book_id = 1007 # The Art of Computer Programming
    member_id = 2019 # Siddharth Nair (Active student, 0 loans)
    librarian_id = 301

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT title, total_copies, available_copies FROM BOOK WHERE book_id = ?;", (book_id,))
    b_title, tot_before, avail_before = c.fetchone()
    conn.close()

    print(f"Book: '{b_title}' | Stock Before: {avail_before}/{tot_before}")
    success, msg = issue_book_proc(book_id, member_id, librarian_id)
    print(f"Operation Result: {msg}")

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT available_copies FROM BOOK WHERE book_id = ?;", (book_id,))
    avail_after = c.fetchone()[0]
    c.execute("SELECT issue_id, issue_date, due_date, status FROM ISSUE_TRANSACTION WHERE book_id = ? AND member_id = ? AND status = 'Issued';", (book_id, member_id))
    issue_row = c.fetchone()
    conn.close()

    print(f"Stock After: {avail_after}/{tot_before} (Delta: {avail_after - avail_before})")
    print(f"Verified Issue in DB -> ID: #{issue_row[0]} | Due Date: {issue_row[2]} | Status: {issue_row[3]}")
    assert avail_after == avail_before - 1, f"FAIL: Expected stock {avail_before - 1}, got {avail_after}"
    print("ASSERTION PASSED: Stock decremented by EXACTLY 1 via database trigger trg_issue_decrement_stock.")

    # ------------------------------------------------------------------------
    # DEMO 2: Issue Rejection — Zero Available Stock
    # ------------------------------------------------------------------------
    print('\n--- [2/8] Issue Rejection — Out-of-Stock Title ---')
    book_id_zero = 1005 # Design Patterns (0 copies available)
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT title, available_copies FROM BOOK WHERE book_id = ?;", (book_id_zero,))
    b_title_zero, avail_zero = c.fetchone()
    c.execute("SELECT COUNT(*) FROM ISSUE_TRANSACTION;")
    issues_count_before = c.fetchone()[0]
    conn.close()

    print(f"Book: '{b_title_zero}' | Available Copies: {avail_zero}")
    success, msg = issue_book_proc(book_id_zero, 2004, 301)
    print(f"Operation Result: {msg}")
    assert not success, "FAIL: Checkout should have been rejected!"

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM ISSUE_TRANSACTION;")
    issues_count_after = c.fetchone()[0]
    conn.close()

    assert issues_count_after == issues_count_before, "FAIL: Database changed on rejected transaction!"
    print("ASSERTION PASSED: Transaction aborted cleanly; database remains untouched.")

    # ------------------------------------------------------------------------
    # DEMO 3: Issue Rejection — Suspended Patron Account / Limit Violation
    # ------------------------------------------------------------------------
    print('\n--- [3/8] Issue Rejection — Suspended Patron Account ---')
    suspended_member_id = 2017 # Gaurav Saxena (Suspended due to dues)
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT member_code, first_name || ' ' || last_name, status FROM MEMBER WHERE member_id = ?;", (suspended_member_id,))
    m_code, m_name, m_status = c.fetchone()
    conn.close()

    print(f"Patron: {m_name} ({m_code}) | Account Status: {m_status}")
    success, msg = issue_book_proc(1001, suspended_member_id, 301)
    print(f"Operation Result: {msg}")
    assert not success, "FAIL: Issue to suspended member should have been rejected!"
    print("ASSERTION PASSED: Institutional circulation block enforced for non-active members.")

    # ------------------------------------------------------------------------
    # DEMO 4: Return Book on Time (Restores Stock by Exactly 1, No Fine)
    # ------------------------------------------------------------------------
    print('\n--- [4/8] Return Book on Time (Stock Restored, No Fine) ---')
    issue_id_ontime = 5016 # Book 1001 issued to 2010, due in future
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT book_id FROM ISSUE_TRANSACTION WHERE issue_id = ?;", (issue_id_ontime,))
    ret_book_id = c.fetchone()[0]
    c.execute("SELECT available_copies, total_copies FROM BOOK WHERE book_id = ?;", (ret_book_id,))
    b_avail_pre, b_tot = c.fetchone()
    conn.close()

    print(f"Issue #{issue_id_ontime} (Book #{ret_book_id}) | Stock Before Return: {b_avail_pre}/{b_tot}")
    success, msg = return_book_proc(issue_id_ontime)
    print(f"Operation Result: {msg}")

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT available_copies FROM BOOK WHERE book_id = ?;", (ret_book_id,))
    b_avail_post = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM FINE WHERE issue_id = ?;", (issue_id_ontime,))
    fines_logged = c.fetchone()[0]
    conn.close()

    print(f"Stock After Return: {b_avail_post}/{b_tot} (Delta: +{b_avail_post - b_avail_pre})")
    assert b_avail_post == b_avail_pre + 1, "FAIL: Stock was not restored by 1!"
    assert fines_logged == 0, "FAIL: On-time return should not incur fines!"
    print("ASSERTION PASSED: Stock restored by EXACTLY 1 via trigger trg_return_increment_stock; zero fines logged.")

    # ------------------------------------------------------------------------
    # DEMO 5: Return Overdue Book with Automated Fine Assessment
    # ------------------------------------------------------------------------
    print('\n--- [5/8] Return Overdue Book (Automated Fine Assessment) ---')
    issue_id_late = 5021 # Book 1005 issued to 2001, 11 days overdue
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    SELECT i.due_date, b.title, b.price, m.first_name || ' ' || m.last_name
    FROM ISSUE_TRANSACTION i
    JOIN BOOK b ON i.book_id = b.book_id
    JOIN MEMBER m ON i.member_id = m.member_id
    WHERE i.issue_id = ?;
    """, (issue_id_late,))
    due_date, book_title, book_price, borrower = c.fetchone()
    conn.close()

    print(f"Issue #{issue_id_late}: '{book_title}' | Borrower: {borrower} | Due Date: {due_date}")
    success, msg = return_book_proc(issue_id_late)
    print(f"Operation Result: {msg}")

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT fine_id, days_overdue, fine_amount, payment_status FROM FINE WHERE issue_id = ?;", (issue_id_late,))
    fine_row = c.fetchone()
    conn.close()

    print(f"Fine Record in DB -> ID: #{fine_row[0]} | Overdue Days: {fine_row[1]} | Amount: ₹{fine_row[2]:,.2f} | Status: {fine_row[3]}")
    assert fine_row[2] > 0, "FAIL: Expected positive fine amount!"
    print("ASSERTION PASSED: Automated penalty correctly generated via Calculate_Fine_Func.")

    # ------------------------------------------------------------------------
    # DEMO 6: Reserve Out-of-Stock Catalog Title (Queue Sequencing)
    # ------------------------------------------------------------------------
    print('\n--- [6/8] Reserve Out-of-Stock Catalog Title ---')
    reserve_book_id = 1005 # Design Patterns (out of stock)
    reserve_member_id = 2008 # Tara Mukherjee

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COALESCE(MAX(queue_position), 0) FROM RESERVATION WHERE book_id = ? AND status = 'Waiting';", (reserve_book_id,))
    prev_pos = c.fetchone()[0]
    conn.close()

    print(f"Current Queue Depth for Book #{reserve_book_id}: {prev_pos}")
    success, msg = reserve_book_proc(reserve_book_id, reserve_member_id)
    print(f"Operation Result: {msg}")

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT reservation_id, queue_position, expires_on, status FROM RESERVATION WHERE book_id = ? AND member_id = ? AND status = 'Waiting';", (reserve_book_id, reserve_member_id))
    res_row = c.fetchone()
    conn.close()

    print(f"Verified Reservation -> ID: #{res_row[0]} | Queue Position: #{res_row[1]} | Expiry: {res_row[2]}")
    assert res_row[1] == prev_pos + 1, "FAIL: Queue position did not increment!"
    print("ASSERTION PASSED: Patron queued with next incremental position.")

    # ------------------------------------------------------------------------
    # DEMO 7: Settle Overdue Fine and Auto-Reactivate Member
    # ------------------------------------------------------------------------
    print('\n--- [7/8] Settle Overdue Fine & Patron Auto-Reactivation ---')
    suspended_member = 2017 # Suspended because fine 7010 was 570.00
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT status FROM MEMBER WHERE member_id = ?;", (suspended_member,))
    status_before = c.fetchone()[0]
    c.execute("SELECT fine_id, fine_amount, payment_status FROM FINE WHERE member_id = ? AND payment_status = 'Pending';", (suspended_member,))
    fine_to_pay = c.fetchone()
    conn.close()

    print(f"Member #{suspended_member} Status Before: {status_before} | Pending Fine: #{fine_to_pay[0]} (₹{fine_to_pay[1]:,.2f})")
    success, msg = pay_fine_proc(fine_to_pay[0], 'UPI', 'TXN_DEMO_7010_UPI')
    print(f"Operation Result: {msg}")

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT status FROM MEMBER WHERE member_id = ?;", (suspended_member,))
    status_after = c.fetchone()[0]
    conn.close()

    print(f"Member #{suspended_member} Status After Settlement: {status_after}")
    assert status_after == 'Active', f"FAIL: Expected member status 'Active', got '{status_after}'"
    print("ASSERTION PASSED: Member auto-reactivated to 'Active' via trigger trg_fine_paid_reactivate.")

    # ------------------------------------------------------------------------
    # DEMO 8: Relational Foreign Key Integrity Enforcement & Safe Cancellation
    # ------------------------------------------------------------------------
    print('\n--- [8/8] Relational Integrity (FK RESTRICT) & Waitlist Cancellation ---')
    # Attempting to delete Book 1001 which has loan history
    success, msg = delete_book(1001)
    print(f"Deletion Test on Referenced Book #1001: {msg}")
    assert not success, "FAIL: Deletion of referenced book should have been blocked!"
    print("Verified: ON DELETE RESTRICT prevented orphaned foreign key records.")

    # Safe cancellation of reservation
    cancel_success, cancel_msg = cancel_reservation(res_row[0])
    print(f"Reservation Cancellation: {cancel_msg}")
    assert cancel_success, "FAIL: Cancellation failed!"

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT status FROM RESERVATION WHERE reservation_id = ?;", (res_row[0],))
    canceled_status = c.fetchone()[0]
    conn.close()
    assert canceled_status == 'Cancelled', "FAIL: Status not updated to Cancelled!"
    print("ASSERTION PASSED: Reservation successfully marked as Cancelled.")

    print('\n' + '=' * 80)
    print(' ALL 8 REAL-WORLD ACID TRANSACTIONS VERIFIED & PASSED!')
    print('=' * 80 + '\n')

if __name__ == '__main__':
    run_all_transactions()
