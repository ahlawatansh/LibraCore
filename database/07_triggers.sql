-- ============================================================================
-- LibraCore — Oracle PL/SQL Triggers
-- Database Systems Lab (BCSE302P) Submission File
-- Enforces business rules, real-time stock integrity, and automated penalties
-- ============================================================================

-- Trigger 1: Decrement available book stock upon issue
CREATE OR REPLACE TRIGGER trg_issue_decrement_stock
AFTER INSERT ON ISSUE_TRANSACTION
FOR EACH ROW
WHEN (NEW.status = 'Issued')
BEGIN
    UPDATE BOOK
    SET available_copies = available_copies - 1
    WHERE book_id = :NEW.book_id;
END;
/

-- Trigger 2: Increment available book stock upon return
CREATE OR REPLACE TRIGGER trg_return_increment_stock
AFTER UPDATE OF return_date ON ISSUE_TRANSACTION
FOR EACH ROW
WHEN (OLD.return_date IS NULL AND NEW.return_date IS NOT NULL)
BEGIN
    UPDATE BOOK
    SET available_copies = available_copies + 1
    WHERE book_id = :NEW.book_id;
END;
/

-- Trigger 3: Prevent issuing a book when available copies reach 0
CREATE OR REPLACE TRIGGER trg_prevent_issue_no_stock
BEFORE INSERT ON ISSUE_TRANSACTION
FOR EACH ROW
DECLARE
    v_available INTEGER;
BEGIN
    SELECT available_copies INTO v_available
    FROM BOOK
    WHERE book_id = :NEW.book_id;

    IF v_available <= 0 THEN
        RAISE_APPLICATION_ERROR(-20001, 'CIRCULATION ERROR: No copies available for book ID ' || :NEW.book_id);
    END IF;
END;
/

-- Trigger 4: Block circulation if the member is Suspended or Expired
CREATE OR REPLACE TRIGGER trg_block_inactive_member
BEFORE INSERT ON ISSUE_TRANSACTION
FOR EACH ROW
DECLARE
    v_status VARCHAR2(20);
    v_expiry DATE;
BEGIN
    SELECT status, membership_expiry INTO v_status, v_expiry
    FROM MEMBER
    WHERE member_id = :NEW.member_id;

    IF v_status != 'Active' THEN
        RAISE_APPLICATION_ERROR(-20002, 'CIRCULATION ERROR: Member status is ' || v_status || '. Circulation suspended.');
    END IF;

    IF v_expiry < SYSDATE THEN
        RAISE_APPLICATION_ERROR(-20003, 'CIRCULATION ERROR: Membership has expired on ' || TO_CHAR(v_expiry, 'YYYY-MM-DD'));
    END IF;
END;
/

-- Trigger 5: Automatically suspend member if cumulative pending fines exceed ₹500
CREATE OR REPLACE TRIGGER trg_fine_suspend_member
AFTER INSERT ON FINE
FOR EACH ROW
DECLARE
    v_total_pending NUMBER;
BEGIN
    SELECT NVL(SUM(fine_amount), 0) INTO v_total_pending
    FROM FINE
    WHERE member_id = :NEW.member_id AND payment_status = 'Pending';

    IF v_total_pending > 500.00 THEN
        UPDATE MEMBER
        SET status = 'Suspended'
        WHERE member_id = :NEW.member_id AND status = 'Active';
    END IF;
END;
/

-- Trigger 6: Automatically reactivate suspended member when outstanding dues drop <= ₹200
CREATE OR REPLACE TRIGGER trg_fine_paid_reactivate
AFTER UPDATE OF payment_status ON FINE
FOR EACH ROW
DECLARE
    v_total_pending NUMBER;
    v_status VARCHAR2(20);
BEGIN
    SELECT status INTO v_status FROM MEMBER WHERE member_id = :NEW.member_id;

    IF v_status = 'Suspended' THEN
        SELECT NVL(SUM(fine_amount), 0) INTO v_total_pending
        FROM FINE
        WHERE member_id = :NEW.member_id AND payment_status = 'Pending';

        IF v_total_pending <= 200.00 THEN
            UPDATE MEMBER
            SET status = 'Active'
            WHERE member_id = :NEW.member_id;
        END IF;
    END IF;
END;
/
