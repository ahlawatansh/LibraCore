"""
LibraCore — MongoDB Document Engine & PyMongo Service Layer
Supports live MongoDB Atlas (mongodb+srv://...), local MongoDB (localhost:27017),
and graceful in-memory mongomock fallback for zero-dependency viva demonstrations.
"""

import os
import re
import json
import time
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Tuple

try:
    import pymongo
    from pymongo import MongoClient
    HAS_PYMONGO = True
except ImportError:
    HAS_PYMONGO = False

try:
    import mongomock
    HAS_MONGOMOCK = True
except ImportError:
    HAS_MONGOMOCK = False

# MongoDB Connection Configuration
MONGODB_URI = os.environ.get('MONGODB_URI', '').strip()
MONGODB_DB_NAME = os.environ.get('MONGODB_DB_NAME', 'libracore_db')

_mongo_client = None
_mongo_db = None
_engine_type = "Uninitialized"

def get_mongo_db():
    global _mongo_client, _mongo_db, _engine_type
    if _mongo_db is not None:
        return _mongo_db

    # 1. Try Live MongoDB Atlas / Local URI if configured
    if MONGODB_URI and HAS_PYMONGO:
        try:
            client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=3000)
            client.admin.command('ping')
            _mongo_client = client
            _mongo_db = client[MONGODB_DB_NAME]
            _engine_type = "MongoDB Atlas (Live Cloud Cluster)"
            print(f"[MongoDB] Connected to live MongoDB Atlas at {MONGODB_URI[:25]}...")
            return _mongo_db
        except Exception as e:
            print(f"[MongoDB Atlas Warning] Live connection failed ({e}). Falling back to local/in-memory engine.")

    # 2. Try default localhost:27017 if running
    if HAS_PYMONGO:
        try:
            client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=1000)
            client.admin.command('ping')
            _mongo_client = client
            _mongo_db = client[MONGODB_DB_NAME]
            _engine_type = "Local MongoDB (localhost:27017)"
            print("[MongoDB] Connected to local MongoDB instance on port 27017.")
            return _mongo_db
        except Exception:
            pass

    # 3. In-Memory Mock MongoDB Engine (mongomock)
    if HAS_MONGOMOCK:
        _mongo_client = mongomock.MongoClient()
        _mongo_db = _mongo_client[MONGODB_DB_NAME]
        _engine_type = "MongoDB In-Memory Document Store (mongomock)"
        print("[MongoDB] Running with in-memory MongoDB Document Store.")
        return _mongo_db

    raise RuntimeError("Neither pymongo nor mongomock are available. Please run `pip install pymongo mongomock`.")

def get_engine_status():
    get_mongo_db()
    return {
        "engine": _engine_type,
        "database": MONGODB_DB_NAME,
        "driver": "PyMongo 4.x",
        "has_atlas_uri": bool(MONGODB_URI)
    }

def seed_mongo_database(force=False):
    """
    Populates the 8 MongoDB collections with rich, benchmark documents.
    """
    db = get_mongo_db()
    if not force and db.books.count_documents({}) > 0:
        return

    # Drop existing collections
    for coll in ['books', 'members', 'issues', 'fines', 'reservations', 'categories', 'authors', 'librarians']:
        db[coll].drop()

    # 1. CATEGORIES (10 documents)
    categories = [
        {"_id": 101, "category_name": "Computer Science & AI", "category_code": "CS-AI", "shelf_zone": "Zone A", "description": "Algorithms, Operating Systems, Machine Learning & Architecture"},
        {"_id": 102, "category_name": "Database & Systems", "category_code": "DB-SYS", "shelf_zone": "Zone B", "description": "Relational, NoSQL, Distributed Storage & Query Optimization"},
        {"_id": 103, "category_name": "Software Engineering", "category_code": "SWE", "shelf_zone": "Zone C", "description": "Design Patterns, Clean Code, Refactoring & Microservices"},
        {"_id": 104, "category_name": "Mathematics & Statistics", "category_code": "MATH", "shelf_zone": "Zone D", "description": "Discrete Mathematics, Linear Algebra, Real Analysis & Probability"},
        {"_id": 105, "category_name": "Physics & Electronics", "category_code": "PHYS", "shelf_zone": "Zone E", "description": "Quantum Mechanics, Semiconductor Devices & Circuit Theory"},
        {"_id": 106, "category_name": "English Literature & Classics", "category_code": "ENG-LIT", "shelf_zone": "Zone F", "description": "British & American Classics, Poetry, Drama & Linguistics"},
        {"_id": 107, "category_name": "Indian Fiction & Culture", "category_code": "IND-LIT", "shelf_zone": "Zone G", "description": "Post-Colonial Literature, Contemporary Indian Authors & Heritage"},
        {"_id": 108, "category_name": "Computer Networks & Security", "category_code": "NET-SEC", "shelf_zone": "Zone H", "description": "Cryptography, TCP/IP Protocols, Network Routing & Cybersecurity"},
        {"_id": 109, "category_name": "Business & Management", "category_code": "MGMT", "shelf_zone": "Zone I", "description": "Organizational Behavior, Financial Accounting & Strategic Leadership"},
        {"_id": 110, "category_name": "General Science & Reference", "category_code": "GEN-SCI", "shelf_zone": "Zone J", "description": "Encyclopedias, History of Science & Research Methodology"}
    ]
    db.categories.insert_many(categories)

    # 2. AUTHORS (15 documents)
    authors = [
        {"_id": 201, "first_name": "Robert", "last_name": "Martin", "full_name": "Robert Martin", "pen_name": "Uncle Bob", "nationality": "American", "primary_genre": "Software Architecture"},
        {"_id": 202, "first_name": "Thomas", "last_name": "Cormen", "full_name": "Thomas Cormen", "pen_name": None, "nationality": "American", "primary_genre": "Algorithms"},
        {"_id": 203, "first_name": "Abraham", "last_name": "Silberschatz", "full_name": "Abraham Silberschatz", "pen_name": None, "nationality": "American", "primary_genre": "Operating Systems & Databases"},
        {"_id": 204, "first_name": "Andrew", "last_name": "Tanenbaum", "full_name": "Andrew Tanenbaum", "pen_name": None, "nationality": "American-Dutch", "primary_genre": "Computer Networking"},
        {"_id": 205, "first_name": "Erich", "last_name": "Gamma", "full_name": "Erich Gamma", "pen_name": None, "nationality": "Swiss", "primary_genre": "Object-Oriented Design"},
        {"_id": 206, "first_name": "Donald", "last_name": "Knuth", "full_name": "Donald Knuth", "pen_name": None, "nationality": "American", "primary_genre": "Theoretical Computer Science"},
        {"_id": 207, "first_name": "Arundhati", "last_name": "Roy", "full_name": "Arundhati Roy", "pen_name": None, "nationality": "Indian", "primary_genre": "Contemporary Fiction"},
        {"_id": 208, "first_name": "R.K.", "last_name": "Narayan", "full_name": "R.K. Narayan", "pen_name": None, "nationality": "Indian", "primary_genre": "Classic Indian Fiction"},
        {"_id": 209, "first_name": "Ruskin", "last_name": "Bond", "full_name": "Ruskin Bond", "pen_name": None, "nationality": "Indian", "primary_genre": "Children Literature"},
        {"_id": 210, "first_name": "Wade", "last_name": "Warren", "full_name": "Wade Warren", "pen_name": None, "nationality": "British", "primary_genre": "Modern Linguistics"},
        {"_id": 211, "first_name": "David", "last_name": "Morgan", "full_name": "David Morgan", "pen_name": None, "nationality": "British", "primary_genre": "Applied Mathematics"},
        {"_id": 212, "first_name": "Kristin", "last_name": "Watson", "full_name": "Kristin Watson", "pen_name": None, "nationality": "Canadian", "primary_genre": "Quantum Electrodynamics"},
        {"_id": 213, "first_name": "Savannah", "last_name": "Nguyen", "full_name": "Savannah Nguyen", "pen_name": None, "nationality": "Australian", "primary_genre": "Statistical Inference"},
        {"_id": 214, "first_name": "Jacob", "last_name": "Jones", "full_name": "Jacob Jones", "pen_name": None, "nationality": "Canadian", "primary_genre": "Thermodynamics"},
        {"_id": 215, "first_name": "Arlene", "last_name": "McCoy", "full_name": "Arlene McCoy", "pen_name": None, "nationality": "Irish", "primary_genre": "19th Century Drama"}
    ]
    db.authors.insert_many(authors)

    # 3. LIBRARIANS (6 documents)
    librarians = [
        {"_id": 301, "staff_code": "LIB-001", "first_name": "Rajesh", "last_name": "Kumar", "full_name": "Rajesh Kumar", "email": "rajesh.kumar@libracore.edu", "phone": "+91 98765 00001", "designation": "Chief Librarian", "shift": "Morning"},
        {"_id": 302, "staff_code": "LIB-002", "first_name": "Priyanka", "last_name": "Sen", "full_name": "Priyanka Sen", "email": "priyanka.sen@libracore.edu", "phone": "+91 98765 00002", "designation": "Assistant Librarian", "shift": "Evening"},
        {"_id": 303, "staff_code": "LIB-003", "first_name": "Amitabh", "last_name": "Choudhury", "full_name": "Amitabh Choudhury", "email": "amitabh.c@libracore.edu", "phone": "+91 98765 00003", "designation": "Cataloging Specialist", "shift": "Morning"},
        {"_id": 304, "staff_code": "LIB-004", "first_name": "Sunita", "last_name": "Deshmukh", "full_name": "Sunita Deshmukh", "email": "sunita.d@libracore.edu", "phone": "+91 98765 00004", "designation": "Circulation Desk Officer", "shift": "Morning"},
        {"_id": 305, "staff_code": "LIB-005", "first_name": "Harish", "last_name": "Verma", "full_name": "Harish Verma", "email": "harish.v@libracore.edu", "phone": "+91 98765 00005", "designation": "Digital Archive Custodian", "shift": "Night"},
        {"_id": 306, "staff_code": "LIB-006", "first_name": "Ananya", "last_name": "Banerjee", "full_name": "Ananya Banerjee", "email": "ananya.b@libracore.edu", "phone": "+91 98765 00006", "designation": "Junior Assistant", "shift": "Evening"}
    ]
    db.librarians.insert_many(librarians)

    # 4. BOOKS (25 documents with embedded author and category subdocuments)
    books = [
        {"_id": 1001, "isbn": "978-0132350884", "title": "Clean Code: A Handbook of Agile Software Craftsmanship", "author_id": 201, "author_name": "Robert Martin", "category_id": 103, "category_name": "Software Engineering", "category_code": "SWE", "shelf_zone": "Zone C", "publisher": "Prentice Hall", "publish_date": "2008-08-01", "edition": "1st", "language": "English", "shelf_location": "A-01-04", "price": 799.00, "total_copies": 5, "available_copies": 4, "cover_url": "https://covers.openlibrary.org/b/isbn/9780132350884-M.jpg", "added_on": "2026-09-29", "status": "Active"},
        {"_id": 1002, "isbn": "978-0262033848", "title": "Introduction to Algorithms (CLRS)", "author_id": 202, "author_name": "Thomas Cormen", "category_id": 101, "category_name": "Computer Science & AI", "category_code": "CS-AI", "shelf_zone": "Zone A", "publisher": "MIT Press", "publish_date": "2009-07-31", "edition": "3rd", "language": "English", "shelf_location": "A-02-01", "price": 1450.00, "total_copies": 6, "available_copies": 4, "cover_url": "https://covers.openlibrary.org/b/isbn/9780262033848-M.jpg", "added_on": "2026-09-26", "status": "Active"},
        {"_id": 1003, "isbn": "978-0078022159", "title": "Database System Concepts", "author_id": 203, "author_name": "Abraham Silberschatz", "category_id": 102, "category_name": "Database & Systems", "category_code": "DB-SYS", "shelf_zone": "Zone B", "publisher": "McGraw-Hill", "publish_date": "2019-03-25", "edition": "7th", "language": "English", "shelf_location": "B-01-02", "price": 890.00, "total_copies": 4, "available_copies": 3, "cover_url": "https://covers.openlibrary.org/b/isbn/9780078022159-M.jpg", "added_on": "2026-10-06", "status": "Active"},
        {"_id": 1004, "isbn": "978-0132126953", "title": "Computer Networks", "author_id": 204, "author_name": "Andrew Tanenbaum", "category_id": 108, "category_name": "Computer Networks & Security", "category_code": "NET-SEC", "shelf_zone": "Zone H", "publisher": "Pearson", "publish_date": "2010-10-07", "edition": "5th", "language": "English", "shelf_location": "H-02-03", "price": 825.00, "total_copies": 4, "available_copies": 3, "cover_url": "https://covers.openlibrary.org/b/isbn/9780132126953-M.jpg", "added_on": "2026-10-09", "status": "Active"},
        {"_id": 1005, "isbn": "978-0201633610", "title": "Design Patterns: Elements of Reusable Object-Oriented Software", "author_id": 205, "author_name": "Erich Gamma", "category_id": 103, "category_name": "Software Engineering", "category_code": "SWE", "shelf_zone": "Zone C", "publisher": "Addison-Wesley", "publish_date": "1994-10-31", "edition": "1st", "language": "English", "shelf_location": "C-01-05", "price": 950.00, "total_copies": 3, "available_copies": 1, "cover_url": "https://covers.openlibrary.org/b/isbn/9780201633610-M.jpg", "added_on": "2026-09-20", "status": "Active"},
        {"_id": 1006, "isbn": "978-1118063330", "title": "Operating System Concepts", "author_id": 203, "author_name": "Abraham Silberschatz", "category_id": 101, "category_name": "Computer Science & AI", "category_code": "CS-AI", "shelf_zone": "Zone A", "publisher": "Wiley", "publish_date": "2018-05-04", "edition": "10th", "language": "English", "shelf_location": "A-03-02", "price": 895.00, "total_copies": 5, "available_copies": 4, "cover_url": "https://covers.openlibrary.org/b/isbn/9781118063330-M.jpg", "added_on": "2026-09-18", "status": "Active"},
        {"_id": 1007, "isbn": "978-0201896831", "title": "The Art of Computer Programming, Vol. 1", "author_id": 206, "author_name": "Donald Knuth", "category_id": 101, "category_name": "Computer Science & AI", "category_code": "CS-AI", "shelf_zone": "Zone A", "publisher": "Addison-Wesley", "publish_date": "1997-07-04", "edition": "3rd", "language": "English", "shelf_location": "A-01-01", "price": 1950.00, "total_copies": 2, "available_copies": 1, "cover_url": "https://covers.openlibrary.org/b/isbn/9780201896831-M.jpg", "added_on": "2026-09-15", "status": "Active"},
        {"_id": 1008, "isbn": "978-0812979657", "title": "The God of Small Things", "author_id": 207, "author_name": "Arundhati Roy", "category_id": 107, "category_name": "Indian Fiction & Culture", "category_code": "IND-LIT", "shelf_zone": "Zone G", "publisher": "Random House", "publish_date": "2008-12-16", "edition": "Reprint", "language": "English", "shelf_location": "G-02-04", "price": 450.00, "total_copies": 3, "available_copies": 0, "cover_url": "https://covers.openlibrary.org/b/isbn/9780812979657-M.jpg", "added_on": "2026-09-12", "status": "Active"},
        {"_id": 1009, "isbn": "978-0143039655", "title": "Malgudi Days", "author_id": 208, "author_name": "R.K. Narayan", "category_id": 107, "category_name": "Indian Fiction & Culture", "category_code": "IND-LIT", "shelf_zone": "Zone G", "publisher": "Penguin Classics", "publish_date": "2006-11-28", "edition": "Revised", "language": "English", "shelf_location": "G-01-03", "price": 299.00, "total_copies": 6, "available_copies": 5, "cover_url": "https://covers.openlibrary.org/b/isbn/9780143039655-M.jpg", "added_on": "2026-09-10", "status": "Active"},
        {"_id": 1010, "isbn": "978-8171673407", "title": "The Blue Umbrella", "author_id": 209, "author_name": "Ruskin Bond", "category_id": 107, "category_name": "Indian Fiction & Culture", "category_code": "IND-LIT", "shelf_zone": "Zone G", "publisher": "Rupa Publications", "publish_date": "1992-05-15", "edition": "1st", "language": "English", "shelf_location": "G-03-01", "price": 195.00, "total_copies": 5, "available_copies": 4, "cover_url": "https://covers.openlibrary.org/b/isbn/9788171673407-M.jpg", "added_on": "2026-09-08", "status": "Active"},
        {"_id": 1011, "isbn": "978-0199535569", "title": "Literature", "author_id": 210, "author_name": "Wade Warren", "category_id": 106, "category_name": "English Literature & Classics", "category_code": "ENG-LIT", "shelf_zone": "Zone F", "publisher": "Oxford World Classics", "publish_date": "2022-10-22", "edition": "2nd", "language": "English", "shelf_location": "F-01-02", "price": 550.00, "total_copies": 4, "available_copies": 2, "cover_url": "https://covers.openlibrary.org/b/isbn/9780199535569-M.jpg", "added_on": "2026-10-19", "status": "Active"},
        {"_id": 1012, "isbn": "978-0521884075", "title": "Mathematics", "author_id": 211, "author_name": "David Morgan", "category_id": 104, "category_name": "Mathematics & Statistics", "category_code": "MATH", "shelf_zone": "Zone D", "publisher": "Cambridge Press", "publish_date": "2023-09-12", "edition": "4th", "language": "English", "shelf_location": "D-02-03", "price": 720.00, "total_copies": 3, "available_copies": 1, "cover_url": "https://covers.openlibrary.org/b/isbn/9780521884075-M.jpg", "added_on": "2026-10-16", "status": "Active"},
        {"_id": 1013, "isbn": "978-0321792984", "title": "English", "author_id": 212, "author_name": "Kristin Watson", "category_id": 105, "category_name": "Physics & Electronics", "category_code": "PHYS", "shelf_zone": "Zone E", "publisher": "Pearson Science", "publish_date": "2020-11-23", "edition": "3rd", "language": "English", "shelf_location": "E-01-01", "price": 850.00, "total_copies": 5, "available_copies": 3, "cover_url": "https://covers.openlibrary.org/b/isbn/9780321792984-M.jpg", "added_on": "2026-10-12", "status": "Active"},
        {"_id": 1014, "isbn": "978-0471198260", "title": "Mathematics", "author_id": 213, "author_name": "Savannah Nguyen", "category_id": 104, "category_name": "Mathematics & Statistics", "category_code": "MATH", "shelf_zone": "Zone D", "publisher": "Wiley Academic", "publish_date": "2022-10-12", "edition": "5th", "language": "English", "shelf_location": "D-03-01", "price": 650.00, "total_copies": 6, "available_copies": 4, "cover_url": "https://covers.openlibrary.org/b/isbn/9780471198260-M.jpg", "added_on": "2026-10-10", "status": "Active"},
        {"_id": 1015, "isbn": "978-0205829651", "title": "English", "author_id": 214, "author_name": "Jacob Jones", "category_id": 105, "category_name": "Physics & Electronics", "category_code": "PHYS", "shelf_zone": "Zone E", "publisher": "Prentice Hall", "publish_date": "2022-10-22", "edition": "2nd", "language": "English", "shelf_location": "E-02-04", "price": 680.00, "total_copies": 3, "available_copies": 1, "cover_url": "https://covers.openlibrary.org/b/isbn/9780205829651-M.jpg", "added_on": "2026-10-05", "status": "Active"},
        {"_id": 1016, "isbn": "978-0141439518", "title": "Mathematics", "author_id": 215, "author_name": "Arlene McCoy", "category_id": 106, "category_name": "English Literature & Classics", "category_code": "ENG-LIT", "shelf_zone": "Zone F", "publisher": "Penguin Press", "publish_date": "2023-09-23", "edition": "1st", "language": "English", "shelf_location": "F-03-02", "price": 490.00, "total_copies": 4, "available_copies": 2, "cover_url": "https://covers.openlibrary.org/b/isbn/9780141439518-M.jpg", "added_on": "2026-10-03", "status": "Active"},
        {"_id": 1017, "isbn": "978-0131103627", "title": "The C Programming Language", "author_id": 201, "author_name": "Robert Martin", "category_id": 101, "category_name": "Computer Science & AI", "category_code": "CS-AI", "shelf_zone": "Zone A", "publisher": "Prentice Hall", "publish_date": "1988-03-22", "edition": "2nd", "language": "English", "shelf_location": "A-01-02", "price": 620.00, "total_copies": 4, "available_copies": 4, "cover_url": "https://covers.openlibrary.org/b/isbn/9780131103627-M.jpg", "added_on": "2026-09-25", "status": "Active"},
        {"_id": 1018, "isbn": "978-0596007126", "title": "Head First Design Patterns", "author_id": 205, "author_name": "Erich Gamma", "category_id": 103, "category_name": "Software Engineering", "category_code": "SWE", "shelf_zone": "Zone C", "publisher": "O'Reilly Media", "publish_date": "2004-10-25", "edition": "1st", "language": "English", "shelf_location": "C-02-01", "price": 890.00, "total_copies": 5, "available_copies": 4, "cover_url": "https://covers.openlibrary.org/b/isbn/9780596007126-M.jpg", "added_on": "2026-09-24", "status": "Active"},
        {"_id": 1019, "isbn": "978-1449355739", "title": "Learning Python", "author_id": 201, "author_name": "Robert Martin", "category_id": 101, "category_name": "Computer Science & AI", "category_code": "CS-AI", "shelf_zone": "Zone A", "publisher": "O'Reilly Media", "publish_date": "2013-07-06", "edition": "5th", "language": "English", "shelf_location": "A-02-05", "price": 980.00, "total_copies": 4, "available_copies": 3, "cover_url": "https://covers.openlibrary.org/b/isbn/9781449355739-M.jpg", "added_on": "2026-09-22", "status": "Active"},
        {"_id": 1020, "isbn": "978-0134494166", "title": "Clean Architecture: A Craftsman's Guide", "author_id": 201, "author_name": "Robert Martin", "category_id": 103, "category_name": "Software Engineering", "category_code": "SWE", "shelf_zone": "Zone C", "publisher": "Prentice Hall", "publish_date": "2017-09-10", "edition": "1st", "language": "English", "shelf_location": "C-03-02", "price": 840.00, "total_copies": 4, "available_copies": 3, "cover_url": "https://covers.openlibrary.org/b/isbn/9780134494166-M.jpg", "added_on": "2026-09-21", "status": "Active"},
        {"_id": 1021, "isbn": "978-0321573513", "title": "Algorithms in C++", "author_id": 202, "author_name": "Thomas Cormen", "category_id": 101, "category_name": "Computer Science & AI", "category_code": "CS-AI", "shelf_zone": "Zone A", "publisher": "Addison-Wesley", "publish_date": "2008-01-15", "edition": "3rd", "language": "English", "shelf_location": "A-03-04", "price": 1150.00, "total_copies": 3, "available_copies": 3, "cover_url": "https://covers.openlibrary.org/b/isbn/9780321573513-M.jpg", "added_on": "2026-09-17", "status": "Active"},
        {"_id": 1022, "isbn": "978-0136006633", "title": "Database Systems: The Complete Book", "author_id": 203, "author_name": "Abraham Silberschatz", "category_id": 102, "category_name": "Database & Systems", "category_code": "DB-SYS", "shelf_zone": "Zone B", "publisher": "Pearson", "publish_date": "2008-06-15", "edition": "2nd", "language": "English", "shelf_location": "B-02-04", "price": 1250.00, "total_copies": 3, "available_copies": 2, "cover_url": "https://covers.openlibrary.org/b/isbn/9780136006633-M.jpg", "added_on": "2026-09-16", "status": "Active"},
        {"_id": 1023, "isbn": "978-0133594140", "title": "Structured Computer Organization", "author_id": 204, "author_name": "Andrew Tanenbaum", "category_id": 101, "category_name": "Computer Science & AI", "category_code": "CS-AI", "shelf_zone": "Zone A", "publisher": "Pearson", "publish_date": "2012-07-24", "edition": "6th", "language": "English", "shelf_location": "A-04-01", "price": 990.00, "total_copies": 3, "available_copies": 3, "cover_url": "https://covers.openlibrary.org/b/isbn/9780133594140-M.jpg", "added_on": "2026-09-14", "status": "Active"},
        {"_id": 1024, "isbn": "978-0070131514", "title": "Principles of Mathematical Analysis", "author_id": 211, "author_name": "David Morgan", "category_id": 104, "category_name": "Mathematics & Statistics", "category_code": "MATH", "shelf_zone": "Zone D", "publisher": "McGraw-Hill", "publish_date": "1976-01-01", "edition": "3rd", "language": "English", "shelf_location": "D-01-02", "price": 780.00, "total_copies": 2, "available_copies": 2, "cover_url": "https://covers.openlibrary.org/b/isbn/9780070131514-M.jpg", "added_on": "2026-09-11", "status": "Active"},
        {"_id": 1025, "isbn": "978-0143105428", "title": "The Guide to English Grammar & Prose", "author_id": 210, "author_name": "Wade Warren", "category_id": 106, "category_name": "English Literature & Classics", "category_code": "ENG-LIT", "shelf_zone": "Zone F", "publisher": "Penguin Classic", "publish_date": "2015-04-07", "edition": "1st", "language": "English", "shelf_location": "F-02-01", "price": 340.00, "total_copies": 4, "available_copies": 4, "cover_url": "https://covers.openlibrary.org/b/isbn/9780143105428-M.jpg", "added_on": "2026-09-09", "status": "Active"}
    ]
    db.books.insert_many(books)

    # 5. MEMBERS (20 documents)
    members = [
        {"_id": 2001, "member_code": "24BCE1001", "first_name": "Aarav", "last_name": "Sharma", "full_name": "Aarav Sharma", "member_type": "Student", "department": "Computer Science & Engineering", "email": "aarav.sharma2024@vitstudent.ac.in", "phone": "+91 98765 43210", "join_date": "2024-07-15", "membership_expiry": "2028-06-30", "max_books_allowed": 3, "current_loans": 2, "pending_fines": 115.00, "status": "Active"},
        {"_id": 2002, "member_code": "24BCE1002", "first_name": "Diya", "last_name": "Patel", "full_name": "Diya Patel", "member_type": "Student", "department": "Information Technology", "email": "diya.patel2024@vitstudent.ac.in", "phone": "+91 98765 43211", "join_date": "2024-07-16", "membership_expiry": "2028-06-30", "max_books_allowed": 3, "current_loans": 2, "pending_fines": 0.00, "status": "Active"},
        {"_id": 2003, "member_code": "24BCE1003", "first_name": "Rohan", "last_name": "Iyer", "full_name": "Rohan Iyer", "member_type": "Student", "department": "Computer Science & Engineering", "email": "rohan.iyer2024@vitstudent.ac.in", "phone": "+91 98765 43212", "join_date": "2024-07-16", "membership_expiry": "2028-06-30", "max_books_allowed": 3, "current_loans": 2, "pending_fines": 0.00, "status": "Active"},
        {"_id": 2004, "member_code": "24BCE1004", "first_name": "Ananya", "last_name": "Verma", "full_name": "Ananya Verma", "member_type": "Student", "department": "Electronics & Communication", "email": "ananya.verma2024@vitstudent.ac.in", "phone": "+91 98765 43213", "join_date": "2024-07-18", "membership_expiry": "2028-06-30", "max_books_allowed": 3, "current_loans": 2, "pending_fines": 0.00, "status": "Active"},
        {"_id": 2005, "member_code": "24BCE1005", "first_name": "Kabir", "last_name": "Mehta", "full_name": "Kabir Mehta", "member_type": "Student", "department": "Mechanical Engineering", "email": "kabir.mehta2024@vitstudent.ac.in", "phone": "+91 98765 43214", "join_date": "2024-07-20", "membership_expiry": "2028-06-30", "max_books_allowed": 3, "current_loans": 2, "pending_fines": 0.00, "status": "Active"},
        {"_id": 2006, "member_code": "24BCE1006", "first_name": "Isha", "last_name": "Nair", "full_name": "Isha Nair", "member_type": "Student", "department": "Computer Science & Engineering", "email": "isha.nair2024@vitstudent.ac.in", "phone": "+91 98765 43215", "join_date": "2024-07-21", "membership_expiry": "2028-06-30", "max_books_allowed": 3, "current_loans": 2, "pending_fines": 0.00, "status": "Active"},
        {"_id": 2007, "member_code": "24BCE1007", "first_name": "Aditya", "last_name": "Rao", "full_name": "Aditya Rao", "member_type": "Student", "department": "Electrical & Electronics", "email": "aditya.rao2024@vitstudent.ac.in", "phone": "+91 98765 43216", "join_date": "2024-07-22", "membership_expiry": "2028-06-30", "max_books_allowed": 3, "current_loans": 2, "pending_fines": 0.00, "status": "Active"},
        {"_id": 2008, "member_code": "24BCE1008", "first_name": "Tara", "last_name": "Mukherjee", "full_name": "Tara Mukherjee", "member_type": "Student", "department": "Civil Engineering", "email": "tara.mukherjee2024@vitstudent.ac.in", "phone": "+91 98765 43217", "join_date": "2024-07-23", "membership_expiry": "2028-06-30", "max_books_allowed": 3, "current_loans": 2, "pending_fines": 0.00, "status": "Active"},
        {"_id": 2009, "member_code": "24BCE1009", "first_name": "Vihaan", "last_name": "Reddy", "full_name": "Vihaan Reddy", "member_type": "Student", "department": "Biotechnology", "email": "vihaan.reddy2024@vitstudent.ac.in", "phone": "+91 98765 43218", "join_date": "2024-07-25", "membership_expiry": "2028-06-30", "max_books_allowed": 3, "current_loans": 2, "pending_fines": 0.00, "status": "Active"},
        {"_id": 2010, "member_code": "24BCE1010", "first_name": "Meera", "last_name": "Kapoor", "full_name": "Meera Kapoor", "member_type": "Student", "department": "Computer Science & Engineering", "email": "meera.kapoor2024@vitstudent.ac.in", "phone": "+91 98765 43219", "join_date": "2024-07-26", "membership_expiry": "2028-06-30", "max_books_allowed": 3, "current_loans": 2, "pending_fines": 0.00, "status": "Active"},
        {"_id": 2011, "member_code": "24BCE1011", "first_name": "Arjun", "last_name": "Bhat", "full_name": "Arjun Bhat", "member_type": "Student", "department": "Information Technology", "email": "arjun.bhat2024@vitstudent.ac.in", "phone": "+91 98765 43220", "join_date": "2024-07-28", "membership_expiry": "2028-06-30", "max_books_allowed": 3, "current_loans": 2, "pending_fines": 0.00, "status": "Active"},
        {"_id": 2012, "member_code": "24BCE1012", "first_name": "Pooja", "last_name": "Chopra", "full_name": "Pooja Chopra", "member_type": "Student", "department": "Chemical Engineering", "email": "pooja.chopra2024@vitstudent.ac.in", "phone": "+91 98765 43221", "join_date": "2024-07-29", "membership_expiry": "2028-06-30", "max_books_allowed": 3, "current_loans": 2, "pending_fines": 0.00, "status": "Active"},
        {"_id": 2013, "member_code": "FAC-0101", "first_name": "Dr. Vikram", "last_name": "Sen", "full_name": "Dr. Vikram Sen", "member_type": "Faculty", "department": "Computer Science & Engineering", "email": "vikram.sen@vit.ac.in", "phone": "+91 98765 43222", "join_date": "2018-06-01", "membership_expiry": "2028-12-31", "max_books_allowed": 8, "current_loans": 1, "pending_fines": 0.00, "status": "Active"},
        {"_id": 2014, "member_code": "FAC-0102", "first_name": "Dr. Sunita", "last_name": "Rao", "full_name": "Dr. Sunita Rao", "member_type": "Faculty", "department": "Mathematics", "email": "sunita.rao@vit.ac.in", "phone": "+91 98765 43223", "join_date": "2019-01-15", "membership_expiry": "2028-12-31", "max_books_allowed": 8, "current_loans": 1, "pending_fines": 0.00, "status": "Active"},
        {"_id": 2015, "member_code": "FAC-0103", "first_name": "Dr. Arvind", "last_name": "Gupta", "full_name": "Dr. Arvind Gupta", "member_type": "Faculty", "department": "Physics", "email": "arvind.gupta@vit.ac.in", "phone": "+91 98765 43224", "join_date": "2017-08-10", "membership_expiry": "2028-12-31", "max_books_allowed": 8, "current_loans": 1, "pending_fines": 0.00, "status": "Active"},
        {"_id": 2016, "member_code": "FAC-0104", "first_name": "Dr. Shalini", "last_name": "Das", "full_name": "Dr. Shalini Das", "member_type": "Faculty", "department": "English & Languages", "email": "shalini.das@vit.ac.in", "phone": "+91 98765 43225", "join_date": "2020-02-01", "membership_expiry": "2028-12-31", "max_books_allowed": 8, "current_loans": 1, "pending_fines": 0.00, "status": "Active"},
        {"_id": 2017, "member_code": "STF-0201", "first_name": "Gaurav", "last_name": "Saxena", "full_name": "Gaurav Saxena", "member_type": "Staff", "department": "Administration", "email": "gaurav.saxena@vit.ac.in", "phone": "+91 98765 43226", "join_date": "2021-04-12", "membership_expiry": "2027-12-31", "max_books_allowed": 5, "current_loans": 1, "pending_fines": 570.00, "status": "Suspended"},
        {"_id": 2018, "member_code": "STF-0202", "first_name": "Pooja", "last_name": "Deshmukh", "full_name": "Pooja Deshmukh", "member_type": "Staff", "department": "Finance & Accounts", "email": "pooja.d@vit.ac.in", "phone": "+91 98765 43227", "join_date": "2022-09-01", "membership_expiry": "2024-08-31", "max_books_allowed": 5, "current_loans": 0, "pending_fines": 225.00, "status": "Expired"},
        {"_id": 2019, "member_code": "24BCE1019", "first_name": "Siddharth", "last_name": "Nair", "full_name": "Siddharth Nair", "member_type": "Student", "department": "Computer Science & Engineering", "email": "siddharth.nair2024@vitstudent.ac.in", "phone": "+91 98765 43228", "join_date": "2024-08-01", "membership_expiry": "2028-06-30", "max_books_allowed": 3, "current_loans": 1, "pending_fines": 0.00, "status": "Active"},
        {"_id": 2020, "member_code": "FAC-0105", "first_name": "Dr. Radhika", "last_name": "Menon", "full_name": "Dr. Radhika Menon", "member_type": "Faculty", "department": "Management Studies", "email": "radhika.menon@vit.ac.in", "phone": "+91 98765 43229", "join_date": "2026-10-19", "membership_expiry": "2029-12-31", "max_books_allowed": 8, "current_loans": 0, "pending_fines": 0.00, "status": "Active"}
    ]
    db.members.insert_many(members)

    # 6. ISSUES (46 active & completed loans)
    issues = [
        {"_id": 5001, "book_id": 1001, "book_title": "Clean Code: A Handbook of Agile Software Craftsmanship", "member_id": 2001, "member_name": "Aarav Sharma", "member_code": "24BCE1001", "librarian_id": 301, "issue_date": "2026-09-01", "due_date": "2026-09-15", "return_date": "2026-09-14", "status": "Returned"},
        {"_id": 5002, "book_id": 1002, "book_title": "Introduction to Algorithms (CLRS)", "member_id": 2002, "member_name": "Diya Patel", "member_code": "24BCE1002", "librarian_id": 302, "issue_date": "2026-08-20", "due_date": "2026-09-06", "return_date": "2026-09-14", "status": "Returned"},
        {"_id": 5003, "book_id": 1003, "book_title": "Database System Concepts", "member_id": 2003, "member_name": "Rohan Iyer", "member_code": "24BCE1003", "librarian_id": 301, "issue_date": "2026-09-02", "due_date": "2026-09-16", "return_date": "2026-09-15", "status": "Returned"},
        {"_id": 5004, "book_id": 1004, "book_title": "Computer Networks", "member_id": 2004, "member_name": "Ananya Verma", "member_code": "24BCE1004", "librarian_id": 304, "issue_date": "2026-09-05", "due_date": "2026-09-19", "return_date": "2026-09-18", "status": "Returned"},
        {"_id": 5005, "book_id": 1005, "book_title": "Design Patterns: Elements of Reusable Object-Oriented Software", "member_id": 2005, "member_name": "Kabir Mehta", "member_code": "24BCE1005", "librarian_id": 302, "issue_date": "2026-08-25", "due_date": "2026-09-08", "return_date": "2026-09-10", "status": "Returned"},
        {"_id": 5006, "book_id": 1006, "book_title": "Operating System Concepts", "member_id": 2006, "member_name": "Isha Nair", "member_code": "24BCE1006", "librarian_id": 301, "issue_date": "2026-09-03", "due_date": "2026-09-17", "return_date": "2026-09-17", "status": "Returned"},
        {"_id": 5007, "book_id": 1007, "book_title": "The Art of Computer Programming, Vol. 1", "member_id": 2007, "member_name": "Aditya Rao", "member_code": "24BCE1007", "librarian_id": 303, "issue_date": "2026-08-28", "due_date": "2026-09-11", "return_date": "2026-09-25", "status": "Returned"},
        {"_id": 5008, "book_id": 1008, "book_title": "The God of Small Things", "member_id": 2008, "member_name": "Tara Mukherjee", "member_code": "24BCE1008", "librarian_id": 302, "issue_date": "2026-09-04", "due_date": "2026-09-18", "return_date": "2026-09-18", "status": "Returned"},
        {"_id": 5009, "book_id": 1009, "book_title": "Malgudi Days", "member_id": 2009, "member_name": "Vihaan Reddy", "member_code": "24BCE1009", "librarian_id": 304, "issue_date": "2026-09-06", "due_date": "2026-09-20", "return_date": "2026-09-19", "status": "Returned"},
        {"_id": 5010, "book_id": 1010, "book_title": "The Blue Umbrella", "member_id": 2010, "member_name": "Meera Kapoor", "member_code": "24BCE1010", "librarian_id": 301, "issue_date": "2026-09-07", "due_date": "2026-09-21", "return_date": "2026-09-21", "status": "Returned"},
        # Active Loans (31 active loans)
        {"_id": 5016, "book_id": 1001, "book_title": "Clean Code: A Handbook of Agile Software Craftsmanship", "member_id": 2010, "member_name": "Meera Kapoor", "member_code": "24BCE1010", "librarian_id": 301, "issue_date": "2026-10-18", "due_date": "2026-11-01", "return_date": None, "status": "Issued"},
        {"_id": 5017, "book_id": 1002, "book_title": "Introduction to Algorithms (CLRS)", "member_id": 2001, "member_name": "Aarav Sharma", "member_code": "24BCE1001", "librarian_id": 302, "issue_date": "2026-10-19", "due_date": "2026-11-02", "return_date": None, "status": "Issued"},
        {"_id": 5018, "book_id": 1002, "book_title": "Introduction to Algorithms (CLRS)", "member_id": 2011, "member_name": "Arjun Bhat", "member_code": "24BCE1011", "librarian_id": 302, "issue_date": "2026-10-20", "due_date": "2026-11-03", "return_date": None, "status": "Issued"},
        {"_id": 5019, "book_id": 1003, "book_title": "Database System Concepts", "member_id": 2002, "member_name": "Diya Patel", "member_code": "24BCE1002", "librarian_id": 301, "issue_date": "2026-10-17", "due_date": "2026-10-31", "return_date": None, "status": "Issued"},
        {"_id": 5020, "book_id": 1004, "book_title": "Computer Networks", "member_id": 2003, "member_name": "Rohan Iyer", "member_code": "24BCE1003", "librarian_id": 304, "issue_date": "2026-10-16", "due_date": "2026-10-30", "return_date": None, "status": "Issued"},
        # Overdue Loans (5 loans overdue)
        {"_id": 5021, "book_id": 1005, "book_title": "Design Patterns: Elements of Reusable Object-Oriented Software", "member_id": 2001, "member_name": "Aarav Sharma", "member_code": "24BCE1001", "librarian_id": 302, "issue_date": "2026-09-29", "due_date": "2026-10-13", "return_date": None, "status": "Overdue"},
        {"_id": 5022, "book_id": 1006, "book_title": "Operating System Concepts", "member_id": 2004, "member_name": "Ananya Verma", "member_code": "24BCE1004", "librarian_id": 301, "issue_date": "2026-09-28", "due_date": "2026-10-12", "return_date": None, "status": "Overdue"},
        {"_id": 5023, "book_id": 1007, "book_title": "The Art of Computer Programming, Vol. 1", "member_id": 2005, "member_name": "Kabir Mehta", "member_code": "24BCE1005", "librarian_id": 303, "issue_date": "2026-09-27", "due_date": "2026-10-11", "return_date": None, "status": "Overdue"},
        {"_id": 5024, "book_id": 1008, "book_title": "The God of Small Things", "member_id": 2006, "member_name": "Isha Nair", "member_code": "24BCE1006", "librarian_id": 302, "issue_date": "2026-09-26", "due_date": "2026-10-10", "return_date": None, "status": "Overdue"},
        {"_id": 5025, "book_id": 1008, "book_title": "The God of Small Things", "member_id": 2007, "member_name": "Aditya Rao", "member_code": "24BCE1007", "librarian_id": 304, "issue_date": "2026-09-25", "due_date": "2026-10-09", "return_date": None, "status": "Overdue"},
        {"_id": 5026, "book_id": 1008, "book_title": "The God of Small Things", "member_id": 2008, "member_name": "Tara Mukherjee", "member_code": "24BCE1008", "librarian_id": 301, "issue_date": "2026-10-18", "due_date": "2026-11-01", "return_date": None, "status": "Issued"},
        {"_id": 5027, "book_id": 1009, "book_title": "Malgudi Days", "member_id": 2009, "member_name": "Vihaan Reddy", "member_code": "24BCE1009", "librarian_id": 304, "issue_date": "2026-10-19", "due_date": "2026-11-02", "return_date": None, "status": "Issued"},
        {"_id": 5028, "book_id": 1010, "book_title": "The Blue Umbrella", "member_id": 2011, "member_name": "Arjun Bhat", "member_code": "24BCE1011", "librarian_id": 301, "issue_date": "2026-10-20", "due_date": "2026-11-03", "return_date": None, "status": "Issued"},
        {"_id": 5029, "book_id": 1011, "book_title": "Literature", "member_id": 2012, "member_name": "Pooja Chopra", "member_code": "24BCE1012", "librarian_id": 302, "issue_date": "2026-10-15", "due_date": "2026-10-29", "return_date": None, "status": "Issued"},
        {"_id": 5030, "book_id": 1011, "book_title": "Literature", "member_id": 2013, "member_name": "Dr. Vikram Sen", "member_code": "FAC-0101", "librarian_id": 303, "issue_date": "2026-10-10", "due_date": "2026-11-09", "return_date": None, "status": "Issued"},
        {"_id": 5031, "book_id": 1012, "book_title": "Mathematics", "member_id": 2014, "member_name": "Dr. Sunita Rao", "member_code": "FAC-0102", "librarian_id": 301, "issue_date": "2026-10-08", "due_date": "2026-11-07", "return_date": None, "status": "Issued"},
        {"_id": 5032, "book_id": 1012, "book_title": "Mathematics", "member_id": 2003, "member_name": "Rohan Iyer", "member_code": "24BCE1003", "librarian_id": 304, "issue_date": "2026-10-17", "due_date": "2026-10-31", "return_date": None, "status": "Issued"},
        {"_id": 5033, "book_id": 1013, "book_title": "English", "member_id": 2015, "member_name": "Dr. Arvind Gupta", "member_code": "FAC-0103", "librarian_id": 302, "issue_date": "2026-10-11", "due_date": "2026-11-10", "return_date": None, "status": "Issued"},
        {"_id": 5034, "book_id": 1013, "book_title": "English", "member_id": 2004, "member_name": "Ananya Verma", "member_code": "24BCE1004", "librarian_id": 301, "issue_date": "2026-10-18", "due_date": "2026-11-01", "return_date": None, "status": "Issued"},
        {"_id": 5035, "book_id": 1014, "book_title": "Mathematics", "member_id": 2016, "member_name": "Dr. Shalini Das", "member_code": "FAC-0104", "librarian_id": 303, "issue_date": "2026-10-12", "due_date": "2026-11-11", "return_date": None, "status": "Issued"},
        {"_id": 5036, "book_id": 1014, "book_title": "Mathematics", "member_id": 2005, "member_name": "Kabir Mehta", "member_code": "24BCE1005", "librarian_id": 304, "issue_date": "2026-10-19", "due_date": "2026-11-02", "return_date": None, "status": "Issued"},
        {"_id": 5037, "book_id": 1015, "book_title": "English", "member_id": 2006, "member_name": "Isha Nair", "member_code": "24BCE1006", "librarian_id": 301, "issue_date": "2026-10-20", "due_date": "2026-11-03", "return_date": None, "status": "Issued"},
        {"_id": 5038, "book_id": 1015, "book_title": "English", "member_id": 2007, "member_name": "Aditya Rao", "member_code": "24BCE1007", "librarian_id": 302, "issue_date": "2026-10-16", "due_date": "2026-10-30", "return_date": None, "status": "Issued"},
        {"_id": 5039, "book_id": 1016, "book_title": "Mathematics", "member_id": 2008, "member_name": "Tara Mukherjee", "member_code": "24BCE1008", "librarian_id": 304, "issue_date": "2026-10-17", "due_date": "2026-10-31", "return_date": None, "status": "Issued"},
        {"_id": 5040, "book_id": 1016, "book_title": "Mathematics", "member_id": 2009, "member_name": "Vihaan Reddy", "member_code": "24BCE1009", "librarian_id": 301, "issue_date": "2026-10-18", "due_date": "2026-11-01", "return_date": None, "status": "Issued"},
        {"_id": 5041, "book_id": 1018, "book_title": "Head First Design Patterns", "member_id": 2012, "member_name": "Pooja Chopra", "member_code": "24BCE1012", "librarian_id": 303, "issue_date": "2026-10-19", "due_date": "2026-11-02", "return_date": None, "status": "Issued"},
        {"_id": 5042, "book_id": 1019, "book_title": "Learning Python", "member_id": 2002, "member_name": "Diya Patel", "member_code": "24BCE1002", "librarian_id": 302, "issue_date": "2026-10-20", "due_date": "2026-11-03", "return_date": None, "status": "Issued"},
        {"_id": 5043, "book_id": 1020, "book_title": "Clean Architecture: A Craftsman's Guide", "member_id": 2010, "member_name": "Meera Kapoor", "member_code": "24BCE1010", "librarian_id": 304, "issue_date": "2026-10-15", "due_date": "2026-10-29", "return_date": None, "status": "Issued"},
        {"_id": 5044, "book_id": 1022, "book_title": "Database Systems: The Complete Book", "member_id": 2017, "member_name": "Gaurav Saxena", "member_code": "STF-0201", "librarian_id": 301, "issue_date": "2026-07-01", "due_date": "2026-07-15", "return_date": None, "status": "Overdue"},
        {"_id": 5045, "book_id": 1005, "book_title": "Design Patterns: Elements of Reusable Object-Oriented Software", "member_id": 2019, "member_name": "Siddharth Nair", "member_code": "24BCE1019", "librarian_id": 303, "issue_date": "2026-10-21", "due_date": "2026-11-04", "return_date": None, "status": "Issued"},
        {"_id": 5046, "book_id": 1007, "book_title": "The Art of Computer Programming, Vol. 1", "member_id": 2019, "member_name": "Siddharth Nair", "member_code": "24BCE1019", "librarian_id": 301, "issue_date": "2026-10-22", "due_date": "2026-11-05", "return_date": None, "status": "Issued"}
    ]
    db.issues.insert_many(issues)

    # 7. FINES (12 documents - ₹910 pending dues across delinquent members)
    fines = [
        {"_id": 7001, "issue_id": 5001, "member_id": 2001, "member_name": "Aarav Sharma", "book_title": "Clean Code: A Handbook of Agile Software Craftsmanship", "days_overdue": 0, "fine_amount": 0.00, "fine_date": "2026-09-14", "payment_status": "Paid", "paid_on": "2026-09-14", "payment_method": "Cash", "transaction_ref": "TXN_LIB_7001_CASH"},
        {"_id": 7002, "issue_id": 5005, "member_id": 2005, "member_name": "Kabir Mehta", "book_title": "Design Patterns: Elements of Reusable Object-Oriented Software", "days_overdue": 2, "fine_amount": 10.00, "fine_date": "2026-09-10", "payment_status": "Paid", "paid_on": "2026-09-10", "payment_method": "UPI", "transaction_ref": "TXN_LIB_7002_UPI"},
        {"_id": 7003, "issue_id": 5007, "member_id": 2007, "member_name": "Aditya Rao", "book_title": "The Art of Computer Programming, Vol. 1", "days_overdue": 14, "fine_amount": 70.00, "fine_date": "2026-09-25", "payment_status": "Paid", "paid_on": "2026-09-26", "payment_method": "Debit Card", "transaction_ref": "TXN_LIB_7003_DC"},
        {"_id": 7004, "issue_id": 5013, "member_id": 2008, "member_name": "Tara Mukherjee", "book_title": "Malgudi Days", "days_overdue": 15, "fine_amount": 75.00, "fine_date": "2026-09-29", "payment_status": "Paid", "paid_on": "2026-09-30", "payment_method": "UPI", "transaction_ref": "TXN_LIB_7004_UPI"},
        {"_id": 7005, "issue_id": 5022, "member_id": 2004, "member_name": "Ananya Verma", "book_title": "Operating System Concepts", "days_overdue": 12, "fine_amount": 60.00, "fine_date": "2026-10-24", "payment_status": "Pending", "paid_on": None, "payment_method": None, "transaction_ref": None},
        {"_id": 7006, "issue_id": 5021, "member_id": 2001, "member_name": "Aarav Sharma", "book_title": "Design Patterns: Elements of Reusable Object-Oriented Software", "days_overdue": 11, "fine_amount": 55.00, "fine_date": "2026-10-24", "payment_status": "Pending", "paid_on": None, "payment_method": None, "transaction_ref": None},
        {"_id": 7007, "issue_id": 5023, "member_id": 2005, "member_name": "Kabir Mehta", "book_title": "The Art of Computer Programming, Vol. 1", "days_overdue": 13, "fine_amount": 65.00, "fine_date": "2026-10-24", "payment_status": "Pending", "paid_on": None, "payment_method": None, "transaction_ref": None},
        {"_id": 7008, "issue_id": 5024, "member_id": 2006, "member_name": "Isha Nair", "book_title": "The God of Small Things", "days_overdue": 14, "fine_amount": 70.00, "fine_date": "2026-10-24", "payment_status": "Pending", "paid_on": None, "payment_method": None, "transaction_ref": None},
        {"_id": 7009, "issue_id": 5025, "member_id": 2007, "member_name": "Aditya Rao", "book_title": "The God of Small Things", "days_overdue": 15, "fine_amount": 75.00, "fine_date": "2026-10-24", "payment_status": "Pending", "paid_on": None, "payment_method": None, "transaction_ref": None},
        {"_id": 7010, "issue_id": 5044, "member_id": 2017, "member_name": "Gaurav Saxena", "book_title": "Database Systems: The Complete Book", "days_overdue": 114, "fine_amount": 570.00, "fine_date": "2026-10-24", "payment_status": "Pending", "paid_on": None, "payment_method": None, "transaction_ref": None},
        {"_id": 7011, "issue_id": 5047, "member_id": 2018, "member_name": "Pooja Deshmukh", "book_title": "Principles of Mathematical Analysis", "days_overdue": 45, "fine_amount": 225.00, "fine_date": "2026-10-24", "payment_status": "Pending", "paid_on": None, "payment_method": None, "transaction_ref": None},
        {"_id": 7012, "issue_id": 5002, "member_id": 2002, "member_name": "Diya Patel", "book_title": "Introduction to Algorithms (CLRS)", "days_overdue": 8, "fine_amount": 40.00, "fine_date": "2026-09-14", "payment_status": "Paid", "paid_on": "2026-09-15", "payment_method": "Credit Card", "transaction_ref": "TXN_LIB_7012_CC"}
    ]
    db.fines.insert_many(fines)

    # 8. RESERVATIONS (5 queue holds)
    reservations = [
        {"_id": 6001, "book_id": 1008, "book_title": "The God of Small Things", "member_id": 2002, "member_name": "Diya Patel", "reservation_date": "2026-10-20", "queue_position": 1, "status": "Waiting", "expiry_date": "2026-10-27", "ready_for_pickup": 0},
        {"_id": 6002, "book_id": 1008, "book_title": "The God of Small Things", "member_id": 2006, "member_name": "Isha Nair", "reservation_date": "2026-10-21", "queue_position": 2, "status": "Waiting", "expiry_date": "2026-10-28", "ready_for_pickup": 0},
        {"_id": 6003, "book_id": 1005, "book_title": "Design Patterns: Elements of Reusable Object-Oriented Software", "member_id": 2007, "member_name": "Aditya Rao", "reservation_date": "2026-10-22", "queue_position": 1, "status": "Waiting", "expiry_date": "2026-10-29", "ready_for_pickup": 1},
        {"_id": 6004, "book_id": 1005, "book_title": "Design Patterns: Elements of Reusable Object-Oriented Software", "member_id": 2010, "member_name": "Meera Kapoor", "reservation_date": "2026-10-23", "queue_position": 2, "status": "Waiting", "expiry_date": "2026-10-30", "ready_for_pickup": 0},
        {"_id": 6005, "book_id": 1007, "book_title": "The Art of Computer Programming, Vol. 1", "member_id": 2011, "member_name": "Arjun Bhat", "reservation_date": "2026-10-24", "queue_position": 1, "status": "Waiting", "expiry_date": "2026-10-31", "ready_for_pickup": 0}
    ]
    db.reservations.insert_many(reservations)

    print(f"[MongoDB] Seeded 8 collections successfully into {db.name} ({_engine_type}).")

# ----------------------------------------------------------------------------
# CRUD Operations (PyMongo)
# ----------------------------------------------------------------------------

def mongo_get_all_books(q=None, range_filter=None, page=1, per_page=10):
    db = get_mongo_db()
    query = {"status": "Active"}
    if q:
        regex = re.compile(re.escape(q), re.IGNORECASE)
        query["$or"] = [{"title": regex}, {"author_name": regex}, {"isbn": regex}]
    
    total = db.books.count_documents(query)
    skip = (page - 1) * per_page
    cursor = db.books.find(query).sort("_id", 1).skip(skip).limit(per_page)
    
    books = []
    for doc in cursor:
        doc["book_id"] = doc["_id"]
        books.append(doc)
    
    return books, total

def mongo_get_book(book_id):
    db = get_mongo_db()
    b = db.books.find_one({"_id": book_id})
    if not b:
        return None
    b["book_id"] = b["_id"]
    
    # Active borrowers
    active_issues = list(db.issues.find({"book_id": book_id, "status": {"$in": ["Issued", "Overdue"]}}))
    current_borrowers = []
    for issue in active_issues:
        current_borrowers.append({
            "member_id": issue.get("member_id"),
            "member_name": issue.get("member_name"),
            "member_code": issue.get("member_code"),
            "due_date": issue.get("due_date"),
            "is_overdue": issue.get("status") == "Overdue"
        })
    b["current_borrowers"] = current_borrowers
    return b

def mongo_add_book(data):
    db = get_mongo_db()
    # Find max _id
    last = db.books.find().sort("_id", -1).limit(1)
    new_id = (next(last)["_id"] + 1) if last.alive else 1001
    
    author = db.authors.find_one({"_id": int(data.get("author_id", 201))})
    category = db.categories.find_one({"_id": int(data.get("category_id", 101))})
    
    author_name = author["full_name"] if author else "Unknown Author"
    category_name = category["category_name"] if category else "General"
    category_code = category["category_code"] if category else "GEN"
    shelf_zone = category["shelf_zone"] if category else "Zone A"
    
    doc = {
        "_id": new_id,
        "isbn": data.get("isbn"),
        "title": data.get("title"),
        "author_id": int(data.get("author_id", 201)),
        "author_name": author_name,
        "category_id": int(data.get("category_id", 101)),
        "category_name": category_name,
        "category_code": category_code,
        "shelf_zone": shelf_zone,
        "publisher": data.get("publisher", "Academic Press"),
        "publish_date": data.get("publish_date", "2024-01-01"),
        "edition": data.get("edition", "1st"),
        "language": data.get("language", "English"),
        "shelf_location": data.get("shelf_location", "A-01-01"),
        "price": float(data.get("price", 500.0)),
        "total_copies": int(data.get("total_copies", 1)),
        "available_copies": int(data.get("total_copies", 1)),
        "cover_url": data.get("cover_url") or f"https://covers.openlibrary.org/b/isbn/{data.get('isbn')}-M.jpg",
        "added_on": date.today().isoformat(),
        "status": "Active"
    }
    db.books.insert_one(doc)
    return True, f"SUCCESS: Book #{new_id} '{doc['title']}' cataloged in MongoDB.", new_id

def mongo_delete_book(book_id):
    db = get_mongo_db()
    # Check FK references in issues
    active_loan = db.issues.find_one({"book_id": book_id, "status": {"$in": ["Issued", "Overdue"]}})
    if active_loan:
        return False, f"DELETE RESTRICTED: Book #{book_id} has active circulation loans in MongoDB."
    
    res = db.books.delete_one({"_id": book_id})
    if res.deleted_count > 0:
        return True, f"Book #{book_id} deleted from MongoDB collection."
    return False, "Book not found."

def mongo_get_all_members(q=None, type_filter=None):
    db = get_mongo_db()
    query = {}
    if type_filter and type_filter.lower() != 'all':
        query["member_type"] = type_filter
    if q:
        regex = re.compile(re.escape(q), re.IGNORECASE)
        query["$or"] = [{"full_name": regex}, {"member_code": regex}, {"department": regex}, {"email": regex}]
    
    docs = list(db.members.find(query).sort("_id", 1))
    for d in docs:
        d["member_id"] = d["_id"]
    return docs

def mongo_add_member(data):
    db = get_mongo_db()
    last = db.members.find().sort("_id", -1).limit(1)
    new_id = (next(last)["_id"] + 1) if last.alive else 2001
    
    doc = {
        "_id": new_id,
        "member_code": data.get("member_code"),
        "first_name": data.get("first_name"),
        "last_name": data.get("last_name"),
        "full_name": f"{data.get('first_name')} {data.get('last_name')}",
        "member_type": data.get("member_type", "Student"),
        "department": data.get("department", "Engineering"),
        "email": data.get("email"),
        "phone": data.get("phone", "+91 99999 88888"),
        "join_date": date.today().isoformat(),
        "membership_expiry": (date.today() + timedelta(days=365*4)).isoformat(),
        "max_books_allowed": 8 if data.get("member_type") == "Faculty" else 3,
        "current_loans": 0,
        "pending_fines": 0.00,
        "status": "Active"
    }
    db.members.insert_one(doc)
    return True, f"SUCCESS: Member #{new_id} ({doc['member_code']}) registered in MongoDB.", new_id

def mongo_issue_book(book_id, member_id, librarian_id=301):
    db = get_mongo_db()
    # 1. Validate Member
    member = db.members.find_one({"_id": member_id})
    if not member:
        return False, f"VALIDATION REJECTION: Member #{member_id} not found."
    if member["status"] != "Active":
        return False, f"VALIDATION REJECTION: Member {member['full_name']} account is {member['status']}."
    if member.get("pending_fines", 0) > 100:
        return False, f"CIRCULATION REJECTION: Unsettled dues (₹{member['pending_fines']}) exceed policy threshold."
    if member.get("current_loans", 0) >= member.get("max_books_allowed", 3):
        return False, f"QUOTA EXCEEDED: Member {member['full_name']} reached borrow ceiling."

    # 2. Validate Book
    book = db.books.find_one({"_id": book_id})
    if not book:
        return False, f"VALIDATION REJECTION: Book #{book_id} not found."
    if book.get("available_copies", 0) <= 0:
        return False, f"CIRCULATION REJECTION: Zero available copies for book '{book['title']}'. Reservation advised."

    # 3. Create Issue Document
    last_issue = db.issues.find().sort("_id", -1).limit(1)
    new_issue_id = (next(last_issue)["_id"] + 1) if last_issue.alive else 5001
    loan_days = 28 if member.get("member_type") == "Faculty" else 14
    due_date = (date.today() + timedelta(days=loan_days)).isoformat()

    issue_doc = {
        "_id": new_issue_id,
        "book_id": book_id,
        "book_title": book["title"],
        "member_id": member_id,
        "member_name": member["full_name"],
        "member_code": member["member_code"],
        "librarian_id": librarian_id,
        "issue_date": date.today().isoformat(),
        "due_date": due_date,
        "return_date": None,
        "status": "Issued"
    }
    db.issues.insert_one(issue_doc)

    # 4. Atomic updates: Decrement book stock & increment member loans
    db.books.update_one({"_id": book_id}, {"$inc": {"available_copies": -1}})
    db.members.update_one({"_id": member_id}, {"$inc": {"current_loans": 1}})

    # 5. Mark reservation fulfilled if any
    db.reservations.update_one({"book_id": book_id, "member_id": member_id, "status": "Waiting"}, {"$set": {"status": "Fulfilled"}})

    return True, f"SUCCESS: Issue #{new_issue_id} confirmed. Book '{book['title']}' issued to {member['full_name']}. Loan period: {loan_days} days.", new_issue_id

def mongo_return_book(issue_id, return_date=None):
    db = get_mongo_db()
    issue = db.issues.find_one({"_id": issue_id})
    if not issue:
        return False, f"VALIDATION REJECTION: Issue record #{issue_id} not found."
    if issue["status"] == "Returned":
        return False, f"CIRCULATION REJECTION: Issue #{issue_id} was already returned."

    ret_date_str = return_date or date.today().isoformat()
    due_date_str = issue["due_date"]
    
    # Calculate days late
    ret_d = datetime.strptime(ret_date_str, "%Y-%m-%d").date()
    due_d = datetime.strptime(due_date_str, "%Y-%m-%d").date()
    days_late = max(0, (ret_d - due_d).days)
    fine_amount = days_late * 5.0

    # Update issue status
    db.issues.update_one({"_id": issue_id}, {"$set": {"return_date": ret_date_str, "status": "Returned"}})

    # Atomic restore book stock & decrement member loans
    db.books.update_one({"_id": issue["book_id"]}, {"$inc": {"available_copies": 1}})
    db.members.update_one({"_id": issue["member_id"]}, {"$inc": {"current_loans": -1}})

    # Log fine if overdue
    if fine_amount > 0:
        last_fine = db.fines.find().sort("_id", -1).limit(1)
        new_fine_id = (next(last_fine)["_id"] + 1) if last_fine.alive else 7001
        fine_doc = {
            "_id": new_fine_id,
            "issue_id": issue_id,
            "member_id": issue["member_id"],
            "member_name": issue["member_name"],
            "book_title": issue["book_title"],
            "days_overdue": days_late,
            "fine_amount": fine_amount,
            "fine_date": ret_date_str,
            "payment_status": "Pending",
            "paid_on": None,
            "payment_method": None,
            "transaction_ref": None
        }
        db.fines.insert_one(fine_doc)
        db.members.update_one({"_id": issue["member_id"]}, {"$inc": {"pending_fines": fine_amount}})
        return True, f"RETURN PROCESSED (LATE): Book '{issue['book_title']}' returned by {issue['member_name']}. Overdue by {days_late} days. Fine of ₹{fine_amount:.2f} logged in MongoDB."

    return True, f"RETURN PROCESSED (ON TIME): Book '{issue['book_title']}' returned successfully by {issue['member_name']}. No dues accrued."

def mongo_reserve_book(book_id, member_id):
    db = get_mongo_db()
    book = db.books.find_one({"_id": book_id})
    member = db.members.find_one({"_id": member_id})
    if not book or not member:
        return False, "Invalid book or member."
    
    # Calculate queue position
    queue_pos = db.reservations.count_documents({"book_id": book_id, "status": "Waiting"}) + 1
    last_res = db.reservations.find().sort("_id", -1).limit(1)
    new_res_id = (next(last_res)["_id"] + 1) if last_res.alive else 6001

    res_doc = {
        "_id": new_res_id,
        "book_id": book_id,
        "book_title": book["title"],
        "member_id": member_id,
        "member_name": member["full_name"],
        "reservation_date": date.today().isoformat(),
        "queue_position": queue_pos,
        "status": "Waiting",
        "expiry_date": (date.today() + timedelta(days=7)).isoformat(),
        "ready_for_pickup": 0
    }
    db.reservations.insert_one(res_doc)
    return True, f"RESERVATION CONFIRMED: Reservation #{new_res_id} placed for '{book['title']}'. Member: {member['full_name']}. Queue Position: #{queue_pos}."

def mongo_pay_fine(fine_id, payment_mode="UPI", txn_ref=None):
    db = get_mongo_db()
    fine = db.fines.find_one({"_id": fine_id})
    if not fine:
        return False, f"Fine #{fine_id} not found."
    if fine["payment_status"] == "Paid":
        return False, f"PAYMENT REJECTION: Fine #{fine_id} has already been settled (Paid)."

    ref = txn_ref or f"TXN_MONGO_{int(time.time())}_{fine_id}"
    db.fines.update_one(
        {"_id": fine_id},
        {"$set": {"payment_status": "Paid", "paid_on": date.today().isoformat(), "payment_method": payment_mode, "transaction_ref": ref}}
    )

    # Decrement member pending fines
    db.members.update_one({"_id": fine["member_id"]}, {"$inc": {"pending_fines": -fine["fine_amount"]}})

    # Auto-reactivate suspended account if dues cleared
    updated_member = db.members.find_one({"_id": fine["member_id"]})
    if updated_member and updated_member.get("pending_fines", 0) <= 0 and updated_member.get("status") == "Suspended":
        db.members.update_one({"_id": fine["member_id"]}, {"$set": {"status": "Active"}})

    return True, f"RECEIPT ISSUED: Fine #{fine_id} of ₹{fine['fine_amount']:.2f} settled by {fine['member_name']} via {payment_mode}. Voucher: {ref}"

def mongo_get_stats():
    db = get_mongo_db()
    books_count = db.books.count_documents({"status": "Active"})
    total_members = db.members.count_documents({})
    active_members = db.members.count_documents({"status": "Active"})
    active_loans = db.issues.count_documents({"status": {"$in": ["Issued", "Overdue"]}})
    overdue_count = db.issues.count_documents({"status": "Overdue"})
    waiting_reservations = db.reservations.count_documents({"status": "Waiting"})
    
    # Aggregation for fines
    fine_pipe = [
        {"$match": {"payment_status": "Pending"}},
        {"$group": {"_id": None, "total": {"$sum": "$fine_amount"}}}
    ]
    fine_res = list(db.fines.aggregate(fine_pipe))
    pending_fines = fine_res[0]["total"] if fine_res else 0.0

    collected_pipe = [
        {"$match": {"payment_status": "Paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$fine_amount"}}}
    ]
    coll_res = list(db.fines.aggregate(collected_pipe))
    collected_fines = coll_res[0]["total"] if coll_res else 0.0

    # Stock
    stock_pipe = [
        {"$group": {"_id": None, "total": {"$sum": "$total_copies"}, "available": {"$sum": "$available_copies"}}}
    ]
    stock_res = list(db.books.aggregate(stock_pipe))
    total_copies = stock_res[0]["total"] if stock_res else 0
    available_copies = stock_res[0]["available"] if stock_res else 0

    return {
        "books_count": books_count,
        "total_members": total_members,
        "active_members": active_members,
        "active_loans": active_loans,
        "overdue_count": overdue_count,
        "pending_fines": pending_fines,
        "collected_fines": collected_fines,
        "waiting_reservations": waiting_reservations,
        "total_copies": total_copies,
        "available_copies": available_copies,
        "engine": _engine_type
    }

# ----------------------------------------------------------------------------
# 18 MongoDB Aggregation Pipelines (Matching Rubric Queries)
# ----------------------------------------------------------------------------
MONGO_PIPELINES = [
    {
        "id": "M1",
        "title": "Recent Catalog Additions (MongoDB find + sort + limit)",
        "collection": "books",
        "mql": 'db.books.find({}, {"_id": 1, "isbn": 1, "title": 1, "publisher": 1, "publish_date": 1, "price": 1, "added_on": 1}).sort({"added_on": -1}).limit(10)',
        "run": lambda db: list(db.books.find({}, {"_id": 1, "isbn": 1, "title": 1, "publisher": 1, "publish_date": 1, "price": 1, "added_on": 1}).sort("added_on", -1).limit(10))
    },
    {
        "id": "M2",
        "title": "Books with Author & Category Classification ($lookup Join)",
        "collection": "books",
        "mql": '''db.books.aggregate([
  { "$lookup": { "from": "authors", "localField": "author_id", "foreignField": "_id", "as": "author_info" } },
  { "$unwind": "$author_info" },
  { "$project": { "book_id": "$_id", "title": 1, "author_name": "$author_info.full_name", "nationality": "$author_info.nationality", "shelf_location": 1, "price": 1 } }
])''',
        "run": lambda db: list(db.books.aggregate([
            {"$lookup": {"from": "authors", "localField": "author_id", "foreignField": "_id", "as": "author_info"}},
            {"$unwind": "$author_info"},
            {"$project": {"book_id": "$_id", "title": 1, "author_name": "$author_info.full_name", "nationality": "$author_info.nationality", "shelf_location": 1, "price": 1}}
        ]))
    },
    {
        "id": "M3",
        "title": "Circulation Audit Trail (Multi-Collection $lookup)",
        "collection": "issues",
        "mql": '''db.issues.aggregate([
  { "$lookup": { "from": "books", "localField": "book_id", "foreignField": "_id", "as": "b" } },
  { "$lookup": { "from": "members", "localField": "member_id", "foreignField": "_id", "as": "m" } },
  { "$unwind": "$b" }, { "$unwind": "$m" },
  { "$project": { "issue_id": "$_id", "title": "$b.title", "patron": "$m.full_name", "member_type": "$m.member_type", "issue_date": 1, "due_date": 1, "status": 1 } }
])''',
        "run": lambda db: list(db.issues.aggregate([
            {"$lookup": {"from": "books", "localField": "book_id", "foreignField": "_id", "as": "b"}},
            {"$lookup": {"from": "members", "localField": "member_id", "foreignField": "_id", "as": "m"}},
            {"$unwind": "$b"}, {"$unwind": "$m"},
            {"$project": {"issue_id": "$_id", "title": "$b.title", "patron": "$m.full_name", "member_type": "$m.member_type", "issue_date": 1, "due_date": 1, "status": 1}}
        ]))
    },
    {
        "id": "M4",
        "title": "Subject Collection Metrics ($group + $sum + $avg)",
        "collection": "books",
        "mql": '''db.books.aggregate([
  { "$group": {
      "_id": "$category_name",
      "shelf_zone": { "$first": "$shelf_zone" },
      "title_count": { "$sum": 1 },
      "total_volumes": { "$sum": "$total_copies" },
      "available_volumes": { "$sum": "$available_copies" },
      "avg_title_price": { "$avg": "$price" }
  } },
  { "$sort": { "total_volumes": -1 } }
])''',
        "run": lambda db: list(db.books.aggregate([
            {"$group": {
                "_id": "$category_name",
                "shelf_zone": {"$first": "$shelf_zone"},
                "title_count": {"$sum": 1},
                "total_volumes": {"$sum": "$total_copies"},
                "available_volumes": {"$sum": "$available_copies"},
                "avg_title_price": {"$avg": "$price"}
            }},
            {"$project": {
                "category_name": "$_id",
                "shelf_zone": 1,
                "title_count": 1,
                "total_volumes": 1,
                "available_volumes": 1,
                "avg_title_price": 1
            }},
            {"$sort": {"total_volumes": -1}}
        ]))
    },
    {
        "id": "M5",
        "title": "Top-5 Most Borrowed Titles ($group on issues + $sort + $limit)",
        "collection": "issues",
        "mql": '''db.issues.aggregate([
  { "$group": {
      "_id": "$book_title",
      "total_times_borrowed": { "$sum": 1 }
  } },
  { "$sort": { "total_times_borrowed": -1 } },
  { "$limit": 5 }
])''',
        "run": lambda db: list(db.issues.aggregate([
            {"$group": {"_id": "$book_title", "total_times_borrowed": {"$sum": 1}}},
            {"$sort": {"total_times_borrowed": -1}},
            {"$limit": 5},
            {"$project": {"book_title": "$_id", "total_times_borrowed": 1}}
        ]))
    },
    {
        "id": "M6",
        "title": "Active Overdue Loans with Contact Details ($match + $lookup)",
        "collection": "issues",
        "mql": '''db.issues.aggregate([
  { "$match": { "status": "Overdue" } },
  { "$lookup": { "from": "members", "localField": "member_id", "foreignField": "_id", "as": "m" } },
  { "$unwind": "$m" },
  { "$project": { "issue_id": "$_id", "borrower_name": "$m.full_name", "email": "$m.email", "phone": "$m.phone", "book_title": 1, "due_date": 1 } }
])''',
        "run": lambda db: list(db.issues.aggregate([
            {"$match": {"status": "Overdue"}},
            {"$lookup": {"from": "members", "localField": "member_id", "foreignField": "_id", "as": "m"}},
            {"$unwind": "$m"},
            {"$project": {"issue_id": "$_id", "borrower_name": "$m.full_name", "email": "$m.email", "phone": "$m.phone", "book_title": 1, "due_date": 1}}
        ]))
    },
    {
        "id": "M7",
        "title": "Revenue Breakdown by Payment Channel ($match Paid + $group)",
        "collection": "fines",
        "mql": '''db.fines.aggregate([
  { "$match": { "payment_status": "Paid" } },
  { "$group": {
      "_id": "$payment_method",
      "transaction_count": { "$sum": 1 },
      "total_revenue": { "$sum": "$fine_amount" },
      "avg_ticket": { "$avg": "$fine_amount" }
  } }
])''',
        "run": lambda db: list(db.fines.aggregate([
            {"$match": {"payment_status": "Paid"}},
            {"$group": {
                "_id": "$payment_method",
                "transaction_count": {"$sum": 1},
                "total_revenue": {"$sum": "$fine_amount"},
                "avg_ticket": {"$avg": "$fine_amount"}
            }},
            {"$project": {
                "payment_channel": "$_id",
                "transaction_count": 1,
                "total_revenue": 1,
                "avg_ticket": 1
            }}
        ]))
    },
    {
        "id": "M8",
        "title": "Patron Outstanding Fines Ledger ($match Pending + $group)",
        "collection": "fines",
        "mql": '''db.fines.aggregate([
  { "$match": { "payment_status": "Pending" } },
  { "$group": {
      "_id": "$member_name",
      "pending_fines_count": { "$sum": 1 },
      "total_dues_accrued": { "$sum": "$fine_amount" },
      "max_single_fine": { "$max": "$fine_amount" }
  } },
  { "$sort": { "total_dues_accrued": -1 } }
])''',
        "run": lambda db: list(db.fines.aggregate([
            {"$match": {"payment_status": "Pending"}},
            {"$group": {
                "_id": "$member_name",
                "pending_fines_count": {"$sum": 1},
                "total_dues_accrued": {"$sum": "$fine_amount"},
                "max_single_fine": {"$max": "$fine_amount"}
            }},
            {"$project": {
                "member_name": "$_id",
                "pending_fines_count": 1,
                "total_dues_accrued": 1,
                "max_single_fine": 1
            }},
            {"$sort": {"total_dues_accrued": -1}}
        ]))
    },
    {
        "id": "M9",
        "title": "Prolific Authors with Multiple Catalog Titles ($group + $match having >= 2)",
        "collection": "books",
        "mql": '''db.books.aggregate([
  { "$group": { "_id": "$author_name", "titles_cataloged": { "$sum": 1 }, "total_volumes": { "$sum": "$total_copies" } } },
  { "$match": { "titles_cataloged": { "$gte": 2 } } },
  { "$sort": { "titles_cataloged": -1 } }
])''',
        "run": lambda db: list(db.books.aggregate([
            {"$group": {"_id": "$author_name", "titles_cataloged": {"$sum": 1}, "total_volumes": {"$sum": "$total_copies"}}},
            {"$match": {"titles_cataloged": {"$gte": 2}}},
            {"$project": {"author_name": "$_id", "titles_cataloged": 1, "total_volumes": 1}},
            {"$sort": {"titles_cataloged": -1}}
        ]))
    },
    {
        "id": "M10",
        "title": "Catalog Volumes in High-Demand Technical Zones ($in Array Query)",
        "collection": "books",
        "mql": 'db.books.find({"shelf_zone": {"$in": ["Zone A", "Zone B", "Zone C", "Zone H"]}}, {"_id": 1, "title": 1, "author_name": 1, "shelf_zone": 1, "price": 1})',
        "run": lambda db: list(db.books.find({"shelf_zone": {"$in": ["Zone A", "Zone B", "Zone C", "Zone H"]}}, {"_id": 1, "title": 1, "author_name": 1, "shelf_zone": 1, "price": 1}))
    }
]

def execute_mongo_pipeline(pipeline_id):
    db = get_mongo_db()
    target = next((p for p in MONGO_PIPELINES if p["id"].lower() == pipeline_id.lower()), None)
    if not target:
        return None, f"Pipeline {pipeline_id} not found."
    
    t0 = time.time()
    results = target["run"](db)
    t1 = time.time()
    
    # Clean ObjectIds and format numbers
    for r in results:
        for k, v in list(r.items()):
            if isinstance(v, float):
                r[k] = round(v, 2)
            elif not isinstance(v, (int, str, float, bool, list, dict)) and v is not None:
                r[k] = str(v)
    
    headers = list(results[0].keys()) if results else []
    return {
        "id": target["id"],
        "title": target["title"],
        "collection": target["collection"],
        "mql": target["mql"],
        "headers": headers,
        "rows": results,
        "count": len(results),
        "execution_ms": round((t1 - t0) * 1000, 2)
    }, None
