/**
 * LibraCore — MongoDB Database Seed Script
 * For mongosh (MongoDB Shell) or MongoDB Compass Executable Script
 * Database: libracore_db
 */

const dbName = 'libracore_db';
const d = db.getSiblingDB(dbName);

print(">>> Initializing LibraCore MongoDB Collections in '" + dbName + "'...");

// 1. Drop existing collections
d.categories.drop();
d.authors.drop();
d.librarians.drop();
d.books.drop();
d.members.drop();
d.issues.drop();
d.fines.drop();
d.reservations.drop();

// 2. Categories
d.categories.insertMany([
  { _id: 101, category_name: "Computer Science & AI", category_code: "CS-AI", shelf_zone: "Zone A", description: "Algorithms, Operating Systems, Machine Learning & Architecture" },
  { _id: 102, category_name: "Database & Systems", category_code: "DB-SYS", shelf_zone: "Zone B", description: "Relational, NoSQL, Distributed Storage & Query Optimization" },
  { _id: 103, category_name: "Software Engineering", category_code: "SWE", shelf_zone: "Zone C", description: "Design Patterns, Clean Code, Refactoring & Microservices" },
  { _id: 104, category_name: "Mathematics & Statistics", category_code: "MATH", shelf_zone: "Zone D", description: "Discrete Mathematics, Linear Algebra, Real Analysis & Probability" },
  { _id: 105, category_name: "Physics & Electronics", category_code: "PHYS", shelf_zone: "Zone E", description: "Quantum Mechanics, Semiconductor Devices & Circuit Theory" },
  { _id: 106, category_name: "English Literature & Classics", category_code: "ENG-LIT", shelf_zone: "Zone F", description: "British & American Classics, Poetry, Drama & Linguistics" },
  { _id: 107, category_name: "Indian Fiction & Culture", category_code: "IND-LIT", shelf_zone: "Zone G", description: "Post-Colonial Literature, Contemporary Indian Authors & Heritage" },
  { _id: 108, category_name: "Computer Networks & Security", category_code: "NET-SEC", shelf_zone: "Zone H", description: "Cryptography, TCP/IP Protocols, Network Routing & Cybersecurity" },
  { _id: 109, category_name: "Business & Management", category_code: "MGMT", shelf_zone: "Zone I", description: "Organizational Behavior, Financial Accounting & Strategic Leadership" },
  { _id: 110, category_name: "General Science & Reference", category_code: "GEN-SCI", shelf_zone: "Zone J", description: "Encyclopedias, History of Science & Research Methodology" }
]);

// 3. Authors
d.authors.insertMany([
  { _id: 201, first_name: "Robert", last_name: "Martin", full_name: "Robert Martin", nationality: "American", primary_genre: "Software Architecture" },
  { _id: 202, first_name: "Thomas", last_name: "Cormen", full_name: "Thomas Cormen", nationality: "American", primary_genre: "Algorithms" },
  { _id: 203, first_name: "Abraham", last_name: "Silberschatz", full_name: "Abraham Silberschatz", nationality: "American", primary_genre: "Operating Systems & Databases" },
  { _id: 204, first_name: "Andrew", last_name: "Tanenbaum", full_name: "Andrew Tanenbaum", nationality: "American-Dutch", primary_genre: "Computer Networking" },
  { _id: 205, first_name: "Erich", last_name: "Gamma", full_name: "Erich Gamma", nationality: "Swiss", primary_genre: "Object-Oriented Design" },
  { _id: 206, first_name: "Donald", last_name: "Knuth", full_name: "Donald Knuth", nationality: "American", primary_genre: "Theoretical Computer Science" },
  { _id: 207, first_name: "Arundhati", last_name: "Roy", full_name: "Arundhati Roy", nationality: "Indian", primary_genre: "Contemporary Fiction" },
  { _id: 208, first_name: "R.K.", last_name: "Narayan", full_name: "R.K. Narayan", nationality: "Indian", primary_genre: "Classic Indian Fiction" },
  { _id: 209, first_name: "Ruskin", last_name: "Bond", full_name: "Ruskin Bond", nationality: "Indian", primary_genre: "Children Literature" },
  { _id: 210, first_name: "Wade", last_name: "Warren", full_name: "Wade Warren", nationality: "British", primary_genre: "Modern Linguistics" },
  { _id: 211, first_name: "David", last_name: "Morgan", full_name: "David Morgan", nationality: "British", primary_genre: "Applied Mathematics" },
  { _id: 212, first_name: "Kristin", last_name: "Watson", full_name: "Kristin Watson", nationality: "Canadian", primary_genre: "Quantum Electrodynamics" },
  { _id: 213, first_name: "Savannah", last_name: "Nguyen", full_name: "Savannah Nguyen", nationality: "Australian", primary_genre: "Statistical Inference" },
  { _id: 214, first_name: "Jacob", last_name: "Jones", full_name: "Jacob Jones", nationality: "Canadian", primary_genre: "Thermodynamics" },
  { _id: 215, first_name: "Arlene", last_name: "McCoy", full_name: "Arlene McCoy", nationality: "Irish", primary_genre: "19th Century Drama" }
]);

// 4. Books
d.books.insertMany([
  { _id: 1001, isbn: "978-0132350884", title: "Clean Code: A Handbook of Agile Software Craftsmanship", author_id: 201, author_name: "Robert Martin", category_id: 103, category_name: "Software Engineering", category_code: "SWE", shelf_zone: "Zone C", publisher: "Prentice Hall", publish_date: "2008-08-01", price: 799.00, total_copies: 5, available_copies: 4, cover_url: "https://covers.openlibrary.org/b/isbn/9780132350884-M.jpg", status: "Active" },
  { _id: 1002, isbn: "978-0262033848", title: "Introduction to Algorithms (CLRS)", author_id: 202, author_name: "Thomas Cormen", category_id: 101, category_name: "Computer Science & AI", category_code: "CS-AI", shelf_zone: "Zone A", publisher: "MIT Press", publish_date: "2009-07-31", price: 1450.00, total_copies: 6, available_copies: 4, cover_url: "https://covers.openlibrary.org/b/isbn/9780262033848-M.jpg", status: "Active" },
  { _id: 1003, isbn: "978-0078022159", title: "Database System Concepts", author_id: 203, author_name: "Abraham Silberschatz", category_id: 102, category_name: "Database & Systems", category_code: "DB-SYS", shelf_zone: "Zone B", publisher: "McGraw-Hill", publish_date: "2019-03-25", price: 890.00, total_copies: 4, available_copies: 3, cover_url: "https://covers.openlibrary.org/b/isbn/9780078022159-M.jpg", status: "Active" },
  { _id: 1004, isbn: "978-0132126953", title: "Computer Networks", author_id: 204, author_name: "Andrew Tanenbaum", category_id: 108, category_name: "Computer Networks & Security", category_code: "NET-SEC", shelf_zone: "Zone H", publisher: "Pearson", publish_date: "2010-10-07", price: 825.00, total_copies: 4, available_copies: 3, cover_url: "https://covers.openlibrary.org/b/isbn/9780132126953-M.jpg", status: "Active" },
  { _id: 1005, isbn: "978-0201633610", title: "Design Patterns: Elements of Reusable Object-Oriented Software", author_id: 205, author_name: "Erich Gamma", category_id: 103, category_name: "Software Engineering", category_code: "SWE", shelf_zone: "Zone C", publisher: "Addison-Wesley", publish_date: "1994-10-31", price: 950.00, total_copies: 3, available_copies: 1, cover_url: "https://covers.openlibrary.org/b/isbn/9780201633610-M.jpg", status: "Active" },
  { _id: 1006, isbn: "978-1118063330", title: "Operating System Concepts", author_id: 203, author_name: "Abraham Silberschatz", category_id: 101, category_name: "Computer Science & AI", category_code: "CS-AI", shelf_zone: "Zone A", publisher: "Wiley", publish_date: "2018-05-04", price: 895.00, total_copies: 5, available_copies: 4, cover_url: "https://covers.openlibrary.org/b/isbn/9781118063330-M.jpg", status: "Active" },
  { _id: 1007, isbn: "978-0201896831", title: "The Art of Computer Programming, Vol. 1", author_id: 206, author_name: "Donald Knuth", category_id: 101, category_name: "Computer Science & AI", category_code: "CS-AI", shelf_zone: "Zone A", publisher: "Addison-Wesley", publish_date: "1997-07-04", price: 1950.00, total_copies: 2, available_copies: 1, cover_url: "https://covers.openlibrary.org/b/isbn/9780201896831-M.jpg", status: "Active" },
  { _id: 1008, isbn: "978-0812979657", title: "The God of Small Things", author_id: 207, author_name: "Arundhati Roy", category_id: 107, category_name: "Indian Fiction & Culture", category_code: "IND-LIT", shelf_zone: "Zone G", publisher: "Random House", publish_date: "2008-12-16", price: 450.00, total_copies: 3, available_copies: 0, cover_url: "https://covers.openlibrary.org/b/isbn/9780812979657-M.jpg", status: "Active" },
  { _id: 1009, isbn: "978-0143039655", title: "Malgudi Days", author_id: 208, author_name: "R.K. Narayan", category_id: 107, category_name: "Indian Fiction & Culture", category_code: "IND-LIT", shelf_zone: "Zone G", publisher: "Penguin Classics", publish_date: "2006-11-28", price: 299.00, total_copies: 6, available_copies: 5, cover_url: "https://covers.openlibrary.org/b/isbn/9780143039655-M.jpg", status: "Active" },
  { _id: 1010, isbn: "978-8171673407", title: "The Blue Umbrella", author_id: 209, author_name: "Ruskin Bond", category_id: 107, category_name: "Indian Fiction & Culture", category_code: "IND-LIT", shelf_zone: "Zone G", publisher: "Rupa Publications", publish_date: "1992-05-15", price: 195.00, total_copies: 5, available_copies: 4, cover_url: "https://covers.openlibrary.org/b/isbn/9788171673407-M.jpg", status: "Active" }
]);

// 5. Indexes for High-Velocity Queries
d.books.createIndex({ title: "text", author_name: "text", isbn: "text" });
d.books.createIndex({ category_id: 1 });
d.books.createIndex({ price: -1 });
d.members.createIndex({ member_code: 1 }, { unique: true });
d.issues.createIndex({ status: 1, due_date: 1 });
d.fines.createIndex({ payment_status: 1 });

print(">>> SUCCESS: LibraCore MongoDB Database Ready with 8 Collections & Production Indexes.");
