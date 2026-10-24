-- ============================================================================
-- LibraCore — Oracle PL/SQL Cursors
-- Database Systems Lab (BCSE302P) Submission File
-- Explicit Cursors for Institutional Overdue Audits and Patron Activity Classification
-- ============================================================================

-- ============================================================================
-- CURSOR 1: Overdue_Report_Cursor
-- Iterates through active overdue loans, categorizes risk severity, and aggregates dues.
-- ============================================================================
CREATE OR REPLACE PROCEDURE Overdue_Report_Cursor
IS
    -- Explicit cursor definition
    CURSOR cur_overdue IS
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
               TRUNC(SYSDATE) - TRUNC(i.due_date) AS days_late
        FROM ISSUE_TRANSACTION i
        JOIN MEMBER m ON i.member_id = m.member_id
        JOIN BOOK b ON i.book_id = b.book_id
        WHERE i.return_date IS NULL AND i.due_date < TRUNC(SYSDATE)
        ORDER BY days_late DESC;

    -- Record variable
    r_overdue cur_overdue%ROWTYPE;

    -- Aggregate counters
    v_total_overdue      INTEGER := 0;
    v_minor_count        INTEGER := 0;
    v_serious_count      INTEGER := 0;
    v_critical_count     INTEGER := 0;
    v_total_projected    NUMBER := 0.00;
    v_projected_fine     NUMBER := 0.00;
    v_severity           VARCHAR2(30);
BEGIN
    DBMS_OUTPUT.PUT_LINE('================================================================================');
    DBMS_OUTPUT.PUT_LINE('               LIBRACORE — INSTITUTIONAL OVERDUE AUDIT REPORT                   ');
    DBMS_OUTPUT.PUT_LINE('================================================================================');
    DBMS_OUTPUT.PUT_LINE(RPAD('ISSUE', 7) || RPAD('MEMBER', 12) || RPAD('NAME', 20) || RPAD('BOOK TITLE', 24) || RPAD('DAYS', 6) || RPAD('FINE(INR)', 11) || 'SEVERITY');
    DBMS_OUTPUT.PUT_LINE('--------------------------------------------------------------------------------');

    OPEN cur_overdue;
    LOOP
        FETCH cur_overdue INTO r_overdue;
        EXIT WHEN cur_overdue%NOTFOUND;

        v_total_overdue := v_total_overdue + 1;
        v_projected_fine := LEAST(r_overdue.days_late * 5.00, r_overdue.book_price);
        v_total_projected := v_total_projected + v_projected_fine;

        IF r_overdue.days_late <= 7 THEN
            v_severity := 'Minor Overdue';
            v_minor_count := v_minor_count + 1;
        ELSIF r_overdue.days_late <= 30 THEN
            v_severity := 'Serious Overdue';
            v_serious_count := v_serious_count + 1;
        ELSE
            v_severity := 'Critical Overdue';
            v_critical_count := v_critical_count + 1;
        END IF;

        DBMS_OUTPUT.PUT_LINE(
            RPAD('#' || r_overdue.issue_id, 7) ||
            RPAD(r_overdue.member_code, 12) ||
            RPAD(SUBSTR(r_overdue.member_name, 1, 18), 20) ||
            RPAD(SUBSTR(r_overdue.book_title, 1, 22), 24) ||
            RPAD(TO_CHAR(r_overdue.days_late), 6) ||
            RPAD(TO_CHAR(v_projected_fine, 'FM990.00'), 11) ||
            v_severity
        );
    END LOOP;
    CLOSE cur_overdue;

    DBMS_OUTPUT.PUT_LINE('================================================================================');
    DBMS_OUTPUT.PUT_LINE('AUDIT SUMMARY:');
    DBMS_OUTPUT.PUT_LINE('Total Overdue Loans : ' || v_total_overdue);
    DBMS_OUTPUT.PUT_LINE('  - Minor (1-7 days)      : ' || v_minor_count);
    DBMS_OUTPUT.PUT_LINE('  - Serious (8-30 days)   : ' || v_serious_count);
    DBMS_OUTPUT.PUT_LINE('  - Critical (> 30 days)  : ' || v_critical_count);
    DBMS_OUTPUT.PUT_LINE('Total Accrued Fines (INR): ' || TO_CHAR(v_total_projected, 'FM99,990.00'));
    DBMS_OUTPUT.PUT_LINE('================================================================================');
END Overdue_Report_Cursor;
/

-- ============================================================================
-- CURSOR 2: Member_Activity_Cursor
-- Explicit cursor to profile member engagement, circulation frequency, and dues.
-- ============================================================================
CREATE OR REPLACE PROCEDURE Member_Activity_Cursor
IS
    CURSOR cur_activity IS
        SELECT m.member_id,
               m.member_code,
               m.first_name || ' ' || m.last_name AS full_name,
               m.member_type,
               m.department,
               m.status,
               COUNT(i.issue_id) AS total_loans,
               SUM(CASE WHEN i.status = 'Issued' THEN 1 ELSE 0 END) AS active_loans,
               SUM(CASE WHEN i.status = 'Returned' THEN 1 ELSE 0 END) AS returned_loans,
               NVL(f.pending_amount, 0.00) AS pending_fines
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

    r_act cur_activity%ROWTYPE;
    v_standing VARCHAR2(30);
BEGIN
    DBMS_OUTPUT.PUT_LINE('================================================================================');
    DBMS_OUTPUT.PUT_LINE('               LIBRACORE — PATRON ACTIVITY & ENGAGEMENT MATRIX                 ');
    DBMS_OUTPUT.PUT_LINE('================================================================================');
    DBMS_OUTPUT.PUT_LINE(RPAD('CODE', 12) || RPAD('PATRON NAME', 22) || RPAD('TYPE', 9) || RPAD('TOTAL', 7) || RPAD('ACTIVE', 8) || RPAD('FINES(INR)', 12) || 'TIER');
    DBMS_OUTPUT.PUT_LINE('--------------------------------------------------------------------------------');

    OPEN cur_activity;
    LOOP
        FETCH cur_activity INTO r_act;
        EXIT WHEN cur_activity%NOTFOUND;

        IF r_act.total_loans >= 4 THEN
            v_standing := 'Power Reader';
        ELSIF r_act.total_loans >= 1 THEN
            v_standing := 'Regular Reader';
        ELSE
            v_standing := 'Inactive Patron';
        END IF;

        DBMS_OUTPUT.PUT_LINE(
            RPAD(r_act.member_code, 12) ||
            RPAD(SUBSTR(r_act.full_name, 1, 20), 22) ||
            RPAD(r_act.member_type, 9) ||
            RPAD(TO_CHAR(r_act.total_loans), 7) ||
            RPAD(TO_CHAR(NVL(r_act.active_loans, 0)), 8) ||
            RPAD(TO_CHAR(r_act.pending_fines, 'FM990.00'), 12) ||
            v_standing
        );
    END LOOP;
    CLOSE cur_activity;
    DBMS_OUTPUT.PUT_LINE('================================================================================');
END Member_Activity_Cursor;
/
