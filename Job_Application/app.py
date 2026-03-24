from flask import Flask, render_template, request, redirect, url_for, session
import re

app = Flask(__name__)
app.secret_key = "secretkey"

# ---------------- STORAGE ----------------
users = {}
applications = []

DEV_USERNAME = "developer"
DEV_PASSWORD = "admin123"

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("Homepage.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if "tries" not in session:
        session["tries"] = 3

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return render_template(
                "Login.html",
                error="All fields are required",
                tries=session["tries"]
            )

        # Developer login
        if username == DEV_USERNAME and password == DEV_PASSWORD:
            session["user"] = username
            session["tries"] = 3
            return redirect(url_for("developer_dashboard"))

        # Check if user exists
        if username in users:
            # Check if user account is deleted
            if users[username].get("deleted", False):
                return render_template(
                    "Login.html",
                    error="Your account has been deleted",
                    tries=session["tries"]
                )
            
            # Normal user login
            if users[username]["password"] == password:
                session["user"] = username
                session["tries"] = 3
                return redirect(url_for("dashboard"))

        session["tries"] -= 1

        if session["tries"] <= 0:
            session["tries"] = 3
            return redirect(url_for("home"))

        return render_template(
            "Login.html",
            error="Wrong username or password",
            tries=session["tries"]
        )

    return render_template("Login.html", tries=session["tries"])

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username")
        name = request.form.get("name")
        age = request.form.get("age")
        address = request.form.get("address")
        password = request.form.get("password")

        if not username or not name or not age or not address or not password:
            return render_template("Register.html", error="All fields are required")

        try:
            age = int(age)
        except:
            return render_template("Register.html", error="Age must be a number")

        if age < 18 or age > 90:
            return render_template("Register.html", error="Age must be between 18 and 90")

        if username in users:
            return render_template("Register.html", error="Username already exists")

        users[username] = {
            "password": password,
            "name": name,
            "age": age,
            "address": address,
            "deleted": False
        }

        return redirect(url_for("login"))

    return render_template("Register.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():

    if "user" not in session or session["user"] == DEV_USERNAME:
        return redirect(url_for("login"))

    return render_template("Dashboard.html")

# ---------------- DEVELOPER DASHBOARD ----------------
@app.route("/developer_dashboard")
def developer_dashboard():

    if "user" not in session or session["user"] != DEV_USERNAME:
        return redirect(url_for("login"))

    return render_template(
        "Developer_dashboard.html",
        applications=applications
    )

# ---------------- ADMIN MANAGE USERS ----------------
@app.route("/manage_users")
def manage_users():
    if "user" not in session or session["user"] != DEV_USERNAME:
        return redirect(url_for("login"))
    
    return render_template(
        "admin_manage_users.html",
        users=users
    )

# ---------------- ADMIN ACTION (UPDATE/DELETE/RESTORE) ----------------
@app.route("/admin_action", methods=["POST"])
def admin_action():
    if "user" not in session or session["user"] != DEV_USERNAME:
        return redirect(url_for("login"))
    
    action = request.form.get("action")
    username = request.form.get("username")
    
    if not username or username not in users:
        return render_template("admin_manage_users.html", users=users, error="User not found")
    
    if action == "update":
        name = request.form.get("name")
        age = request.form.get("age")
        address = request.form.get("address")
        
        if name:
            users[username]["name"] = name
        if age:
            try:
                users[username]["age"] = int(age)
            except:
                pass
        if address:
            users[username]["address"] = address
        
        return render_template("admin_manage_users.html", users=users, success=f"User '{username}' updated successfully")
    
    elif action == "delete":
        admin_password = request.form.get("admin_password")
        
        # Verify admin password
        if admin_password != DEV_PASSWORD:
            return render_template("admin_manage_users.html", users=users, error="Incorrect admin password. Delete cancelled.")
        
        # Soft delete the user
        users[username]["deleted"] = True
        return render_template("admin_manage_users.html", users=users, success=f"User '{username}' has been deleted")
    
    elif action == "restore":
        users[username]["deleted"] = False
        return render_template("admin_manage_users.html", users=users, success=f"User '{username}' has been restored")
    
    return render_template("admin_manage_users.html", users=users)

# ---------------- THANK YOU ----------------
@app.route("/thank_you")
def thank_you():
    return render_template("thank_you.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# ---------------- SAVE APPLICATION ----------------
def save_application(job):
    username = session.get("user")
    user_info = users.get(username)

    # Initialize a dictionary to store specific field errors
    errors = {}

    fullname = request.form.get("fullname")
    email = request.form.get("email")
    license_number = request.form.get("license")
    question1 = request.form.get("question1")
    question2 = request.form.get("question2")
    question3 = request.form.get("question3")
    question4 = request.form.get("question4")
    cover_letter = request.form.get("cover_letter")

    # Check each field and assign error to specific key
    if not fullname: errors["fullname"] = "Full Name is required."
    if not email: 
        errors["email"] = "Email address is required."
    else:
        email_pattern = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'
        if not re.match(email_pattern, email):
            errors["email"] = "Invalid email format (e.g. name@domain.com)."
            
    if not license_number: errors["license"] = "License/Military ID is required."
    if not question1: errors["question1"] = "Answer to Question 1 is required."
    if not question2: errors["question2"] = "Answer to Question 2 is required."
    if not question3: errors["question3"] = "Answer to Question 3 is required."
    if not question4: errors["question4"] = "Answer to Question 4 is required."
    if not cover_letter: errors["cover_letter"] = "Cover Letter is required."

    # If there are any errors, return the dictionary
    if errors:
        return errors

    application = {
        "username": username,
        "fullname": fullname,
        "email": email,
        "license": license_number,
        "name": user_info["name"],
        "age": user_info["age"],
        "address": user_info["address"],
        "job": job,
        "cover_letter": cover_letter,
        "question1": question1,
        "question2": question2,
        "question3": question3,
        "question4": question4
    }

    applications.append(application)
    return "SUCCESS"

# ---------------- JOB APPLICATIONS ----------------
@app.route("/doctor_application", methods=["GET", "POST"])
def doctor_application():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        result = save_application("Doctor")
        if result == "SUCCESS":
            return redirect(url_for("thank_you"))
        # result is the error dictionary
        return render_template("doctor_application.html", errors=result)

    return render_template("doctor_application.html", errors={})


@app.route("/soldier_application", methods=["GET", "POST"])
def soldier_application():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        result = save_application("Soldier")
        if result == "SUCCESS":
            return redirect(url_for("thank_you"))
        return render_template("soldier_application.html", errors=result)

    return render_template("soldier_application.html", errors={})


@app.route("/engineer_application", methods=["GET", "POST"])
def engineer_application():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        result = save_application("Engineer")
        if result == "SUCCESS":
            return redirect(url_for("thank_you"))
        return render_template("engineer_application.html", errors=result)

    return render_template("engineer_application.html", errors={})


@app.route("/game_developer_application", methods=["GET", "POST"])
def game_developer_application():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        result = save_application("Game Developer")
        if result == "SUCCESS":
            return redirect(url_for("thank_you"))
        return render_template("game_developer_application.html", errors=result)

    return render_template("game_developer_application.html", errors={})


@app.route("/data_analyst_application", methods=["GET", "POST"])
def data_analyst_application():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        result = save_application("Data Analyst")
        if result == "SUCCESS":
            return redirect(url_for("thank_you"))
        return render_template("data_analyst_application.html", errors=result)

    return render_template("data_analyst_application.html", errors={})

# ---------------- EDIT PROFILE ROUTE ----------------
# ---------------- PROFILE (EDITING ONLY) ----------------
@app.route("/profile", methods=["GET", "POST"])
def profile():
    # 1. Security Check: Must be logged in
    if "user" not in session:
        return redirect(url_for("login"))

    current_session_username = session["user"]

    # Prevent Developer from accessing user profile logic if necessary
    if current_session_username == DEV_USERNAME:
        return redirect(url_for("developer_dashboard"))

    if current_session_username not in users:
        return redirect(url_for("logout"))

    if request.method == "POST":
        # Get all data from the form
        new_username = request.form.get("new_username")
        name = request.form.get("name")
        age = request.form.get("age")
        address = request.form.get("address")
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")

        # 2. Server-Side Validation (Since 'required' tags were removed from HTML)
        if not new_username or not name or not age or not address:
            return render_template("profile.html", info=users[current_session_username], error="All personal fields are required")

        try:
            age = int(age)
            if age < 18 or age > 90:
                return render_template("profile.html", info=users[current_session_username], error="Age must be between 18 and 90")
        except ValueError:
            return render_template("profile.html", info=users[current_session_username], error="Age must be a valid number")

        # 3. Identity Verification (Strict requirement for current password)
        if not old_password:
            return render_template("profile.html", info=users[current_session_username], error="Current password is required to save any changes")
        
        if old_password != users[current_session_username]["password"]:
            return render_template("profile.html", info=users[current_session_username], error="Current password is incorrect")

        # 4. Handle Username Migration Logic
        # If the user is changing their username, we must move the dictionary key
        target_username = current_session_username 
        
        if new_username != current_session_username:
            if new_username in users:
                return render_template("profile.html", info=users[current_session_username], error="That username is already taken")
            
            # Move the user data to the new key and delete the old one
            users[new_username] = users.pop(current_session_username)
            # Update the session so the user stays logged in under the new name
            session["user"] = new_username
            target_username = new_username

        # 5. Update the Data
        users[target_username]["name"] = name
        users[target_username]["age"] = age
        users[target_username]["address"] = address
        
        # Optional password update
        if new_password:
            if len(new_password) < 4:
                return render_template("profile.html", info=users[target_username], error="New password must be at least 4 characters")
            users[target_username]["password"] = new_password

        return render_template("profile.html", info=users[target_username], success=True)

    # GET request: Show the form with current data
    return render_template("profile.html", info=users[current_session_username])

# ---------------- EDIT PROFILE ALIAS ----------------
@app.route("/edit_profile")
def edit_profile():
    # Simply redirect to profile since it is now the dedicated editing route
    return redirect(url_for("profile"))

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)