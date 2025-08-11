-- bookstore_setup.sql
CREATE DATABASE IF NOT EXISTS Bookstore;
USE Bookstore;

CREATE TABLE IF NOT EXISTS Books (
    BookID INT PRIMARY KEY AUTO_INCREMENT,
    Title VARCHAR(200) NOT NULL,
    Author VARCHAR(150),
    Genre VARCHAR(80),
    Price DECIMAL(8,2),
    Stock INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS IssuedBooks (
    IssueID INT PRIMARY KEY AUTO_INCREMENT,
    BookID INT NOT NULL,
    CustomerName VARCHAR(150) NOT NULL,
    IssueDate DATE NOT NULL,
    ReturnDate DATE DEFAULT NULL,
    FOREIGN KEY (BookID) REFERENCES Books(BookID)
);

-- sample data
INSERT INTO Books (Title, Author, Genre, Price, Stock) VALUES
('The Alchemist', 'Paulo Coelho', 'Fiction', 9.99, 5),
('Atomic Habits', 'James Clear', 'Self-help', 15.50, 3),
('Clean Code', 'Robert C. Martin', 'Programming', 29.99, 2);
