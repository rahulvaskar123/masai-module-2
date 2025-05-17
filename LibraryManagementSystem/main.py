# Project 2: Library Management System

import csv
import bcrypt
from datetime import datetime, timedelta
import argparse
import os

# ------------------- models.py -------------------
from dataclasses import dataclass

@dataclass
class Book:
    ISBN: str
    Title: str
    Author: str
    CopiesTotal: int
    CopiesAvailable: int

@dataclass
class Member:
    MemberID: str
    Name: str
    PasswordHash: str
    Email: str
    JoinDate: str

@dataclass
class Loan:
    LoanID: str
    MemberID: str
    ISBN: str
    IssueDate: str
    DueDate: str
    ReturnDate: str

# ------------------- storage.py -------------------
class CSVStorage:
    def __init__(self, data_dir):
        self.data_dir = data_dir

    def read_csv(self, filename):
        path = os.path.join(self.data_dir, filename)
        with open(path, newline='') as f:
            return list(csv.DictReader(f))

    def write_csv(self, filename, fieldnames, rows):
        path = os.path.join(self.data_dir, filename)
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

# ------------------- auth.py -------------------
def hash_password(password):
    return password  # No hashing for now

def verify_password(password, hashed):
    return password == hashed  # Plain text check

def register_member(storage, member_id, name, password, email):
    members = storage.read_csv('members.csv')
    if any(m['MemberID'] == member_id for m in members):
        raise Exception("Duplicate Member ID")
    hashed = hash_password(password)
    join_date = datetime.today().strftime('%Y-%m-%d')
    members.append({"MemberID": member_id, "Name": name, "PasswordHash": hashed, "Email": email, "JoinDate": join_date})
    storage.write_csv('members.csv', members[0].keys(), members)

def login(storage, member_id, password):
    members = storage.read_csv('members.csv')
    for m in members:
        if m['MemberID'] == member_id and verify_password(password, m['PasswordHash']):
            return m
    return None

# ------------------- librarian_menu -------------------
def librarian_menu(storage, session):
    while True:
        print("\n=== Librarian Dashboard ===")
        print("1. Add Book")
        print("2. Register Member")
        print("3. Issue Book")
        print("4. Return Book")
        print("5. Overdue List")
        print("6. Logout")
        choice = input("> ")

        if choice == '1':
            isbn = input("ISBN: ")
            title = input("Title: ")
            author = input("Author: ")
            copies = int(input("Total Copies: "))
            books = storage.read_csv('books.csv')
            books.append({"ISBN": isbn, "Title": title, "Author": author, "CopiesTotal": copies, "CopiesAvailable": copies})
            storage.write_csv('books.csv', books[0].keys(), books)
            print("Book added.")

        elif choice == '2':
            member_id = input("Member ID: ")
            name = input("Name: ")
            password = input("Password: ")
            email = input("Email: ")
            register_member(storage, member_id, name, password, email)
            print("Member registered.")

        elif choice == '3':
            isbn = input("ISBN to issue: ")
            member_id = input("Member ID: ")
            issue_book(storage, member_id, isbn)

        elif choice == '4':
            isbn = input("ISBN to return: ")
            member_id = input("Member ID: ")
            return_book(storage, member_id, isbn)

        elif choice == '5':
            overdue_report(storage)

        elif choice == '6':
            break

# ------------------- member_menu -------------------
def member_menu(storage, session):
    user = session['user']
    while True:
        print("\n=== Member Dashboard ===")
        print("1. Search Catalogue")
        print("2. Borrow Book")
        print("3. My Loans")
        print("4. Logout")
        choice = input("> ")

        if choice == '1':
            keyword = input("Enter title/author keyword: ").lower()
            books = storage.read_csv('books.csv')
            results = [b for b in books if keyword in b['Title'].lower() or keyword in b['Author'].lower()]
            for b in results:
                print(b)

        elif choice == '2':
            isbn = input("ISBN to borrow: ")
            issue_book(storage, user['MemberID'], isbn)

        elif choice == '3':
            loans = storage.read_csv('loans.csv')
            my_loans = [l for l in loans if l['MemberID'] == user['MemberID']]
            for loan in my_loans:
                print(loan)

        elif choice == '4':
            break

# ------------------- utils for issue/return -------------------
def issue_book(storage, member_id, isbn):
    books = storage.read_csv('books.csv')
    loans = storage.read_csv('loans.csv')
    book = next((b for b in books if b['ISBN'] == isbn), None)
    if not book or int(book['CopiesAvailable']) <= 0:
        raise Exception("Book not available")
    book['CopiesAvailable'] = str(int(book['CopiesAvailable']) - 1)
    loan_id = str(len(loans) + 1)
    issue_date = datetime.today()
    due_date = issue_date + timedelta(days=14)
    loans.append({"LoanID": loan_id, "MemberID": member_id, "ISBN": isbn, "IssueDate": issue_date.strftime('%Y-%m-%d'), "DueDate": due_date.strftime('%Y-%m-%d'), "ReturnDate": ''})
    storage.write_csv('loans.csv', loans[0].keys(), loans)
    storage.write_csv('books.csv', books[0].keys(), books)
    print(f"\u2713 Book issued. Due on {due_date.strftime('%d-%b-%Y')}.")

def return_book(storage, member_id, isbn):
    loans = storage.read_csv('loans.csv')
    books = storage.read_csv('books.csv')
    for loan in loans:
        if loan['MemberID'] == member_id and loan['ISBN'] == isbn and loan['ReturnDate'] == '':
            loan['ReturnDate'] = datetime.today().strftime('%Y-%m-%d')
            for book in books:
                if book['ISBN'] == isbn:
                    book['CopiesAvailable'] = str(int(book['CopiesAvailable']) + 1)
            storage.write_csv('loans.csv', loans[0].keys(), loans)
            storage.write_csv('books.csv', books[0].keys(), books)
            print("\u2713 Book returned.")
            return
    print("Loan not found or already returned.")

# ------------------- overdue_report -------------------
def overdue_report(storage):
    loans = storage.read_csv('loans.csv')
    today = datetime.today().strftime('%Y-%m-%d')
    overdue = [l for l in loans if l['ReturnDate'] == '' and l['DueDate'] < today]
    for loan in overdue:
        print(f"LoanID: {loan['LoanID']}, MemberID: {loan['MemberID']}, ISBN: {loan['ISBN']}, DueDate: {loan['DueDate']}")

# ------------------- Entry Point -------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', default='.')
    args = parser.parse_args()
    storage = CSVStorage(args.data_dir)

    session = {}
    print("Login")
    member_id = input("Member ID: ")
    password = input("Password: ")
    user = login(storage, member_id, password)
    if user:
        session['user'] = user
        if user['MemberID'] == 'admin':
            librarian_menu(storage, session)
        else:
            member_menu(storage, session)
    else:
        print("Invalid credentials")

if __name__ == '__main__':
    main()
