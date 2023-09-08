from abc import ABC, abstractmethod


class DataManagerInterface(ABC):
    """deals with ,movie app generic data"""

    @abstractmethod
    def list_all_users(self) -> dict:
        pass

    @abstractmethod
    def list_user_movies(self) -> dict:
        pass

    @abstractmethod
    def list_user_movies(self, user_id) -> dict:
        pass

    @abstractmethod
    def add_user(self) -> dict:
        pass

    @abstractmethod
    def add_movie(self, user_id) -> dict:
        pass

    @abstractmethod
    def update_movie(self, user_id, movie_id) -> dict:
        pass

    @abstractmethod
    def delete_movie(self, user_id, movie_id) -> dict:
        pass

    @abstractmethod
    def delete_user(self, user_id) -> dict:
        pass


