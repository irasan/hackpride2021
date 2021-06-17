import os
from functools import wraps
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)

# @login_required decorator
# https://flask.palletsprojects.com/en/2.0.x/patterns/viewdecorators/#login-required-decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # no "user" in session
        if "user" not in session:
            flash("You must log in to view this page")
            return redirect(url_for("login"))
        # user is in session
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
@app.route("/home")
def home():
    """
    The homepage to display a lit of all artwork from the database
    """
    art = list(mongo.db.art.find())
    return render_template("home.html", art=art)


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user" not in session:
        # only if there isn't a current session["user"]
        if request.method == "POST":
            # check if username already exists in db
            existing_user = mongo.db.users.find_one(
                {"username": request.form.get("username").lower()})

            if existing_user:
                flash("Username already exists")
                return redirect(url_for("register"))

            if request.form.get("password") == request.form.get("password-confirm"):
                register = {
                    "username": request.form.get("username").lower(),
                    "password": generate_password_hash(
                        request.form.get("password")),
                    "is_admin": False,
                    "reviews": [],
                    "favorites": [],
                    "avatar": request.form.get("avatar")
                }
                mongo.db.users.insert_one(register)

                # put the new user into 'session' cookie
                session["user"] = request.form.get("username").lower()
                flash("Registration Successful!")
                return redirect(url_for("profile", username=session["user"]))

            # passwords don't match each other
            flash("Passwords must match")
            return redirect(url_for("register"))

        # generate the form to register a new user
        avatars = [
            "alien", "artist", "astronaut", "basketball-player", "bear",
            "biker", "boy", "cheerleader", "clown", "cop", "cowboy", "deer",
            "detective", "dog", "elf", "emo", "eskimo", "fisherman", "fox",
            "geisha", "girl-1", "girl-2", "hippie", "hipster-boy",
            "hipster-girl", "husky", "king", "kitten", "knight", "man-1",
            "man-2", "mermaid", "monkey", "muslim", "penguin", "pilot",
            "pirate", "princess", "punk-1", "punk-2", "rapper", "robot",
            "runner", "singer", "spy", "squirrel", "student", "vampire",
            "viking", "woman"
        ]
        return render_template("register.html", avatars=avatars)

    # user is already logged-in, direct them to their profile
    return redirect(url_for("profile", username=session["user"]))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" not in session:
        # only if there isn't a current session["user"]
        if request.method == "POST":
            # check if username exists in db
            existing_user = mongo.db.users.find_one(
                {"username": request.form.get("username").lower()})

            if existing_user:
                # ensure hashed password matches user input
                if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                        session["user"] = request.form.get("username").lower()
                        flash(f"Welcome, {request.form.get('username')}")
                        return redirect(url_for(
                            "profile", username=session["user"]))
                else:
                    # invalid password match
                    flash("Incorrect Username and/or Password")
                    return redirect(url_for("login"))

            else:
                # username doesn't exist
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        return render_template("login.html")

    # user is already logged-in, direct them to their profile
    return redirect(url_for("profile", username=session["user"]))


@app.route("/profile/<username>", methods=["GET", "POST"])
@login_required
def profile(username):
    # grab only the session["user"] profile
    if session["user"].lower() == username.lower():
        # find the session["user"] record
        user = mongo.db.users.find_one({"username": username})
        # grab the user's favorites list
        favs = list(mongo.db.art.find(
            {"_id": {"$in": user["favorites"]}}).sort("title", 1))
        return render_template("profile.html", user=user, favs=favs)

    # take the incorrect user to their own profile
    return redirect(url_for("profile", username=session["user"]))


@app.route("/logout")
@login_required
def logout():
    # remove user from session cookies
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_art", methods=["GET", "POST"])
def add_art():
    categories = list(mongo.db.categories.find().sort(
                    "category_name", 1))
    result = {}
    if "user" in session:
        is_admin = mongo.db.users.find_one(
            {"username": session["user"]})["is_admin"]
        if is_admin:
            if request.method == "POST":
                art = {
                        "title": request.form.get("title").lower(),
                        "author": request.form.get("author").lower(),
                        "year": int(request.form.get("year")),
                        "country": request.form.get("country"),
                        "category": request.form.get("category_name"),
                        "is_explicit": request.form.get("is_explicit"),
                        "summary": request.form.get("summary"),
                        "website": request.form.get("website"),
                        "image": request.form.get("cover"),
                    }
                # check if cover url is preperly formatted
                # if not - reload the page but save user's inputs
                if not request.form.get("cover").endswith(('jpeg', 'png', 'jpg')):
                    flash("Please enter a valid url!")
                    result = {
                        "title": request.form.get("title").lower(),
                        "author": request.form.get("author"),
                        "year": int(request.form.get("year")),
                        "country": request.form.get("country"),
                        "category": request.form.get("category_name"),
                        "is_explicit": request.form.get("is_explicit"),
                        "summary": request.form.get("summary"),
                        "website": request.form.get("website")
                    }
                    return render_template(
                        "add_art.html", result=result, categories=categories)

                else:
                    mongo.db.art.insert_one(art)
                    flash("Your Review Was Successfully Added")
                    return render_template("home.html")

        return render_template(
            "add_art.html", result=result, categories=categories)
    return render_template("unauthorised_error.html")


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
