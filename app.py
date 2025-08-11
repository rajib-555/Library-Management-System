# app.py
import streamlit as st
import mysql.connector
import pandas as pd
from datetime import date

# ---------- DB CONFIG ----------
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "root"   # <-- replace
DB_NAME = "Bookstore"
# --------------------------------

def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

def load_data(query, params=None):
    conn = get_connection()
    try:
        df = pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()
    return df

def run_modify(query, params=None):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()
        last_id = cursor.lastrowid
        cursor.close()
        return last_id
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()

def issue_book_tx(book_id, customer_name, issue_dt):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # start transaction implicitly
        cursor.execute("SELECT Stock FROM Books WHERE BookID = %s FOR UPDATE", (book_id,))
        row = cursor.fetchone()
        if not row or row[0] <= 0:
            conn.rollback()
            return False, "Book out of stock"
        cursor.execute(
            "INSERT INTO IssuedBooks (BookID, CustomerName, IssueDate, ReturnDate) VALUES (%s, %s, %s, NULL)",
            (book_id, customer_name, issue_dt)
        )
        cursor.execute("UPDATE Books SET Stock = Stock - 1 WHERE BookID = %s", (book_id,))
        conn.commit()
        cursor.close()
        return True, "Book issued"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def return_book_tx(issue_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT BookID, ReturnDate FROM IssuedBooks WHERE IssueID = %s", (issue_id,))
        row = cursor.fetchone()
        if not row:
            return False, "Issue record not found"
        book_id, return_date = row
        if return_date is not None:
            return False, "Already returned"
        today = date.today().isoformat()
        cursor.execute("UPDATE IssuedBooks SET ReturnDate = %s WHERE IssueID = %s", (today, issue_id))
        cursor.execute("UPDATE Books SET Stock = Stock + 1 WHERE BookID = %s", (book_id,))
        conn.commit()
        cursor.close()
        return True, "Book returned"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

# Streamlit UI
st.title("📚 MySQL Bookstore Management")

menu = ["Add Book", "Available Books", "Issue a Book", "Issued Books", "All Books"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Add Book":
    st.header("Add New Book")
    with st.form("add_book"):
        title = st.text_input("Title")
        author = st.text_input("Author")
        genre = st.text_input("Genre")
        price = st.number_input("Price", min_value=0.0, step=0.01)
        stock = st.number_input("Stock", min_value=0, step=1)
        submit = st.form_submit_button("Add Book")
        if submit:
            if not title:
                st.error("Title is required")
            else:
                run_modify(
                    "INSERT INTO Books (Title, Author, Genre, Price, Stock) VALUES (%s, %s, %s, %s, %s)",
                    (title, author, genre, price, int(stock))
                )
                st.success(f"Book '{title}' added.")

elif choice == "Available Books":
    st.header("Available Books (Stock > 0)")
    df = load_data("SELECT BookID, Title, Author, Genre, Price, Stock FROM Books WHERE Stock > 0")
    st.dataframe(df)

elif choice == "Issue a Book":
    st.header("Issue a Book")
    books = load_data("SELECT BookID, Title, Stock FROM Books WHERE Stock > 0")
    if books.empty:
        st.info("No books available to issue.")
    else:
        book_options = {f"{row['Title']} (stock: {row['Stock']})": int(row['BookID']) for _, row in books.iterrows()}
        selected = st.selectbox("Select Book", list(book_options.keys()))
        customer = st.text_input("Customer name")
        issue_dt = st.date_input("Issue date", value=date.today())
        if st.button("Issue"):
            if not customer.strip():
                st.error("Enter customer name")
            else:
                success, msg = issue_book_tx(book_options[selected], customer.strip(), issue_dt.isoformat())
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

elif choice == "Issued Books":
    st.header("Issued Books")
    df = load_data("""
        SELECT ib.IssueID, b.Title, ib.CustomerName, ib.IssueDate, ib.ReturnDate
        FROM IssuedBooks ib
        JOIN Books b ON ib.BookID = b.BookID
        ORDER BY ib.IssueDate DESC
    """)
    if df.empty:
        st.info("No issued records.")
    else:
        # Show table and add return buttons per row
        for _, row in df.iterrows():
            st.write(f"**{row['Title']}** — {row['CustomerName']} — Issued: {row['IssueDate']} — Returned: {row['ReturnDate']}")
            if pd.isna(row['ReturnDate']):
                if st.button("Return Book", key=f"ret_{int(row['IssueID'])}"):
                    ok, msg = return_book_tx(int(row['IssueID']))
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

elif choice == "All Books":
    st.header("All Books")
    df = load_data("SELECT * FROM Books")
    st.dataframe(df)
