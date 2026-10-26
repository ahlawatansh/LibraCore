-- ============================================================================
-- LibraCore — Demonstration of Real-World ACID Transactions
-- Database Systems Lab (BCSE302P) Submission File
-- 8 Comprehensive Transaction Scenarios with State Verifications and Constraint Tests
-- ============================================================================

-- ----------------------------------------------------------------------------
-- TRANSACTION 1: Issue Book Successfully (ACID Insertion & Trigger Verification)
-- Demonstrates: Valid member checkout, loan limit check, stock decrement trigger
-- ----------------------------------------------------------------------------
-- Step 1: Check initial stock for Book 1007 (The Art of Computer Programming)
SELECT book_id, title, total_copies, available_copies FROM BOOK WHERE book_id = 1007;

-- Step 2: Issue book to Member 2019 (Siddharth Nair - Student, 0 active loans)
INSERT INTO ISSUE_TRANSACTION (issue_id, book_id, member_id, librarian_id, issue_date, due_date, status)
VALUES (5091, 1007, 2019, 301, date('now'), date('now', '+14 days'), 'Issued');

-- Step 3: Verify trigger trg_issue_decrement_stock decremented available_copies from 2 to 1
SELECT book_id, title, total_copies, available_copies FROM BOOK WHERE book_id = 1007;

-- ----------------------------------------------------------------------------
-- TRANSACTION 2: Prevent Checkout of Out-of-Stock Title (Trigger Abort)
-- Demonstrates: trg_prevent_issue_no_stock rejecting issue when available_copies = 0
-- ----------------------------------------------------------------------------
-- Book 1005 (Design Patterns) has available_copies = 0
SELECT book_id, title, available_copies FROM BOOK WHERE book_id = 1005;

-- The following INSERT fails and aborts cleanly due to trigger enforcement:
-- INSERT INTO ISSUE_TRANSACTION (issue_id, book_id, member_id, librarian_id, issue_date, due_date, status)
-- VALUES (5092, 1005, 2004, 301, date('now'), date('now', '+14 days'), 'Issued');
-- Expected: TRIGGER REJECTION: No copies available for this book.

-- ----------------------------------------------------------------------------
-- TRANSACTION 3: Prevent Checkout for Inactive / Suspended Patron
-- Demonstrates: trg_block_inactive_member rejecting checkout for Member 2017 (Suspended)
-- ----------------------------------------------------------------------------
SELECT member_id, member_code, first_name || ' ' || last_name, status FROM MEMBER WHERE member_id = 2017;

-- The following INSERT fails due to trigger enforcement:
-- INSERT INTO ISSUE_TRANSACTION (issue_id, book_id, member_id, librarian_id, issue_date, due_date, status)
-- VALUES (5093, 1001, 2017, 301, date('now'), date('now', '+14 days'), 'Issued');
-- Expected: TRIGGER REJECTION: Member account is not Active (Suspended or Expired).

-- ----------------------------------------------------------------------------
-- TRANSACTION 4: Return Book on Time (Restoration of Stock, No Fine)
-- Demonstrates: Check-in, trigger trg_return_increment_stock restoring stock
-- ----------------------------------------------------------------------------
-- Check active issue 5016 (Book 1001, due in +9 days)
SELECT issue_id, book_id, member_id, due_date, return_date, status FROM ISSUE_TRANSACTION WHERE issue_id = 5016;
SELECT book_id, available_copies FROM BOOK WHERE book_id = 1001;

-- Process return
UPDATE ISSUE_TRANSACTION
SET return_date = date('now'), status = 'Returned'
WHERE issue_id = 5016;

-- Verify stock incremented by exactly 1
SELECT book_id, available_copies FROM BOOK WHERE book_id = 1001;

-- ----------------------------------------------------------------------------
-- TRANSACTION 5: Return Overdue Book with Fine Generation
-- Demonstrates: Fine assessment at ₹5/day late, capped at book price, insertion into FINE
-- ----------------------------------------------------------------------------
-- Issue 5021: Book 1005, due 11 days ago, return_date IS NULL
SELECT i.issue_id, b.title, b.price, i.due_date, i.return_date
FROM ISSUE_TRANSACTION i
JOIN BOOK b ON i.book_id = b.book_id
WHERE i.issue_id = 5021;

-- Process late return
UPDATE ISSUE_TRANSACTION
SET return_date = date('now'), status = 'Returned'
WHERE issue_id = 5021;

-- Compute and insert fine (11 days * ₹5 = ₹55.00)
INSERT INTO FINE (fine_id, issue_id, member_id, days_overdue, fine_amount, fine_date, payment_status)
VALUES (7091, 5021, 2001, 11, 55.00, date('now'), 'Pending');

SELECT * FROM FINE WHERE fine_id = 7091;

-- ----------------------------------------------------------------------------
-- TRANSACTION 6: Reserve Out-of-Stock Catalog Book
-- Demonstrates: Queue sequencing for popular titles with 0 available stock
-- ----------------------------------------------------------------------------
-- Check current reservation queue for Book 1005
SELECT reservation_id, book_id, member_id, queue_position, status FROM RESERVATION WHERE book_id = 1005 AND status = 'Waiting';

-- Place reservation for Member 2008 (next queue position = 4)
INSERT INTO RESERVATION (reservation_id, book_id, member_id, reserved_on, expires_on, queue_position, status)
VALUES (6091, 1005, 2008, date('now'), date('now', '+7 days'), 4, 'Waiting');

SELECT * FROM RESERVATION WHERE reservation_id = 6091;

-- ----------------------------------------------------------------------------
-- TRANSACTION 7: Settle Overdue Fine and Auto-Reactivate Member
-- Demonstrates: Fine remittance voucher and trigger trg_fine_paid_reactivate
-- ----------------------------------------------------------------------------
-- Member 2017 is Suspended due to fine 7010 (₹570.00)
SELECT member_id, first_name || ' ' || last_name, status FROM MEMBER WHERE member_id = 2017;
SELECT fine_id, member_id, fine_amount, payment_status FROM FINE WHERE fine_id = 7010;

-- Settle fine in full
UPDATE FINE
SET payment_status = 'Paid',
    paid_on = date('now'),
    payment_method = 'UPI',
    transaction_ref = 'TXN_SETTLE_7010_UPI'
WHERE fine_id = 7010;

-- Verify member status automatically flipped back to 'Active' via trigger
SELECT member_id, first_name || ' ' || last_name, status FROM MEMBER WHERE member_id = 2017;

-- ----------------------------------------------------------------------------
-- TRANSACTION 8: Relational Foreign Key Integrity Enforcement (ON DELETE RESTRICT)
-- Demonstrates: Attempting to delete a catalog book with active circulation history
-- ----------------------------------------------------------------------------
-- Book 1001 has active/historical issues in ISSUE_TRANSACTION
-- The following DELETE fails with FOREIGN KEY constraint failed:
-- DELETE FROM BOOK WHERE book_id = 1001;
-- Expected: IntegrityError: FOREIGN KEY constraint failed (Restricted deletion)

-- Demonstrates safe deletion of an unreferenced waitlist reservation:
DELETE FROM RESERVATION WHERE reservation_id = 6091;
SELECT count(*) AS remaining_reservations FROM RESERVATION WHERE reservation_id = 6091;
