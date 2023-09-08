from datamanager.data_manager_interface import DataManagerInterface
from sqlalchemy import create_engine, text
from datamanager.accessory_data import API_KEY
import requests


# main class
class SQLiteDataManager(DataManagerInterface):
    def __init__(self, filename):
        # constructors
        self.filename = filename
        self.engine = create_engine(filename, connect_args={"timeout": 30})

    # methods

    def commit_query(self, query, param=''):
        """establishes query and commit when changes happen"""
        with  self.engine.connect() as connection:
            query = text(query)
            connection.execute(query, param)
            connection.commit()

    def get_query(self, query, param=''):
        """establishes query and connection"""
        with  self.engine.connect() as connection:
            query = text(query)
            query_results = connection.execute(query, param)
            connection.commit()
            get_results = query_results.fetchall()
            return get_results

    def get_user_list_movie_lenght(self, user):
        """get users movie length"""
        params = {'user': user}
        result = self.get_query("SELECT user_id, id FROM movies WHERE user_id = :user ORDER BY id DESC", params)
        return len(result)

    def make_query_user(self, query, params):
        """make query related with users"""
        get_results = self.get_query(query, params)
        results = []
        if len(get_results) == 0:
            results = []
        else:
            for result in get_results:
                result = {
                    'user_id': result[0],
                    'name': result[1],
                    'about': result[2],
                    'number_movies': result[3]
                }
                results.append(result)
        return results

    def get_all_movies(self):
        """simply returns all movies independently of user"""
        params = {}
        query = "SELECT * FROM movies ORDER BY id DESC "
        return self.make_query_movie(query, params)

    def make_query_movie(self, query, params):
        """make query related with movies"""
        get_results = self.get_query(query, params)
        results = []

        if len(get_results) == 0:
            results = []
        else:
            for result in get_results:
                result = {
                    'id': result[0],
                    'title': result[1],
                    'image': result[2],
                    'rating': float(result[3]),
                    'director': result[4],
                    'year': result[5],
                    'user_id': int(result[6])
                }
                results.append(result)
        return results

    def get_last_movies(self):
        """simply returns last 10 inserted movies, independently of user"""
        params = {}
        query = "SELECT * FROM movies ORDER BY title ASC LIMIT 10"
        return self.make_query_movie(query, params)

    def list_user_movies(self, user_id):
        """returns list of movies per user"""
        params = {'user_id': user_id}
        query = "SELECT * FROM movies WHERE user_id = :user_id ORDER BY title ASC"
        return self.make_query_movie(query, params)

    def search_movies(self, user_input):
        """returns list of movies where the input matches"""
        params = {'user_input': str('%') + user_input + str('%')}
        query = "SELECT * FROM movies WHERE title LIKE :user_input ORDER BY title ASC"
        return self.make_query_movie(query, params)

    def list_all_users(self):
        """returns a list of users"""
        params = {}
        query = "SELECT * FROM user ORDER BY name ASC"
        return self.make_query_user(query, params)

    def delete_user(self, user_id):
        """deletes user and its films"""
        params = {'user_id': user_id}
        query = "DELETE FROM user WHERE user_id = :user_id"
        query_user_movies = "DELETE FROM movies WHERE user_id = :user_id"
        self.commit_query(query, params)
        self.commit_query(query_user_movies, params)
        return self.list_all_users()

    def get_user_movies(self, user_id):
        """returns movies that belong to certain user"""
        params = {'user_id': user_id}
        query = "SELECT * FROM movies WHERE user_id = :user_id ORDER BY title DESC"
        self.make_query_movie(query, params)
        return self.list_user_movies(user_id)

    def add_user(self, username, about):
        """adds user to database"""
        params = {'id': id, 'username': username, 'about': about}
        query = "INSERT INTO user (name, about) VALUES ( :username, :about)"
        self.commit_query(query, params)
        return self.list_all_users()

    def get_user_name(self, user_id):
        """returns a name string of the given user"""
        params = {'user_id': user_id}
        query = "SELECT * FROM user WHERE user_id = :user_id"
        results = self.make_query_user(query, params)
        name = results[0]['name']
        return name

    def add_movie(self, Title, Director, Rating, Year, user_id):
        """adds a movie to current user list"""
        Year = int(Year)
        Rating = float(Rating)
        url_movie = f'https://omdbapi.com/?apikey={API_KEY}&s={Title}'
        data = requests.get(url_movie)
        data.raise_for_status()
        response = requests.get(url_movie).json()
        if response['Response'] == 'False':
            return 'Please write a valid movie name'
        image = response['Search'][0]['Poster']
        params = {'title': Title, 'image': image, 'director': Director, 'rating': Rating, 'year': Year,
                  'user_id': user_id}
        params_count = {'user_id': user_id}
        query = "INSERT INTO movies (title, image, director, rating, year, user_id) VALUES ( :title, :image, " \
                ":director, :rating, :year, :user_id)"
        query_insert_movie_count = "UPDATE user SET number_movies = number_movies + 1 WHERE user_id = :user_id"
        self.commit_query(query, params)
        self.commit_query(query_insert_movie_count, params_count)
        return self.list_user_movies(user_id)

    def delete_movie(self, movie_id, user_id):
        """deletes movie from user list"""
        params = {'movie_id': movie_id, 'user_id': user_id}
        params_count = {'user_id': user_id}
        query = "DELETE FROM movies WHERE id = :movie_id AND user_id = :user_id"
        query_substract_movie_count = "UPDATE user SET number_movies = number_movies - 1 WHERE user_id = :user_id"
        self.commit_query(query, params)
        self.commit_query(query_substract_movie_count, params_count)
        return self.list_user_movies(user_id)

    def check_if_movie_exists(self, movie_title, user_id):
        """checks is movie already exists in user list"""
        current_movies = self.list_user_movies(user_id)
        movie_titles = []
        for movie in current_movies:
            movie_titles.append(movie['title'])
        if movie_title in movie_titles:
            return True

    def check_if_username_exists(self, username):
        """checks if username already exists in user list"""
        current_users = self.list_all_users()
        usernames = []
        for user in current_users:
            usernames.append(user['name'])
        if username in usernames:
            return True

    def check_if_user_id_exists(self, user_id):
        """checks if user id exists """
        current_users = self.list_all_users()
        user_ids = []
        for user in current_users:
            ids = str(user['user_id'])
            user_ids.append(ids)
        if user_id in user_ids:
            return True

    def check_if_movie_id_exists(self, movie_id):
        """checks if movie id exist """
        all_movies = self.get_all_movies()
        movie_ids = []
        for movie in all_movies:
            id_movie = str(movie['id'])
            movie_ids.append(id_movie)
        if movie_id in movie_ids:
            return True

    def movie_title(self, movie_id):
        """returns a string of movie title"""
        all_movies = self.get_all_movies()
        for movie in all_movies:
            id_movie = str(movie['id'])
            if movie_id == id_movie:
                return movie['title']

    def movie_director(self, movie_id):
        """returns a string of movie director"""
        all_movies = self.get_all_movies()
        for movie in all_movies:
            id_movie = str(movie['id'])
            if movie_id == id_movie:
                return movie['director']

    def movie_rating(self, movie_id):
        """returns a float of movie rating"""
        all_movies = self.get_all_movies()
        for movie in all_movies:
            id_movie = str(movie['id'])
            if movie_id == id_movie:
                return float(movie['rating'])

    def movie_year(self, movie_id):
        """returns a int of movie year"""
        all_movies = self.get_all_movies()
        for movie in all_movies:
            id_movie = str(movie['id'])
            if movie_id == id_movie:
                return int(movie['year'])


    def update_movie(self, new_title, new_director, new_rating, new_year, user_id, movie_id):
        """update movie"""
        current_movies = self.list_user_movies(user_id)
        for movie in current_movies:
            if movie_id == str(movie['id']):
                url_movie = f'https://omdbapi.com/?apikey={API_KEY}&s={new_title}'
                data = requests.get(url_movie)
                data.raise_for_status()
                response = requests.get(url_movie).json()
                # change image if the new movie does exist
                if response['Response'] == 'False':
                    new_image = movie['image']
                else:
                    new_image = response['Search'][0]['Poster']
                params = {'title': new_title, 'image': new_image, 'director': new_director, 'rating': new_rating,
                          'year': new_year, 'id': movie_id, 'user_id': user_id}
                query = "UPDATE  movies SET title = :title, image = :image, director = :director, rating = :rating, " \
                        "year = :year WHERE id=:id AND user_id = :user_id"
                self.commit_query(query, params)
                return self.list_user_movies(user_id)
