import pandas as pd 
from models import MovieRating, Movie
from lenskit.algorithms import Recommender
from lenskit.algorithms.user_knn import UserUser
from lenskit.algorithms.item_knn import ItemItem
from lenskit.algorithms.ranking import TopN

amount_recs = 10

#TODO: get the algo fitting out of calling function

def recommendUserUser(user_id):

     # get the ratings data
    ratings = MovieRating.query.all()
    movies = Movie.query.all()

    # for rating in data[:10]:
    #     print(rating.user_id, rating.movie_id, rating.rating)

    # convert to Pandas DataFrame to make accessible for Lenskit
    data = pd.DataFrame([(rating.user_id, rating.movie_id, rating.rating) for rating in ratings], columns=['user', 'item', 'rating'])
    data_movies = pd.DataFrame([(movie.id, movie.title, movie.genres) for movie in movies], columns=['item', 'title' , 'genres'])
    # joined_data = data.join(data_movies['genres'], on='item')
    # joined_data = data.join(data_movies['title'], on='item')

    #print(joined_data.head(10))

    # Collaborative Fitlering User-User similarity
    user_user = UserUser(15, min_nbrs=3, feedback='explicit') # define min and max of users as neighbours
    algo = Recommender.adapt(user_user)
    algo.fit(data)
    print('setup lenskit User-User algorithm')
     
    top_recommendations = algo.recommend(user_id, amount_recs)
    joined_data = top_recommendations.join(data_movies['genres'], on='item')
    joined_data = joined_data.join(data_movies['title'], on='item')
    #TODO: find out why predicted scores fall outside the range of 0-5??
    print(joined_data)

def recommendItemItem(item_id):

    # get the ratings data
    ratings = MovieRating.query.all()
    movies = Movie.query.all()

    # for rating in data[:10]:
    #     print(rating.user_id, rating.movie_id, rating.rating)

    # convert to Pandas DataFrame to make accessible for Lenskit
    data = pd.DataFrame([(rating.user_id, rating.movie_id, rating.rating) for rating in ratings], columns=['user', 'item', 'rating'])
    data_movies = pd.DataFrame([(movie.id, movie.title, movie.genres) for movie in movies], columns=['item', 'title' , 'genres'])

    #print(data.head(10))

    # Collaborative Fitlering Item-Item similarity
    item_item = ItemItem(15, min_nbrs=3, feedback='explicit')
    algo = Recommender.adapt(item_item)
    algo.fit(data)
    print('setup lenskit Item-Item algorithm')

    top_recommendations = algo.recommend(item_id, amount_recs)
    joined_data = top_recommendations.join(data_movies['genres'], on='item')
    joined_data = joined_data.join(data_movies['title'], on='item')
    print(joined_data)

def recommendMostPopular(user_id):
    #TODO: adjust to exclde already seen movies for a user
    ratings = MovieRating.query.all()
    movies = Movie.query.all()
    data = pd.DataFrame([(rating.user_id, rating.movie_id, rating.rating) for rating in ratings], columns=['user', 'item', 'rating'])
    data_movies = pd.DataFrame([(movie.id, movie.title, movie.genres) for movie in movies], columns=['item', 'title' , 'genres'])
 

    # pred = item_knn.ItemItem(10, feebaack='explicit')
    # select = UnratedItemCandidateSelector()
    # topn = TopN(pred, select)

    minimum_to_include = 15

    average_ratings = (data).groupby(['item']).mean()
    rating_counts = (data).groupby(['item']).count()
    average_ratings = average_ratings.loc[rating_counts['rating'] > minimum_to_include]
    sorted_avg_ratings = average_ratings.sort_values(by="rating", ascending=False)
    joined_data = sorted_avg_ratings.join(data_movies['genres'], on='item')
    joined_data = joined_data.join(data_movies['title'], on='item')
    # joined_data = joined_data[joined_data.columns[3:]]

    most_popular = joined_data.head(amount_recs)
    print(most_popular)

     
    