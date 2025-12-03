"""
Seed database with demo books if empty
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app import create_app
from extensions import db
from models.book_model import Book


def seed_books():
    """Add demo books if database is empty"""
    # Ensure we're in the project directory
    import os
    from pathlib import Path
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    app = create_app()
    
    with app.app_context():
        # Check if books exist
        if Book.query.count() > 0:
            print("Database already contains books. Skipping seed.")
            return
        
        # Demo books
        demo_books = [
            {
                'title': 'The Great Gatsby',
                'author': 'F. Scott Fitzgerald',
                'description': 'A classic American novel about the Jazz Age and the American Dream.',
                'genres': 'Fiction; Classic; American Literature',
                'year': 1925,
                'language': 'en',
                'avg_rating': 4.2,
                'ratings_count': 1500
            },
            {
                'title': '1984',
                'author': 'George Orwell',
                'description': 'A dystopian social science fiction novel about totalitarian control.',
                'genres': 'Fiction; Dystopian; Science Fiction',
                'year': 1949,
                'language': 'en',
                'avg_rating': 4.5,
                'ratings_count': 2000
            },
            {
                'title': 'To Kill a Mockingbird',
                'author': 'Harper Lee',
                'description': 'A novel about racial inequality and loss of innocence in the American South.',
                'genres': 'Fiction; Classic; Coming of Age',
                'year': 1960,
                'language': 'en',
                'avg_rating': 4.7,
                'ratings_count': 1800
            },
            {
                'title': 'Pride and Prejudice',
                'author': 'Jane Austen',
                'description': 'A romantic novel of manners about Elizabeth Bennet and Mr. Darcy.',
                'genres': 'Fiction; Romance; Classic',
                'year': 1813,
                'language': 'en',
                'avg_rating': 4.4,
                'ratings_count': 1200
            },
            {
                'title': 'The Catcher in the Rye',
                'author': 'J.D. Salinger',
                'description': 'A controversial novel about teenage rebellion and alienation.',
                'genres': 'Fiction; Coming of Age; Classic',
                'year': 1951,
                'language': 'en',
                'avg_rating': 3.8,
                'ratings_count': 900
            }
        ]
        
        try:
            for book_data in demo_books:
                book = Book(**book_data, source='seed')
                db.session.add(book)
            
            db.session.commit()
            print(f"Successfully seeded {len(demo_books)} demo books!")
        except Exception as e:
            db.session.rollback()
            print(f"Error seeding books: {e}")
            sys.exit(1)


if __name__ == '__main__':
    seed_books()

