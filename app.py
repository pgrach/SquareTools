rom flask import Flask, render_template, request, redirect, url_for
app = Flask(__name__)

import sqlite3 as sql

# Define a Function to establish a new connection to the database
def get_db_connection():
    dbCon = sql.connect("square_share.db") #connection object
    dbCursor = dbCon.cursor() #cursor object
    return dbCon, dbCursor

# Ensure the table exists before starting the app
conn, cursor = get_db_connection()

# Create the flats table
cursor.execute("""
CREATE TABLE IF NOT EXISTS "flats" (
"flatID" INTEGER PRIMARY KEY AUTOINCREMENT,
"fname" TEXT NOT NULL
)""")

# Create the items table
cursor.execute("""
CREATE TABLE IF NOT EXISTS "items" (
"itemID" INTEGER PRIMARY KEY AUTOINCREMENT, 
"flatID" INTEGER NOT NULL,
"class" VARCHAR (10),
"item_name" VARCHAR (50),
"availability" VARCHAR (20), 
FOREIGN KEY (flatID) REFERENCES flats (flatID)               
)""")

# Create the items table
conn.commit()
conn.close()

