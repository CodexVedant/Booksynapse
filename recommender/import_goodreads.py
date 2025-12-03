import sys
import os
from pathlib import Path
import pandas as pd
from sqlalchemy.exc import IntegrityError
from app import create_app
from extensions import db
from models.book_model import Book
from models.rating_model import Rating
from models.user_model import User
from models.tag_model import Tag, BookTag
from config import Config

project_dir = Path(__file__).parent.parent
os.chdir(project_dir)
sys.path.insert(0, str(project_dir))

def import_books(path):
    app = create_app()
    with app.app_context():
        if not path:
            return 0
        p = Path(path)
        if not p.exists():
            return 0
        df = pd.read_csv(p, low_memory=False)
        df.columns = df.columns.str.lower().str.strip()
        imported = 0
        for _, row in df.iterrows():
            gr_id = row.get('book_id', row.get('goodreads_book_id', None))
            title = str(row.get('title', '')).strip()
            author = str(row.get('authors', row.get('author', 'Unknown'))).strip()
            if not title:
                continue
            description = str(row.get('description', row.get('desc', ''))).strip() or None
            genres = str(row.get('genres', row.get('tags', row.get('genre', '')))).strip() or None
            avg_rating = float(row.get('average_rating', row.get('avg_rating', 0))) if pd.notna(row.get('average_rating', row.get('avg_rating', None))) else 0.0
            ratings_count = int(row.get('ratings_count', row.get('num_ratings', 0))) if pd.notna(row.get('ratings_count', row.get('num_ratings', None))) else 0
            year = int(row.get('publication_year', row.get('year', row.get('publication_date', 0)))) if pd.notna(row.get('publication_year', row.get('year', row.get('publication_date', None)))) else None
            language = str(row.get('language_code', row.get('language', ''))).strip() or None
            book = None
            if gr_id is not None and pd.notna(gr_id):
                try:
                    gr_id_int = int(gr_id)
                except Exception:
                    gr_id_int = None
                if gr_id_int is not None:
                    book = Book.query.filter_by(goodreads_book_id=gr_id_int).first()
            if not book:
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
                if gr_id is not None and pd.notna(gr_id):
                    try:
                        book.goodreads_book_id = int(gr_id)
                    except Exception:
                        pass
                book.avg_rating = avg_rating
                book.ratings_count = ratings_count
                book.source = 'goodreads'
            else:
                book = Book(
                    goodreads_book_id=int(gr_id) if gr_id is not None and pd.notna(gr_id) else None,
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
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        return imported

def ensure_users(user_ids):
    created = 0
    for uid in user_ids:
        u = User.query.get(uid)
        if not u:
            username = f"gr_{uid}"
            email = f"gr_{uid}@example.com"
            u = User(id=uid, username=username, email=email, password_hash='x', is_admin=0)
            db.session.add(u)
            created += 1
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
    return created

def import_ratings(path, limit=0):
    app = create_app()
    with app.app_context():
        if not path:
            return 0
        p = Path(path)
        if not p.exists():
            return 0
        imported = 0
        total = 0
        chunks = pd.read_csv(p, low_memory=False, chunksize=100000)
        for chunk in chunks:
            chunk.columns = chunk.columns.str.lower().str.strip()
            if 'user_id' not in chunk.columns or 'book_id' not in chunk.columns or 'rating' not in chunk.columns:
                continue
            if limit and total >= limit:
                break
            if limit:
                remaining = max(0, limit - total)
                chunk = chunk.head(remaining)
            user_ids = set(int(u) for u in chunk['user_id'].tolist())
            ensure_users(user_ids)
            for _, row in chunk.iterrows():
                try:
                    uid = int(row['user_id'])
                    gid = int(row['book_id'])
                    r = int(row['rating'])
                except Exception:
                    continue
                book = Book.query.filter_by(goodreads_book_id=gid).first()
                bid = book.id if book else None
                if not bid:
                    continue
                existing = Rating.query.filter_by(user_id=uid, book_id=bid).first()
                if existing:
                    existing.rating = r
                else:
                    rating = Rating(user_id=uid, book_id=bid, rating=r)
                    db.session.add(rating)
                    imported += 1
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
            total += len(chunk)
        return imported

def import_tags(path):
    app = create_app()
    with app.app_context():
        p = Path(path)
        if not p.exists():
            return 0
        df = pd.read_csv(p, low_memory=False)
        df.columns = df.columns.str.lower().str.strip()
        imported = 0
        name_col = 'tag_name' if 'tag_name' in df.columns else 'name'
        id_col = 'tag_id' if 'tag_id' in df.columns else None
        for _, row in df.iterrows():
            name = str(row.get(name_col, '')).strip()
            if not name:
                continue
            existing = Tag.query.filter_by(name=name).first()
            if existing:
                continue
            if id_col and pd.notna(row.get(id_col, None)):
                try:
                    tid = int(row.get(id_col))
                except Exception:
                    tid = None
            else:
                tid = None
            if tid is not None:
                tag = Tag(id=tid, name=name)
            else:
                tag = Tag(name=name)
            db.session.add(tag)
            imported += 1
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        return imported

def import_book_tags(path):
    app = create_app()
    with app.app_context():
        p = Path(path)
        if not p.exists():
            return 0
        df = pd.read_csv(p, low_memory=False)
        df.columns = df.columns.str.lower().str.strip()
        imported = 0
        # Goodbooks-10k uses 'goodreads_book_id', 'tag_id', 'count'
        if 'goodreads_book_id' not in df.columns or 'tag_id' not in df.columns:
            return 0
        for _, row in df.iterrows():
            try:
                gid = int(row['goodreads_book_id'])
                tid = int(row['tag_id'])
                cnt = int(row.get('count', 0)) if pd.notna(row.get('count', None)) else 0
            except Exception:
                continue
            book = Book.query.filter_by(goodreads_book_id=gid).first()
            bid = book.id if book else None
            if not bid:
                continue
            existing = BookTag.query.filter_by(book_id=bid, tag_id=tid).first()
            if existing:
                existing.count = cnt
            else:
                bt = BookTag(book_id=bid, tag_id=tid, count=cnt)
                db.session.add(bt)
                imported += 1
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        return imported

def main():
    books_path = Config.GOODREADS_BOOKS_PATH
    ratings_path = Config.GOODREADS_RATINGS_PATH
    tags_path = Config.GOODREADS_TAGS_PATH
    book_tags_path = Config.GOODREADS_BOOK_TAGS_PATH
    limit = Config.GOODREADS_RATINGS_LIMIT
    b = import_books(books_path)
    r = import_ratings(ratings_path, limit)
    t = 0
    bt = 0
    if tags_path:
        t = import_tags(tags_path)
    if book_tags_path:
        bt = import_book_tags(book_tags_path)
    print(f"Books imported: {b}")
    print(f"Ratings imported: {r}")
    print(f"Tags imported: {t}")
    print(f"Book-Tag links imported: {bt}")

if __name__ == '__main__':
    main()
