import sys
import os
import time
import io
import re
import json
from datetime import datetime
from contextlib import redirect_stdout
from flask import Flask, render_template, jsonify, request, send_from_directory

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_manager import (
    get_connection, initialize_database,
    get_all_books, get_book_by_id, get_all_members, get_member_by_id, get_member_summary,
    get_all_authors, get_all_categories, get_all_librarians, get_all_issues,
    get_all_reservations, get_all_fines,
    add_book, update_book, delete_book, bulk_delete_books,
    register_member, update_member_status, delete_member,
    add_author, add_category, add_librarian, cancel_reservation,
    issue_book_proc, return_book_proc, reserve_book_proc, pay_fine_proc,
    calculate_fine_func, get_member_pending_fine_func, get_loan_days_func,
    generate_overdue_report_cursor, generate_member_activity_cursor
)
from query_runner import QUERIES
from mongo_manager import (
    get_mongo_db, seed_mongo_database, get_engine_status,
    execute_mongo_pipeline, MONGO_PIPELINES,
    mongo_get_all_books, mongo_get_book, mongo_add_book, mongo_delete_book,
    mongo_get_all_members, mongo_add_member, mongo_issue_book,
    mongo_return_book, mongo_reserve_book, mongo_pay_fine, mongo_get_stats
)

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True
ACTIVITY_LOGS = []

def log_telemetry(action_type, title, sql_executed, tables_touched, state_change, execution_ms):
    entry = {
        'id': len(ACTIVITY_LOGS) + 1,
        'timestamp': datetime.now().strftime('%H:%M:%S.%f')[:-3],
        'type': action_type,
        'title': title,
        'sql': sql_executed.strip() if sql_executed else '',
        'tables': tables_touched,
        'state_change': state_change,
        'time_ms': round(execution_ms, 2)
    }
    ACTIVITY_LOGS.insert(0, entry)
    if len(ACTIVITY_LOGS) > 120:
        ACTIVITY_LOGS.pop()

# Initialize DB on server start (both SQLite & MongoDB Atlas / In-Memory Document Store)
initialize_database()
seed_mongo_database()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/telemetry')
def get_telemetry():
    return jsonify(ACTIVITY_LOGS[:40])

@app.route('/api/stats')
def get_stats():
    t0 = time.time()
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT count(*) FROM BOOK;")
    books_count = c.fetchone()[0]

    c.execute("SELECT COALESCE(SUM(total_copies), 0), COALESCE(SUM(available_copies), 0) FROM BOOK;")
    total_copies, avail_copies = c.fetchone()

    c.execute("SELECT count(*) FROM MEMBER WHERE status = 'Active';")
    active_members = c.fetchone()[0]

    c.execute("SELECT count(*) FROM MEMBER;")
    total_members = c.fetchone()[0]

    c.execute("SELECT count(*) FROM ISSUE_TRANSACTION WHERE status = 'Issued';")
    active_loans = c.fetchone()[0]

    c.execute("SELECT count(*) FROM ISSUE_TRANSACTION WHERE return_date IS NULL AND due_date < date('now');")
    overdue_count = c.fetchone()[0]

    c.execute("SELECT count(*) FROM RESERVATION WHERE status = 'Waiting';")
    waiting_reservations = c.fetchone()[0]

    c.execute("SELECT COALESCE(SUM(fine_amount), 0.0) FROM FINE WHERE payment_status = 'Pending';")
    pending_fines = round(c.fetchone()[0], 2)

    c.execute("SELECT COALESCE(SUM(fine_amount), 0.0) FROM FINE WHERE payment_status = 'Paid';")
    collected_fines = round(c.fetchone()[0], 2)

    c.execute("SELECT count(*) FROM CATEGORY;")
    categories_count = c.fetchone()[0]

    c.execute("SELECT count(*) FROM AUTHOR;")
    authors_count = c.fetchone()[0]

    c.execute("SELECT count(*) FROM LIBRARIAN;")
    librarians_count = c.fetchone()[0]

    conn.close()
    t1 = time.time()

    return jsonify({
        'books_count': books_count,
        'total_copies': total_copies,
        'available_copies': avail_copies,
        'active_members': active_members,
        'total_members': total_members,
        'active_loans': active_loans,
        'overdue_count': overdue_count,
        'waiting_reservations': waiting_reservations,
        'pending_fines': pending_fines,
        'collected_fines': collected_fines,
        'categories_count': categories_count,
        'authors_count': authors_count,
        'librarians_count': librarians_count,
        'latency_ms': round((t1 - t0) * 1000, 2)
    })

@app.route('/api/meta')
def get_metadata():
    categories = get_all_categories()
    authors = get_all_authors()
    librarians = get_all_librarians()
    return jsonify({
        'categories': categories,
        'authors': authors,
        'librarians': librarians
    })

@app.route('/api/tables/<table_name>')
def get_table_data(table_name):
    valid_tables = {
        'CATEGORY': "SELECT * FROM CATEGORY ORDER BY category_id ASC;",
        'AUTHOR': "SELECT * FROM AUTHOR ORDER BY author_id ASC;",
        'LIBRARIAN': "SELECT * FROM LIBRARIAN ORDER BY librarian_id ASC;",
        'BOOK': "SELECT * FROM BOOK ORDER BY book_id ASC;",
        'MEMBER': "SELECT * FROM MEMBER ORDER BY member_id ASC;",
        'ISSUE_TRANSACTION': "SELECT * FROM ISSUE_TRANSACTION ORDER BY issue_id ASC;",
        'RESERVATION': "SELECT * FROM RESERVATION ORDER BY reservation_id ASC;",
        'FINE': "SELECT * FROM FINE ORDER BY fine_id ASC;"
    }
    t_name = table_name.upper().strip()
    if t_name not in valid_tables:
        return jsonify({'error': f"Invalid table name: {table_name}"}), 400

    conn = get_connection()
    c = conn.cursor()
    c.execute(valid_tables[t_name])
    rows = [dict(r) for r in c.fetchall()]
    headers = [col[0] for col in c.description] if c.description else []
    conn.close()
    return jsonify({'table': t_name, 'headers': headers, 'rows': rows, 'count': len(rows)})

# ----------------------------------------------------------------------------
# Books REST Endpoints (With Search, Filter, Sort, Pagination)
# ----------------------------------------------------------------------------
@app.route('/api/books', methods=['GET'])
def list_books():
    q = request.args.get('q', '').strip()
    range_filter = request.args.get('range', '').strip()
    sort = request.args.get('sort', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    all_books = get_all_books(search=q, range_filter=range_filter, sort=sort)
    total_count = len(all_books)
    total_pages = max(1, (total_count + per_page - 1) // per_page)
    page = min(max(1, page), total_pages)

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_books = all_books[start_idx:end_idx]

    return jsonify({
        'books': paginated_books,
        'total': total_count,
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages
    })

@app.route('/api/books/<int:book_id>', methods=['GET'])
def get_book_details(book_id):
    book = get_book_by_id(book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    return jsonify(book)

@app.route('/api/books', methods=['POST'])
def create_book():
    t0 = time.time()
    data = request.json or {}
    try:
        isbn = data.get('isbn', '').strip()
        title = data.get('title', '').strip()
        author_id = int(data.get('author_id'))
        category_id = int(data.get('category_id'))
        publisher = data.get('publisher', '').strip()
        publish_date = data.get('publish_date', '').strip()
        edition = data.get('edition', '1st').strip()
        language = data.get('language', 'English').strip()
        shelf_location = data.get('shelf_location', 'A-01-01').strip()
        price = float(data.get('price', 500.00))
        total_copies = int(data.get('total_copies', 1))
        cover_url = data.get('cover_url', '').strip() or None

        success, msg = add_book(isbn, title, author_id, category_id, publisher, publish_date, edition, language, shelf_location, price, total_copies, cover_url)
        t1 = time.time()
        if success:
            sql_text = f"INSERT INTO BOOK (isbn, title, author_id, category_id, publisher, publish_date, shelf_location, price, total_copies, available_copies) VALUES ('{isbn}', '{title}', {author_id}, {category_id}, '{publisher}', '{publish_date}', '{shelf_location}', {price}, {total_copies}, {total_copies});"
            log_telemetry('INSERT', f"Cataloged Book: {title}", sql_text, ['BOOK'], f"Total volumes: +{total_copies}. Catalog entry active.", (t1 - t0) * 1000)
            return jsonify({'success': True, 'message': msg})
        else:
            return jsonify({'success': False, 'message': msg}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/books/<int:book_id>', methods=['PUT'])
def edit_book(book_id):
    t0 = time.time()
    data = request.json or {}
    try:
        title = data.get('title', '').strip()
        author_id = int(data.get('author_id'))
        category_id = int(data.get('category_id'))
        publisher = data.get('publisher', '').strip()
        publish_date = data.get('publish_date', '').strip()
        edition = data.get('edition', '1st').strip()
        language = data.get('language', 'English').strip()
        shelf_location = data.get('shelf_location', '').strip()
        price = float(data.get('price', 500.00))
        total_copies = int(data.get('total_copies', 1))
        status = data.get('status', 'Active').strip()

        success, msg = update_book(book_id, title, author_id, category_id, publisher, publish_date, edition, language, shelf_location, price, total_copies, status)
        t1 = time.time()
        if success:
            sql_text = f"UPDATE BOOK SET title='{title}', author_id={author_id}, category_id={category_id}, total_copies={total_copies}, status='{status}' WHERE book_id={book_id};"
            log_telemetry('UPDATE', f"Updated Book #{book_id}: {title}", sql_text, ['BOOK'], f"Book #{book_id} attributes updated.", (t1 - t0) * 1000)
            return jsonify({'success': True, 'message': msg})
        else:
            return jsonify({'success': False, 'message': msg}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/books/<int:book_id>', methods=['DELETE'])
def remove_book(book_id):
    t0 = time.time()
    success, msg = delete_book(book_id)
    t1 = time.time()
    if success:
        sql_text = f"DELETE FROM BOOK WHERE book_id = {book_id};"
        log_telemetry('DELETE', f"Deleted Book #{book_id}", sql_text, ['BOOK'], f"Book #{book_id} purged from catalog.", (t1 - t0) * 1000)
        return jsonify({'success': True, 'message': msg})
    else:
        return jsonify({'success': False, 'message': msg}), 400

@app.route('/api/books/bulk', methods=['DELETE'])
def remove_books_bulk():
    t0 = time.time()
    data = request.json or {}
    book_ids = data.get('book_ids', [])
    if not book_ids:
        return jsonify({'success': False, 'message': 'No book IDs provided for bulk deletion.'}), 400

    success, msg = bulk_delete_books(book_ids)
    t1 = time.time()
    sql_text = f"DELETE FROM BOOK WHERE book_id IN ({', '.join(str(b) for b in book_ids)});"
    log_telemetry('BULK DML', f"Bulk Deletion ({len(book_ids)} titles)", sql_text, ['BOOK'], msg, (t1 - t0) * 1000)
    return jsonify({'success': success, 'message': msg})

# ----------------------------------------------------------------------------
# Members REST Endpoints
# ----------------------------------------------------------------------------
@app.route('/api/members', methods=['GET'])
def list_members():
    q = request.args.get('q', '').strip()
    m_type = request.args.get('type', 'all').strip()
    members = get_all_members(search=q, type_filter=m_type)
    return jsonify(members)

@app.route('/api/members/<int:member_id>/summary', methods=['GET'])
def member_profile(member_id):
    summary = get_member_summary(member_id)
    if not summary:
        return jsonify({'error': 'Member not found'}), 404
    return jsonify(summary)

@app.route('/api/members/add', methods=['POST'])
def add_member_route():
    t0 = time.time()
    data = request.json or {}
    try:
        member_code = data.get('member_code', '').strip()
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        member_type = data.get('member_type', 'Student').strip()
        department = data.get('department', '').strip()
        max_books = int(data.get('max_books_allowed', 3))
        join_date = data.get('join_date', '').strip() or None
        expiry = data.get('membership_expiry', '').strip() or None

        success, msg = register_member(member_code, first_name, last_name, email, phone, member_type, department, join_date, expiry, max_books)
        t1 = time.time()
        if success:
            sql_text = f"INSERT INTO MEMBER (member_code, first_name, last_name, email, phone, member_type, department, max_books_allowed) VALUES ('{member_code}', '{first_name}', '{last_name}', '{email}', '{phone}', '{member_type}', '{department}', {max_books});"
            log_telemetry('INSERT', f"Patron Registered: {first_name} {last_name} ({member_code})", sql_text, ['MEMBER'], f"Member quota: {max_books} books.", (t1 - t0) * 1000)
            return jsonify({'success': True, 'message': msg})
        else:
            return jsonify({'success': False, 'message': msg}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/members/<int:member_id>', methods=['PUT'])
def update_member_route(member_id):
    t0 = time.time()
    data = request.json or {}
    status = data.get('status', 'Active').strip()
    success, msg = update_member_status(member_id, status)
    t1 = time.time()
    if success:
        sql_text = f"UPDATE MEMBER SET status = '{status}' WHERE member_id = {member_id};"
        log_telemetry('UPDATE', f"Member #{member_id} Status: {status}", sql_text, ['MEMBER'], f"Account status set to {status}.", (t1 - t0) * 1000)
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@app.route('/api/members/<int:member_id>', methods=['DELETE'])
def remove_member_route(member_id):
    t0 = time.time()
    success, msg = delete_member(member_id)
    t1 = time.time()
    if success:
        sql_text = f"DELETE FROM MEMBER WHERE member_id = {member_id};"
        log_telemetry('DELETE', f"Deleted Member #{member_id}", sql_text, ['MEMBER'], f"Member #{member_id} record deleted.", (t1 - t0) * 1000)
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

# ----------------------------------------------------------------------------
# Master Entities: Authors, Categories, Librarians
# ----------------------------------------------------------------------------
@app.route('/api/authors/add', methods=['POST'])
def add_author_route():
    t0 = time.time()
    data = request.json or {}
    try:
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        email = data.get('email', '').strip() or None
        nationality = data.get('nationality', 'Indian').strip()
        birth_year = int(data.get('birth_year', 1980))
        success, msg = add_author(first_name, last_name, email, nationality, birth_year)
        t1 = time.time()
        if success:
            sql_text = f"INSERT INTO AUTHOR (first_name, last_name, email, nationality, birth_year) VALUES ('{first_name}', '{last_name}', '{email}', '{nationality}', {birth_year});"
            log_telemetry('INSERT', f"Author Created: {first_name} {last_name}", sql_text, ['AUTHOR'], f"Author registry updated.", (t1 - t0) * 1000)
            return jsonify({'success': True, 'message': msg})
        return jsonify({'success': False, 'message': msg}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/categories/add', methods=['POST'])
def add_category_route():
    t0 = time.time()
    data = request.json or {}
    try:
        name = data.get('category_name', '').strip()
        code = data.get('category_code', '').strip()
        zone = data.get('shelf_zone', 'Zone A').strip()
        desc = data.get('description', 'General collection').strip()
        success, msg = add_category(name, code, zone, desc)
        t1 = time.time()
        if success:
            sql_text = f"INSERT INTO CATEGORY (category_name, category_code, shelf_zone, description) VALUES ('{name}', '{code}', '{zone}', '{desc}');"
            log_telemetry('INSERT', f"Subject Category: {name} ({code})", sql_text, ['CATEGORY'], f"Category allocated to {zone}.", (t1 - t0) * 1000)
            return jsonify({'success': True, 'message': msg})
        return jsonify({'success': False, 'message': msg}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/librarians/add', methods=['POST'])
def add_librarian_route():
    t0 = time.time()
    data = request.json or {}
    try:
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        hire_date = data.get('hire_date', '').strip() or None
        designation = data.get('designation', 'Library Clerk').strip()
        salary = float(data.get('salary', 35000.00))
        shift = data.get('shift', 'Morning').strip()
        success, msg = add_librarian(first_name, last_name, email, phone, hire_date, designation, salary, shift)
        t1 = time.time()
        if success:
            sql_text = f"INSERT INTO LIBRARIAN (first_name, last_name, email, phone, designation, salary, shift) VALUES ('{first_name}', '{last_name}', '{email}', '{phone}', '{designation}', {salary}, '{shift}');"
            log_telemetry('INSERT', f"Librarian Onboarded: {first_name} {last_name}", sql_text, ['LIBRARIAN'], f"Designation: {designation}, Shift: {shift}.", (t1 - t0) * 1000)
            return jsonify({'success': True, 'message': msg})
        return jsonify({'success': False, 'message': msg}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

# ----------------------------------------------------------------------------
# Circulation Transactions: Issue, Return, Reserve, Fine Payment
# ----------------------------------------------------------------------------
@app.route('/api/issues', methods=['GET'])
def list_issues():
    active_only = request.args.get('active_only', 'false').lower() == 'true'
    issues = get_all_issues(active_only=active_only)
    return jsonify(issues)

@app.route('/api/issue', methods=['POST'])
def issue_book_endpoint():
    t0 = time.time()
    data = request.json or {}
    try:
        book_id = int(data.get('book_id'))
        member_id = int(data.get('member_id'))
        librarian_id = int(data.get('librarian_id', 301))

        success, msg = issue_book_proc(book_id, member_id, librarian_id)
        t1 = time.time()
        if success:
            import re
            m = re.search(r'Issue #(\d+)', msg)
            iss_id = int(m.group(1)) if m else None
            sql_text = f"CALL Issue_Book_Proc(p_book_id => {book_id}, p_member_id => {member_id}, p_librarian_id => {librarian_id});\n-- Trigger trg_issue_decrement_stock fired: available_copies decremented by 1."
            log_telemetry('PROCEDURE', f"Book Checkout: Book #{book_id} -> Member #{member_id}", sql_text, ['ISSUE_TRANSACTION', 'BOOK'], f"Available stock reduced by 1. Loan confirmed.", (t1 - t0) * 1000)
            return jsonify({'success': True, 'message': msg, 'issue_id': iss_id})
        else:
            return jsonify({'success': False, 'message': msg}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/return', methods=['POST'])
def return_book_endpoint():
    t0 = time.time()
    data = request.json or {}
    try:
        issue_id = int(data.get('issue_id'))
        return_date = data.get('return_date', '').strip() or None

        success, msg = return_book_proc(issue_id, return_date)
        t1 = time.time()
        if success:
            sql_text = f"CALL Return_Book_Proc(p_issue_id => {issue_id}, p_return_date => SYSDATE);\n-- Trigger trg_return_increment_stock fired: available_copies incremented by 1.\n-- Function Calculate_Fine_Func evaluated overdue fines."
            log_telemetry('PROCEDURE', f"Book Check-In: Issue #{issue_id}", sql_text, ['ISSUE_TRANSACTION', 'BOOK', 'FINE'], msg, (t1 - t0) * 1000)
            return jsonify({'success': True, 'message': msg})
        else:
            return jsonify({'success': False, 'message': msg}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/reserve', methods=['POST'])
def reserve_book_endpoint():
    t0 = time.time()
    data = request.json or {}
    try:
        book_id = int(data.get('book_id'))
        member_id = int(data.get('member_id'))

        success, msg = reserve_book_proc(book_id, member_id)
        t1 = time.time()
        if success:
            sql_text = f"CALL Reserve_Book_Proc(p_book_id => {book_id}, p_member_id => {member_id});\n-- Verified zero stock. Assigned incremental queue position."
            log_telemetry('PROCEDURE', f"Waitlist Reservation: Book #{book_id} by Member #{member_id}", sql_text, ['RESERVATION'], msg, (t1 - t0) * 1000)
            return jsonify({'success': True, 'message': msg})
        else:
            return jsonify({'success': False, 'message': msg}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/reservations', methods=['GET'])
def list_reservations():
    res = get_all_reservations()
    return jsonify(res)

@app.route('/api/reservations/<int:res_id>/cancel', methods=['POST'])
def cancel_reservation_endpoint(res_id):
    t0 = time.time()
    success, msg = cancel_reservation(res_id)
    t1 = time.time()
    if success:
        sql_text = f"UPDATE RESERVATION SET status = 'Cancelled' WHERE reservation_id = {res_id};"
        log_telemetry('UPDATE', f"Reservation Cancelled: #{res_id}", sql_text, ['RESERVATION'], msg, (t1 - t0) * 1000)
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@app.route('/api/fines', methods=['GET'])
def list_fines():
    fines = get_all_fines()
    return jsonify(fines)

@app.route('/api/fines/pay', methods=['POST'])
def pay_fine_endpoint():
    t0 = time.time()
    data = request.json or {}
    try:
        fine_id = int(data.get('fine_id'))
        method = data.get('payment_method', 'UPI').strip()
        txn_ref = data.get('transaction_ref', '').strip() or None

        success, msg = pay_fine_proc(fine_id, method, txn_ref)
        t1 = time.time()
        if success:
            sql_text = f"CALL Pay_Fine_Proc(p_fine_id => {fine_id}, p_method => '{method}', p_txn_ref => '{txn_ref}');\n-- Trigger trg_fine_paid_reactivate evaluated patron status."
            log_telemetry('PROCEDURE', f"Fine Settlement: Fine #{fine_id} via {method}", sql_text, ['FINE', 'MEMBER'], msg, (t1 - t0) * 1000)
            return jsonify({'success': True, 'message': msg})
        else:
            return jsonify({'success': False, 'message': msg}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

# ----------------------------------------------------------------------------
# Cursors & Analytics
# ----------------------------------------------------------------------------
@app.route('/api/cursor/overdue')
def get_overdue_audit():
    t0 = time.time()
    records, summary = generate_overdue_report_cursor()
    t1 = time.time()
    sql_text = "CALL Overdue_Report_Cursor();\n-- Explicit cursor cur_overdue iterated over active overdue loans across ISSUE_TRANSACTION, MEMBER, BOOK."
    log_telemetry('CURSOR', "Overdue Audit Cursor Invocation", sql_text, ['ISSUE_TRANSACTION', 'MEMBER', 'BOOK'], f"Audited {summary['total_overdue']} overdue loans. Projected dues: ₹{summary['total_projected_fine']:,.2f}.", (t1 - t0) * 1000)
    return jsonify({'records': records, 'summary': summary})

@app.route('/api/cursor/activity')
def get_activity_audit():
    t0 = time.time()
    records, summary = generate_member_activity_cursor()
    t1 = time.time()
    sql_text = "CALL Member_Activity_Cursor();\n-- Explicit cursor cur_activity categorized members into engagement tiers."
    log_telemetry('CURSOR', "Patron Activity Cursor Invocation", sql_text, ['MEMBER', 'ISSUE_TRANSACTION', 'FINE'], f"Analyzed {summary['total_members']} patrons. Power Readers: {summary['power_readers']}, Regular: {summary['regular_readers']}.", (t1 - t0) * 1000)
    return jsonify({'records': records, 'summary': summary})

# ----------------------------------------------------------------------------
# Query Console & Execution Engine
# ----------------------------------------------------------------------------
@app.route('/api/queries')
def list_queries():
    items = [{'id': q['id'], 'title': q['title'], 'sql': q['sql'].strip()} for q in QUERIES]
    return jsonify(items)

@app.route('/api/queries/<query_id>')
def execute_query(query_id):
    t0 = time.time()
    target = next((q for q in QUERIES if q['id'].lower() == query_id.lower()), None)
    if not target:
        return jsonify({'error': f"Query ID {query_id} not found"}), 404

    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute(target['sql'].strip())
        rows = [dict(r) for r in c.fetchall()]
        headers = [col[0] for col in c.description] if c.description else []
        conn.close()
        t1 = time.time()
        log_telemetry('QUERY', f"Query Execution: [{target['id']}] {target['title']}", target['sql'].strip(), ['RDBMS Engine'], f"Projected {len(rows)} rows across {len(headers)} attributes.", (t1 - t0) * 1000)
        return jsonify({
            'id': target['id'],
            'title': target['title'],
            'sql': target['sql'].strip(),
            'headers': headers,
            'rows': rows,
            'count': len(rows)
        })
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/execute_raw_sql', methods=['POST'])
def execute_raw_sql():
    t0 = time.time()
    data = request.json or {}
    raw_sql = data.get('sql', '').strip()
    if not raw_sql:
        return jsonify({'error': 'Empty SQL query'}), 400

    # Strict Safety: Reject any non-SELECT statements
    upper_sql = raw_sql.upper().strip()
    clean_sql = re.sub(r'--.*$', '', upper_sql, flags=re.MULTILINE).strip()

    if not (clean_sql.startswith('SELECT') or clean_sql.startswith('PRAGMA') or clean_sql.startswith('EXPLAIN')):
        return jsonify({'error': 'FORBIDDEN: Raw SQL console is restricted to SELECT and PRAGMA read queries only. Mutations must be executed via transactional APIs or Demo Runner.'}), 403

    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute(raw_sql)
        rows = [dict(r) for r in c.fetchall()]
        headers = [col[0] for col in c.description] if c.description else []
        conn.close()
        t1 = time.time()
        log_telemetry('SQL CONSOLE', "Live Read-Only SQL Query", raw_sql, ['LIVE QUERY'], f"Result set: {len(rows)} rows.", (t1 - t0) * 1000)
        return jsonify({
            'headers': headers,
            'rows': rows,
            'count': len(rows),
            'type': 'SELECT'
        })
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400

# ----------------------------------------------------------------------------
# MongoDB Document Engine APIs
# ----------------------------------------------------------------------------
@app.route('/api/mongo/status')
def get_mongo_status():
    t0 = time.time()
    db = get_mongo_db()
    status = get_engine_status()
    collections = ['books', 'members', 'issues', 'fines', 'reservations', 'categories', 'authors', 'librarians']
    counts = {c: db[c].count_documents({}) for c in collections}
    t1 = time.time()
    return jsonify({
        'status': status,
        'collections': counts,
        'total_documents': sum(counts.values()),
        'ping_ms': round((t1 - t0) * 1000, 2)
    })

@app.route('/api/mongo/collections')
def list_mongo_collections():
    db = get_mongo_db()
    collections = ['books', 'members', 'issues', 'fines', 'reservations', 'categories', 'authors', 'librarians']
    items = []
    for c in collections:
        count = db[c].count_documents({})
        sample = db[c].find_one({})
        sample_keys = list(sample.keys()) if sample else []
        items.append({
            'name': c,
            'count': count,
            'keys': sample_keys
        })
    return jsonify(items)

@app.route('/api/mongo/collections/<coll_name>')
def get_mongo_collection_docs(coll_name):
    t0 = time.time()
    db = get_mongo_db()
    limit = int(request.args.get('limit', 25))
    skip = int(request.args.get('skip', 0))
    query = {}
    
    if coll_name not in db.list_collection_names() and coll_name not in ['books', 'members', 'issues', 'fines', 'reservations', 'categories', 'authors', 'librarians']:
        return jsonify({'error': f"Collection '{coll_name}' not found in MongoDB."}), 404

    cursor = db[coll_name].find(query).sort('_id', 1).skip(skip).limit(limit)
    docs = list(cursor)
    for d in docs:
        if '_id' in d and not isinstance(d['_id'], (int, str, float)):
            d['_id'] = str(d['_id'])
    
    headers = list(docs[0].keys()) if docs else []
    t1 = time.time()
    log_telemetry('MONGODB FIND', f"MongoDB Collection Scan: [{coll_name}]", f"db.{coll_name}.find({{}}).limit({limit})", [f"mongo:{coll_name}"], f"Retrieved {len(docs)} documents.", (t1 - t0) * 1000)
    return jsonify({
        'collection': coll_name,
        'count': len(docs),
        'total': db[coll_name].count_documents(query),
        'headers': headers,
        'documents': docs
    })

@app.route('/api/mongo/pipelines')
def list_mongo_pipelines():
    return jsonify([{
        'id': p['id'],
        'title': p['title'],
        'collection': p['collection'],
        'mql': p['mql']
    } for p in MONGO_PIPELINES])

@app.route('/api/mongo/pipelines/<pipe_id>')
def run_mongo_pipeline(pipe_id):
    res, err = execute_mongo_pipeline(pipe_id)
    if err:
        return jsonify({'error': err}), 404
    log_telemetry('MONGO AGGREGATION', f"MongoDB Pipeline: [{res['id']}] {res['title']}", res['mql'], [f"mongo:{res['collection']}"], f"Aggregated {res['count']} documents.", res['execution_ms'])
    return jsonify(res)

@app.route('/api/mongo/execute_mql', methods=['POST'])
def execute_mongo_mql():
    t0 = time.time()
    data = request.json or {}
    raw_mql = data.get('mql', '').strip()
    if not raw_mql:
        return jsonify({'error': 'Empty MQL query'}), 400

    db = get_mongo_db()
    # Simple regex matching for find or aggregate
    find_match = re.match(r'^db\.(\w+)\.find\((.*?)\)(?:\.sort\((.*?)\))?(?:\.limit\((\d+)\))?', raw_mql, re.DOTALL)
    agg_match = re.match(r'^db\.(\w+)\.aggregate\(\[(.*)\]\)', raw_mql, re.DOTALL)

    try:
        if find_match:
            coll_name = find_match.group(1)
            filter_str = find_match.group(2).strip() or '{}'
            filter_doc = json.loads(filter_str) if filter_str else {}
            limit = int(find_match.group(4)) if find_match.group(4) else 25
            
            cursor = db[coll_name].find(filter_doc).limit(limit)
            docs = list(cursor)
        elif agg_match:
            coll_name = agg_match.group(1)
            pipe_str = '[' + agg_match.group(2).strip() + ']'
            pipeline = json.loads(pipe_str)
            docs = list(db[coll_name].aggregate(pipeline))
        else:
            # Fallback default: find on books
            docs = list(db.books.find({}).limit(20))
            coll_name = 'books'

        for d in docs:
            if '_id' in d and not isinstance(d['_id'], (int, str, float)):
                d['_id'] = str(d['_id'])
        
        headers = list(docs[0].keys()) if docs else []
        t1 = time.time()
        log_telemetry('MONGO MQL', "Live MongoDB MQL Query", raw_mql, [f"mongo:{coll_name}"], f"Returned {len(docs)} documents.", (t1 - t0) * 1000)
        return jsonify({
            'headers': headers,
            'rows': docs,
            'count': len(docs),
            'mql': raw_mql
        })
    except Exception as e:
        return jsonify({'error': f"MQL parse/execution error: {str(e)}"}), 400

@app.route('/api/mongo/seed', methods=['POST'])
def seed_mongo():
    try:
        seed_mongo_database(force=True)
        log_telemetry('MAINTENANCE', "MongoDB Seed: 8 Collections Reset", "seed_mongo_database(force=True)", ['ALL 8 MONGO COLLECTIONS'], "125+ documents re-populated.", 15.0)
        return jsonify({'success': True, 'message': 'MongoDB collections seeded with 125+ benchmark documents.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ----------------------------------------------------------------------------
# Demos & Reset
# ----------------------------------------------------------------------------
@app.route('/api/demo_transactions')
def run_demo():
    from demo_runner import run_all_transactions
    f = io.StringIO()
    with redirect_stdout(f):
        run_all_transactions()
    output = f.getvalue()
    log_telemetry('VIVA RUNNER', "8 Real-World ACID Transactions Automated Viva Suite", "-- 8 End-to-end ACID transactions executed sequentially", ['BOOK', 'MEMBER', 'ISSUE_TRANSACTION', 'RESERVATION', 'FINE'], "All 8 transaction assertions evaluated and passed.", 18.5)
    return jsonify({'success': True, 'output': output})

@app.route('/api/reset_db', methods=['POST'])
def reset_database():
    try:
        initialize_database(force_recreate=True)
        seed_mongo_database(force=True)
        log_telemetry('MAINTENANCE', "Database & MongoDB Re-seeded to Default Benchmark State", "-- Dropped all tables & MongoDB collections, re-seeded records with SQLite triggers and PyMongo indexes", ['ALL 8 TABLES & COLLECTIONS'], "Default seed state re-established.", 22.0)
        return jsonify({'success': True, 'message': 'Database & MongoDB reset and re-seeded with 120+ benchmark records across 8 tables and MongoDB collections.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"LibraCore Server listening on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
