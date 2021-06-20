import os
import random
from functools import wraps
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from datetime import datetime
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


# @is_admin decorator
def is_admin(f):
    @wraps(f)
    @login_required  # must be logged-in to access this function
    def decorated_function(*args, **kwargs):
        # get session user
        user = mongo.db.users.find_one({"username": session["user"].lower()})
        if not user["is_admin"]:
            flash("This page is restricted to admin access")
            return redirect(url_for("home"))
        # user is an admin
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
@app.route("/home")
def home():
    """
    The homepage to display a list of all artwork from the database,
    a random record for each category, and a brief intro about the site.
    """
    # find all records that are "approved"
    art = list(mongo.db.art.find({"is_approved": True}))
    # generate each sub-category list
    artwork = []
    books = []
    movies = []
    music = []
    podcasts = []
    for record in art:
        if record["category"] == "artwork":
            artwork.append(record)
        elif record["category"] == "books":
            books.append(record)
        elif record["category"] == "movies":
            movies.append(record)
        elif record["category"] == "music":
            music.append(record)
        elif record["category"] == "podcasts":
            podcasts.append(record)
        else:
            print("Invalid category")
    # get a random record from each category
    rand_artwork = random.choice(artwork) if len(artwork) > 0 else ""
    rand_book = random.choice(books) if len(books) > 0 else ""
    rand_movie = random.choice(movies) if len(movies) > 0 else ""
    rand_music = random.choice(music) if len(music) > 0 else ""
    rand_podcast = random.choice(podcasts) if len(podcasts) > 0 else ""
    return render_template(
        "home.html", artwork=artwork, books=books,
        movies=movies, music=music, podcasts=podcasts,
        rand_artwork=rand_artwork, rand_book=rand_book,
        rand_movie=rand_movie, rand_music=rand_music,
        rand_podcast=rand_podcast
    )


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
                    "is_admin": bool(False),
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
                        session["is_admin"] = True
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
        artwork = []
        books = []
        movies = []
        music = []
        podcasts = []
        for record in favs:
            if record["category"] == "artwork":
                artwork.append(record)
            elif record["category"] == "books":
                books.append(record)
            elif record["category"] == "movies":
                movies.append(record)
            elif record["category"] == "music":
                music.append(record)
            elif record["category"] == "podcasts":
                podcasts.append(record)
            else:
                print("Invalid category")
        return render_template(
            "profile.html", user=user, favs=favs,
            artwork=artwork, books=books,
            movies=movies, music=music, podcasts=podcasts)

    # take the incorrect user to their own profile
    return redirect(url_for("profile", username=session["user"]))


@app.route("/admin")
@login_required
@is_admin
def admin():
    """
    Admin-Only page
    """
    pending = list(mongo.db.suggestions.find({"is_approved": False}))
    return render_template("admin.html", pending=pending)


@app.route("/logout")
@login_required
def logout():
    # remove user from session cookies
    flash("You have been logged out")
    session.pop("user")
    session.pop("is_admin")
    return redirect(url_for("login"))


@app.route("/add_art", methods=["GET", "POST"])
@login_required
@is_admin
def add_art():
    result = {}
    categories = list(mongo.db.categories.find().sort("category_name", 1))
    if request.method == "POST":
        art = {
                "title": request.form.get("title"),
                "author": request.form.get("author"),
                "year": int(request.form.get("year")),
                "country": request.form.get("country"),
                "category": request.form.get("category"),
                "is_explicit": request.form.get("is_explicit"),
                "summary": request.form.get("summary"),
                "website": request.form.get("website"),
                "image": request.form.get("cover"),
                "reviews": int(0),
                "favorites": int(0)
            }
        # check if cover url is preperly formatted
        # if not - reload the page but save user's inputs
        if not request.form.get("cover").endswith(('jpeg', 'png', 'jpg')):
            flash("Please enter a valid url!")
            result = {
                "title": request.form.get("title"),
                "author": request.form.get("author"),
                "year": int(request.form.get("year")),
                "country": request.form.get("country"),
                "category": request.form.get("category"),
                "is_explicit": request.form.get("is_explicit"),
                "summary": request.form.get("summary"),
                "website": request.form.get("website"),
                "image": "",
                "reviews": int(0),
                "favorites": int(0)
            }
            return render_template(
                "add_art.html", result=result, categories=categories)

        else:
            mongo.db.art.insert_one(art)
            flash("Your Review Was Successfully Added")
            return render_template("home.html")
    return render_template(
        "add_art.html", result=result, categories=categories)


@app.route("/edit_art/<id>", methods=["GET", "POST"])
@login_required
@is_admin
def edit_art(id):
    result = {}
    categories = list(mongo.db.categories.find().sort("category_name", 1))
    if request.method == "POST":
        art = {
                "title": request.form.get("title"),
                "author": request.form.get("author"),
                "year": int(request.form.get("year")),
                "country": request.form.get("country"),
                "category": request.form.get("category"),
                "is_explicit": request.form.get("is_explicit"),
                "summary": request.form.get("summary"),
                "website": request.form.get("website"),
                "image": request.form.get("cover"),
                "reviews": int(0),
                "favorites": int(0)
            }
        # check if cover url is preperly formatted
        # if not - reload the page but save user's inputs
        if not request.form.get("cover").endswith(('jpeg', 'png', 'jpg')):
            flash("Please enter a valid url!")
            result = {
                "title": request.form.get("title"),
                "author": request.form.get("author"),
                "year": int(request.form.get("year")),
                "country": request.form.get("country"),
                "category": request.form.get("category"),
                "is_explicit": request.form.get("is_explicit"),
                "summary": request.form.get("summary"),
                "website": request.form.get("website"),
                "image": "",
                "reviews": int(0),
                "favorites": int(0)
            }
            return render_template(
                "edit_art.html", result=result, categories=categories)

        else:
            mongo.db.art.insert_one(art)
            flash("Your Review Was Successfully Added")
            return render_template("home.html")
    return render_template("edit_art.html", result=result, categories=categories)


@app.route("/artpiece/<id>", methods=["GET", "POST"])
def artpiece(id):
    # get the id and display the full page with reviews
    item = mongo.db.art.find_one({"_id": ObjectId(id)})
    reviews = list(mongo.db.reviews.find(
        {"item_id": ObjectId(id)}))

    if request.method == "POST":
        if "user" in session:
            # create document for reviews collection
            user_review = {
                "review": request.form.get("review"),
                "username": session["user"],
                "date": datetime.now().strftime("%d %B, %Y"),
                "item_id": ObjectId(id),
            }
            mongo.db.reviews.insert_one(user_review)
            mongo.db.users.find_one_and_update(
                {"username": session["user"].lower()},
                {"$push": {"reviews": ObjectId(id)}})
            mongo.db.art.update_one(
                {"_id": ObjectId(id)},
                {"$inc": {"reviews": 1}})
            flash("Your Review Was Successfully Added")
            return redirect(url_for("artpiece", id=id))
        else:
            flash("Please log in to leave a review")
            return redirect(url_for("login"))

    return render_template("artpiece.html", item=item, reviews=reviews)


@app.route("/add_favorite/<id>")
# add art piece to user's favorites'
def add_favorite(id):
    # check if item is already in favorites!!!

    mongo.db.users.find_one_and_update(
        {"username": session["user"].lower()},
        {"$push": {"favorites": ObjectId(id)}})
    mongo.db.art.update_one({"_id": ObjectId(id)},
        {"$inc": {"favorites": 1}})
    flash("This art piece has been saved to your favorites!")
    return redirect(url_for("profile", username=session["user"]))


@app.route("/remove_favorite/<id>")
@login_required
# remove art piece from user's favorites'
def remove_favorite(id):
    mongo.db.users.find_one_and_update(
        {"username": session["user"].lower()},
        {"$pull": {"favorites": ObjectId(id)}})
    mongo.db.art.update_one({"_id": ObjectId(id)},
        {"$inc": {"favorites": -1}})
    flash("This art piece has been removed from your favorites!")
    return redirect(url_for("profile", username=session["user"]))


@app.route("/category/<category>")
def category(category):
    # display all records for each category
    art = list(mongo.db.art.find({"category": category}))
    return render_template("category.html", art=art)


@app.route("/suggestions", methods=["GET", "POST"])
@login_required
def suggestions():
    if request.method == "POST":
        suggestion = {
                "title": request.form.get("title"),
                "author": request.form.get("author"),
                "year": int(request.form.get("year")),
                "country": request.form.get("country"),
                "category": request.form.get("category"),
                "is_explicit": request.form.get("is_explicit"),
                "summary": request.form.get("summary"),
                "website": request.form.get("website"),
                "image": request.form.get("cover"),
                "is_approved": bool(False)
        }
        mongo.db.suggestions.insert_one(suggestion)
        flash("Thank You! Your suggestions is being reviewed!")
        return redirect(url_for("home"))
    categories = list(mongo.db.categories.find().sort("category_name", 1))
    return render_template("suggestions.html", categories=categories)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
