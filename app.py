import os
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

@app.route("/")
@app.route("/home")
def home():
    art = mongo.db.art.find()
    return render_template("home.html", art=art)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        if (request.form.get("password") == request.form.get("password1")):
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
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}!".format(
                    request.form.get("username")))
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


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    if "user" in session:
        if session["user"] == username:
            favs_list = mongo.db.users.find_one(
                {"username": username})["favorites"]
            favs = list(mongo.db.art.find(
                {"_id": {"$in": favs_list}}).sort([("title", 1)]))
            print(favs)

            return render_template(
                "profile.html", favs=favs)
        return redirect(url_for("home"))

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookie
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
