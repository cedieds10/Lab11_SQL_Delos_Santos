# Exercise 3

import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

# Config initialization
app = Flask(__name__)
app.secret_key = "secret_key_for_flask_messages"
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Limit files to 2MB maximum
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Mock user session variable for Exercise 3 requirements
CURRENT_USER_ID = 1


# ==========================================
# DATABASE INITIALIZATION
# ==========================================

def init_profile_db():
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_profiles (
        user_id INTEGER PRIMARY KEY,
        display_name TEXT NOT NULL,
        image_filename TEXT DEFAULT 'default.png'
    );
    """)
    # Seed current user profile if empty
    cursor.execute("SELECT COUNT(*) FROM user_profiles WHERE user_id = ?", (CURRENT_USER_ID,))
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO user_profiles (user_id, display_name, image_filename) 
        VALUES (?, ?, ?)
        """, (CURRENT_USER_ID, "Juan Dela Cruz", "default.png"))
        conn.commit()
    conn.close()


def get_db_connection():
    conn = sqlite3.connect("app.db")
    conn.row_factory = sqlite3.Row
    return conn


# ==========================================
# VALIDATION HELPER FUNCTIONS
# ==========================================

def allowed_file(filename, file_stream):
    """Performs both filename and MIME type checks."""
    ext_valid = '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    # Check MIME type
    file_stream.seek(0)
    mime_type = file_stream.content_type
    mime_valid = mime_type in ["image/png", "image/jpeg"]
    
    return ext_valid and mime_valid


# ==========================================
# ROUTES
# ==========================================

@app.route("/", methods=["GET", "POST"])
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        display_name = request.form.get("display_name", "").strip()
        file = request.files.get("profile_picture")

        if not display_name:
            flash("Display name cannot be empty.", "error")
            return redirect(url_for("dashboard"))

        # Baseline update query
        update_query = "UPDATE user_profiles SET display_name = ? WHERE user_id = ?"
        params = [display_name, CURRENT_USER_ID]

        # File Upload validation logic
        if file and file.filename != '':
            if allowed_file(file.filename, file):
                # Sanitize using secure_filename
                filename = secure_filename(file.filename)
                
                # Append user ID to filename to make it uniquely identifiable
                base, ext = os.path.splitext(filename)
                unique_filename = f"user_{CURRENT_USER_ID}{ext}"
                
                file.seek(0)  # Reset pointer after MIME validation check
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                
                # Expand update parameters to include new image file
                update_query = "UPDATE user_profiles SET display_name = ?, image_filename = ? WHERE user_id = ?"
                params = [display_name, unique_filename, CURRENT_USER_ID]
            else:
                flash("Invalid file type or format. Only .jpg, .png, and .jpeg are allowed.", "error")
                return redirect(url_for("dashboard"))

        # Commit changes securely using parameterized queries
        cursor.execute(update_query, params)
        conn.commit()
        flash("Profile successfully updated!", "success")
        return redirect(url_for("dashboard"))

    # Fetch existing profile values
    cursor.execute("SELECT display_name, image_filename FROM user_profiles WHERE user_id = ?", (CURRENT_USER_ID,))
    user_profile = cursor.fetchone()
    conn.close()

    return render_template("dashboard.html", user=user_profile)


if __name__ == "__main__":
    init_profile_db()
    app.run(debug=True, use_reloader=False)