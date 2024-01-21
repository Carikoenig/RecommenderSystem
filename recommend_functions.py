import pandas as pd 
from models import MovieRating, Movie
from lenskit.algorithms import Recommender
from lenskit.algorithms.user_knn import UserUser
from lenskit.algorithms.item_knn import ItemItem
from lenskit.algorithms.ranking import TopN

amount_recs = 20

def recommendUserUser(user_id, data_ratings, data_movies, algo_user):
    
    # get the ratings data
    # ratings = MovieRating.query.all()
    # movies = Movie.query.all()

    # for rating in data[:10]:
    #     print(rating.user_id, rating.movie_id, rating.rating)

    # convert to Pandas DataFrame to make accessible for Lenskit
    # data = pd.DataFrame([(rating.user_id, rating.movie_id, rating.rating) for rating in ratings], columns=['user', 'item', 'rating'])
    # data_movies = pd.DataFrame([(movie.id, movie.title, movie.genres) for movie in movies], columns=['item', 'title' , 'genres'])
    # joined_data = data.join(data_movies['genres'], on='item')
    # joined_data = data.join(data_movies['title'], on='item')

    #print(joined_data.head(10))

     
    top_recommendations = algo_user.recommend(user_id, amount_recs)

    joined_data = top_recommendations.join(data_movies['genres'], on='item')
    joined_data = joined_data.join(data_movies['title'], on='item')
    #TODO: find out why predicted scores fall outside the range of 0-5??
    print('joined data UserUser', joined_data)

    rec_movies_ids = set(top_recommendations['item'])
    print('rec_movies_ids', rec_movies_ids)

    rec_movies =  Movie.query.filter(Movie.id.in_(rec_movies_ids)).all()

    return rec_movies, rec_movies_ids


def recommendItemItem(item_id, data_ratings, data_movies, algo_item):

    # get the ratings data
    # ratings = MovieRating.query.all()
    # movies = Movie.query.all()

    # for rating in data[:10]:
    #     print(rating.user_id, rating.movie_id, rating.rating)

    # convert to Pandas DataFrame to make accessible for Lenskit
    # data = pd.DataFrame([(rating.user_id, rating.movie_id, rating.rating) for rating in ratings], columns=['user', 'item', 'rating'])
    # data_movies = pd.DataFrame([(movie.id, movie.title, movie.genres) for movie in movies], columns=['item', 'title' , 'genres'])

    #print(data.head(10))

    top_recommendations = algo_item.recommend(item_id, amount_recs)

    joined_data = top_recommendations.join(data_movies['genres'], on='item')
    joined_data = joined_data.join(data_movies['title'], on='item')
    print('joined data ItemItem', joined_data)

    rec_movies_ids = set(top_recommendations['item'])
    print('rec_movies_ids', rec_movies_ids)

    rec_movies =  Movie.query.filter(Movie.id.in_(rec_movies_ids)).all()

    return rec_movies, rec_movies_ids


def recommendReWatch(userid):
    # function returning movies that user has already seen
    rated_movies = MovieRating.query.filter_by(user_id=userid).all()
    print('rated_movies', rated_movies)
    rated_movie_ids = set(rating.movie_id for rating in rated_movies)
    print('rated_movie_ids', rated_movie_ids)
    rec_rewatch = Movie.query.filter(Movie.id.in_(rated_movie_ids)).all()
    
    return rec_rewatch, rated_movie_ids


def recommendMostPopular(data_ratings, data_movies):
    
    # ratings = MovieRating.query.all()
    # movies = Movie.query.all()
    # data = pd.DataFrame([(rating.user_id, rating.movie_id, rating.rating) for rating in ratings], columns=['user', 'item', 'rating'])
    # data_movies = pd.DataFrame([(movie.id, movie.title, movie.genres) for movie in movies], columns=['item', 'title' , 'genres'])

    minimum_to_include = 15

    average_ratings = (data_ratings).groupby(['item']).mean()
    rating_counts = (data_ratings).groupby(['item']).count()
    average_ratings = average_ratings.loc[rating_counts['rating'] > minimum_to_include]
    sorted_avg_ratings = average_ratings.sort_values(by="rating", ascending=False)

    # joined_data = sorted_avg_ratings.join(data_movies['genres'], on='item')
    # joined_data = joined_data.join(data_movies['title'], on='item')
    # most_popular = joined_data.head(amount_recs)
    # print(most_popular)

    most_popular = sorted_avg_ratings.head(amount_recs).reset_index()
    #print(most_popular)

    rec_movies_ids = set(most_popular['item'])
    #print('rec_movies_ids', rec_movies_ids)

    rec_movies =  Movie.query.filter(Movie.id.in_(rec_movies_ids)).all()

    return rec_movies, rec_movies_ids






     
    