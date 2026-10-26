import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_manager import (
    initialize_database, get_connection,
    get_all_books, get_all_members, get_all_authors, get_all_categories,
    get_all_librarians, get_all_issues, get_all_reservations, get_all_fines,
    add_book, register_member, issue_book_proc, return_book_proc,
    reserve_book_proc, pay_fine_proc, generate_overdue_report_cursor,
    generate_member_activity_cursor
)
from demo_runner import run_all_transactions
from query_runner import run_all_queries

def print_header(title):
    print('\n' + '=' * 80)
    print(f" {title.center(78)} ")
    print('=' * 80)

def print_table(headers, rows):
    if not rows:
        print('  [No records found]')
        return
    col_widths = [
        max(len(str(h)), max((len(str(row[i])) for row in rows), default=0))
        for i, h in enumerate(headers)
    ]
    header_line = ' | '.join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    separator = '-+-'.join('-' * col_widths[i] for i in range(len(headers)))
    print(header_line)
    print(separator)
    for row in rows:
        print(' | '.join(str(val).ljust(col_widths[i]) for i, val in enumerate(row)))
    print(f"Total Records: {len(rows)}")

def handle_view_books():
    print_header("CATALOG INVENTORY")
    books = get_all_books()
    headers = ['ID', 'ISBN', 'TITLE', 'AUTHOR', 'CATEGORY', 'COPIES', 'PRICE', 'ZONE']
    rows = [
        [f"#{b['book_id']}", b['isbn'], b['title'][:32], b['author_name'][:18], b['category_code'], f"{b['available_copies']}/{b['total_copies']}", f"₹{b['price']}", b['shelf_zone']]
        for b in books
    ]
    print_table(headers, rows)

def handle_view_members():
    print_header("REGISTERED PATRON DIRECTORY")
    members = get_all_members()
    headers = ['ID', 'CODE', 'NAME', 'TYPE', 'DEPT', 'ACTIVE LOANS', 'DUES(₹)', 'STATUS']
    rows = [
        [m['member_id'], m['member_code'], m['full_name'][:20], m['member_type'], m['department'][:18], m['current_loans'], f"₹{m['pending_fines']:.2f}", m['status']]
        for m in members
    ]
    print_table(headers, rows)

def handle_issue_book():
    print_header("ISSUE BOOK (TRANSACTION)")
    try:
        book_id = int(input("Enter Book ID (e.g. 1001): ").strip())
        member_id = int(input("Enter Member ID (e.g. 2001): ").strip())
        librarians = get_all_librarians()
        print("\nAvailable Librarians:")
        for l in librarians:
            print(f"  {l['librarian_id']}: {l['first_name']} {l['last_name']} ({l['designation']})")
        lib_id = int(input("Select Librarian ID (default 301): ").strip() or "301")

        success, msg = issue_book_proc(book_id, member_id, lib_id)
        print('\n' + ('[*] ' if success else '[!] ') + msg)
    except Exception as e:
        print(f"[!] Input Error: {e}")

def handle_return_book():
    print_header("RETURN BOOK (TRANSACTION)")
    try:
        issues = get_all_issues(active_only=True)
        if not issues:
            print("No active loans to return.")
            return

        print("\nActive Loans:")
        for i in issues[:8]:
            overdue_tag = " [OVERDUE]" if i['is_overdue'] else ""
            print(f"  #{i['issue_id']}: '{i['book_title'][:25]}' -> {i['member_name']} (Due: {i['due_date']}){overdue_tag}")

        issue_id = int(input("\nEnter Issue ID to return: ").strip())
        success, msg = return_book_proc(issue_id)
        print('\n' + ('[*] ' if success else '[!] ') + msg)
    except Exception as e:
        print(f"[!] Input Error: {e}")

def handle_reserve_book():
    print_header("RESERVE OUT-OF-STOCK TITLE")
    try:
        book_id = int(input("Enter Book ID (must have 0 copies available): ").strip())
        member_id = int(input("Enter Member ID: ").strip())
        success, msg = reserve_book_proc(book_id, member_id)
        print('\n' + ('[*] ' if success else '[!] ') + msg)
    except Exception as e:
        print(f"[!] Input Error: {e}")

def handle_pay_fine():
    print_header("SETTLE OVERDUE FINE")
    try:
        fines = get_all_fines()
        pending = [f for f in fines if f['payment_status'] == 'Pending']
        if not pending:
            print("No outstanding fines found.")
            return

        print("\nOutstanding Fines:")
        for f in pending:
            print(f"  Fine #{f['fine_id']}: Patron {f['member_name']} ({f['member_code']}) | ₹{f['fine_amount']:.2f} | Overdue: {f['days_overdue']} days")

        fine_id = int(input("\nEnter Fine ID to settle: ").strip())
        print("Payment Methods: 1. UPI  2. Cash  3. Credit Card  4. Debit Card  5. Net Banking")
        m_choice = input("Select Method (1-5, default 1): ").strip()
        method_map = {'1': 'UPI', '2': 'Cash', '3': 'Credit Card', '4': 'Debit Card', '5': 'Net Banking'}
        method = method_map.get(m_choice, 'UPI')

        success, msg = pay_fine_proc(fine_id, method)
        print('\n' + ('[*] ' if success else '[!] ') + msg)
    except Exception as e:
        print(f"[!] Input Error: {e}")

def handle_overdue_audit():
    print_header("OVERDUE AUDIT REPORT (CURSOR)")
    records, summary = generate_overdue_report_cursor()
    headers = ['ISSUE', 'CODE', 'PATRON', 'BOOK TITLE', 'DAYS', 'FINE(₹)', 'SEVERITY']
    rows = [
        [f"#{r['issue_id']}", r['member_code'], r['member_name'][:18], r['book_title'][:22], r['days_late'], f"₹{r['projected_fine']:.2f}", r['severity']]
        for r in records
    ]
    print_table(headers, rows)
    print(f"\nSummary: {summary['total_overdue']} Overdue Loans | Projected Dues: ₹{summary['total_projected_fine']:,.2f}")
    print(f"  Minor (1-7 days): {summary['minor_count']} | Serious (8-30 days): {summary['serious_count']} | Critical (>30 days): {summary['critical_count']}")

def handle_member_activity():
    print_header("PATRON ENGAGEMENT AUDIT (CURSOR)")
    records, summary = generate_member_activity_cursor()
    headers = ['CODE', 'PATRON NAME', 'TYPE', 'TOTAL', 'ACTIVE', 'DUES(₹)', 'TIER']
    rows = [
        [r['member_code'], r['full_name'][:20], r['member_type'], r['total_loans'], r['active_loans'], f"₹{r['pending_fines']:.2f}", r['tier']]
        for r in records[:15]
    ]
    print_table(headers, rows)
    print(f"\nSummary: Total Members: {summary['total_members']} | Power Readers: {summary['power_readers']} | Regular: {summary['regular_readers']} | Inactive: {summary['inactive_patrons']}")

def main_menu():
    initialize_database()
    while True:
        print('\n' + '=' * 80)
        print("          LIBRACORE — LIBRARY MANAGEMENT SYSTEM (CLI CONSOLE)          ")
        print('=' * 80)
        print("  1.  View Catalog Inventory")
        print("  2.  View Patron Roster")
        print("  3.  Issue a Book (Issue_Book_Proc)")
        print("  4.  Return a Book (Return_Book_Proc)")
        print("  5.  Reserve an Out-of-Stock Title (Reserve_Book_Proc)")
        print("  6.  Settle an Overdue Fine (Pay_Fine_Proc)")
        print("  7.  Run Overdue Audit Report (Explicit Cursor)")
        print("  8.  Run Patron Engagement Audit (Explicit Cursor)")
        print("  9.  Execute All 18 Pre-compiled SQL Queries")
        print("  10. Run 8 End-to-End Real-World ACID Transactions")
        print("  11. Reset & Re-seed Database to Default State")
        print("  0.  Exit")
        print('=' * 80)

        choice = input("Enter choice (0-11): ").strip()
        if choice == '1':
            handle_view_books()
        elif choice == '2':
            handle_view_members()
        elif choice == '3':
            handle_issue_book()
        elif choice == '4':
            handle_return_book()
        elif choice == '5':
            handle_reserve_book()
        elif choice == '6':
            handle_pay_fine()
        elif choice == '7':
            handle_overdue_audit()
        elif choice == '8':
            handle_member_activity()
        elif choice == '9':
            run_all_queries()
        elif choice == '10':
            run_all_transactions()
        elif choice == '11':
            initialize_database(force_recreate=True)
            print("\n[*] Database successfully re-created and seeded with 120+ benchmark records.")
        elif choice == '0':
            print("\nExiting LibraCore CLI. Goodbye!\n")
            break
        else:
            print("\n[!] Invalid option. Please select 0-11.")

if __name__ == '__main__':
    main_menu()
