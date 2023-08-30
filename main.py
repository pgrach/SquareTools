from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import os
from PIL import Image

# created an instance of the Flask application 
app = Flask(__name__)
app.secret_key = 'RS1234SecretKey'

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

# Create a table named "feedback" with columns
cursor.execute("""
CREATE TABLE IF NOT EXISTS "feedback" (
"ID" INTEGER PRIMARY KEY AUTOINCREMENT,
"title" VARCHAR (50),
"message" VARCHAR (500),
"flatID" INTEGER NOT NULL,
"fname" TEXT NOT NULL,
FOREIGN KEY (flatID) REFERENCES members (flatID),
FOREIGN KEY (fname) REFERENCES members (fname)
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

    # allow for combinations of filters. building the SQL query and values
    query = """
        SELECT items.*, members.fname 
        FROM items
        JOIN members ON items.memberID = members.memberID
        WHERE 1=1
    """
    values = []

    # Check item_filter and flatID_filter values
    item_filter = request.args.get('item_filter')
    flatID_filter = request.args.get('flatID_filter')

    if item_filter == 'borrower' and flatID_filter:
        query += " AND items.borrower_flatID = ?"
        values.append(flatID_filter)

    elif item_filter == 'owner' and flatID_filter:
        query += " AND items.flatID = ?"
        values.append(flatID_filter)

    # filters to the query based on provided parameters
    if request.args.get('flatID'):
        query += " AND items.flatID = ?"
        values.append(request.args.get('flatID'))

    if request.args.get('availability'):
        query += " AND items.availability = ?"
        values.append(request.args.get('availability'))

    if request.args.get('borrowed_by_flatID'):
        query += " AND items.borrower_flatID = ?"
        values.append(request.args.get('borrowed_by_flatID'))

    if request.args.get('class'):
        query += " AND items.class = ?"
        values.append(request.args.get('class'))

    # Add ordering to the query
    query += " ORDER BY CASE WHEN items.availability = 'Available' THEN 1 ELSE 2 END, items.item_name"
    
    cursor.execute(query, tuple(values))
    items = cursor.fetchall()
    
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

# Define a function to resize an image
def resize_image(image, base_width=300):
    """Resize an image preserving its aspect ratio.
    
    Args:
        image (PIL.Image): Image to be resized.
        base_width (int): The base width to resize to. 
                          The height will be adjusted to maintain the aspect ratio.

    Returns:
        PIL.Image: Resized image.
    """
    w_percent = base_width / float(image.size[0])
    h_size = int(float(image.size[1]) * float(w_percent))
    return image.resize((base_width, h_size))

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
            flash(f'Welcome to the community, {fname}!')  # Flash the welcome message here

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
                
                # Load the image using Pillow
                image = Image.open(file)

                # Resize the image
                image_resized = resize_image(image)

                # Save the resized image
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                image_resized.save(file_path)

                # Update the items table with the image filename
                cursor.execute("UPDATE items SET image_filename = ? WHERE itemID = ?", (new_filename, itemID))

        conn.commit()
        conn.close()

        return redirect(url_for('view_items'))  # Redirect to the main page after adding
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
    borrower_name = request.form["borrower_name"] # this is for welcome slash message

    conn, cursor = get_db_connection()

    # Only check for member existence if the item is being borrowed
    if availability == 'Borrowed' and borrower_name and borrower_flatID:
        cursor.execute("SELECT * FROM members WHERE flatID = ? AND fname = ?", (borrower_flatID, borrower_name))
        existing_member = cursor.fetchone()

        # If the member doesn't exist, add them
        if not existing_member:
            cursor.execute("INSERT INTO members (flatID, fname) VALUES (?, ?)", (borrower_flatID, borrower_name))
            flash(f'Welcome to the community, {borrower_name}!')  # Flash the welcome message here

    # Update the item's availability and borrower details (if provided)
    cursor.execute("UPDATE items SET availability = ?, borrower_name = ?, borrower_flatID = ? WHERE itemID = ?",
                   (availability, borrower_name, borrower_flatID, itemID))

    conn.commit()
    conn.close()

    return redirect(url_for('view_items'))  # Redirect back to items.html page


# # Define a Function to retrieve all feedback entries
# def get_all_feedback():
#     conn, cursor = get_db_connection()
#     cursor.execute("SELECT * FROM feedback ORDER BY ID DESC")
#     feedback = cursor.fetchall()
#     conn.close()
#     print(feedback)  # Add this line
#     return feedback


# Define a Function to delete feedback by ID
def delete_feedback_by_id(feedback_id):
    conn, cursor = get_db_connection()
    cursor.execute("DELETE FROM feedback WHERE ID = ?", (feedback_id,))
    conn.commit()
    conn.close()

# Flask View Function to handle the Q&A forum
@app.route('/forum', methods=["GET", "POST"])
def forum():
    conn, cursor = get_db_connection()

    if request.method == "POST":
        title = request.form["title"]
        message = request.form["message"]
        name = request.form["name"]
        flat_number = request.form["flat_number"]

        # Check if the flat already exists, if not insert
        cursor.execute("SELECT * FROM flats WHERE flatID = ?", (flat_number,))
        existing_flat = cursor.fetchone()
        if not existing_flat:
            cursor.execute("INSERT INTO flats (flatID) VALUES (?)", (flat_number,))

        # Check if a member with the same name exists in the same flat
        cursor.execute("SELECT * FROM members WHERE flatID = ? AND fname = ?", (flat_number, name))
        existing_member = cursor.fetchone()

        # If the member doesn't exist, add them
        if not existing_member:
            cursor.execute("INSERT INTO members (flatID, fname) VALUES (?, ?)", (flat_number, name))
            flash(f'Welcome to the community, {name}!')  # Flash the welcome message here

        # Add feedback to the database
        cursor.execute("INSERT INTO feedback (title, message, flatID, fname) VALUES (?, ?, ?, ?)", (title, message, flat_number, name))
        conn.commit()

        flash("Your feedback has been submitted!")
        return redirect(url_for('forum'))

    cursor.execute("SELECT * FROM feedback ORDER BY ID DESC")
    feedback_list = cursor.fetchall()
    conn.close()

    return render_template('forum.html', feedback_list=feedback_list)

# Flask View Function for Admin to delete specific feedback
@app.route('/delete_feedback/<int:feedback_id>')
def delete_feedback(feedback_id):
    secret_key = request.args.get('secret_key')
    if secret_key != SECRET_KEY_VALUE:
        flash("You are not authorized to perform this action!")
        return redirect(url_for('forum'))
    delete_feedback_by_id(feedback_id)
    flash("Feedback has been deleted.")
    return redirect(url_for('forum'))


if __name__ == '__main__':
    app.run(debug=True)