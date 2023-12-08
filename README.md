# RecommenderSystem
-> second project for "AI and the Web" uni course, recommends movies from MovieLens dataset to user

                                   
## Project 2: Build a movie recommender system

Build a personalized recommender system with these components:

    User management, including account creation, login, and logout
    A database component for storing and retrieving movie details and ratings
    A rating function where users can rate movies
    A recommender function that recommends movies according to the user's previous ratings


A list of movies and ratings is to be taken from the Movielens dataset. We use a small version:

Small: 100,000 ratings and 3,600 tag applications applied to 9,000 movies by 600 users. Last updated 9/2018.

    README.html
    ml-latest-small.zip (size: 1 MB)

 

Make the result available on the provided demo server.

Submit the code and the link to the demo deployment.

 

Proposed steps:

Week 1

    setup the base app on your development machine
    play around with the base app and make sure to understand the code
    add database models for the links.csv and tags.csv files
    extend the read_data.py code to populate the database
    extend the views also to show links to movie databases and tags
