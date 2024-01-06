# Contains parts from: https://flask-user.readthedocs.io/en/latest/quickstart_app.html

from flask import Flask, render_template, request
from flask_user import login_required, UserManager, current_user

from models import db, User, Movie, MovieGenre, MovieLink, MovieTag, MovieRating
from read_data import check_and_read_data
from recommend_functions import recommendUserUser, recommendItemItem, recommendMostPopular

import click

# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

    # Flask-SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///movie_recommender.sqlite'  # File-based SQL database
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Avoids SQLAlchemy warning

    # Flask-User settings
    USER_APP_NAME = "Movie Recommender"  # Shown in and email templates and page footers
    USER_ENABLE_EMAIL = False  # Disable email authentication
    USER_ENABLE_USERNAME = True  # Enable username authentication
    USER_REQUIRE_RETYPE_PASSWORD = True  # Simplify register form

# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db
db.init_app(app)  # initialize database
db.create_all()  # create database if necessary
user_manager = UserManager(app, db, User)  # initialize Flask-User management



@app.cli.command('initdb')
def initdb_command():
    global db
    """Creates the database tables."""
    check_and_read_data(db)
    print('Initialized the database.')

@app.cli.command('recommendUserUser')
@click.argument('user_id', type=int)
def recommendUserUser_command(user_id):
    """Creates the database tables."""
    recommendUserUser(user_id)
    print('Ran recommendUserUser')

@app.cli.command('recommendItemItem')
@click.argument('movie_id', type=int)
def recommendItemItem_command(movie_id):
    """Creates the database tables."""
    recommendItemItem(movie_id)
    print('Ran recommendItemItem')

@app.cli.command('recommendMostPopular')
@click.argument('user_id', type=int)
def recommendMostPopular_command(user_id):
    """Creates the database tables."""
    recommendMostPopular(user_id)
    print('Ran recommendMostPopular')


# The Home page is accessible to anyone
@app.route('/')
def home_page():
    # render home.html template
    return render_template("home.html")


# The Members page is only accessible to authenticated users via the @login_required decorator
@app.route('/movies')
@login_required  # User must be authenticated
def movies_page():
    # String-based templates

    # first 10 movies
    movies = Movie.query.limit(20).all()

    tags = MovieTag.query.filter(MovieTag.movie_id.in_((1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20))).all()
    print('tags', tags)

    links = MovieLink.query.filter(MovieLink.movie_id.in_((1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20))).all()
    print('links', links)

    # only Romance movies
    # movies = Movie.query.filter(Movie.genres.any(MovieGenre.genre == 'Romance')).limit(10).all()

    # only Romance AND Horror movies
    # movies = Movie.query\
    #     .filter(Movie.genres.any(MovieGenre.genre == 'Romance')) \
    #     .filter(Movie.genres.any(MovieGenre.genre == 'Horror')) \
    #     .limit(10).all()

    return render_template("movies.html", movies=movies, tags=tags, links=links)


@app.route('/rate', methods=['POST'])
@login_required  # User must be authenticated
def rate():
    movieid = request.form.get('movieid')
    rating = request.form.get('rating')
    # userid = current_user.get_id()
    userid = current_user.id
    print("Rate {} for {} by {}".format(rating, movieid, userid))
    return render_template("rated.html", rating=rating)


# Start development web server
if __name__ == '__main__':
    app.run(port=5000, debug=True)
