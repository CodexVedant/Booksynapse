from datetime import datetime
from extensions import db


class Book(db.Model):
    __tablename__ = 'books'
    
    id = db.Column(db.Integer, primary_key=True)
    goodreads_book_id = db.Column(db.Integer, nullable=True, index=True)
    title = db.Column(db.String(500), nullable=False, index=True)
    author = db.Column(db.String(300), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    genres = db.Column(db.String(500), nullable=True)  # semicolon-separated
    avg_rating = db.Column(db.Float, default=0.0, nullable=False)
    ratings_count = db.Column(db.Integer, default=0, nullable=False)
    year = db.Column(db.Integer, nullable=True)
    language = db.Column(db.String(50), nullable=True)
    source = db.Column(db.String(100), nullable=True)  # e.g., 'goodreads', 'manual'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    ratings = db.relationship('Rating', backref='book', lazy='dynamic', cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='book', lazy='dynamic', cascade='all, delete-orphan')
    feedbacks = db.relationship('Feedback', backref='book', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_genres_list(self):
        if not self.genres:
            return []
        return [g.strip() for g in self.genres.split(';') if g.strip()]
    
    def __repr__(self):
        return f'<Book {self.title} by {self.author}>'

