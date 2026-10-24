-- ============================================================================
-- LibraCore — Oracle PL/SQL Procedures
-- Database Systems Lab (BCSE302P) Submission File
-- Production-Grade Procedures with Custom Exceptions, OUT Parameters, and ACID Integrity
-- ============================================================================

-- ============================================================================
-- PROCEDURE 1: Issue_Book_Proc
-- Validates borrower eligibility, stock availability, and checks out a catalog book.
-- Stock decrement is handled exclusively by trg_issue_decrement_stock.
-- ============================================================================
CREATE OR REPLACE PROCEDURE Issue_Book_Proc (
    p_book_id       IN  INTEGER,
    p_member_id     IN  INTEGER,
    p_librarian_id  IN  INTEGER,
    p_status_msg    OUT VARCHAR2
)
IS
    v_member_name       VARCHAR2(100);
    v_member_type       VARCHAR2(20);
    v_member_status     VARCHAR2(20);
    v_member_expiry     DATE;
    v_max_allowed       INTEGER;
    v_active_loans      INTEGER;
    v_pending_fines     NUMBER;
    v_already_holding   INTEGER;

    v_book_title        VARCHAR2(150);
    v_book_status       VARCHAR2(20);
    v_available_copies  INTEGER;
    v_loan_days         INTEGER;
    v_new_issue_id      INTEGER;

    -- Custom Exceptions
    e_member_not_found      EXCEPTION;
    e_member_not_active     EXCEPTION;
    e_membership_expired    EXCEPTION;
    e_borrowing_limit_hit   EXCEPTION;
    e_unpaid_fines_blocked  EXCEPTION;
    e_already_borrowed      EXCEPTION;
    e_book_not_found        EXCEPTION;
    e_book_archived         EXCEPTION;
    e_out_of_stock          EXCEPTION;
BEGIN
    -- 1. Validate Member
    BEGIN
        SELECT first_name || ' ' || last_name, member_type, status, membership_expiry, max_books_allowed
        INTO v_member_name, v_member_type, v_member_status, v_member_expiry, v_max_allowed
        FROM MEMBER
        WHERE member_id = p_member_id;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RAISE e_member_not_found;
    END;

    IF v_member_status != 'Active' THEN
        RAISE e_member_not_active;
    END IF;

    IF v_member_expiry < SYSDATE THEN
        RAISE e_membership_expired;
    END IF;

    -- 2. Check pending dues (Policy: loans blocked if unpaid fines > 200)
    v_pending_fines := Get_Member_Pending_Fine_Func(p_member_id);
    IF v_pending_fines > 200.00 THEN
        RAISE e_unpaid_fines_blocked;
    END IF;

    -- 3. Check active loan count against max allowance
    SELECT COUNT(*)
    INTO v_active_loans
    FROM ISSUE_TRANSACTION
    WHERE member_id = p_member_id AND status = 'Issued';

    IF v_active_loans >= v_max_allowed THEN
        RAISE e_borrowing_limit_hit;
    END IF;

    -- 4. Check if member already has an active copy of this exact book
    SELECT COUNT(*)
    INTO v_already_holding
    FROM ISSUE_TRANSACTION
    WHERE member_id = p_member_id AND book_id = p_book_id AND status = 'Issued';

    IF v_already_holding > 0 THEN
        RAISE e_already_borrowed;
    END IF;

    -- 5. Validate Book Catalog Entry & Stock
    BEGIN
        SELECT title, status, available_copies
        INTO v_book_title, v_book_status, v_available_copies
        FROM BOOK
        WHERE book_id = p_book_id;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RAISE e_book_not_found;
    END;

    IF v_book_status != 'Active' THEN
        RAISE e_book_archived;
    END IF;

    IF v_available_copies <= 0 THEN
        RAISE e_out_of_stock;
    END IF;

    -- 6. Compute Loan Duration based on Member Type
    v_loan_days := Get_Loan_Days_Func(v_member_type);

    -- 7. Generate Issue PK and Insert Record
    SELECT NVL(MAX(issue_id), 5000) + 1 INTO v_new_issue_id FROM ISSUE_TRANSACTION;

    INSERT INTO ISSUE_TRANSACTION (
        issue_id, book_id, member_id, librarian_id, issue_date, due_date, return_date, status
    ) VALUES (
        v_new_issue_id, p_book_id, p_member_id, p_librarian_id,
        TRUNC(SYSDATE), TRUNC(SYSDATE) + v_loan_days, NULL, 'Issued'
    );
    -- Note: Stock decrement is performed automatically by trigger trg_issue_decrement_stock

    -- 8. If member had a waiting reservation for this book, mark it Fulfilled
    UPDATE RESERVATION
    SET status = 'Fulfilled'
    WHERE book_id = p_book_id AND member_id = p_member_id AND status = 'Waiting';

    COMMIT;
    p_status_msg := 'SUCCESS: Issue #' || v_new_issue_id || ' confirmed. Book "' || v_book_title || 
                    '" issued to ' || v_member_name || '. Due date: ' || TO_CHAR(TRUNC(SYSDATE) + v_loan_days, 'YYYY-MM-DD');
    DBMS_OUTPUT.PUT_LINE(p_status_msg);

EXCEPTION
    WHEN e_member_not_found THEN
        ROLLBACK;
        p_status_msg := 'VALIDATION REJECTION: Member ID ' || p_member_id || ' does not exist in library registry.';
    WHEN e_member_not_active THEN
        ROLLBACK;
        p_status_msg := 'VALIDATION REJECTION: Member ' || v_member_name || ' account is ' || v_member_status || '. Circulation suspended.';
    WHEN e_membership_expired THEN
        ROLLBACK;
        p_status_msg := 'VALIDATION REJECTION: Membership expired on ' || TO_CHAR(v_member_expiry, 'YYYY-MM-DD') || '. Renewal required.';
    WHEN e_unpaid_fines_blocked THEN
        ROLLBACK;
        p_status_msg := 'VALIDATION REJECTION: Member has outstanding pending fines of INR ' || TO_CHAR(v_pending_fines, 'FM999.00') || ' (> INR 200 threshold).';
    WHEN e_borrowing_limit_hit THEN
        ROLLBACK;
        p_status_msg := 'VALIDATION REJECTION: Member quota full (' || v_active_loans || '/' || v_max_allowed || ' books currently borrowed).';
    WHEN e_already_borrowed THEN
        ROLLBACK;
        p_status_msg := 'VALIDATION REJECTION: Member is already holding an active copy of book #' || p_book_id || '.';
    WHEN e_book_not_found THEN
        ROLLBACK;
        p_status_msg := 'VALIDATION REJECTION: Book ID ' || p_book_id || ' not found in catalog.';
    WHEN e_book_archived THEN
        ROLLBACK;
        p_status_msg := 'VALIDATION REJECTION: Book "' || v_book_title || '" is Archived and unavailable for circulation.';
    WHEN e_out_of_stock THEN
        ROLLBACK;
        p_status_msg := 'CIRCULATION REJECTION: Zero available copies for book "' || v_book_title || '". Reservation advised.';
    WHEN OTHERS THEN
        ROLLBACK;
        p_status_msg := 'SYSTEM ERROR: ' || SQLERRM;
END Issue_Book_Proc;
/

-- ============================================================================
-- PROCEDURE 2: Return_Book_Proc
-- Processes check-in of borrowed books, invokes fine computation, and logs penalties.
-- Stock increment is handled exclusively by trg_return_increment_stock.
-- ============================================================================
CREATE OR REPLACE PROCEDURE Return_Book_Proc (
    p_issue_id      IN  INTEGER,
    p_return_date   IN  DATE DEFAULT SYSDATE,
    p_status_msg    OUT VARCHAR2
)
IS
    v_book_id       INTEGER;
    v_member_id     INTEGER;
    v_issue_status  VARCHAR2(20);
    v_due_date      DATE;
    v_book_title    VARCHAR2(150);
    v_member_name   VARCHAR2(100);
    v_days_overdue  INTEGER;
    v_fine_amt      NUMBER;
    v_new_fine_id   INTEGER;

    e_issue_not_found   EXCEPTION;
    e_already_returned  EXCEPTION;
BEGIN
    BEGIN
        SELECT i.book_id, i.member_id, i.status, i.due_date, b.title, m.first_name || ' ' || m.last_name
        INTO v_book_id, v_member_id, v_issue_status, v_due_date, v_book_title, v_member_name
        FROM ISSUE_TRANSACTION i
        JOIN BOOK b ON i.book_id = b.book_id
        JOIN MEMBER m ON i.member_id = m.member_id
        WHERE i.issue_id = p_issue_id;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RAISE e_issue_not_found;
    END;

    IF v_issue_status = 'Returned' THEN
        RAISE e_already_returned;
    END IF;

    -- Update issue transaction record
    UPDATE ISSUE_TRANSACTION
    SET return_date = TRUNC(p_return_date), status = 'Returned'
    WHERE issue_id = p_issue_id;
    -- Note: Stock increment is performed automatically by trigger trg_return_increment_stock

    -- Compute fine via function
    v_fine_amt := Calculate_Fine_Func(p_issue_id);

    IF v_fine_amt > 0 THEN
        v_days_overdue := TRUNC(p_return_date) - TRUNC(v_due_date);
        SELECT NVL(MAX(fine_id), 7000) + 1 INTO v_new_fine_id FROM FINE;

        INSERT INTO FINE (
            fine_id, issue_id, member_id, days_overdue, fine_amount, fine_date, payment_status
        ) VALUES (
            v_new_fine_id, p_issue_id, v_member_id, v_days_overdue, v_fine_amt, TRUNC(SYSDATE), 'Pending'
        );

        p_status_msg := 'RETURN PROCESSED (LATE): Book "' || v_book_title || '" returned by ' || v_member_name || 
                        '. Overdue by ' || v_days_overdue || ' days. Fine assessed: INR ' || TO_CHAR(v_fine_amt, 'FM999.00') || ' (Fine ID #' || v_new_fine_id || ').';
    ELSE
        p_status_msg := 'RETURN PROCESSED (ON TIME): Book "' || v_book_title || '" returned successfully by ' || v_member_name || '. No fines incurred.';
    END IF;

    COMMIT;
    DBMS_OUTPUT.PUT_LINE(p_status_msg);

EXCEPTION
    WHEN e_issue_not_found THEN
        ROLLBACK;
        p_status_msg := 'VALIDATION REJECTION: Issue record #' || p_issue_id || ' not found.';
    WHEN e_already_returned THEN
        ROLLBACK;
        p_status_msg := 'VALIDATION REJECTION: Issue record #' || p_issue_id || ' has already been checked in and returned.';
    WHEN OTHERS THEN
        ROLLBACK;
        p_status_msg := 'SYSTEM ERROR: ' || SQLERRM;
END Return_Book_Proc;
/

-- ============================================================================
-- PROCEDURE 3: Reserve_Book_Proc
-- Places a reservation on an out-of-stock catalog title and assigns queue position.
-- ============================================================================
CREATE OR REPLACE PROCEDURE Reserve_Book_Proc (
    p_book_id       IN  INTEGER,
    p_member_id     IN  INTEGER,
    p_status_msg    OUT VARCHAR2
)
IS
    v_available_copies  INTEGER;
    v_book_title        VARCHAR2(150);
    v_member_name       VARCHAR2(100);
    v_member_status     VARCHAR2(20);
    v_duplicate_res     INTEGER;
    v_active_loan       INTEGER;
    v_next_pos          INTEGER;
    v_new_res_id        INTEGER;

    e_copies_available      EXCEPTION;
    e_member_inactive       EXCEPTION;
    e_already_reserved      EXCEPTION;
    e_already_has_copy      EXCEPTION;
BEGIN
    SELECT title, available_copies
    INTO v_book_title, v_available_copies
    FROM BOOK
    WHERE book_id = p_book_id;

    -- Reservations allowed only when stock = 0
    IF v_available_copies > 0 THEN
        RAISE e_copies_available;
    END IF;

    SELECT first_name || ' ' || last_name, status
    INTO v_member_name, v_member_status
    FROM MEMBER
    WHERE member_id = p_member_id;

    IF v_member_status != 'Active' THEN
        RAISE e_member_inactive;
    END IF;

    -- Check if duplicate active reservation exists
    SELECT COUNT(*)
    INTO v_duplicate_res
    FROM RESERVATION
    WHERE book_id = p_book_id AND member_id = p_member_id AND status = 'Waiting';

    IF v_duplicate_res > 0 THEN
        RAISE e_already_reserved;
    END IF;

    -- Check if borrower currently holds a loaned copy
    SELECT COUNT(*)
    INTO v_active_loan
    FROM ISSUE_TRANSACTION
    WHERE book_id = p_book_id AND member_id = p_member_id AND status = 'Issued';

    IF v_active_loan > 0 THEN
        RAISE e_already_has_copy;
    END IF;

    -- Calculate next queue position
    SELECT NVL(MAX(queue_position), 0) + 1
    INTO v_next_pos
    FROM RESERVATION
    WHERE book_id = p_book_id AND status = 'Waiting';

    SELECT NVL(MAX(reservation_id), 6000) + 1 INTO v_new_res_id FROM RESERVATION;

    INSERT INTO RESERVATION (
        reservation_id, book_id, member_id, reserved_on, expires_on, queue_position, status
    ) VALUES (
        v_new_res_id, p_book_id, p_member_id, TRUNC(SYSDATE), TRUNC(SYSDATE) + 7, v_next_pos, 'Waiting'
    );

    COMMIT;
    p_status_msg := 'RESERVATION CONFIRMED: Reservation #' || v_new_res_id || ' placed for "' || v_book_title || 
                    '". Member: ' || v_member_name || '. Queue Position: #' || v_next_pos || '. Expires in 7 days.';
    DBMS_OUTPUT.PUT_LINE(p_status_msg);

EXCEPTION
    WHEN e_copies_available THEN
        ROLLBACK;
        p_status_msg := 'RESERVATION REJECTION: Book "' || v_book_title || '" currently has ' || v_available_copies || ' copy available. Direct checkout permitted.';
    WHEN e_member_inactive THEN
        ROLLBACK;
        p_status_msg := 'RESERVATION REJECTION: Member account is not in Active status.';
    WHEN e_already_reserved THEN
        ROLLBACK;
        p_status_msg := 'RESERVATION REJECTION: Member ' || v_member_name || ' already has an active waitlist reservation for this title.';
    WHEN e_already_has_copy THEN
        ROLLBACK;
        p_status_msg := 'RESERVATION REJECTION: Member is already in possession of a borrowed copy of this book.';
    WHEN OTHERS THEN
        ROLLBACK;
        p_status_msg := 'SYSTEM ERROR: ' || SQLERRM;
END Reserve_Book_Proc;
/

-- ============================================================================
-- PROCEDURE 4: Pay_Fine_Proc
-- Processes fine remittance, validates unique transaction vouchers, and triggers reactivation.
-- ============================================================================
CREATE OR REPLACE PROCEDURE Pay_Fine_Proc (
    p_fine_id       IN  INTEGER,
    p_method        IN  VARCHAR2,
    p_txn_ref       IN  VARCHAR2,
    p_receipt_msg   OUT VARCHAR2
)
IS
    v_fine_amt          NUMBER;
    v_payment_status    VARCHAR2(20);
    v_member_id         INTEGER;
    v_member_name       VARCHAR2(100);
    v_ref_duplicate     INTEGER;

    e_fine_not_found        EXCEPTION;
    e_already_settled       EXCEPTION;
    e_invalid_method        EXCEPTION;
    e_duplicate_ref         EXCEPTION;
BEGIN
    BEGIN
        SELECT f.fine_amount, f.payment_status, f.member_id, m.first_name || ' ' || m.last_name
        INTO v_fine_amt, v_payment_status, v_member_id, v_member_name
        FROM FINE f
        JOIN MEMBER m ON f.member_id = m.member_id
        WHERE f.fine_id = p_fine_id;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RAISE e_fine_not_found;
    END;

    IF v_payment_status IN ('Paid', 'Waived') THEN
        RAISE e_already_settled;
    END IF;

    IF p_method NOT IN ('UPI', 'Cash', 'Credit Card', 'Debit Card', 'Net Banking') THEN
        RAISE e_invalid_method;
    END IF;

    IF p_txn_ref IS NOT NULL THEN
        SELECT COUNT(*) INTO v_ref_duplicate FROM FINE WHERE transaction_ref = p_txn_ref;
        IF v_ref_duplicate > 0 THEN
            RAISE e_duplicate_ref;
        END IF;
    END IF;

    UPDATE FINE
    SET payment_status = 'Paid',
        paid_on = TRUNC(SYSDATE),
        payment_method = p_method,
        transaction_ref = p_txn_ref
    WHERE fine_id = p_fine_id;
    -- Note: Reactivation of suspended member is triggered by trg_fine_paid_reactivate

    COMMIT;
    p_receipt_msg := 'RECEIPT ISSUED: Fine #' || p_fine_id || ' of INR ' || TO_CHAR(v_fine_amt, 'FM999.00') || 
                     ' paid by ' || v_member_name || ' via ' || p_method || '. Ref: ' || NVL(p_txn_ref, 'CASH_VOUCHER');
    DBMS_OUTPUT.PUT_LINE(p_receipt_msg);

EXCEPTION
    WHEN e_fine_not_found THEN
        ROLLBACK;
        p_receipt_msg := 'PAYMENT REJECTION: Fine record #' || p_fine_id || ' does not exist.';
    WHEN e_already_settled THEN
        ROLLBACK;
        p_receipt_msg := 'PAYMENT REJECTION: Fine #' || p_fine_id || ' has already been settled (' || v_payment_status || ').';
    WHEN e_invalid_method THEN
        ROLLBACK;
        p_receipt_msg := 'PAYMENT REJECTION: Invalid payment method. Allowed: UPI, Cash, Credit Card, Debit Card, Net Banking.';
    WHEN e_duplicate_ref THEN
        ROLLBACK;
        p_receipt_msg := 'PAYMENT REJECTION: Duplicate transaction reference "' || p_txn_ref || '". Voucher already used.';
    WHEN OTHERS THEN
        ROLLBACK;
        p_receipt_msg := 'SYSTEM ERROR: ' || SQLERRM;
END Pay_Fine_Proc;
/
