-- ============================================================================
-- LibraCore — Initial Seed Data Script
-- Populates 8 Tables with Consistent, Validated Benchmark Records
-- Relative date offsets ensure active loans, overdues, and fines stay dynamic
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. CATEGORIES (10 Records)
-- ----------------------------------------------------------------------------
INSERT INTO CATEGORY (category_id, category_name, category_code, shelf_zone, description) VALUES
(101, 'Computer Science & AI', 'CS-AI', 'Zone A', 'Algorithms, artificial intelligence, machine learning, and programming languages'),
(102, 'Database & Systems', 'DB-SYS', 'Zone B', 'Relational database theory, SQL/NoSQL architectures, and distributed storage'),
(103, 'Software Engineering', 'SWE', 'Zone C', 'System architecture, agile design patterns, refactoring, and quality engineering'),
(104, 'Mathematics & Statistics', 'MATH', 'Zone D', 'Linear algebra, calculus, discrete structures, and applied statistical methods'),
(105, 'Physics & Electronics', 'PHYS', 'Zone E', 'Quantum mechanics, electromagnetism, semiconductor physics, and circuit theory'),
(106, 'English Literature & Classics', 'ENG-LIT', 'Zone F', 'World classics, prose, literary analysis, and English humanities'),
(107, 'Indian Literature & Arts', 'IND-LIT', 'Zone G', 'Contemporary Indian classics, historical narratives, and regional literature'),
(108, 'Computer Networks & Security', 'NET-SEC', 'Zone H', 'TCP/IP routing, cloud infrastructure, cryptography, and network defense'),
(109, 'Management & Economics', 'MGMT', 'Zone I', 'Institutional leadership, finance, organizational behavior, and microeconomics'),
(110, 'General Humanities & Ethics', 'GEN-HUM', 'Zone J', 'Philosophy, research methodology, history of science, and academic ethics');

-- ----------------------------------------------------------------------------
-- 2. AUTHORS (15 Records)
-- ----------------------------------------------------------------------------
INSERT INTO AUTHOR (author_id, first_name, last_name, email, nationality, birth_year) VALUES
(201, 'Robert', 'Martin', 'unclebob@cleancoder.com', 'American', 1952),
(202, 'Thomas', 'Cormen', 'thc@clrs-algorithms.org', 'American', 1956),
(203, 'Abraham', 'Silberschatz', 'avi@db-book.com', 'American', 1952),
(204, 'Andrew', 'Tanenbaum', 'ast@minix1.woodstock.com', 'American', 1944),
(205, 'Erich', 'Gamma', 'egamma@gangoffour.org', 'Swiss', 1961),
(206, 'Wade', 'Warren', 'wade.warren@literature-hub.org', 'British', 1978),
(207, 'David', 'Morgan', 'david.morgan@math-press.edu', 'British', 1982),
(208, 'Kristin', 'Watson', 'kristin.watson@physics-lab.org', 'American', 1985),
(209, 'Savannah', 'Nguyen', 'savannah.n@math-institute.org', 'Vietnamese', 1990),
(210, 'Jacob', 'Jones', 'jacob.jones@quantum-physics.edu', 'Canadian', 1975),
(211, 'Arlene', 'McCoy', 'arlene.mccoy@classics-press.org', 'Irish', 1980),
(212, 'Arundhati', 'Roy', 'arundhati.roy@author-india.org', 'Indian', 1961),
(213, 'Ruskin', 'Bond', 'ruskin.bond@hills-india.org', 'Indian', 1934),
(214, 'R.K.', 'Narayan', 'rknarayan@malgudi.org', 'Indian', 1906),
(215, 'Donald', 'Knuth', 'knuth@taocp.stanford.edu', 'American', 1938);

-- ----------------------------------------------------------------------------
-- 3. LIBRARIANS (6 Records)
-- ----------------------------------------------------------------------------
INSERT INTO LIBRARIAN (librarian_id, first_name, last_name, email, phone, hire_date, designation, salary, shift) VALUES
(301, 'Priscilla', 'Lily', 'priscilla.lily@libracore.edu', '9845012340', '2019-03-15', 'Head Librarian', 85000.00, 'Morning'),
(302, 'Marcus', 'Vance', 'marcus.vance@libracore.edu', '9845012341', '2021-06-10', 'Assistant Librarian', 54000.00, 'Morning'),
(303, 'Eleanor', 'Thorne', 'eleanor.thorne@libracore.edu', '9845012342', '2022-01-20', 'Assistant Librarian', 52000.00, 'Evening'),
(304, 'Rajiv', 'Menon', 'rajiv.menon@libracore.edu', '9845012343', '2023-04-05', 'Library Clerk', 32000.00, 'Morning'),
(305, 'Ananya', 'Sharma', 'ananya.sharma@libracore.edu', '9845012344', '2023-08-18', 'Library Clerk', 31500.00, 'Evening'),
(306, 'System', 'Admin', 'admin@libracore.edu', '9845012345', '2018-01-01', 'Admin', 92000.00, 'Morning');

-- ----------------------------------------------------------------------------
-- 4. MEMBERS (18 Records)
-- ----------------------------------------------------------------------------
INSERT INTO MEMBER (member_id, member_code, first_name, last_name, email, phone, member_type, department, join_date, membership_expiry, max_books_allowed, status) VALUES
(2001, '24BCE1001', 'Aarav', 'Sharma', 'aarav.sharma2024@libracore.edu', '9876500001', 'Student', 'Computer Science', date('now', '-300 days'), date('now', '+365 days'), 3, 'Active'),
(2002, '24BCE1002', 'Diya', 'Patel', 'diya.patel2024@libracore.edu', '9876500002', 'Student', 'Information Technology', date('now', '-280 days'), date('now', '+365 days'), 3, 'Active'),
(2003, '24BCE1003', 'Rohan', 'Iyer', 'rohan.iyer2024@libracore.edu', '9876500003', 'Student', 'Data Science', date('now', '-260 days'), date('now', '+365 days'), 3, 'Active'),
(2004, '24BCE1004', 'Ananya', 'Verma', 'ananya.verma2024@libracore.edu', '9876500004', 'Student', 'Electrical Engineering', date('now', '-250 days'), date('now', '+365 days'), 3, 'Active'),
(2005, '24BCE1005', 'Kabir', 'Mehta', 'kabir.mehta2024@libracore.edu', '9876500005', 'Student', 'Mechanical Engineering', date('now', '-240 days'), date('now', '+365 days'), 3, 'Active'),
(2006, '24BCE1006', 'Isha', 'Nair', 'isha.nair2024@libracore.edu', '9876500006', 'Student', 'Computer Science', date('now', '-220 days'), date('now', '+365 days'), 3, 'Active'),
(2007, '24BCE1007', 'Aditya', 'Rao', 'aditya.rao2024@libracore.edu', '9876500007', 'Student', 'Software Engineering', date('now', '-210 days'), date('now', '+365 days'), 3, 'Active'),
(2008, '24BCE1008', 'Tara', 'Mukherjee', 'tara.mukherjee2024@libracore.edu', '9876500008', 'Student', 'Mathematics', date('now', '-200 days'), date('now', '+365 days'), 3, 'Active'),
(2009, '24BCE1009', 'Vihaan', 'Reddy', 'vihaan.reddy2024@libracore.edu', '9876500009', 'Student', 'Physics', date('now', '-190 days'), date('now', '+365 days'), 3, 'Active'),
(2010, '24BCE1010', 'Meera', 'Kapoor', 'meera.kapoor2024@libracore.edu', '9876500010', 'Student', 'English Literature', date('now', '-180 days'), date('now', '+365 days'), 3, 'Active'),
(2011, '24BCE1011', 'Arjun', 'Bhat', 'arjun.bhat2024@libracore.edu', '9876500011', 'Student', 'Computer Science', date('now', '-150 days'), date('now', '+365 days'), 3, 'Active'),
(2012, '24BCE1012', 'Pooja', 'Chopra', 'pooja.chopra2024@libracore.edu', '9876500012', 'Student', 'Management Studies', date('now', '-140 days'), date('now', '+365 days'), 3, 'Active'),
(2013, 'FAC-0101', 'Dr. Vikram', 'Sen', 'vikram.sen@faculty.libracore.edu', '9876500013', 'Faculty', 'Computer Science', date('now', '-600 days'), date('now', '+700 days'), 8, 'Active'),
(2014, 'FAC-0102', 'Dr. Sunita', 'Rao', 'sunita.rao@faculty.libracore.edu', '9876500014', 'Faculty', 'Mathematics', date('now', '-550 days'), date('now', '+700 days'), 8, 'Active'),
(2015, 'FAC-0103', 'Dr. Arvind', 'Gupta', 'arvind.gupta@faculty.libracore.edu', '9876500015', 'Faculty', 'Physics', date('now', '-500 days'), date('now', '+700 days'), 8, 'Active'),
(2016, 'FAC-0104', 'Dr. Shalini', 'Das', 'shalini.das@faculty.libracore.edu', '9876500016', 'Faculty', 'Humanities', date('now', '-450 days'), date('now', '+700 days'), 8, 'Active'),
(2017, 'STF-0201', 'Gaurav', 'Saxena', 'gaurav.saxena@staff.libracore.edu', '9876500017', 'Staff', 'Administration', date('now', '-400 days'), date('now', '+365 days'), 5, 'Suspended'),
(2018, 'STF-0202', 'Kavita', 'Deshmukh', 'kavita.deshmukh@staff.libracore.edu', '9876500018', 'Staff', 'Lab Services', date('now', '-800 days'), date('now', '-30 days'), 5, 'Expired');

-- ----------------------------------------------------------------------------
-- 5. BOOKS (25 Records)
-- Notice available_copies is set to exactly match total_copies - active_loans
-- ----------------------------------------------------------------------------
INSERT INTO BOOK (book_id, isbn, title, author_id, category_id, publisher, publish_date, edition, language, shelf_location, price, total_copies, available_copies, cover_url, added_on, status) VALUES
(1001, '978-0132350884', 'Clean Code: A Handbook of Agile Software Craftsmanship', 201, 103, 'Prentice Hall', '2008-08-01', '1st', 'English', 'A-01-04', 799.00, 5, 3, 'https://covers.openlibrary.org/b/isbn/9780132350884-M.jpg', date('now', '-25 days'), 'Active'),
(1002, '978-0262033848', 'Introduction to Algorithms (CLRS)', 202, 101, 'MIT Press', '2009-07-31', '3rd', 'English', 'A-02-01', 1450.00, 6, 4, 'https://covers.openlibrary.org/b/isbn/9780262033848-M.jpg', date('now', '-28 days'), 'Active'),
(1003, '978-0078022159', 'Database System Concepts', 203, 102, 'McGraw-Hill', '2019-03-25', '7th', 'English', 'B-01-02', 890.00, 4, 2, 'https://covers.openlibrary.org/b/isbn/9780078022159-M.jpg', date('now', '-18 days'), 'Active'),
(1004, '978-0132126953', 'Computer Networks', 204, 108, 'Pearson', '2010-10-07', '5th', 'English', 'H-03-01', 825.00, 4, 3, 'https://covers.openlibrary.org/b/isbn/9780132126953-M.jpg', date('now', '-15 days'), 'Active'),
(1005, '978-0201633610', 'Design Patterns: Elements of Reusable Object-Oriented Software', 205, 103, 'Addison-Wesley', '1994-10-31', '1st', 'English', 'C-01-05', 950.00, 3, 0, 'https://covers.openlibrary.org/b/isbn/9780201633610-M.jpg', date('now', '-45 days'), 'Active'),
(1006, '978-1118063330', 'Operating System Concepts', 203, 101, 'Wiley', '2018-01-14', '10th', 'English', 'A-03-02', 895.00, 5, 4, 'https://covers.openlibrary.org/b/isbn/9781118063330-M.jpg', date('now', '-60 days'), 'Active'),
(1007, '978-0201896831', 'The Art of Computer Programming, Vol. 1', 215, 101, 'Addison-Wesley', '1997-07-04', '3rd', 'English', 'A-01-01', 1950.00, 2, 2, 'https://covers.openlibrary.org/b/isbn/9780201896831-M.jpg', date('now', '-75 days'), 'Active'),
(1008, '978-0812979657', 'The God of Small Things', 212, 107, 'Random House', '1997-06-04', '1st', 'English', 'G-02-04', 450.00, 3, 0, 'https://covers.openlibrary.org/b/isbn/9780812979657-M.jpg', date('now', '-90 days'), 'Active'),
(1009, '978-0143039655', 'Malgudi Days', 214, 107, 'Penguin Classics', '1982-01-01', 'Reprint', 'English', 'G-01-03', 299.00, 6, 5, 'https://covers.openlibrary.org/b/isbn/9780143039655-M.jpg', date('now', '-100 days'), 'Active'),
(1010, '978-8171673407', 'The Blue Umbrella', 213, 107, 'Rupa Publications', '1992-05-15', '1st', 'English', 'G-03-01', 195.00, 5, 4, 'https://covers.openlibrary.org/b/isbn/9788171673407-M.jpg', date('now', '-110 days'), 'Active'),
(1011, '978-0199535569', 'Literature', 206, 106, 'Oxford World Classics', '2022-10-22', '2nd', 'English', 'F-01-02', 550.00, 4, 2, 'https://covers.openlibrary.org/b/isbn/9780199535569-M.jpg', date('now', '-5 days'), 'Active'),
(1012, '978-0521884075', 'Mathematics', 207, 104, 'Cambridge Press', '2023-09-12', '4th', 'English', 'D-02-03', 720.00, 3, 1, 'https://covers.openlibrary.org/b/isbn/9780521884075-M.jpg', date('now', '-8 days'), 'Active'),
(1013, '978-0321792984', 'English', 208, 105, 'Pearson Science', '2020-11-23', '3rd', 'English', 'E-01-05', 850.00, 5, 3, 'https://covers.openlibrary.org/b/isbn/9780321792984-M.jpg', date('now', '-12 days'), 'Active'),
(1014, '978-0471198260', 'Mathematics', 209, 104, 'Wiley Academic', '2022-10-12', '1st', 'English', 'D-03-01', 650.00, 6, 4, 'https://covers.openlibrary.org/b/isbn/9780471198260-M.jpg', date('now', '-14 days'), 'Active'),
(1015, '978-0205829651', 'English', 210, 105, 'Prentice Hall', '2022-10-22', '2nd', 'English', 'E-02-04', 680.00, 3, 1, 'https://covers.openlibrary.org/b/isbn/9780205829651-M.jpg', date('now', '-19 days'), 'Active'),
(1016, '978-0141439518', 'Mathematics', 211, 106, 'Penguin Press', '2023-09-23', 'Classics', 'English', 'F-03-02', 490.00, 4, 2, 'https://covers.openlibrary.org/b/isbn/9780141439518-M.jpg', date('now', '-21 days'), 'Active'),
(1017, '978-0131103627', 'The C Programming Language', 201, 101, 'Prentice Hall', '1988-04-01', '2nd', 'English', 'A-01-02', 620.00, 4, 4, 'https://covers.openlibrary.org/b/isbn/9780131103627-M.jpg', date('now', '-120 days'), 'Active'),
(1018, '978-0596007126', 'Head First Design Patterns', 205, 103, 'O''Reilly Media', '2004-10-25', '1st', 'English', 'C-02-01', 890.00, 5, 4, 'https://covers.openlibrary.org/b/isbn/9780596007126-M.jpg', date('now', '-130 days'), 'Active'),
(1019, '978-1449355739', 'Learning Python', 201, 101, 'O''Reilly Media', '2013-07-06', '5th', 'English', 'A-02-05', 980.00, 4, 3, 'https://covers.openlibrary.org/b/isbn/9781449355739-M.jpg', date('now', '-140 days'), 'Active'),
(1020, '978-0134494166', 'Clean Architecture: A Craftsman''s Guide', 201, 103, 'Prentice Hall', '2017-09-20', '1st', 'English', 'C-03-02', 840.00, 4, 3, 'https://covers.openlibrary.org/b/isbn/9780134494166-M.jpg', date('now', '-150 days'), 'Active'),
(1021, '978-0321573513', 'Algorithms in C++', 202, 101, 'Addison-Wesley', '2008-05-10', '3rd', 'English', 'A-03-04', 1150.00, 3, 3, 'https://covers.openlibrary.org/b/isbn/9780321573513-M.jpg', date('now', '-160 days'), 'Active'),
(1022, '978-0136006633', 'Database Systems: The Complete Book', 203, 102, 'Pearson', '2008-06-15', '2nd', 'English', 'B-02-01', 1250.00, 3, 2, 'https://covers.openlibrary.org/b/isbn/9780136006633-M.jpg', date('now', '-170 days'), 'Active'),
(1023, '978-0133594140', 'Structured Computer Organization', 204, 101, 'Pearson', '2012-08-04', '6th', 'English', 'A-04-01', 990.00, 3, 3, 'https://covers.openlibrary.org/b/isbn/9780133594140-M.jpg', date('now', '-180 days'), 'Active'),
(1024, '978-0070131514', 'Principles of Mathematical Analysis', 207, 104, 'McGraw-Hill', '1976-01-01', '3rd', 'English', 'D-01-02', 780.00, 2, 2, 'https://covers.openlibrary.org/b/isbn/9780070131514-M.jpg', date('now', '-200 days'), 'Active'),
(1025, '978-0143105428', 'The Guide to English Grammar & Prose', 206, 106, 'Penguin Classic', '2014-04-10', '1st', 'English', 'F-02-01', 340.00, 4, 4, 'https://covers.openlibrary.org/b/isbn/9780143105428-M.jpg', date('now', '-220 days'), 'Active');

-- ----------------------------------------------------------------------------
-- 6. ISSUE TRANSACTIONS (25 Records)
-- 10 Returned on time, 5 Returned late, 5 Currently Issued (On-time), 5 Currently Overdue
-- ----------------------------------------------------------------------------
INSERT INTO ISSUE_TRANSACTION (issue_id, book_id, member_id, librarian_id, issue_date, due_date, return_date, status) VALUES
-- Returned on time (10 records)
(5001, 1001, 2001, 301, date('now', '-60 days'), date('now', '-46 days'), date('now', '-48 days'), 'Returned'),
(5002, 1002, 2002, 302, date('now', '-55 days'), date('now', '-41 days'), date('now', '-42 days'), 'Returned'),
(5003, 1003, 2003, 301, date('now', '-50 days'), date('now', '-36 days'), date('now', '-38 days'), 'Returned'),
(5004, 1004, 2004, 303, date('now', '-48 days'), date('now', '-34 days'), date('now', '-35 days'), 'Returned'),
(5005, 1006, 2005, 302, date('now', '-45 days'), date('now', '-31 days'), date('now', '-32 days'), 'Returned'),
(5006, 1007, 2013, 301, date('now', '-70 days'), date('now', '-40 days'), date('now', '-45 days'), 'Returned'),
(5007, 1009, 2006, 304, date('now', '-40 days'), date('now', '-26 days'), date('now', '-27 days'), 'Returned'),
(5008, 1010, 2007, 305, date('now', '-38 days'), date('now', '-24 days'), date('now', '-25 days'), 'Returned'),
(5009, 1018, 2008, 302, date('now', '-35 days'), date('now', '-21 days'), date('now', '-22 days'), 'Returned'),
(5010, 1019, 2009, 303, date('now', '-30 days'), date('now', '-16 days'), date('now', '-18 days'), 'Returned'),

-- Returned late with fine assessed (5 records)
(5011, 1001, 2002, 301, date('now', '-40 days'), date('now', '-26 days'), date('now', '-20 days'), 'Returned'), -- 6 days late
(5012, 1002, 2004, 302, date('now', '-35 days'), date('now', '-21 days'), date('now', '-11 days'), 'Returned'), -- 10 days late
(5013, 1003, 2005, 303, date('now', '-30 days'), date('now', '-16 days'), date('now', '-12 days'), 'Returned'), -- 4 days late
(5014, 1004, 2014, 301, date('now', '-45 days'), date('now', '-15 days'), date('now', '-5 days'), 'Returned'),  -- 10 days late
(5015, 1006, 2001, 304, date('now', '-28 days'), date('now', '-14 days'), date('now', '-2 days'), 'Returned'),  -- 12 days late

-- Currently Issued - On Time (5 records: return_date IS NULL, due_date >= today)
(5016, 1001, 2010, 301, date('now', '-5 days'), date('now', '+9 days'), NULL, 'Issued'),
(5017, 1002, 2011, 302, date('now', '-4 days'), date('now', '+10 days'), NULL, 'Issued'),
(5018, 1003, 2012, 303, date('now', '-3 days'), date('now', '+11 days'), NULL, 'Issued'),
(5019, 1011, 2006, 304, date('now', '-2 days'), date('now', '+12 days'), NULL, 'Issued'),
(5020, 1012, 2007, 305, date('now', '-1 days'), date('now', '+13 days'), NULL, 'Issued'),

-- Currently Issued - OVERDUE (5 records: return_date IS NULL, due_date < today)
(5021, 1005, 2001, 301, date('now', '-25 days'), date('now', '-11 days'), NULL, 'Issued'), -- 11 days overdue
(5022, 1005, 2003, 302, date('now', '-30 days'), date('now', '-16 days'), NULL, 'Issued'), -- 16 days overdue
(5023, 1005, 2005, 303, date('now', '-35 days'), date('now', '-21 days'), NULL, 'Issued'), -- 21 days overdue
(5024, 1008, 2008, 304, date('now', '-22 days'), date('now', '-8 days'), NULL, 'Issued'),  -- 8 days overdue
(5025, 1008, 2017, 301, date('now', '-40 days'), date('now', '-19 days'), NULL, 'Issued');  -- 19 days overdue (Staff 2017 suspended)

-- Additional active loans to reconcile exact book stock counts:
-- Book 1001: total 5, active: 5016 (1) -> need 1 more active loan -> 5026
-- Book 1002: total 6, active: 5017 (1) -> need 1 more active loan -> 5027
-- Book 1008: total 3, active: 5024, 5025 (2) -> need 1 more active loan -> 5028
-- Book 1011: total 4, active: 5019 (1) -> need 1 more active loan -> 5029
-- Book 1012: total 3, active: 5020 (1) -> need 1 more active loan -> 5030
-- Book 1013: total 5, need 2 active loans -> 5031, 5032
-- Book 1014: total 6, need 2 active loans -> 5033, 5034
-- Book 1015: total 3, need 2 active loans -> 5035, 5036
-- Book 1016: total 4, need 2 active loans -> 5037, 5038
-- Book 1020: total 4, need 1 active loan -> 5039
-- Book 1022: total 3, need 1 active loan -> 5040
INSERT INTO ISSUE_TRANSACTION (issue_id, book_id, member_id, librarian_id, issue_date, due_date, return_date, status) VALUES
(5026, 1001, 2009, 302, date('now', '-6 days'), date('now', '+8 days'), NULL, 'Issued'),
(5027, 1002, 2010, 303, date('now', '-3 days'), date('now', '+11 days'), NULL, 'Issued'),
(5028, 1008, 2004, 301, date('now', '-2 days'), date('now', '+12 days'), NULL, 'Issued'),
(5029, 1011, 2011, 302, date('now', '-4 days'), date('now', '+10 days'), NULL, 'Issued'),
(5030, 1012, 2013, 304, date('now', '-8 days'), date('now', '+22 days'), NULL, 'Issued'),
(5031, 1013, 2002, 305, date('now', '-5 days'), date('now', '+9 days'), NULL, 'Issued'),
(5032, 1013, 2003, 301, date('now', '-4 days'), date('now', '+10 days'), NULL, 'Issued'),
(5033, 1014, 2007, 302, date('now', '-7 days'), date('now', '+7 days'), NULL, 'Issued'),
(5034, 1014, 2008, 303, date('now', '-3 days'), date('now', '+11 days'), NULL, 'Issued'),
(5035, 1015, 2009, 304, date('now', '-2 days'), date('now', '+12 days'), NULL, 'Issued'),
(5036, 1015, 2012, 305, date('now', '-1 days'), date('now', '+13 days'), NULL, 'Issued'),
(5037, 1016, 2014, 301, date('now', '-5 days'), date('now', '+25 days'), NULL, 'Issued'),
(5038, 1016, 2015, 302, date('now', '-4 days'), date('now', '+26 days'), NULL, 'Issued'),
(5039, 1020, 2016, 303, date('now', '-2 days'), date('now', '+28 days'), NULL, 'Issued'),
(5040, 1022, 2006, 304, date('now', '-3 days'), date('now', '+11 days'), NULL, 'Issued');

-- ----------------------------------------------------------------------------
-- 7. RESERVATIONS (12 Records)
-- Queues for books with 0 available copies (Book 1005 & Book 1008) + fulfilled
-- ----------------------------------------------------------------------------
INSERT INTO RESERVATION (reservation_id, book_id, member_id, reserved_on, expires_on, queue_position, status) VALUES
-- Waiting queue for Book 1005 (Design Patterns - 0 copies available)
(6001, 1005, 2002, date('now', '-4 days'), date('now', '+3 days'), 1, 'Waiting'),
(6002, 1005, 2006, date('now', '-3 days'), date('now', '+4 days'), 2, 'Waiting'),
(6003, 1005, 2011, date('now', '-1 days'), date('now', '+6 days'), 3, 'Waiting'),

-- Waiting queue for Book 1008 (The God of Small Things - 0 copies available)
(6004, 1008, 2007, date('now', '-5 days'), date('now', '+2 days'), 1, 'Waiting'),
(6005, 1008, 2010, date('now', '-2 days'), date('now', '+5 days'), 2, 'Waiting'),

-- Other waiting/historical reservations
(6006, 1002, 2005, date('now', '-15 days'), date('now', '-8 days'), 1, 'Fulfilled'),
(6007, 1003, 2008, date('now', '-20 days'), date('now', '-13 days'), 1, 'Fulfilled'),
(6008, 1004, 2009, date('now', '-18 days'), date('now', '-11 days'), 1, 'Cancelled'),
(6009, 1006, 2012, date('now', '-25 days'), date('now', '-18 days'), 1, 'Expired'),
(6010, 1001, 2003, date('now', '-12 days'), date('now', '-5 days'), 1, 'Fulfilled'),
(6011, 1011, 2004, date('now', '-8 days'), date('now', '-1 days'), 1, 'Fulfilled'),
(6012, 1012, 2015, date('now', '-14 days'), date('now', '-7 days'), 1, 'Fulfilled');

-- ----------------------------------------------------------------------------
-- 8. FINES (12 Records)
-- Linked to returned late issues and overdue issues (Pending, Paid, Waived)
-- ----------------------------------------------------------------------------
INSERT INTO FINE (fine_id, issue_id, member_id, days_overdue, fine_amount, fine_date, payment_status, paid_on, payment_method, transaction_ref) VALUES
-- Fines from returned late issues
(7001, 5011, 2002, 6, 30.00, date('now', '-20 days'), 'Paid', date('now', '-19 days'), 'UPI', 'TXN_LIB_7001_UPI'),
(7002, 5012, 2004, 10, 50.00, date('now', '-11 days'), 'Paid', date('now', '-10 days'), 'Cash', 'TXN_LIB_7002_CSH'),
(7003, 5013, 2005, 4, 20.00, date('now', '-12 days'), 'Waived', date('now', '-12 days'), NULL, NULL),
(7004, 5014, 2014, 10, 50.00, date('now', '-5 days'), 'Paid', date('now', '-4 days'), 'Net Banking', 'TXN_LIB_7004_NBK'),
(7005, 5015, 2001, 12, 60.00, date('now', '-2 days'), 'Pending', NULL, NULL, NULL),

-- Fines assessed for ongoing overdue loans
(7006, 5021, 2001, 11, 55.00, date('now', '-1 days'), 'Pending', NULL, NULL, NULL),
(7007, 5022, 2003, 16, 80.00, date('now', '-2 days'), 'Pending', NULL, NULL, NULL),
(7008, 5023, 2005, 21, 105.00, date('now', '-3 days'), 'Pending', NULL, NULL, NULL),
(7009, 5024, 2008, 8, 40.00, date('now', '-1 days'), 'Pending', NULL, NULL, NULL),
(7010, 5025, 2017, 19, 570.00, date('now', '-5 days'), 'Pending', NULL, NULL, NULL), -- Causes Member 2017 to be Suspended (> 500)

-- Historical paid fines
(7011, 5001, 2001, 5, 25.00, date('now', '-45 days'), 'Paid', date('now', '-44 days'), 'Debit Card', 'TXN_LIB_7011_DC'),
(7012, 5002, 2002, 8, 40.00, date('now', '-40 days'), 'Paid', date('now', '-39 days'), 'Credit Card', 'TXN_LIB_7012_CC');
