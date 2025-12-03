"""
Hybrid recommender: combines content-based filtering (CBF) and collaborative filtering (CF)
"""
import pickle
import numpy as np
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from extensions import db
from models.book_model import Book
from models.rating_model import Rating
from config import Config
import logging

logger = logging.getLogger(__name__)


class HybridRecommender:
    """Hybrid recommendation engine"""
    
    def __init__(self):
        self.embeddings = None
        self.books_index = None
        self.index_books = None  # reverse mapping
        self.cf_matrix = None
        self.user_index = None
        self.item_index = None
    
    def load_artifacts(self):
        """Load embeddings, index, and CF matrix"""
        try:
            # Load embeddings
            if Config.EMBEDDINGS_PATH.exists():
                with open(Config.EMBEDDINGS_PATH, 'rb') as f:
                    self.embeddings = pickle.load(f)
                logger.info(f"Loaded embeddings: {self.embeddings.shape}")
            else:
                logger.warning("Embeddings file not found")
            
            # Load books index
            if Config.BOOKS_INDEX_PATH.exists():
                with open(Config.BOOKS_INDEX_PATH, 'rb') as f:
                    self.books_index = pickle.load(f)
                # Create reverse mapping
                self.index_books = {v: k for k, v in self.books_index.items()}
                logger.info(f"Loaded books index: {len(self.books_index)} books")
            else:
                logger.warning("Books index file not found")
            
            # Load CF matrix (optional)
            if Config.CF_MATRIX_PATH.exists():
                with open(Config.CF_MATRIX_PATH, 'rb') as f:
                    cf_data = pickle.load(f)
                    self.cf_matrix = cf_data.get('matrix')
                    self.user_index = cf_data.get('user_index')
                    self.item_index = cf_data.get('item_index')
                logger.info("Loaded collaborative filtering matrix")
            else:
                logger.info("CF matrix not found, will use CBF only")
        
        except Exception as e:
            logger.error(f"Error loading artifacts: {e}")
            raise
    
    def recommend_by_text(self, query_emb, top_k=12):
        """Recommend books based on text query embedding"""
        if self.embeddings is None or self.books_index is None:
            return []
        
        # Compute cosine similarity
        similarities = cosine_similarity([query_emb], self.embeddings)[0]
        
        # Get top-K indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Get book IDs and scores
        results = []
        app = create_app()
        with app.app_context():
            for idx in top_indices:
                if idx in self.index_books:
                    book_id = self.index_books[idx]
                    book = Book.query.get(book_id)
                    if book:
                        results.append({
                            'id': book.id,
                            'title': book.title,
                            'author': book.author,
                            'genres': book.genres or '',
                            'score': float(similarities[idx])
                        })
        
        return results
    
    def recommend_similar_books(self, book_id, top_k=12):
        """Find similar books based on content"""
        if self.embeddings is None or self.books_index is None:
            return []
        
        if book_id not in self.books_index:
            return []
        
        book_idx = self.books_index[book_id]
        book_emb = self.embeddings[book_idx]
        
        # Compute similarities
        similarities = cosine_similarity([book_emb], self.embeddings)[0]
        
        # Exclude the book itself
        similarities[book_idx] = -1
        
        # Get top-K
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        app = create_app()
        with app.app_context():
            for idx in top_indices:
                if idx in self.index_books:
                    similar_book_id = self.index_books[idx]
                    if similar_book_id != book_id:
                        book = Book.query.get(similar_book_id)
                        if book:
                            results.append({
                                'id': book.id,
                                'title': book.title,
                                'author': book.author,
                                'genres': book.genres or '',
                                'score': float(similarities[idx])
                            })
        
        return results
    
    def recommend_collaborative(self, user_id, top_k=12):
        """Collaborative filtering recommendations"""
        if self.cf_matrix is None or self.user_index is None or self.item_index is None:
            return []
        
        if user_id not in self.user_index:
            return []
        
        user_idx = self.user_index[user_id]
        user_ratings = self.cf_matrix[user_idx]
        
        # Simple item-based CF: find items similar to user's rated items
        # For now, return top-rated items by other users with similar preferences
        # This is a simplified version
        
        # Get items user hasn't rated
        unrated_items = np.where(user_ratings == 0)[0]
        
        if len(unrated_items) == 0:
            return []
        
        # Compute item-item similarity (simplified)
        item_scores = np.zeros(len(unrated_items))
        
        for i, item_idx in enumerate(unrated_items):
            # Find users who rated this item
            item_ratings = self.cf_matrix[:, item_idx]
            rated_by = np.where(item_ratings > 0)[0]
            
            if len(rated_by) > 0:
                # Average rating for this item
                item_scores[i] = np.mean(item_ratings[rated_by])
        
        # Get top-K items
        top_item_indices = np.argsort(item_scores)[::-1][:top_k]
        
        results = []
        app = create_app()
        with app.app_context():
            for item_idx in top_item_indices:
                actual_item_idx = unrated_items[item_idx]
                if actual_item_idx in self.item_index:
                    book_id = self.item_index[actual_item_idx]
                    book = Book.query.get(book_id)
                    if book:
                        results.append({
                            'id': book.id,
                            'title': book.title,
                            'author': book.author,
                            'genres': book.genres or '',
                            'score': float(item_scores[item_idx])
                        })
        
        return results
    
    def recommend_hybrid(self, user_id=None, book_id=None, query_emb=None, top_k=12):
        """Hybrid recommendations combining CBF and CF"""
        results = []
        
        # Content-based recommendations
        cbf_results = []
        if book_id:
            cbf_results = self.recommend_similar_books(book_id, top_k=top_k * 2)
        elif query_emb is not None:
            cbf_results = self.recommend_by_text(query_emb, top_k=top_k * 2)
        else:
            # Fallback: top-rated books
            app = create_app()
            with app.app_context():
                books = Book.query.order_by(Book.avg_rating.desc()).limit(top_k).all()
                cbf_results = [{'id': b.id, 'title': b.title, 'author': b.author, 
                              'genres': b.genres or '', 'score': b.avg_rating} for b in books]
        
        # Collaborative filtering recommendations
        cf_results = []
        if user_id:
            cf_results = self.recommend_collaborative(user_id, top_k=top_k * 2)
        
        # Merge results with weighting (0.6 CBF + 0.4 CF)
        score_dict = {}
        
        # Add CBF results
        for item in cbf_results:
            book_id = item['id']
            if book_id not in score_dict:
                score_dict[book_id] = {'item': item, 'cbf_score': item['score'], 'cf_score': 0.0}
            else:
                score_dict[book_id]['cbf_score'] = item['score']
        
        # Add CF results
        for item in cf_results:
            book_id = item['id']
            if book_id not in score_dict:
                score_dict[book_id] = {'item': item, 'cbf_score': 0.0, 'cf_score': item['score']}
            else:
                score_dict[book_id]['cf_score'] = item['score']
        
        # Calculate hybrid scores
        for book_id, data in score_dict.items():
            hybrid_score = 0.6 * data['cbf_score'] + 0.4 * data['cf_score']
            data['item']['score'] = hybrid_score
        
        # Sort by hybrid score and return top-K
        sorted_results = sorted(score_dict.values(), key=lambda x: x['item']['score'], reverse=True)
        results = [r['item'] for r in sorted_results[:top_k]]
        
        return results

