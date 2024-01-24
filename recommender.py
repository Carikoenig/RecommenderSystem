# Contains parts from: https://flask-user.readthedocs.io/en/latest/quickstart_app.html

from flask import Flask, render_template, request, redirect
from flask_user import login_required, UserManager, current_user
from models import db, User, Movie, MovieGenre, MovieLink, MovieTag, MovieRating
from read_data import check_and_read_data
from recommend_functions import recommendUserUser, recommendItemItem, recommendMostPopular, recommendReWatch, recommendRandomMovies, amount_recs
from lenskit.algorithms import Recommender
from lenskit.algorithms.user_knn import UserUser
from lenskit.algorithms.item_knn import ItemItem
import click
import pandas as pd 
import time

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

print('Preparations running...')
# convert data for lenskit usage
ratings = MovieRating.query.all()
data_ratings = pd.DataFrame([(rating.user_id, rating.movie_id, rating.rating) for rating in ratings], columns=['user', 'item', 'rating'])
movies = Movie.query.all()
data_movies = pd.DataFrame([(movie.id, movie.title, movie.genres) for movie in movies], columns=['item', 'title' , 'genres'])

# Collaborative Fitlering Item-Item similarity
item_item = ItemItem(15, min_nbrs=3, feedback='explicit')
algo_item = Recommender.adapt(item_item)
algo_item.fit(data_ratings)
print('setup lenskit Item-Item algorithm')

# Collaborative Fitlering User-User similarity
user_user = UserUser(15, min_nbrs=3, feedback='explicit') # define min and max of users as neighbours
algo_user = Recommender.adapt(user_user)
algo_user.fit(data_ratings)
print('setup lenskit User-User algorithm')



@app.cli.command('initdb')
def initdb_command():
    global db
    """Creates the database tables."""
    check_and_read_data(db)
    print('Initialized the database.')

@app.cli.command('recommendUserUser')
@click.argument('user_id', type=int)
def recommendUserUser_command(user_id):
    recommendUserUser(user_id)
    print('Ran recommendUserUser')

@app.cli.command('recommendItemItem')
@click.argument('movie_id', type=int)
def recommendItemItem_command(movie_id):
    recommendItemItem(movie_id)
    print('Ran recommendItemItem')

@app.cli.command('recommendMostPopular')
@click.argument('user_id', type=int)
def recommendMostPopular_command(user_id):
    recommendMostPopular(user_id)
    print('Ran recommendMostPopular')

@app.cli.command('recommendReWatch')
@click.argument('user_id', type=int)
def recommendReWatch_command(user_id):
    # movies = Movie.query.all()
    # data_movies = pd.DataFrame([(movie.id, movie.title, movie.genres) for movie in movies], columns=['item', 'title' , 'genres'])
    recommendReWatch(user_id, data_movies)
    print('Ran recommendReWatch')


# The Home page is accessible to anyone
@app.route('/')
def home_page():
    # render home.html template
    return render_template("home.html")


# The Members page is only accessible to authenticated users via the @login_required decorator
@app.route('/movies')
@login_required  # User must be authenticated
def movies_page():

    # first 20 movies
    # movies = Movie.query.limit(20).all()
    # tags = MovieTag.query.filter(MovieTag.movie_id.in_((1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20))).all()
    # print('tags', tags)
    # links = MovieLink.query.filter(MovieLink.movie_id.in_((1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20))).all()
    # print('links', links)

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

    return render_template("movies.html", movies=movies, tags=tags, links=links)

@app.route('/rewatch')
@login_required  # User must be authenticated
def reWatch_page():

    userid = current_user.id
    print('current user', userid)
    #testing, as long as no rating of new users happening yet
    # userid = 12

    # recommend
    # For new Users with few to no interactions
    if not userid or MovieRating.query.filter_by(user_id=userid).count() < 5:

        movies_rec, movies_rec_id = recommendRandomMovies(amount_recs)
    else:
        # For Users with enough interactions
        movies_rec, movies_rec_id = recommendReWatch(userid)
        
    print('movies_rec', movies_rec)
    for movie in movies_rec:
        print(movie.title)

    tags_rec = MovieTag.query.filter(MovieTag.movie_id.in_(movies_rec_id)).all()
    print('tags_rec', tags_rec)

    links_rec = MovieLink.query.filter(MovieLink.movie_id.in_(movies_rec_id)).all()
    print('links_rec', links_rec)

    return render_template("movies.html", movies=movies_rec, tags=tags_rec, links=links_rec)

@app.route('/recUserUser')
@login_required  # User must be authenticated
def recUserUser_page():

    userid = current_user.id
    print('current user id', userid)
    #testing, as long as no rating of new users happening yet
    # userid = 12

    # recommend
    movies_rec, movies_rec_id = recommendUserUser(userid, data_ratings, data_movies, algo_user)
    # print('movies_rec', movies_rec)
    # for movie in movies_rec:
    #     print(movie.title)

    tags_rec = MovieTag.query.filter(MovieTag.movie_id.in_(movies_rec_id)).all()
    # print('tags_rec', tags_rec)

    links_rec = MovieLink.query.filter(MovieLink.movie_id.in_(movies_rec_id)).all()
    # print('links_rec', links_rec)

    return render_template("movies.html", movies=movies_rec, tags=tags_rec, links=links_rec)

@app.route('/recItemItem')
@login_required  # User must be authenticated
def recItemItem_page():

    userid = current_user.id
    print('current_user', userid)
    # testing, as long as no rating of new users happening yet
    # userid = 12

    # recommend
    movies_rec, movies_rec_id = recommendItemItem(userid, data_ratings, data_movies, algo_item)
    # print('movies_rec', movies_rec)
    # for movie in movies_rec:
    #     print(movie.title)

    tags_rec = MovieTag.query.filter(MovieTag.movie_id.in_(movies_rec_id)).all()
    # print('tags_rec', tags_rec)

    links_rec = MovieLink.query.filter(MovieLink.movie_id.in_(movies_rec_id)).all()
    # print('links_rec', links_rec)

    return render_template("movies.html", movies=movies_rec, tags=tags_rec, links=links_rec)

@app.route('/popular')
def recPopular_page():

    # recommend
    movies_rec, movies_rec_id = recommendMostPopular(data_ratings, data_movies)
    # print('movies_rec', movies_rec)
    # for movie in movies_rec:
    #     print(movie.title)

    tags_rec = MovieTag.query.filter(MovieTag.movie_id.in_(movies_rec_id)).all()
    # print('tags_rec', tags_rec)

    links_rec = MovieLink.query.filter(MovieLink.movie_id.in_(movies_rec_id)).all()
    # print('links_rec', links_rec)

    return render_template("movies.html", movies=movies_rec, tags=tags_rec, links=links_rec)


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
            return redirect('/', code=302)
        else:
            return render_template("error.html", error="Invalid rating. Please choose a rating between 1 and 5.")

    except Exception as e:
        return render_template("error.html", error=str(e))


# Start development web server
if __name__ == '__main__':
    app.run(port=5000, debug=True)
