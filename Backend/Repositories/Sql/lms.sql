-- Library Management System Schema

-- Create Authors table
CREATE TABLE Authors (
    AuthorID INT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Country VARCHAR(50)
);

-- Create Categories table
CREATE TABLE Categories (
    CategoryID INT PRIMARY KEY,
    CategoryName VARCHAR(50) NOT NULL
);

-- Create Books table
CREATE TABLE Books (
    BookID INT PRIMARY KEY,
    Title VARCHAR(150) NOT NULL,
    AuthorID INT,
    CategoryID INT,
    YearPublished INT,
    ISBN VARCHAR(20),
    CopiesAvailable INT DEFAULT 1,
    FOREIGN KEY (AuthorID) REFERENCES Authors(AuthorID),
    FOREIGN KEY (CategoryID) REFERENCES Categories(CategoryID)
);

-- Create Members table
CREATE TABLE Members (
    MemberID INT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Email VARCHAR(100) UNIQUE,
    JoinDate DATE
);

-- Create Loans table
CREATE TABLE Loans (
    LoanID INT PRIMARY KEY,
    BookID INT,
    MemberID INT,
    LoanDate DATE,
    DueDate DATE,
    ReturnDate DATE,
    FOREIGN KEY (BookID) REFERENCES Books(BookID),
    FOREIGN KEY (MemberID) REFERENCES Members(MemberID)
);

-- Insert sample data into Authors
INSERT INTO Authors (AuthorID, Name, Country) VALUES
(1, 'J.K. Rowling', 'United Kingdom'),
(2, 'George R.R. Martin', 'United States'),
(3, 'J.R.R. Tolkien', 'United Kingdom');

-- Insert sample data into Categories
INSERT INTO Categories (CategoryID, CategoryName) VALUES
(1, 'Fantasy'),
(2, 'Science Fiction'),
(3, 'Mystery');

-- Insert sample data into Books
INSERT INTO Books (BookID, Title, AuthorID, CategoryID, YearPublished, ISBN, CopiesAvailable) VALUES
(1, 'Harry Potter and the Sorcerer''s Stone', 1, 1, 1997, '9780439708180', 5),
(2, 'A Game of Thrones', 2, 1, 1996, '9780553103540', 3),
(3, 'The Hobbit', 3, 1, 1937, '9780618968633', 4);

-- Insert sample data into Members
INSERT INTO Members (MemberID, Name, Email, JoinDate) VALUES
(1, 'Alice Johnson', 'alice@example.com', '2023-01-15'),
(2, 'Bob Smith', 'bob@example.com', '2023-02-20');

-- Insert sample data into Loans
INSERT INTO Loans (LoanID, BookID, MemberID, LoanDate, DueDate, ReturnDate) VALUES
(1, 1, 1, '2023-03-01', '2023-03-15', NULL),
(2, 2, 2, '2023-03-05', '2023-03-19', '2023-03-18');

-- Query: List all books with author and category
SELECT b.Title, a.Name AS Author, c.CategoryName, b.CopiesAvailable
FROM Books b
JOIN Authors a ON b.AuthorID = a.AuthorID
JOIN Categories c ON b.CategoryID = c.CategoryID;

-- Query: List all overdue books
SELECT m.Name AS Member, b.Title, l.DueDate
FROM Loans l
JOIN Members m ON l.MemberID = m.MemberID
JOIN Books b ON l.BookID = b.BookID
WHERE l.ReturnDate IS NULL AND l.DueDate < CURRENT_DATE;

-- Query: Count books per category
SELECT c.CategoryName, COUNT(b.BookID) AS TotalBooks
FROM Categories c
JOIN Books b ON c.CategoryID = b.CategoryID
GROUP BY c.CategoryName;

-- Query: Find members with more than 1 active loan
SELECT m.Name, COUNT(l.LoanID) AS ActiveLoans
FROM Members m
JOIN Loans l ON m.MemberID = l.MemberID
WHERE l.ReturnDate IS NULL
GROUP BY m.Name
HAVING COUNT(l.LoanID) > 1;

-- Query: List all authors with the number of books
SELECT a.Name AS Author, COUNT(b.BookID) AS TotalBooks
FROM Authors a
LEFT JOIN Books b ON a.AuthorID = b.AuthorID
GROUP BY a.Name;
