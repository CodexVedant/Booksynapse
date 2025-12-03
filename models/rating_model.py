from datetime import datetime
from extensions import db


class Rating(db.Model):

    __tablename__ = 'ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False, index=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    review = db.Column(db.Text, nullable=True)  # optional review text
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Unique constraint: one rating per user per book
    __table_args__ = (db.UniqueConstraint('user_id', 'book_id', name='unique_user_book_rating'),)
    
    def __repr__(self):
        return f'<Rating {self.rating} by user {self.user_id} for book {self.book_id}>'


class Favorite(db.Model):
    __tablename__ = 'favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'book_id', name='unique_user_book_favorite'),)
    
    def __repr__(self):
        return f'<Favorite user {self.user_id} -> book {self.book_id}>'


class Feedback(db.Model):
    __tablename__ = 'feedbacks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False, index=True)
    is_like = db.Column(db.Integer, nullable=False)  # 1 for like, 0 for dislike
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Unique constraint: one feedback per user per book
    __table_args__ = (db.UniqueConstraint('user_id', 'book_id', name='unique_user_book_feedback'),)
    
    def __repr__(self):
        return f'<Feedback user {self.user_id} -> book {self.book_id}: {"like" if self.is_like else "dislike"}>'

