# Run this once to create a test HR database
import sqlite3
conn = sqlite3.connect("test_hr.db")
cursor = conn.cursor()
cursor.executescript("""
    CREATE TABLE employees (
        emp_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        department TEXT,
        salary REAL,
        hire_date DATE
    );
    CREATE TABLE departments (
        dept_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        budget REAL
    );
    INSERT INTO employees VALUES
        (1,'Alice','Engineering',95000,'2020-01-15'),
        (2,'Bob','Marketing',72000,'2019-03-22'),
        (3,'Carol','Engineering',105000,'2018-07-01'),
        (4,'Dave','HR',65000,'2021-09-10'),
        (5,'Eve','Engineering',88000,'2022-02-28');
    INSERT INTO departments VALUES
        (1,'Engineering',500000),
        (2,'Marketing',200000),
        (3,'HR',150000);
""")
conn.commit()
conn.close()
print("test_hr.db created")