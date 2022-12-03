# database.py
"""This module is made to provide easy functions for my @AAU_Robot.
This module provides function for creating, deleting table, inserting data into the table and
deleting data from the table."""

import sqlite3


def createTable() -> None:
    '''Creates a table this is usualy performed once.'''

    try:
        database = sqlite3.connect('student.sql')
        cursor = database.cursor()
        create = """CREATE TABLE Student
        (
        TGID TEXT PRIMARY KEY NOT NULL,
        IDNO TEXT NOT NULL ,
        USERNAME TEXT NOT NULL , 
        CAMPUS TEXT NOT NULL,
        JOINDATE DATE NOT NULL
        )"""
        cursor.execute(create)
        cursor.close()
        database.commit()
    except sqlite3.Error as error:
        print(error)


def InsertData(values: tuple) -> list:
    '''INSERTES User information '''
    try:
        database = sqlite3.connect('student.sql')
        cursor = database.cursor()
        insertdata = """INSERT INTO Student
    (
    TGID,
    IDNO,
    USERNAME,
    CAMPUS,
    JOINDATE) 
    VALUES(
        ?, 
        ?, 
        ?, 
        ?, 
        ?
        )"""
        cursor.execute(insertdata, values)
        recordrow = cursor.fetchall()
        cursor.close()
        database.commit()
        return recordrow
    except sqlite3.Error as error:
        print(error)


def registedcount() -> int:
    """Function that gets the number of  tuples
    in the table """

    databse = sqlite3.connect('student.sql')
    cursor = databse.cursor()
    select_all = """SELECT TGID from Student"""
    cursor.execute(select_all)
    table = cursor.fetchall()
    return len(table)


def registedtoday() -> int:
    """Function that gets the number of  tuples
    in the table """
    databse = sqlite3.connect('student.sql')
    cursor = databse.cursor()
    select = """SELECT * from Student WHERE JOINDATE=?"""
    from datetime import date
    today = date.today()
    today = today.strftime("%d/%m/%Y")
    cursor.execute(select, (today,))
    table = cursor.fetchall()
    return len(table)


def searchTable(id) -> tuple:
    """Searchs a record based on USERID this only returns one record"""
    try:
        database = sqlite3.connect('student.sql')
        cursor = database.cursor()
        search = """SELECT * FROM Student WHERE ID=?"""
        cursor.execute(search, (id,))
        result = cursor.fetchall()
        # for data in result:
        userprofile = (result[0][0], result[0][1], result[0][2], result[0][3])
        cursor.close()
        return userprofile
    except sqlite3.Error as e:
        print(e)


def searchTable2(tg_id) -> tuple:
    """Searchs a record based on MAGICID this only returns one record"""
    try:
        database = sqlite3.connect('student.sql')
        cursor = database.cursor()
        search = """SELECT * FROM Student WHERE TGID=?"""
        cursor.execute(search, (tg_id,))
        table = cursor.fetchall()
        rows = ()
        for row in table:
            rows += row

        return rows
    except sqlite3.Error as e:
        print(e)


def deleteTableData():
    try:
        database = sqlite3.connect('student.sql')
        cursor = database.cursor()
        delete = """delete from Student"""
        cursor.execute(delete)
        database.commit()
        cursor.close()
    except sqlite3.Error as error:
        print(error)


def readTable(idkey: int) -> bool:
    try:
        database = sqlite3.connect('student.sql')
        cursor = database.cursor()
        select_all = """SELECT TGID from Student"""
        cursor.execute(select_all)
        table = cursor.fetchall()
        #print("Total rows are:  ", len(table))
        rows = ()
        registered = False
        for row in table:
            rows += row

        if str(idkey) in rows:
            registered = True
        cursor.close()
        database.commit()

        return registered

    except sqlite3.Error as error:
        print(error)
    finally:
        if database:
            database.close()
            #print("connection is closed")


def deleteFromTable(key) -> None:
    '''Deletes  a specific user from  the table'''
    try:
        database = sqlite3.connect('student.sql')
        cursor = database.cursor()
        deleteRow = """DELETE FROM Student WHERE TGID=?"""
        cursor.execute(deleteRow, (key,))
        cursor.close()
        database.commit()
    except sqlite3.Error as e:
        print(e)
