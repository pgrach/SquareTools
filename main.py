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
"memberID" INTEGER NOT NULL,               
"class" VARCHAR (10),
"item_name" VARCHAR (50),
"availability" VARCHAR (20),
"borrower_name" TEXT,
"borrower_flatID" INTEGER,
FOREIGN KEY (flatID) REFERENCES flats (flatID),
FOREIGN KEY (memberID) REFERENCES members (memberID)
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

  # Join items table with members table to get the fname for each item's owner
  cursor.execute("""
SELECT items.*, members.fname 
FROM items
JOIN members ON items.memberID = members.memberID
""")
  items = cursor.fetchall()
#   print(items) #checking if JOIN works and defining the order
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
        availability = "Available" # Set available by default whenever user adds it to the database.
        
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
            memberID = cursor.lastrowid  # Fetch the ID of the member you just added

        else:
            memberID = existing_member[1]  # Fetch the memberID of the existing member

        # Insert into items
        cursor.execute("INSERT INTO items (flatID, memberID, class, item_name, availability, borrower_name, borrower_flatID) VALUES (?, ?, ?, ?, ?, NULL, NULL)", (flat, memberID, classn, item, availability))

        conn.commit()
        conn.close()
        
        return redirect(url_for('home'))  # Redirect to the main page after adding

    return render_template("add_items.html")


@app.route('/delete', methods=['GET', 'POST'])
def delete():
    if request.method == 'POST':
        delete_type = request.form['delete_type']
        
        conn, cursor = get_db_connection()

        if delete_type == 'item':
            itemID = request.form['itemID']
            cursor.execute("DELETE FROM items WHERE itemID = ?", (itemID,))

        elif delete_type == 'member':
            memberID = request.form['memberID']
            cursor.execute("SELECT flatID FROM members WHERE memberID = ?", (memberID,))
            flatID = cursor.fetchone()
            cursor.execute("DELETE FROM items WHERE flatID = ?", (flatID[0],))
            cursor.execute("DELETE FROM members WHERE memberID = ?", (memberID,))

        conn.commit()
        conn.close()

        return redirect(url_for('home'))
    
    return render_template('delete.html')

@app.route('/update_item', methods=['POST'])
def update_item():
    itemID = request.form['itemID']
    availability = request.form['availability']
    borrower_name = request.form.get('borrower_name')
    borrower_flatID = request.form.get('borrower_flatID')

    conn, cursor = get_db_connection()

    # Only check for member existence if the item is being borrowed
    if availability == 'Borrowed' and borrower_name and borrower_flatID:
        cursor.execute("SELECT * FROM members WHERE flatID = ? AND fname = ?", (borrower_flatID, borrower_name))
        existing_member = cursor.fetchone()

        # If the member doesn't exist, add them
        if not existing_member:
            cursor.execute("INSERT INTO members (flatID, fname) VALUES (?, ?)", (borrower_flatID, borrower_name))

    # Update the item's availability and borrower details (if provided)
    cursor.execute("UPDATE items SET availability = ?, borrower_name = ?, borrower_flatID = ? WHERE itemID = ?",
                   (availability, borrower_name, borrower_flatID, itemID))

    conn.commit()
    conn.close()

    return redirect(url_for('view_items'))  # Redirect back to items.html page

if __name__ == '__main__':
    app.run(debug=True)