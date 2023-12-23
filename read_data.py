import csv
from sqlalchemy.exc import IntegrityError
from models import Movie, MovieGenre, MovieLink, MovieTag

def check_and_read_data(db):
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
                        print("Integrity error --do i need?: " + user_id + movie_id + tagging)
                        print('tagging id? ' + tagging.id)
                        db.session.rollback()
                        pass
                count += 1
                if count % 100 == 0:
                    print(count, " tags read")
    