import pandas as pd 
import numpy as np
from numpy.linalg import norm
import random
from models import MovieRating, Movie, User, db
from lenskit.algorithms import Recommender
from lenskit.algorithms.user_knn import UserUser
from lenskit.algorithms.item_knn import ItemItem
from lenskit.algorithms.ranking import TopN


def recommendRandomMovies(amount_recs):

    random_movies = Movie.query.order_by(db.func.random()).limit(amount_recs).all()
    random_movie_ids = [movie.id for movie in random_movies]
    
    return random_movies, random_movie_ids

def recommendMostPopular(data_ratings, data_movies):

    minimum_to_include = 15

    average_ratings = (data_ratings).groupby(['item']).mean()
    rating_counts = (data_ratings).groupby(['item']).count()
    average_ratings = average_ratings.loc[rating_counts['rating'] > minimum_to_include]
    sorted_avg_ratings = average_ratings.sort_values(by="rating", ascending=False)

    most_popular = sorted_avg_ratings.head(amount_recs).reset_index()
    #print(most_popular)

    rec_movies_ids = set(most_popular['item'])
    #print('rec_movies_ids', rec_movies_ids)

    rec_movies =  Movie.query.filter(Movie.id.in_(rec_movies_ids)).all()

    return rec_movies, rec_movies_ids


def recommendCosine(user_id, ratings):
    # User User collaborative filtering with cosine similarity as comparison measure

    print('Recommend for user: ' + str(user_id))
    ratings_user = MovieRating.query.filter_by(user_id = user_id).all()
    #print(ratings_user)

    ratings_user_list = []
    for rating_object in ratings_user:
        ratings_user_list.append(rating_object.movie_id)
    #print(ratings_user_list)

    # query all users with at least 5 same movies and put the same movie ids in a dict with the other user.id as key.
    compare_with_list = []
    unshared_with_list = []
    users = User.query.all()
    for user in users:
        ratings_other = MovieRating.query.filter_by(user_id = user.id).all()
        ratings_other_list = []
        for rating_object in ratings_other:
            ratings_other_list.append(rating_object.movie_id)
        #print('other list' + str(set(ratings_other_list)))
        # only continue with this user, if that user has seen more movies than the other
        # print('how many unshared did other watch ' + str(user.id)+  ' :' + str(len(set(ratings_other_list).difference(set(ratings_user_list)))))
        # print(str((set(ratings_other_list).difference(set(ratings_user_list)))))
        unshared = set(ratings_other_list).difference(set(ratings_user_list))
        if len(unshared) > 0:
            unshared_with_list.append([[user.id], unshared ])
            rating_present_in_both = set(ratings_user_list).intersection(set(ratings_other_list))
            # print('Intersection ' + str(user.id) + ' and ' + str(user_id) + str(rating_present_in_both))
            if (len(rating_present_in_both) >= 5):
                # turn rating id set into list to assure rating comparison is based on same movie
                compare_with_list.append([[user.id], sorted(rating_present_in_both)])
    #print('Compare_with-list: ' + str(compare_with_list))
    #print('Unshared_with-list: ' + str(unshared_with_list))

    # store the cosine similarities between the chosen users and current user based on their same movies
    cosine_comparison_dict = {}

    def cosine(ratings1, ratings2):
        cosine_similarity = np.dot(ratings1,ratings2)/(norm(ratings1)*norm(ratings2))
        return cosine_similarity
    
    # retrieve the ratings of the users for the same movies
    ratings_other = []
    ratings_current = []
    for element in compare_with_list:
        other_id = element[0][0]
        same_movies = element[1]
        for movie in same_movies:
            rating_object_user = MovieRating.query.filter_by(user_id = user_id, movie_id = movie).first()
            rating_current = rating_object_user.rating
            # print('current_rating ' + rating_current)
            ratings_current.append(rating_current)
            rating_object_other = MovieRating.query.filter_by(user_id = other_id, movie_id = movie).first()
            rating_other = rating_object_other.rating
            # print('other_rating ' + rating_other)
            ratings_other.append(rating_other)
            #print('rating_other vector ' + str(ratings_other))
            #print('rating_current vector ' + str(ratings_current))
            sim = cosine(ratings_current, ratings_other)
            # print(sim)
            cosine_comparison_dict[other_id] = sim
    #print('cosine sim dict: ' + str(cosine_comparison_dict))

    # sort to identify the top 5 most similar other users
    cosine_comparison_dict = sorted(cosine_comparison_dict.items(), key=lambda x:x[1])
    # print('cosine sim dict sorted : ' + str(cosine_comparison_dict))

    # retrieve top 5 similar 
    top_5 = cosine_comparison_dict[-6:-1]
    print(top_5) 
    top_ids = []
    for e in top_5:
        top_ids.append(e[0])
    print(top_ids)

    # retrieve their unshared movie ids with the current user and store the ones rated higher than 4
    recommend_ids = []
    for elem in unshared_with_list:
        for top_id in top_ids:
            if elem[0][0] == top_id:
                for id in elem[1]:
                    #print(elem)
                    rating = MovieRating.query.filter_by(user_id = top_id, movie_id = id).first().rating
                    #print('Rating of user '+ str(top_id) + ' for movie ' + str(id) + ' :' + str(rating))
                    if rating >= 4.5:
                        recommend_ids.append(id)
    # print('recommend_ids', recommend_ids)

    # throw out doubles
    recommend_ids = set(recommend_ids)
    #print('recommend ids set' + str(recommend_ids))

    rec_cosine = Movie.query.filter(Movie.id.in_(recommend_ids)).all()
    # print('rec_cosine', rec_cosine)

    return rec_cosine, recommend_ids


amount_recs = 20

def recommendUserUser(user_id, data_ratings, data_movies):

    print('Preparations running...')
    # convert data for lenskit usage
    ratings = MovieRating.query.all()
    data_ratings = pd.DataFrame([(rating.user_id, rating.movie_id, rating.rating) for rating in ratings], columns=['user', 'item', 'rating'])

    # Collaborative Fitlering User-User similarity
    user_user = UserUser(15, min_nbrs=3, feedback='explicit') # define min and max of users as neighbours
    algo_user = Recommender.adapt(user_user)
    algo_user.fit(data_ratings)
    # Create a mapping between abstract and original item IDs...didn't work
    # original_to_abstract_mapping_user = {original_id: abstract_id for abstract_id, original_id in enumerate(algo_user.item_index_)}
    print('setup lenskit User-User algorithm')
     
    top_recommendations = algo_user.recommend(user_id, amount_recs)
    #print('top_recommendations', top_recommendations)

    joined_data = top_recommendations.join(data_movies['genres'], on='item')
    joined_data = joined_data.join(data_movies['title'], on='item')
    #TODO: find out why predicted scores fall outside the range of 0-5??
    #print('joined_data_UserUserAlgo', joined_data)

    rec_movies_ids = set(top_recommendations['item'])
    print('rec_movies_ids', rec_movies_ids)
    rec_movies =  Movie.query.filter(Movie.id.in_(rec_movies_ids)).all()

    # rec_movies_ids = [original_to_abstract_mapping.get(abstract_id) for abstract_id in top_recommendations['item']]
    # rec_movies = Movie.query.filter(Movie.id.in_(rec_movies_ids)).all()

    return rec_movies, rec_movies_ids


def recommendItemItem(item_id, data_ratings, data_movies):

    print('Preparations running...')
    # convert data for lenskit usage
    ratings = MovieRating.query.all()
    data_ratings = pd.DataFrame([(rating.user_id, rating.movie_id, rating.rating) for rating in ratings], columns=['user', 'item', 'rating'])

    # Collaborative Fitlering Item-Item similarity
    item_item = ItemItem(15, min_nbrs=3, feedback='explicit')
    algo_item = Recommender.adapt(item_item)
    algo_item.fit(data_ratings)
    # Create a mapping between abstract and original item IDs...didnt work
    # original_to_abstract_mapping_item = {original_id: abstract_id for abstract_id, original_id in enumerate(algo_item.item_index_)}
    print('setup lenskit Item-Item algorithm')

    top_recommendations = algo_item.recommend(item_id, amount_recs)
    print('top_recommendations', top_recommendations)

    joined_data = top_recommendations.join(data_movies['genres'], on='item')
    joined_data = joined_data.join(data_movies['title'], on='item')
    print('joined_data_ItemItemAlgo', joined_data)

    rec_movies_ids = set(top_recommendations['item'])
    print('rec_movies_ids', rec_movies_ids)
    rec_movies =  Movie.query.filter(Movie.id.in_(rec_movies_ids)).all()

    # rec_movies_ids = [original_to_abstract_mapping.get(abstract_id) for abstract_id in top_recommendations['item']]
    # rec_movies = Movie.query.filter(Movie.id.in_(rec_movies_ids)).all()

    return rec_movies, rec_movies_ids
    

def recommendReWatch(userid):
    # function returning movies that user has already seen
    rated_movies = MovieRating.query.filter_by(user_id=userid).all()
    #print('rated_movies', rated_movies)
    rated_movie_ids = set(rating.movie_id for rating in rated_movies)
    #print('rated_movie_ids', rated_movie_ids)
    rec_rewatch = Movie.query.filter(Movie.id.in_(rated_movie_ids)).all()
    
    return rec_rewatch, rated_movie_ids






     
    