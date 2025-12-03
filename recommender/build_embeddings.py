"""
Build embeddings for books using SentenceTransformers
"""
import pickle
import pandas as pd
from pathlib import Path
import sys
import os

# Ensure we're in the project directory
project_dir = Path(__file__).parent.parent
os.chdir(project_dir)

# Add parent directory to path for imports
sys.path.insert(0, str(project_dir))

from app import create_app
from extensions import db
from models.book_model import Book
from config import Config
from sentence_transformers import SentenceTransformer
import numpy as np


def build_embeddings():
    """Build and save book embeddings"""
    app = create_app()
    
    with app.app_context():
        csv_path = Path('data/books.csv')
        if csv_path.exists():
            print("Importing books from CSV to database...")
            df = pd.read_csv(csv_path, low_memory=False)
            df.columns = df.columns.str.lower().str.strip()
            title_col = None
            author_col = None
            for col in ['title', 'book_title', 'name', 'book_name']:
                if col in df.columns:
                    title_col = col
                    break
            for col in ['author', 'authors', 'author_name', 'writer']:
                if col in df.columns:
                    author_col = col
                    break
            if not title_col:
                print("No title column found in CSV")
            else:
                imported = 0
                for _, row in df.iterrows():
                    title = str(row.get(title_col, '')).strip()
                    author = str(row.get(author_col, 'Unknown')).strip() if author_col else 'Unknown'
                    if not title or title == 'nan':
                        continue
                    description = str(row.get('description', row.get('desc', ''))).strip() or None
                    genres = str(row.get('genres', row.get('tags', row.get('genre', '')))).strip() or None
                    avg_rating = float(row.get('average_rating', row.get('avg_rating', 0))) if pd.notna(row.get('average_rating', row.get('avg_rating', None))) else 0.0
                    ratings_count = int(row.get('ratings_count', row.get('num_ratings', 0))) if pd.notna(row.get('ratings_count', row.get('num_ratings', None))) else 0
                    year = int(row.get('publication_year', row.get('year', row.get('publication_date', 0)))) if pd.notna(row.get('publication_year', row.get('year', row.get('publication_date', None)))) else None
                    language = str(row.get('language_code', row.get('language', ''))).strip() or None
                    book = Book.query.filter_by(title=title, author=author).first()
                    if book:
                        if description:
                            book.description = description
                        if genres:
                            book.genres = genres
                        if year:
                            book.year = year
                        if language:
                            book.language = language
                        book.avg_rating = avg_rating
                        book.ratings_count = ratings_count
                        book.source = 'goodreads'
                    else:
                        book = Book(
                            title=title,
                            author=author,
                            description=description,
                            genres=genres,
                            avg_rating=avg_rating,
                            ratings_count=ratings_count,
                            year=year,
                            language=language,
                            source='goodreads'
                        )
                        db.session.add(book)
                        imported += 1
                db.session.commit()
                print(f"Imported {imported} new books from CSV")
        print("Reading books from database...")
        books = Book.query.all()
        books_data = []
        for book in books:
            text = f"{book.title} by {book.author}"
            if book.description:
                text += f". {book.description}"
            books_data.append({
                'id': book.id,
                'text': text,
                'title': book.title,
                'author': book.author
            })
        
        if not books_data:
            print("No books found. Please add books first.")
            return
        
        print(f"Processing {len(books_data)} books...")
        
        # Load SentenceTransformer model
        print("Loading SentenceTransformer model (this may take a moment on first run)...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Extract texts
        texts = [b['text'] for b in books_data]
        
        # Generate embeddings in batches
        print("Generating embeddings...")
        batch_size = 32
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = model.encode(batch, show_progress_bar=False)
            embeddings.append(batch_embeddings)
            print(f"Processed {min(i + batch_size, len(texts))}/{len(texts)} books...")
        
        embeddings = np.vstack(embeddings)
        
        # Create index mapping (book_id -> index)
        books_index = {b['id']: idx for idx, b in enumerate(books_data)}
        
        # Save embeddings and index
        print(f"Saving embeddings to {Config.EMBEDDINGS_PATH}...")
        with open(Config.EMBEDDINGS_PATH, 'wb') as f:
            pickle.dump(embeddings, f)
        
        print(f"Saving index to {Config.BOOKS_INDEX_PATH}...")
        with open(Config.BOOKS_INDEX_PATH, 'wb') as f:
            pickle.dump(books_index, f)
        
        print(f"Successfully built embeddings for {len(books_data)} books!")
        print(f"Embeddings shape: {embeddings.shape}")


if __name__ == '__main__':
    build_embeddings()

