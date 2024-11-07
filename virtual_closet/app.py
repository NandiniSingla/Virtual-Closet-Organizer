import os
import sqlite3
import random
from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Ensure the upload folder is set correctly
UPLOAD_FOLDER = os.path.join('static', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Database initialization
def init_db():
    conn = sqlite3.connect('clothes.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clothes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_type TEXT NOT NULL,
            image_path TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route("/", methods=["GET", "POST"])
def index():
    conn = sqlite3.connect('clothes.db')
    cursor = conn.cursor()

    if request.method == "POST":
        # Check if files and item_type are in the form
        files = request.files.getlist('file')  # Get multiple files
        item_type = request.form.get('category')  # Get selected item type

        # Validate item_type
        if not item_type:
            return "No item type selected"

        # Loop through each file and save it
        for file in files:
            if file.filename == '':
                return "No selected file"

            # Save the file
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Insert the item into the database
            cursor.execute("INSERT INTO clothes (item_type, image_path) VALUES (?, ?)", (item_type, filepath))
        
        conn.commit()
        return redirect(url_for("index"))

    # Fetch all items from the database
    cursor.execute("SELECT * FROM clothes")
    clothes = cursor.fetchall()

    # Separate items by type
    tops = [(item[0], item[2]) for item in clothes if item[1] == 'Top']  # (id, image_path)
    bottoms = [(item[0], item[2]) for item in clothes if item[1] == 'Bottom']
    shoes = [(item[0], item[2]) for item in clothes if item[1] == 'Shoes']

    # Suggest an outfit (randomly select one from each type)
    suggested_outfit = []
    if tops:
        suggested_outfit.append(random.choice(tops)[1])
    if bottoms:
        suggested_outfit.append(random.choice(bottoms)[1])
    if shoes:
        suggested_outfit.append(random.choice(shoes)[1])

    conn.close()

    return render_template("index.html", tops=tops, bottoms=bottoms, shoes=shoes, suggested_outfit=suggested_outfit)

@app.route("/delete/<int:item_id>", methods=["POST"])
def delete_item(item_id):
    conn = sqlite3.connect('clothes.db')
    cursor = conn.cursor()

    # Fetch the image path of the item to delete it from filesystem
    cursor.execute("SELECT image_path FROM clothes WHERE id = ?", (item_id,))
    image = cursor.fetchone()

    if image:
        image_path = image[0]

        # Delete the file from filesystem
        if os.path.exists(image_path):
            os.remove(image_path)

        # Delete the record from the database
        cursor.execute("DELETE FROM clothes WHERE id = ?", (item_id,))
        conn.commit()

    conn.close()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
