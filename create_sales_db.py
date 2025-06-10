import sqlite3
from pathlib import Path

# Create a connection to the database
db_path = Path(__file__).parent / "sales.db"
connection = sqlite3.connect(db_path)
cursor = connection.cursor()

# Create the CUSTOMER table with new columns
cursor.execute('''
CREATE TABLE IF NOT EXISTS CUSTOMER (
    CUSTOMER_ID INTEGER PRIMARY KEY,
    NAME VARCHAR(50),
    AGE INTEGER,
    GENDER VARCHAR(10),
    ADDRESS VARCHAR(100),
    CUSTOMER_TYPE VARCHAR(10) CHECK(CUSTOMER_TYPE IN ('partner', 'customer')),
    PARENT_ID INTEGER,
    CUSTOMER_STATUS VARCHAR(10) CHECK(CUSTOMER_STATUS IN ('active', 'inactive')),
    FOREIGN KEY (PARENT_ID) REFERENCES CUSTOMER(CUSTOMER_ID)
)
''')

# Create the INVOICE table (unchanged)
cursor.execute('''
CREATE TABLE IF NOT EXISTS INVOICE (
    INVOICE_ID INTEGER PRIMARY KEY,
    CUSTOMER_ID INTEGER,
    INVOICE_DATE DATE,
    TOTAL_AMOUNT DECIMAL(10, 2),
    PAYMENT_STATUS VARCHAR(20),
    FOREIGN KEY (CUSTOMER_ID) REFERENCES CUSTOMER(CUSTOMER_ID)
)
''')

# Insert sample data into CUSTOMER table with new columns
customers = [
    (1, 'Mary', 35, 'Female', '123 Main St, Georgia, USA', 'partner', None, 'active'),
    (2, 'Jane', 28, 'Female', '456 Oak Ave, Louisiana, USA', 'customer', 1, 'active'),
    (3, 'Bob', 45, 'Male', '789 Pine Rd, North Carolina, USA', 'customer', 1, 'active'),
    (4, 'Alice', 32, 'Female', '101 Elm St, Washington, USA', 'partner', None, 'active'),
    (5, 'Charlie', 50, 'Male', '202 Maple Dr, Kentucky, USA', 'customer', 4, 'inactive')
]

cursor.executemany('INSERT OR REPLACE INTO CUSTOMER VALUES (?, ?, ?, ?, ?, ?, ?, ?)', customers)

# Insert sample data into INVOICE table (unchanged)
invoices = [
    (1, 1, '2023-01-15', 150.00, 'Paid'),
    (2, 2, '2023-02-20', 200.50, 'Pending'),
    (3, 1, '2023-03-10', 75.25, 'Paid'),
    (4, 3, '2023-04-05', 300.00, 'Paid'),
    (5, 4, '2023-05-12', 180.75, 'Pending'),
    (6, 5, '2023-06-18', 250.00, 'Paid'),
    (7, 2, '2023-07-22', 120.50, 'Paid'),
    (8, 3, '2023-08-30', 90.00, 'Pending')
]

cursor.executemany('INSERT OR REPLACE INTO INVOICE VALUES (?, ?, ?, ?, ?)', invoices)

# Commit the changes and close the connection
connection.commit()
connection.close()

print("Sales database created successfully with sample data.")