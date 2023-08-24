from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os

# created an instance of the Flask application 
app = Flask(__name__)

import sqlite3 as sql

# Define the secret key value (functionality available for Admin only)
SECRET_KEY_VALUE = "MY_SECRET_123"  # Placeholder; user should replace with a unique value

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
"image_filename" TEXT,
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


# This is only available for Admin

@app.route("/members")
def view_members():
    secret_key = request.args.get('secret_key')
    if secret_key != SECRET_KEY_VALUE:
        return redirect(url_for("home"))

    conn, cursor = get_db_connection()
    cursor.execute("SELECT * FROM members")
    members = cursor.fetchall()
    conn.close()
    return render_template("members.html", members=members)

@app.route("/items")
def view_items():
  conn, cursor = get_db_connection()
  # Integrating different search possibilities 
  flatID = request.args.get('flatID') # Check if there's a flatID argument in the request
  availability = request.args.get('availability')
  borrowed_by_flatID = request.args.get('borrowed_by_flatID')
  class_filter = request.args.get('class')

  if flatID:
        # Fetch items only for the specified flatID
        # Join items table with members table to get the fname for item's owner
        cursor.execute("""
        SELECT items.*, members.fname 
        FROM items
        JOIN members ON items.memberID = members.memberID
        WHERE items.flatID = ?
        ORDER BY CASE WHEN items.availability = 'Available' THEN 1 ELSE 2 END, items.item_name
        """, (flatID,))

  elif availability:
        # Fetch items only for available
        # Join items table with members table to get the fname for item's owner
        cursor.execute("""
        SELECT items.*, members.fname 
        FROM items
        JOIN members ON items.memberID = members.memberID
        WHERE items.availability = ?
        """, (availability,))
        
  elif borrowed_by_flatID:
        # Fetch items only for the specified flatID
        # Join items table with members table to get the fname for item's owner
        cursor.execute("""
        SELECT items.*, members.fname 
        FROM items
        JOIN members ON items.memberID = members.memberID
        WHERE items.borrower_flatID = ?
        """, (borrowed_by_flatID,))

  elif class_filter:
        # Fetch items only for the specified flatID
        # Join items table with members table to get the fname for item's owner
        cursor.execute("""
        SELECT items.*, members.fname 
        FROM items
        JOIN members ON items.memberID = members.memberID
        WHERE items.class = ?
        ORDER BY CASE WHEN items.availability = 'Available' THEN 1 ELSE 2 END, items.item_name
        """, (class_filter,))
      
  else:
        # Fetch all items
      cursor.execute("""
        SELECT items.*, members.fname 
        FROM items
        JOIN members ON items.memberID = members.memberID
        ORDER BY CASE WHEN items.availability = 'Available' THEN 1 ELSE 2 END, items.item_name
        """)
  items = cursor.fetchall()
#   print(items) #checking if JOIN works and defining the order
  conn.close()
  return render_template("items.html", items=items)

# add a new item to the db

# Here we define where we save the items images:
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Check for allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

        # Get the itemID of the newly inserted item
        itemID = cursor.lastrowid

        # Check if the post request has the file part
        if 'item_image' in request.files:
            file = request.files['item_image']
            # If the user selects a file and it's an allowed type, save it.
            if file.filename != '' and allowed_file(file.filename):
                extension = file.filename.rsplit('.', 1)[1].lower()  # Get the file extension
                new_filename = f"{itemID}.{extension}"  # Rename file to itemID.extension
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                file.save(file_path)

                # Update the items table with the image filename
                cursor.execute("UPDATE items SET image_filename = ? WHERE itemID = ?", (new_filename, itemID))

        conn.commit()
        conn.close()

        return redirect(url_for('home'))  # Redirect to the main page after adding
    return render_template("add_items.html")  # Render the form when the request method is "GET"

@app.route('/delete', methods=['GET', 'POST'])
def delete():
    secret_key = request.args.get('secret_key')
    if secret_key != SECRET_KEY_VALUE:
        return redirect(url_for("home"))
    if request.method == 'POST':
        delete_type = request.form['delete_type']
        
        conn, cursor = get_db_connection()

        if delete_type == 'item':
            itemID = request.form['itemID']

            # Fetch the filename from the database
            cursor.execute("SELECT image_filename FROM items WHERE itemID = ?", (itemID,))
            result = cursor.fetchone()
            if result and result[0]:
                image_filename = result[0]
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))  # Delete the image from the file system

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