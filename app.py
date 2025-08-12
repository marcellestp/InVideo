"""
docstring here
"""
import sqlite3
import multiprocessing
import os
import time
from datetime import datetime
from flask import Flask, request, render_template, redirect, send_file, session
from invideo.tasks import *
# from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)
app.secret_key = 'your_super_secret_key_here'


# Specify a directory to store uploaded files.
UPLOAD_FOLDER = 'images/'
BASE_PATH = 'images/'
FILES_PATH = os.path.join(UPLOAD_FOLDER)
PATH_VIDEO_TEMP = "static/out_temp.mp4"
PATH_VIDEO = "static/output.mp4"

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
# Session(app)

database_file = "invideo.db"
connection = sqlite3.connect(database_file, check_same_thread=False)
db = connection.cursor()

@app.route("/login", methods=['GET', 'POST'])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        user_name = request.form.get("username").lower()

        db.execute(
        "SELECT * FROM users WHERE username = ? OR email = ?",
            (user_name, user_name)
        )
        rows = db.fetchall()
        print(rows)
        session['username'] = request.form.get('username')

        # Ensure username exist and password is correct
        for row in rows:
            if check_password_hash(
                rows[0][3], request.form.get("password")):
                # Remember which user has logged in
                user_id = rows[0][0]
                session['user_id'] = user_id
            else:
                return apology("invalid username and/or password", 400)

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "GET":
        return render_template("register.html")

    # User reached route via POST
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure email was submitted
        if not request.form.get("email"):
            return apology("must provide email", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure password are same
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("different passwords", 400)

        username = request.form.get("username").lower()
        email = request.form.get("email").lower()
        hash = request.form.get("password")

        # Query database for username
        db.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        )

        rows = db.fetchall()

        # Check if username already exist
        if len(rows) != 0:
            return apology("username already exist", 400)

        # Query insert into database for username
        db.execute(
            "INSERT INTO users (username, email, hash, date) VALUES (?, ?, ?, ?)", (username
                , email, generate_password_hash(hash), datetime.now())
        )

        connection.commit()
        login()

        # Redirect user to main page
        return redirect("/")


@app.route("/changepass", methods=["GET", "POST"])
# @login_required
def changepass():
    """Change password"""

    # User reached route via POST (as by submitting a form via POST)
    print("here")
    if request.method == "GET":

        return render_template("changepass.html")

    if request.method == "POST":
        # Ensure email was submitted
        if not request.form.get("email"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure password are same
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("different passwords", 400)

        email = request.form.get("email").lower()

        db.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
        )
        rows = db.fetchall()
        # print(rows)
        user_id = rows[0][0]

        # Ensure user exists and password is correct
        if rows:
            # Query update password into database for username
            db.execute(
                "UPDATE users SET hash = ? WHERE id = ?", (generate_password_hash(
                    request.form.get("password")), user_id)
            )
        else:
            return apology("user not exist", 400)

        # Redirect user to login
        return redirect("/")


@app.route('/download')
@login_required
def download_files():
    """
    It will download the video files in the user's Downloads directory.
    """
    PATH_VIDEO = STATIC + str(session['user_id']) + FINAL_FILENAME
    # print(PATH_VIDEO)
    try:
        return send_file(PATH_VIDEO, as_attachment=True)
    except FileNotFoundError:
        return "File not found!", 404


@app.route('/', methods=['GET', 'POST'])
# @login_required
def upload_process_download():
    """
    It will be responsible for identify which option the user
     is selecting on the system's main page.
    """
    if request.method == 'POST':
        # Check which button was clicked
        if request.form.get('upload'):
            # Call the upload function
            upload_files()
            # Created because the process button wasn't showing up after upload
            time.sleep(1)
            return redirect("/")
        if request.form.get('process'):
            # Call the process function
            print(f"session before processing call: {session['user_id']}")
            process = multiprocessing.Process(target=process_video, kwargs={"user_id": session['user_id']})
            process.start() # Begin the process execution
            process.join()  # Wait for the process to finish
            # print(f"fim do process: {session['user_id']}")
            return redirect('/#download')
        if request.form.get('delete'):
            # Call the delete function
            delete_files()
            return redirect('/')

    # print(f"session before check exist video: {session['user_id']}")
    try:
        if session['user_id']:
            exist_video = check_video_exists()
            exist_file = check_file_upload_exists()
            file_list = check_quant_upload_exists()

            return render_template('index.html', exist_video=exist_video,
                exist_file=exist_file, file_list=file_list)
        else:
            return render_template('index.html')

    except KeyError as err:
        print(f"Error checking session_id: {err}")
        return render_template('index.html')
        

@app.route("/about", methods=["GET", "POST"])
# @login_required
def about():
    """Get about app"""

    if request.method == "GET":
        return render_template("about.html")


@app.route("/faq", methods=["GET", "POST"])
# @login_required
def faq():
    """Get about app"""

    if request.method == "GET":
        return render_template("faq.html")

if __name__ == '__main__':
    app.run(debug=True)
