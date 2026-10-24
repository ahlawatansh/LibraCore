-- ============================================================================
-- LibraCore — Oracle PL/SQL Functions
-- Database Systems Lab (BCSE302P) Submission File
-- Fine Calculation, Outstanding Dues Aggregation, and Loan Period Matrix
-- ============================================================================

-- ============================================================================
-- FUNCTION 1: Calculate_Fine_Func
-- Computes overdue penalty at ₹5 per overdue day, strictly capped at book price.
-- ============================================================================
CREATE OR REPLACE FUNCTION Calculate_Fine_Func (
    p_issue_id IN INTEGER
) RETURN NUMBER
IS
    v_due_date      DATE;
    v_return_date   DATE;
    v_book_price    NUMBER;
    v_days_late     INTEGER;
    v_raw_fine      NUMBER;
    v_final_fine    NUMBER;
BEGIN
    SELECT i.due_date, i.return_date, b.price
    INTO v_due_date, v_return_date, v_book_price
    FROM ISSUE_TRANSACTION i
    JOIN BOOK b ON i.book_id = b.book_id
    WHERE i.issue_id = p_issue_id;

    -- If return_date is recorded, compute days late based on check-in date; otherwise use SYSDATE
    IF v_return_date IS NOT NULL THEN
        v_days_late := TRUNC(v_return_date) - TRUNC(v_due_date);
    ELSE
        v_days_late := TRUNC(SYSDATE) - TRUNC(v_due_date);
    END IF;

    -- No fine if returned on or before due date
    IF v_days_late <= 0 THEN
        RETURN 0.00;
    END IF;

    -- ₹5 per day late, capped at the book's replacement price
    v_raw_fine := v_days_late * 5.00;
    v_final_fine := LEAST(v_raw_fine, v_book_price);

    RETURN ROUND(v_final_fine, 2);

EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RETURN 0.00;
    WHEN OTHERS THEN
        RETURN 0.00;
END Calculate_Fine_Func;
/

-- ============================================================================
-- FUNCTION 2: Get_Member_Pending_Fine_Func
-- Returns cumulative outstanding unpaid fines for a member.
-- ============================================================================
CREATE OR REPLACE FUNCTION Get_Member_Pending_Fine_Func (
    p_member_id IN INTEGER
) RETURN NUMBER
IS
    v_total_pending NUMBER;
BEGIN
    SELECT NVL(SUM(fine_amount), 0.00)
    INTO v_total_pending
    FROM FINE
    WHERE member_id = p_member_id AND payment_status = 'Pending';

    RETURN ROUND(v_total_pending, 2);

EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RETURN 0.00;
    WHEN OTHERS THEN
        RETURN 0.00;
END Get_Member_Pending_Fine_Func;
/

-- ============================================================================
-- FUNCTION 3: Get_Loan_Days_Func
-- Returns allowed loan duration (days) according to patron category.
-- ============================================================================
CREATE OR REPLACE FUNCTION Get_Loan_Days_Func (
    p_member_type IN VARCHAR2
) RETURN NUMBER
IS
BEGIN
    CASE UPPER(TRIM(p_member_type))
        WHEN 'STUDENT' THEN
            RETURN 14;
        WHEN 'FACULTY' THEN
            RETURN 30;
        WHEN 'STAFF' THEN
            RETURN 21;
        ELSE
            RETURN 14;
    END CASE;
END Get_Loan_Days_Func;
/
