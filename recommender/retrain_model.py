"""
Retrain recommendation model: rebuild embeddings and CF matrix
"""
import sys
import os
from pathlib import Path

# Ensure we're in the project directory
project_dir = Path(__file__).parent.parent
os.chdir(project_dir)

# Add parent directory to path
sys.path.insert(0, str(project_dir))

from app import create_app
from extensions import db
from models.book_model import Book
from models.rating_model import Rating
from models.user_model import User
from config import Config
import pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def build_cf_matrix():
    """Build collaborative filtering matrix"""
    app = create_app()
    
    with app.app_context():
        # Get all users and books
        users = User.query.all()
        books = Book.query.all()
        
        if not users or not books:
            print("Not enough data for CF matrix. Need users and books.")
            return
        
        # Create mappings
        user_index = {user.id: idx for idx, user in enumerate(users)}
        item_index = {book.id: idx for idx, book in enumerate(books)}
        
        # Build user-item matrix
        matrix = np.zeros((len(users), len(books)))
        
        ratings = Rating.query.all()
        for rating in ratings:
            if rating.user_id in user_index and rating.book_id in item_index:
                user_idx = user_index[rating.user_id]
                item_idx = item_index[rating.book_id]
                matrix[user_idx, item_idx] = rating.rating
        
        # Save CF matrix
        cf_data = {
            'matrix': matrix,
            'user_index': user_index,
            'item_index': item_index
        }
        
        with open(Config.CF_MATRIX_PATH, 'wb') as f:
            pickle.dump(cf_data, f)
        
        print(f"Built CF matrix: {matrix.shape}")
        print(f"Users: {len(users)}, Books: {len(books)}")


def retrain():
    """Main retrain function"""
    print("Starting model retraining...")
    
    # Step 1: Rebuild embeddings
    print("\nStep 1: Building embeddings...")
    try:
        from recommender.build_embeddings import build_embeddings
        build_embeddings()
    except Exception as e:
        print(f"Error building embeddings: {e}")
        return
    
    # Step 2: Build CF matrix
    print("\nStep 2: Building collaborative filtering matrix...")
    try:
        build_cf_matrix()
    except Exception as e:
        print(f"Error building CF matrix: {e}")
        return
    
    print("\nModel retraining completed successfully!")


if __name__ == '__main__':
    retrain()

