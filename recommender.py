# Contains parts from: https://flask-user.readthedocs.io/en/latest/quickstart_app.html

from flask import Flask, render_template, request, redirect, abort, url_for
from flask_user import login_required, UserManager, current_user
from models import db, User, Movie, MovieGenre, MovieLink, MovieTag, MovieRating
from read_data import check_and_read_data
from recommend_functions import recommendUserUser, recommendItemItem, recommendMostPopular, recommendReWatch, recommendRandomMovies, recommendCosine, amount_recs
from lenskit.algorithms import Recommender
from lenskit.algorithms.user_knn import UserUser
from lenskit.algorithms.item_knn import ItemItem
import click
import pandas as pd 
import time
import traceback

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

    USER_AFTER_REGISTER_ENDPOINT = 'home_page'
    USER_AFTER_CONFIRM_ENDPOINT = 'home_page'
    USER_AFTER_LOGIN_ENDPOINT = 'home_page'
    USER_AFTER_LOGOUT_ENDPOINT = 'home_page'

# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db
db.init_app(app)  # initialize database
db.create_all()  # create database if necessary
user_manager = UserManager(app, db, User)  # initialize Flask-User management


movies = Movie.query.all()
data_movies = pd.DataFrame([(movie.id, movie.title, movie.genres) for movie in movies], columns=['item', 'title' , 'genres'])



@app.cli.command('initdb')
def initdb_command():
    global db
    """Creates the database tables."""
    check_and_read_data(db)
    print('Initialized the database.')

# following command line functions were useful for development and testing of the recommender functions
# @app.cli.command('recommendUserUser')
# @click.argument('user_id', type=int)
# def recommendUserUser_command(user_id):
#     recommendUserUser(user_id)
#     print('Ran recommendUserUser')

# @app.cli.command('recommendItemItem')
# @click.argument('movie_id', type=int)
# def recommendItemItem_command(movie_id):
#     recommendItemItem(movie_id)
#     print('Ran recommendItemItem')

# @app.cli.command('recommendMostPopular')
# @click.argument('user_id', type=int)
# def recommendMostPopular_command(user_id):
#     recommendMostPopular(user_id)
#     print('Ran recommendMostPopular')

# @app.cli.command('recommendReWatch')
# @click.argument('user_id', type=int)
# def recommendReWatch_command(user_id):
#     # movies = Movie.query.all()
#     # data_movies = pd.DataFrame([(movie.id, movie.title, movie.genres) for movie in movies], columns=['item', 'title' , 'genres'])
#     recommendReWatch(user_id, data_movies)
#     print('Ran recommendReWatch')

# @app.cli.command('recommendCosine')
# @click.argument('user_id', type=int)
# def recommendCosine_command(user_id):
#     # movies = Movie.query.all()
#     # data_movies = pd.DataFrame([(movie.id, movie.title, movie.genres) for movie in movies], columns=['item', 'title' , 'genres'])
#     ratings = MovieRating.query.all()
#     # data_ratings = pd.DataFrame([(rating.user_id, rating.movie_id, rating.rating) for rating in ratings], columns=['user', 'item', 'rating'])
#     recommendCosine(user_id, ratings)
#     print('Ran recommendCosine')


# The Home page is accessible to anyone
@app.route('/')
def home_page():
    # render home.html template
    return render_template("home.html")


# The Members page is only accessible to authenticated users via the @login_required decorator
@app.route('/movies')
def movies_page():

    # random movies
    movies = Movie.query.order_by(db.func.random()).limit(10).all()
    movie_ids = [movie.id for movie in movies]
    # print(movies, 'random_movies')
    # print('movie_ids', movie_ids)
    # print('length of numbers in movie_id list: ', len(movie_ids))
    tags = MovieTag.query.filter(MovieTag.movie_id.in_(movie_ids)).all()
    # print('tags', tags)
    links = MovieLink.query.filter(MovieLink.movie_id.in_(movie_ids)).all()
    # print('links', links)

    return render_template("random.html", movies=movies, tags=tags, links=links)


@app.route('/popular')
def recPopular_page():

    ratings = MovieRating.query.all()
    data_ratings = pd.DataFrame([(rating.user_id, rating.movie_id, rating.rating) for rating in ratings], columns=['user', 'item', 'rating'])
    # recommend
    movies_rec, movies_rec_id = recommendMostPopular(data_ratings, data_movies)
    # print('movies_rec', movies_rec)
    # for movie in movies_rec:
    #     print(movie.title)

    tags_rec = MovieTag.query.filter(MovieTag.movie_id.in_(movies_rec_id)).all()
    # print('tags_rec', tags_rec)

    links_rec = MovieLink.query.filter(MovieLink.movie_id.in_(movies_rec_id)).all()
    # print('links_rec', links_rec)

    return render_template("popular.html", movies=movies_rec, tags=tags_rec, links=links_rec)
    

@app.route('/recCosine')
@login_required  # User must be authenticated
def recCosine_page():

    userid = current_user.id

    ratings = MovieRating.query.all()

    rec_cosine, rec_cosine_ids = recommendCosine(userid, ratings)
    # recommend
    print('movies_rec_cosine', rec_cosine)
    for movie in rec_cosine:
        print(movie.title, movie.id)

    tags_rec = MovieTag.query.filter(MovieTag.movie_id.in_(rec_cosine_ids)).all()
    # print('tags_rec', tags_rec)

    links_rec = MovieLink.query.filter(MovieLink.movie_id.in_(rec_cosine_ids)).all()
    # print('links_rec', links_rec)

    return render_template("recommended.html", movies=rec_cosine, tags=tags_rec, links=links_rec)


@app.route('/recUserUser')
@login_required  # User must be authenticated
def recUserUser_page():

    userid = current_user.id
    print('current user id', userid)

    ratings = MovieRating.query.all()
    data_ratings = pd.DataFrame([(rating.user_id, rating.movie_id, rating.rating) for rating in ratings], columns=['user', 'item', 'rating'])

    # recommend
    movies_rec, movies_rec_id = recommendUserUser(userid, data_ratings, data_movies)
    # movies_rec, movies_rec_id = recommendUserUser(userid, data_ratings, data_movies, algo_user, original_to_abstract_mapping_user)
    print('movies_rec', movies_rec)
    for movie in movies_rec:
        print(movie.title, movie.id)

    tags_rec = MovieTag.query.filter(MovieTag.movie_id.in_(movies_rec_id)).all()
    # print('tags_rec', tags_rec)

    links_rec = MovieLink.query.filter(MovieLink.movie_id.in_(movies_rec_id)).all()
    # print('links_rec', links_rec)

    return render_template("recommended.html", movies=movies_rec, tags=tags_rec, links=links_rec)


@app.route('/recItemItem')
@login_required  # User must be authenticated
def recItemItem_page():

    userid = current_user.id
    print('current_user', userid)
    # testing, as long as no rating of new users happening yet
    # userid = 12

    ratings = MovieRating.query.all()
    data_ratings = pd.DataFrame([(rating.user_id, rating.movie_id, rating.rating) for rating in ratings], columns=['user', 'item', 'rating'])

    # recommend
    # movies_rec, movies_rec_id = recommendItemItem(userid, data_ratings, data_movies, algo_item, original_to_abstract_mapping_item)
    movies_rec, movies_rec_id = recommendItemItem(userid, data_ratings, data_movies)
    print('movies_rec', movies_rec)
    for movie in movies_rec:
        print(movie.title, movie.id)

    tags_rec = MovieTag.query.filter(MovieTag.movie_id.in_(movies_rec_id)).all()
    # print('tags_rec', tags_rec)

    links_rec = MovieLink.query.filter(MovieLink.movie_id.in_(movies_rec_id)).all()
    # print('links_rec', links_rec)

    return render_template("recommended.html", movies=movies_rec, tags=tags_rec, links=links_rec)


@app.route('/rate', methods=['GET'])
@login_required  # User must be authenticated
def rate_page():
    return render_template("rate.html")

@app.route('/rate', methods=['POST'])
@login_required  # User must be authenticated
def rate():
    try:
        movie_id = int(request.form.get('movieid'))
        rating = int(request.form.get('rating'))

        if 1 <= rating <= 5:
            user_id = current_user.id
            #print('user_id', user_id)
            existing_rating = MovieRating.query.filter_by(user_id=user_id, movie_id=movie_id).first()
            current_time = time.time()
            #print('current time', current_time)

            if existing_rating:
                #print('existing rating', existing_rating)
                existing_rating.rating = rating
                existing_rating.timestamp = current_time
            else:
                new_rating = MovieRating(user_id=user_id, movie_id=movie_id, rating=rating, timestamp=current_time)
                db.session.add(new_rating)

            db.session.commit()

            # return render_template('home.html') 
           
            # return redirect('/', code=302)
            return redirect(url_for('home_page'), code=302)
        else:
            return render_template("error.html", error="Invalid rating. Please choose a rating between 1 and 5.")

    except Exception as e:
        return render_template("error.html", error=str(e))

@app.route('/rewatch')
@login_required  # User must be authenticated
def reWatch_page():

    userid = current_user.id
    print('current user', userid)

    # recommend
    # For new Users with few to no interactions
    if not userid or MovieRating.query.filter_by(user_id=userid).count() < 5:

        movies_rec, movies_rec_id = recommendRandomMovies(amount_recs)
    else:
        # For Users with enough interactions
        movies_rec, movies_rec_id = recommendReWatch(userid)
        
    print('movies_rec', movies_rec)
    for movie in movies_rec:
        print(movie.title, movie.id)

    tags_rec = MovieTag.query.filter(MovieTag.movie_id.in_(movies_rec_id)).all()
    print('tags_rec', tags_rec)

    links_rec = MovieLink.query.filter(MovieLink.movie_id.in_(movies_rec_id)).all()
    print('links_rec', links_rec)

    return render_template("rewatch.html", movies=movies_rec, tags=tags_rec, links=links_rec)


@app.errorhandler(500)
def internal_error(exception):
   return "<pre>"+traceback.format_exc()+"</pre>"


@app.route("/something")
def yourcode():

    abort(400)  # wrong or illegal request → issue a 400 error


# Start development web server
if __name__ == '__main__':
    app.run(port=5000, debug=True)
