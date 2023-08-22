from flask import Flask, render_template, request, redirect, url_for

# created an instance of the Flask application 
app = Flask(__name__)

import sqlite3 as sql

# Define a Function to establish a new connection to the database
def get_db_connection():
    dbCon = sql.connect("square_share.db") #connection object
    dbCursor = dbCon.cursor() #cursor object
    return dbCon, dbCursor

# establish a connection and get the cursor object for executing SQL statements
conn, cursor = get_db_connection()

# Create the flats table
cursor.execute("""
CREATE TABLE IF NOT EXISTS "flats" (
"flatID" INTEGER PRIMARY KEY AUTOINCREMENT
)""")

# Create the Members Table that will store the names of members (or tenants) of a flat
cursor.execute("""
CREATE TABLE IF NOT EXISTS "members" (
"flatID" INTEGER NOT NULL,
"memberID" INTEGER PRIMARY KEY AUTOINCREMENT,
"fname" TEXT NOT NULL,
FOREIGN KEY (flatID) REFERENCES flats (flatID),
UNIQUE(flatID, fname)
)""")

# Create the items table that will store items associated with a flat
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

# CRUD:
# Add Items
# Delete Items
# Update Items
# View All Items

#Define Flask routes

# Home Page
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/members")
def view_members():
  conn, cursor = get_db_connection()
  cursor.execute("SELECT * FROM members")
  members = cursor.fetchall()
  conn.close()
  return render_template("members.html", members=members)

@app.route("/items")
def view_items():
  conn, cursor = get_db_connection()
  cursor.execute("SELECT * FROM items")
  items = cursor.fetchall()
  conn.close()
  return render_template("items.html", items=items)

# add a new item to the db
@app.route("/add_items", methods=["GET", "POST"])
def add_items():
    if request.method == "POST":
        flat = request.form["flatID"]
        fname = request.form["fname"]
        classn = request.form["class"]
        item = request.form["item_name"]
        availability = request.form["availability"]
        
        conn, cursor = get_db_connection()

        # Check if the flat already exists, if not insert
        cursor.execute("SELECT * FROM flats WHERE flatID = ?", (flat,))
        existing_flat = cursor.fetchone()
        if not existing_flat:
            cursor.execute("INSERT INTO flats (flatID) VALUES (?)", (flat,))

        # Check if a member with the same name exists in the same flat
        cursor.execute("SELECT * FROM members WHERE flatID = ? AND fname = ?", (flat, fname))
        existing_member = cursor.fetchone()

        # If the member doesn't exist, add them
        if not existing_member:
            cursor.execute("INSERT INTO members (flatID, fname) VALUES (?, ?)", (flat, fname))

        # Insert into items
        cursor.execute("INSERT INTO items (flatID, class, item_name, availability) VALUES (?, ?, ?, ?)", (flat, classn, item, availability))

        conn.commit()
        conn.close()
        
        return redirect(url_for('home'))  # Redirect to the main page after adding

    return render_template("add_items.html")

if __name__ == '__main__':
    app.run(debug=True)