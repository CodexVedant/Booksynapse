"""
Admin routes - requires admin authentication
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from extensions import db
from models.book_model import Book
from models.user_model import User
from models.rating_model import Rating
from config import Config
import pandas as pd
import os
from pathlib import Path
import subprocess
from sqlalchemy import or_

admin_bp = Blueprint('admin', __name__, template_folder='../templates')


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'error')
            return redirect(url_for('user.login'))
        return f(*args, **kwargs)
    return decorated_function


def import_csv_to_db(csv_path):
    """Import CSV file to database with robust column mapping"""
    try:
        df = pd.read_csv(csv_path, low_memory=False)
        
        # Normalize column names to lowercase
        df.columns = df.columns.str.lower().str.strip()
        
        # Column mapping (flexible)
        title_col = None
        author_col = None
        
        # Find title column
        for col in ['title', 'book_title', 'name', 'book_name']:
            if col in df.columns:
                title_col = col
                break
        
        # Find author column
        for col in ['author', 'authors', 'author_name', 'writer']:
            if col in df.columns:
                author_col = col
                break
        
        if not title_col:
            return 0, "No title column found in CSV"
        
        if not author_col:
            author_col = 'author'  # default, will be empty if not found
        
        imported = 0
        skipped = 0
        
        for _, row in df.iterrows():
            title = str(row.get(title_col, '')).strip()
            author = str(row.get(author_col, 'Unknown')).strip()
            
            if not title or title == 'nan':
                skipped += 1
                continue
            
            # Get other fields (handle missing columns)
            description = str(row.get('description', row.get('desc', ''))).strip() or None
            genres = str(row.get('genres', row.get('tags', row.get('genre', '')))).strip() or None
            avg_rating = float(row.get('average_rating', row.get('avg_rating', 0))) if pd.notna(row.get('average_rating', row.get('avg_rating', None))) else 0.0
            ratings_count = int(row.get('ratings_count', row.get('num_ratings', 0))) if pd.notna(row.get('ratings_count', row.get('num_ratings', None))) else 0
            year = int(row.get('publication_year', row.get('year', row.get('publication_date', 0)))) if pd.notna(row.get('publication_year', row.get('year', row.get('publication_date', None)))) else None
            language = str(row.get('language_code', row.get('language', ''))).strip() or None
            
            # Upsert: find existing book or create new
            book = Book.query.filter_by(title=title, author=author).first()
            
            if book:
                # Update existing
                if description:
                    book.description = description
                if genres:
                    book.genres = genres
                if year:
                    book.year = year
                if language:
                    book.language = language
                book.source = 'goodreads'
            else:
                # Create new
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
        return imported, f"Successfully imported {imported} books, skipped {skipped} rows"
    
    except Exception as e:
        db.session.rollback()
        return 0, f"Error importing CSV: {str(e)}"


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard with statistics"""
    stats = {
        'books_count': Book.query.count(),
        'users_count': User.query.count(),
        'ratings_count': Rating.query.count(),
        'uploads_count': len(list(Path(Config.UPLOAD_FOLDER).glob('*.csv')))
    }
    
    query = request.args.get('q', '').strip()
    recent_books = []
    search_results = []
    if query:
        search_filter = or_(
            Book.title.ilike(f'%{query}%'),
            Book.author.ilike(f'%{query}%'),
            Book.genres.ilike(f'%{query}%')
        )
        search_results = Book.query.filter(search_filter).order_by(Book.created_at.desc()).limit(50).all()
    else:
        recent_books = Book.query.order_by(Book.created_at.desc()).limit(10).all()
    
    return render_template('admin_dashboard.html', stats=stats, recent_books=recent_books, search_results=search_results, query=query)


@admin_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add_book():
    """Add a new book"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        
        if not title or not author:
            flash('Title and author are required.', 'error')
            return render_template('admin_edit_book.html', book=None)
        
        book = Book(
            title=title,
            author=author,
            description=request.form.get('description', '').strip() or None,
            genres=request.form.get('genres', '').strip() or None,
            year=int(request.form.get('year')) if request.form.get('year') else None,
            language=request.form.get('language', '').strip() or None,
            source='manual'
        )
        
        try:
            db.session.add(book)
            db.session.commit()
            flash('Book added successfully!', 'success')
            return redirect(url_for('admin.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to add book: {str(e)}', 'error')
    
    return render_template('admin_edit_book.html', book=None)


@admin_bp.route('/edit/<int:book_id>', methods=['GET', 'POST'])
@admin_required
def edit_book(book_id):
    """Edit an existing book"""
    book = Book.query.get_or_404(book_id)
    
    if request.method == 'POST':
        book.title = request.form.get('title', '').strip()
        book.author = request.form.get('author', '').strip()
        book.description = request.form.get('description', '').strip() or None
        book.genres = request.form.get('genres', '').strip() or None
        book.year = int(request.form.get('year')) if request.form.get('year') else None
        book.language = request.form.get('language', '').strip() or None
        
        try:
            db.session.commit()
            flash('Book updated successfully!', 'success')
            return redirect(url_for('admin.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to update book: {str(e)}', 'error')
    
    return render_template('admin_edit_book.html', book=book)


@admin_bp.route('/delete/<int:book_id>', methods=['POST'])
@admin_required
def delete_book(book_id):
    """Delete a book"""
    book = Book.query.get_or_404(book_id)
    
    try:
        db.session.delete(book)
        db.session.commit()
        flash('Book deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to delete book: {str(e)}', 'error')
    
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/upload', methods=['GET', 'POST'])
@admin_required
def upload_csv():
    """Upload and import CSV file"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected.', 'error')
            return render_template('admin_upload.html')
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No file selected.', 'error')
            return render_template('admin_upload.html')
        
        if not file.filename.endswith('.csv'):
            flash('Please upload a CSV file.', 'error')
            return render_template('admin_upload.html')
        
        # Save file
        filename = file.filename
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Import to database
        imported, message = import_csv_to_db(filepath)
        
        if imported > 0:
            flash(message, 'success')
        else:
            flash(message, 'error')
        
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin_upload.html')


@admin_bp.route('/retrain', methods=['POST'])
@admin_required
def retrain_model():
    """Retrain recommendation model"""
    try:
        # Run retrain script as subprocess
        script_path = Path(__file__).parent.parent / 'recommender' / 'retrain_model.py'
        result = subprocess.run(
            ['python', str(script_path)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            flash('Model retrained successfully!', 'success')
        else:
            flash(f'Retraining failed: {result.stderr}', 'error')
    
    except subprocess.TimeoutExpired:
        flash('Retraining timed out. This may take a while for large datasets.', 'warning')
    except Exception as e:
        flash(f'Error retraining model: {str(e)}', 'error')
    
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/embpath')
@admin_required
def check_embeddings():
    """Check if embeddings file exists"""
    exists = Config.EMBEDDINGS_PATH.exists()
    return jsonify({'exists': exists, 'path': str(Config.EMBEDDINGS_PATH)})

