# Models package - import all models to register with SQLAlchemy
from .user_model import User
from .book_model import Book
from .rating_model import Rating, Favorite, Feedback

__all__ = ['User', 'Book', 'Rating', 'Favorite', 'Feedback']

