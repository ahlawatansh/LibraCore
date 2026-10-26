-- ============================================================================
-- LibraCore — Real SQLite Triggers
-- Enforces automatic stock decrement/increment, safety checks, and auto-suspension
-- ============================================================================

DROP TRIGGER IF EXISTS trg_prevent_issue_no_stock;
DROP TRIGGER IF EXISTS trg_block_inactive_member;
DROP TRIGGER IF EXISTS trg_issue_decrement_stock;
DROP TRIGGER IF EXISTS trg_return_increment_stock;
DROP TRIGGER IF EXISTS trg_fine_suspend_member;
DROP TRIGGER IF EXISTS trg_fine_paid_reactivate;

-- 1. Prevent issue if available copies = 0
CREATE TRIGGER trg_prevent_issue_no_stock
BEFORE INSERT ON ISSUE_TRANSACTION
FOR EACH ROW
WHEN (SELECT available_copies FROM BOOK WHERE book_id = NEW.book_id) <= 0
BEGIN
    SELECT RAISE(ABORT, 'TRIGGER REJECTION: No copies available for this book.');
END;

-- 2. Prevent issue if member is not Active
CREATE TRIGGER trg_block_inactive_member
BEFORE INSERT ON ISSUE_TRANSACTION
FOR EACH ROW
WHEN (SELECT status FROM MEMBER WHERE member_id = NEW.member_id) != 'Active'
BEGIN
    SELECT RAISE(ABORT, 'TRIGGER REJECTION: Member account is not Active (Suspended or Expired).');
END;

-- 3. Decrement available stock on successful issue
CREATE TRIGGER trg_issue_decrement_stock
AFTER INSERT ON ISSUE_TRANSACTION
FOR EACH ROW
WHEN NEW.status = 'Issued'
BEGIN
    UPDATE BOOK
    SET available_copies = available_copies - 1
    WHERE book_id = NEW.book_id;
END;

-- 4. Increment stock on book return
CREATE TRIGGER trg_return_increment_stock
AFTER UPDATE OF return_date ON ISSUE_TRANSACTION
FOR EACH ROW
WHEN OLD.return_date IS NULL AND NEW.return_date IS NOT NULL
BEGIN
    UPDATE BOOK
    SET available_copies = available_copies + 1
    WHERE book_id = NEW.book_id;
END;

-- 5. Auto-suspend member when unpaid fines exceed ₹500
CREATE TRIGGER trg_fine_suspend_member
AFTER INSERT ON FINE
FOR EACH ROW
WHEN (
    SELECT COALESCE(SUM(fine_amount), 0)
    FROM FINE
    WHERE member_id = NEW.member_id AND payment_status = 'Pending'
) > 500.00
BEGIN
    UPDATE MEMBER
    SET status = 'Suspended'
    WHERE member_id = NEW.member_id AND status = 'Active';
END;

-- 6. Auto-reactivate member when pending dues drop to <= ₹200 after payment
CREATE TRIGGER trg_fine_paid_reactivate
AFTER UPDATE OF payment_status ON FINE
FOR EACH ROW
WHEN NEW.payment_status IN ('Paid', 'Waived') AND (
    SELECT COALESCE(SUM(fine_amount), 0)
    FROM FINE
    WHERE member_id = NEW.member_id AND payment_status = 'Pending'
) <= 200.00
BEGIN
    UPDATE MEMBER
    SET status = 'Active'
    WHERE member_id = NEW.member_id AND status = 'Suspended';
END;
