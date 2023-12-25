import csv
from sqlalchemy.exc import IntegrityError
from models import Movie, MovieGenre, MovieLink, MovieTag, User, MovieRating

def check_and_read_data(db):
    # only want to recreate a specific model part and not recreate all other as well? -> query the model and delete all.
    # E.g. Delete all existing...(uncomment what should get recreated)
    # User.query.delete()
    # MovieRating.query.delete() # needs to be recreated together with User model

    # Movie.query.delete()
    # MovieGenre.query.delete() # needs to get recreated together with Movie model
    
    # MovieLink.query.delete()
    # MovieTag.query.delete() 
    

    # check if we have Users in the database
    # read data if database is empty
    if User.query.count() == 0:
        # read users and ratings from csv
        with open('data/ratings.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            count = 0
            for row in reader:
                if count > 0 and count <9001: # only read the first 9000 not 100.000
                    try:
                        user_id = row[0]
                        movie_id = row[1]
                        rated = row[2]
                        timestamp = row[3]

                        # Check if the user already exists
                        user = User.query.filter_by(id=user_id).first()
                        # print('user object', user)

                        if user:
                            # User already exists, add a new rating to their ratings
                            try:
                                rating = MovieRating(user_id=user_id, movie_id=movie_id, rating=rated, timestamp=timestamp)
                                db.session.add(rating)
                                user.ratings.append(rating)
                            except IntegrityError:
                                print('Rating already exists: '+ rating)
                                db.session.rollback()
                                pass
                        else:
                            # User doesn't exist, create a new user with the first rating
                            user = User(id=user_id, active=False, username='Username{}'.format(user_id), first_name='Old{}'.format(user_id), last_name= 'Name{}'.format(user_id), password='Te$t{}'.format(user_id))
                            db.session.add(user)                            
                            try:
                                rating = MovieRating(user_id=user_id, movie_id=movie_id, rating=rated, timestamp=timestamp)
                                db.session.add(rating)
                                user.ratings.append(rating)
                            except IntegrityError:
                                print('Rating already exists: '+ rating)
                                db.session.rollback()
                                pass
                                
                        db.session.commit()

                    except IntegrityError:
                        print("Integrity error, tries to create an already existing user: " + user_id) # shouldn't ever happen
                        db.session.rollback()
                        pass

                count += 1
                if count % 100 == 0:
                    print(count, " ratings read")
                
    # check if we have movies in the database
    # read data if database is empty
    if Movie.query.count() == 0:
        # read movies from csv
        with open('data/movies.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            count = 0
            for row in reader:
                if count > 0:
                    try:
                        id = row[0]
                        title = row[1]
                        movie = Movie(id=id, title=title)
                        db.session.add(movie)
                        genres = row[2].split('|')  # genres is a list of genres
                        for genre in genres:  # add each genre to the movie_genre table
                            movie_genre = MovieGenre(movie_id=id, genre=genre)
                            db.session.add(movie_genre)
                        db.session.commit()  # save data to database
                    except IntegrityError:
                        print("Ignoring duplicate movie: " + title)
                        db.session.rollback()
                        pass
                count += 1
                if count % 100 == 0:
                    print(count, " movies read")
    
    # check if we have links in the database
    # read data if database is empty
    if MovieLink.query.count() == 0:
        # read links from csv
        with open('data/links.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            count = 0
            for row in reader:
                if count > 0:
                    try:
                        movie_id = row[0]
                        imdbld = row[1]
                        tmdbld = row[2]
                        link = MovieLink(movie_id = movie_id, imdbld = imdbld, tmdbld = tmdbld)
                        db.session.add(link)
                        db.session.commit()  # save data to database
                    except IntegrityError:
                        print("Ignoring duplicate movie: " + movie_id)
                        db.session.rollback()
                        pass
                count += 1
                if count % 100 == 0:
                    print(count, " links read")
    
    # check if we have tags in the database
    # read data if database is empty
    if MovieTag.query.count() == 0:
        # read tags from csv
        with open('data/tags.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            count = 0
            for row in reader:
                if count > 0:
                    try:
                        # id automatic?
                        user_id = row[0]
                        movie_id = row[1]
                        tag = row[2]
                        timestamp = row[3]
                        tagging = MovieTag(user_id = user_id, movie_id = movie_id, tag = tag, timestamp = timestamp)
                        db.session.add(tagging)
                        db.session.commit()  # save data to database
                    except IntegrityError:
                        print("Integrity error tagging: " + user_id + movie_id + tag)
                        db.session.rollback()
                        pass
                count += 1
                if count % 100 == 0:
                    print(count, " tags read")

    
    