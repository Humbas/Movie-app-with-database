from flask import Flask, render_template, session, request, redirect, url_for
from datamanager import sqlite_data_manager
from sqlalchemy import create_engine
from datamanager.accessory_data import API_KEY
import requests

SQLITE_URI = 'sqlite:///data/moviwebapp.db'

data_manager = sqlite_data_manager.SQLiteDataManager(SQLITE_URI)

engine = create_engine(SQLITE_URI)

app = Flask(__name__)


# accessory functions

def deal_with_lenght_all():
    if data_manager.get_all_movies() is None:
        lenght_movies = 0
    else:
        lenght_movies = len(data_manager.get_last_movies())
    return lenght_movies


# main functions

@app.route('/')
def home():
    """shows last movies and allows search by title"""
    movie_lenght = len(data_manager.get_last_movies())
    if request.method == 'GET':
        movie_input = request.args.get('search')  # here query will be the search inputs name
        if movie_input:
            movie_input = str(movie_input)
            movie_results = data_manager.search_movies(movie_input)
            if movie_results:
                message = f"Here you have the following related result(s) for {movie_input} in the database."
                return render_template('home.html', movies=movie_results,
                                       user_lenght=len(data_manager.list_all_users()), message=message,
                                       users=data_manager.list_all_users(),
                                       lenght=movie_lenght)
            else:
                message = f"There is no movie named {movie_input} in the database. Try again."
                movie_results = data_manager.get_last_movies()
                # if there is no results, show las 10 entries
                return render_template('home.html', movies=movie_results,
                                       user_lenght=len(data_manager.list_all_users()), message=message,
                                       users=data_manager.list_all_users(), lenght=movie_lenght)
                return movie_results
    # if post is not send, show last 10 entries
    if movie_lenght > 0:
        message = "These are the available movies inserted ordered by title alfabetically"
    else:
        message = "No movies available at this point"
    movie_results = data_manager.get_last_movies()
    return render_template('home.html', movies=movie_results, message=message,
                           user_lenght=len(data_manager.list_all_users()), users=data_manager.list_all_users(),
                           lenght=movie_lenght)


@app.route('/users', methods=['GET'])
def user_list():
    """shows users list"""
    if len(data_manager.list_all_users()) > 0:
        message = f"Currently we have {len(data_manager.list_all_users())} users available in the database"
    else:
        message = "There are no available users at this point"
    return render_template('users.html', message=message, user_length=len(data_manager.list_all_users()),
                           users=data_manager.list_all_users())


@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    """adds user to database"""
    number_of_users = len(data_manager.list_all_users())
    if request.method == 'POST':
        if not request.form['name']:
            message = "Please insert a username"
        else:
            username = request.form['name']
            if request.form['about']:
                about = request.form['about']
            else:
                about = f"No info about {request.form['name']}"
            if data_manager.check_if_username_exists(username):
                message = f" User {username} already exists!"
            else:
                message = f'Username {username} successfully inserted'
                data_manager.add_user(username, about)
                # refresh
                data_manager.list_all_users()

        return render_template('add_user.html', message=message,
                               user_length=number_of_users, users=data_manager.list_all_users())

    # not post
    if number_of_users > 0:
        message = f"Currently we have {number_of_users} users available in the database"
    else:
        message = "There are no available users at this point"
    return render_template('add_user.html', message=message, user_length=number_of_users,
                           users=data_manager.list_all_users())


@app.route('/users/<user_id>/add_movie', methods=['GET', 'POST'])
def add_movie(user_id):
    """adds a movie to a certain user"""
    if data_manager.check_if_user_id_exists(user_id) is None:
        return render_template('user_not_found.html'), 404
    number_of_users = len(data_manager.list_all_users())
    username = data_manager.get_user_name(user_id)
    movies = data_manager.get_user_movies(user_id)
    movie_length = len(data_manager.get_user_movies(user_id))
    message = f"{username} has currently {movie_length} movie(s) available. "

    if request.method == 'POST':
        if request.form['title'] and request.form['director'] and request.form['rating'] and request.form['year']:
            Title = request.form['title']
            Director = request.form['director']
            Rating = float(request.form['rating'])
            Year = int(request.form['year'])
            url_movie = f'https://omdbapi.com/?apikey={API_KEY}&s={Title}'
            data = requests.get(url_movie)
            data.raise_for_status()
            response = requests.get(url_movie).json()
            if response['Response'] == 'False':
                message += f" {Title} is a movie that does not exist. Try again"
            else:
                if data_manager.check_if_movie_exists(Title, user_id):
                    message += f"This movie already exists in {data_manager.get_user_name(user_id)} list, try another"
                else:
                    message = "movie added successfully!"
                    data_manager.add_movie(Title, Director, Rating, Year, user_id)
                    # refresh user list on submisson
                    movies = data_manager.get_user_movies(user_id)
        else:
            message += "Fill all fileds properly!."
    else:
        message += " Fill the form to add a movie. The image will be added automatically."

    return render_template('add_movie.html', movies=movies, message=message,
                           user_length=number_of_users, users=data_manager.list_all_users(), movie_lenght=movie_length,
                           username=username,
                           user_id=user_id)


@app.route('/users/<user_id>', methods=['GET'])
def list_user_movies(user_id):
    """shows movie list by user"""
    if data_manager.check_if_user_id_exists(user_id) is None:
        return render_template('user_not_found.html'), 404
    number_of_users = len(data_manager.list_all_users())
    username = data_manager.get_user_name(user_id)
    movies = data_manager.get_user_movies(user_id)
    movie_length = len(data_manager.get_user_movies(user_id))
    message = f" There are {movie_length} movies in {username} list."
    return render_template('user_movies.html', movies=movies, message=message,
                           user_length=number_of_users,
                           users=data_manager.list_all_users(), movie_lenght=movie_length, username=username,
                           user_id=user_id)


@app.route('/users/<user_id>/delete', methods=['GET', 'POST'])
def delete_user(user_id):
    """delete user and its movies from database"""
    number_of_users = len(data_manager.list_all_users())
    lenght_movies = len(data_manager.get_user_movies(user_id))
    if request.method == 'GET':
        if data_manager.check_if_user_id_exists(user_id) is None:
            return render_template('user_not_found.html'), 404
        message = f"User and his/her movies successfully deleted!"
        data_manager.delete_user(int(user_id))

        return render_template('add_user.html', movies=data_manager.get_all_movies(), message=message,
                               user_length=number_of_users, users=data_manager.list_all_users(),
                               lenght=lenght_movies)
    message = f"Currently we have {number_of_users} users available in the database"
    return render_template('add_user.html', movies=data_manager.get_all_movies(), message=message,
                           user_length=number_of_users,
                           users=data_manager.list_all_users(), lenght=lenght_movies)


@app.route('/users/<user_id>/delete_movie/<movie_id>', methods=['GET', 'POST'])
def delete_movie(user_id, movie_id):
    """deletes a certain movie from a certain user database"""
    if data_manager.check_if_user_id_exists(user_id) is None:
        return render_template('user_not_found.html'), 404
    if data_manager.check_if_movie_id_exists(movie_id) is None:
        return render_template('movie_not_found.html'), 404
    number_of_users = len(data_manager.list_all_users())
    username = data_manager.get_user_name(user_id)
    message = f"movie successfully deleted!"
    # refresh
    data_manager.get_user_movies(user_id)
    data_manager.delete_movie(int(movie_id), int(user_id))
    return render_template('user_movies.html', movies=data_manager.get_user_movies(user_id), message=message,
                           user_length=number_of_users,
                           users=data_manager.list_all_users(), username=username,
                           lenght=len(data_manager.get_last_movies()))


@app.route('/users/<user_id>/movie/<movie_id>/update_movie', methods=['GET', 'POST'])
def update_movie(user_id, movie_id):
    """updates movie data based on user and movie id. Changes image if the title changes"""
    if data_manager.check_if_user_id_exists(user_id) is None:
        return render_template('user_not_found.html'), 404
    if data_manager.check_if_movie_id_exists(movie_id) is None:
        return render_template('movie_not_found.html'), 404
        # functions for all situations
    number_of_users = len(data_manager.list_all_users())
    lenght_movies = len(data_manager.get_user_movies(user_id))
    if request.method == 'POST':
        if request.form['title'] and request.form['director'] and request.form['rating'] and request.form['year']:
            movie_title = request.form['title']
            director = request.form['director']
            rating = float(request.form['rating'])
            year = int(request.form['year'])
            # check if the movie indeed exists
            url_movie = f'https://omdbapi.com/?apikey={API_KEY}&s={movie_title}'
            data = requests.get(url_movie)
            data.raise_for_status()
            response = requests.get(url_movie).json()
            if response['Response'] == 'False':
                message = f" Movie updated. {movie_title} is a movie that does not exist. We are keeping the older image. Thanks for " \
                          f"nothing."
            else:
                message = "Movie updated! Thanks."
            data_manager.update_movie(movie_title, director, rating, year, user_id, movie_id)
            #refresh
            data_manager.get_user_movies(user_id)
        #post
        return render_template('update_movie.html', movies=data_manager.get_user_movies(user_id),
                               year=year,
                               director=director,
                               rating=rating,
                               movie_title=movie_title, message=message, user_length=number_of_users,
                               users=data_manager.list_all_users(), lenght=lenght_movies,
                               username=data_manager.get_user_name(user_id))
        # if post is not set
    movie_title = data_manager.movie_title(movie_id)
    director = data_manager.movie_director(movie_id)
    rating = data_manager.movie_rating(movie_id)
    year = data_manager.movie_year(movie_id)
    message = f"Use the following form to change all or any of the film {data_manager.movie_title(movie_id)} items"
    return render_template('update_movie.html', movies=data_manager.get_user_movies(user_id),
                           year=year,
                           director=director,
                           rating=rating,
                           movie_title=movie_title, message=message, user_length=number_of_users,
                           users=data_manager.list_all_users(), lenght=lenght_movies,
                           username=data_manager.get_user_name(user_id))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
