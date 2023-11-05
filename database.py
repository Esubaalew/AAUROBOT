# database.py
"""This module is made to provide easy functions for my @AAU_Robot.
This module provides function for creating, deleting table, inserting data
deleting and from the table."""

import sqlite3
from datetime import date

def create_table() -> None:
    """Creates a table; this is usually performed once."""

    try:
        with sqlite3.connect('student.sql') as database:
            cursor = database.cursor()
            create = """
                CREATE TABLE IF NOT EXISTS Student (
                    TGID TEXT PRIMARY KEY NOT NULL,
                    IDNO TEXT NOT NULL,
                    USERNAME TEXT NOT NULL,
                    CAMPUS TEXT NOT NULL,
                    JOINDATE DATE NOT NULL
                )
            """
            cursor.execute(create)

    except sqlite3.Error as error:
        print(error)

def insert_data(values: tuple) -> None:
    """Inserts user information into the database."""

    try:
        with sqlite3.connect('student.sql') as database:
            cursor = database.cursor()
            insertdata = """
                INSERT INTO Student (TGID, IDNO, USERNAME, CAMPUS, JOINDATE)
                VALUES (?, ?, ?, ?, ?)
            """
            cursor.execute(insertdata, values)
            database.commit()
    except sqlite3.Error as error:
        print(error)

def registered_count() -> int:
    """Function that gets the number of tuples in the table."""

    with sqlite3.connect('student.sql') as database:
        cursor = database.cursor()
        select_all = """SELECT TGID FROM Student"""
        cursor.execute(select_all)
        table = cursor.fetchall()
        return len(table)

def registered_today() -> int:
    """Function that gets the number of tuples with today's date in the table."""

    today = date.today().strftime("%d/%m/%Y")

    with sqlite3.connect('student.sql') as database:
        cursor = database.cursor()
        select = """SELECT * FROM Student WHERE JOINDATE = ?"""
        cursor.execute(select, (today,))
        table = cursor.fetchall()
        return len(table)

def search_table_by_tg_id(tg_id) -> tuple:
    """Search for a record based on TGID and return one record if found."""
    try:
        with sqlite3.connect('student.sql') as database:
            cursor = database.cursor()
            search = """SELECT * FROM Student WHERE TGID = ?"""
            cursor.execute(search, (tg_id,))
            row = cursor.fetchone()
            return row
    except sqlite3.Error as e:
        print(e)

def delete_table_data():
    """Delete all records in the Student table."""
    try:
        with sqlite3.connect('student.sql') as database:
            cursor = database.cursor()
            delete = """DELETE FROM Student"""
            cursor.execute(delete)
            database.commit()
    except sqlite3.Error as error:
        print(error)


def delete_from_table(key):
    """Delete a specific user from the table based on TGID."""
    try:
        with sqlite3.connect('student.sql') as database:
            cursor = database.cursor()
            delete_row = """DELETE FROM Student WHERE TGID=?"""
            cursor.execute(delete_row, (key,))
    except sqlite3.Error as e:
        print(e)