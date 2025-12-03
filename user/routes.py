"""
User-facing routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models.user_model import User
from models.book_model import Book
from models.rating_model import Rating, Favorite, Feedback
from sqlalchemy import or_, func

user_bp = Blueprint('user', __name__, template_folder='../templates')


def update_book_rating_stats(book_id):
    """Recalculate average rating and count for a book"""
    book = Book.query.get_or_404(book_id)
    ratings = Rating.query.filter_by(book_id=book_id).all()
    
    if ratings:
        book.avg_rating = sum(r.rating for r in ratings) / len(ratings)
        book.ratings_count = len(ratings)
    else:
        book.avg_rating = 0.0
        book.ratings_count = 0
    
    db.session.commit()


@user_bp.route('/')
def index():
    """Homepage with search form and optional book list"""
    books = None
    query = request.args.get('q', '').strip()
    
    if query:
        # Search across title, author, genres
        search_filter = or_(
            Book.title.ilike(f'%{query}%'),
            Book.author.ilike(f'%{query}%'),
            Book.genres.ilike(f'%{query}%')
        )
        books = Book.query.filter(search_filter).limit(50).all()
    else:
        # Show top-rated books by default
        books = Book.query.order_by(Book.avg_rating.desc(), Book.ratings_count.desc()).limit(20).all()
    
    return render_template('index.html', books=books, query=query)


@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('user.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
            return render_template('register.html')
        
        # Create user
        user = User(username=username, email=email)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash('Registration successful!', 'success')
            return redirect(url_for('user.index'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('register.html')


@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('user.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            
            # Redirect to admin dashboard if admin
            if user.is_admin:
                return redirect(next_page or url_for('admin.dashboard'))
            
            return redirect(next_page or url_for('user.index'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html')


@user_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('user.index'))


@user_bp.route('/search')
def search():
    """Search books with optional genre filtering"""
    query = request.args.get('q', '').strip()
    genres_param = request.args.get('genres', '').strip()
    
    filters = []
    if query:
        filters.append(or_(
            Book.title.ilike(f'%{query}%'),
            Book.author.ilike(f'%{query}%'),
            Book.genres.ilike(f'%{query}%')
        ))
    
    genre_list = []
    if genres_param:
        genre_list = [g.strip() for g in genres_param.split(',') if g.strip()]
        if genre_list:
            genre_filters = [Book.genres.ilike(f'%{g}%') for g in genre_list]
            filters.append(or_(*genre_filters))
    
    query_obj = Book.query
    if filters:
        for f in filters:
            query_obj = query_obj.filter(f)
    
    books = query_obj.order_by(Book.avg_rating.desc(), Book.ratings_count.desc()).limit(50).all()
    
    return render_template('index.html', books=books, query=query)

@user_bp.route('/explore')
def explore():
    """Explore: show random books"""
    count = request.args.get('count', default=12, type=int)
    # SQLite random ordering
    books = Book.query.order_by(func.random()).limit(count).all()
    return render_template('index.html', books=books, query='')

@user_bp.route('/api/search')
def api_search():
    q = request.args.get('q', '').strip()
    genres_param = request.args.get('genres', '').strip()
    filters = []
    if q:
        t = q.lower()
        mood_map = {
            'cozy': ['cozy','comfort','heartwarming','warm','gentle','wholesome','feel-good'],
            'thrilling': ['thrilling','suspense','fast-paced','tense','gripping','page-turner'],
            'thought-provoking': ['thought','philosophy','reflective','introspective','provocative','contemplative'],
            'light & funny': ['humor','funny','witty','lighthearted','comedy','hilarious','satirical'],
            'sad': ['sad','melancholic','melancholy','grief','poignant','somber','tragic','heartbreaking','tear-jerker'],
            'happy': ['happy','joyful','cheerful','uplifting','feel-good'],
            'hopeful': ['hopeful','optimistic','inspiring','encouraging','uplifting'],
            'adventurous': ['adventurous','exciting','exploration','quest','voyage'],
            'romantic': ['romantic','love','heartfelt','passionate'],
            'calm': ['calm','relaxing','soothing','tranquil','peaceful','serene'],
            'anxious': ['anxious','nervous','uneasy','tense','worry'],
            'angry': ['angry','rage','furious','vengeful','wrath'],
            'dark': ['dark','gritty','bleak','noir','grim'],
            'inspiring': ['inspiring','motivational','uplifting','encouraging','empowering'],
            'nostalgic': ['nostalgic','nostalgia','wistful','sentimental']
        }
        terms = [q]
        for k, v in mood_map.items():
            if (k in t) or any(s in t for s in v):
                terms.extend(v + [k])
        if terms:
            term_filters = []
            for term in set(terms):
                term_filters.append(or_(
                    Book.title.ilike(f'%{term}%'),
                    Book.author.ilike(f'%{term}%'),
                    Book.genres.ilike(f'%{term}%'),
                    Book.description.ilike(f'%{term}%')
                ))
            filters.append(or_(*term_filters))
    genre_list = []
    if genres_param:
        genre_list = [g.strip() for g in genres_param.split(',') if g.strip()]
        if genre_list:
            genre_filters = [Book.genres.ilike(f'%{g}%') for g in genre_list]
            filters.append(or_(*genre_filters))
    query_obj = Book.query
    if filters:
        for f in filters:
            query_obj = query_obj.filter(f)
    books = query_obj.order_by(Book.avg_rating.desc(), Book.ratings_count.desc()).limit(50).all()
    return jsonify([
        {
            'id': b.id,
            'title': b.title,
            'author': b.author,
            'genres': b.genres,
            'avg_rating': b.avg_rating,
            'ratings_count': b.ratings_count
        } for b in books
    ])

@user_bp.route('/api/recommendations')
def api_recommendations():
    q = request.args.get('q', '').strip()
    try:
        from recommender.hybrid_recommender import HybridRecommender
        recommender = HybridRecommender()
        recommender.load_artifacts()
        if q:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            query_emb = model.encode([q])[0]
            recs = recommender.recommend_by_text(query_emb, top_k=12)
        else:
            recs = []
        if not recs:
            recs = Book.query.order_by(Book.avg_rating.desc()).limit(12).all()
            return jsonify([
                {'id': b.id, 'title': b.title, 'author': b.author, 'genres': b.genres, 'score': b.avg_rating}
                for b in recs
            ])
        return jsonify(recs)
    except Exception:
        if q:
            t = q.lower()
            mood_map = {
                'cozy': ['cozy','comfort','heartwarming','warm','gentle','wholesome','feel-good'],
                'thrilling': ['thrilling','suspense','fast-paced','tense','gripping','page-turner'],
                'thought-provoking': ['thought','philosophy','reflective','introspective','provocative','contemplative'],
                'light & funny': ['humor','funny','witty','lighthearted','comedy','hilarious','satirical'],
                'sad': ['sad','melancholic','melancholy','grief','poignant','somber','tragic','heartbreaking','tear-jerker'],
                'happy': ['happy','joyful','cheerful','uplifting','feel-good'],
                'hopeful': ['hopeful','optimistic','inspiring','encouraging','uplifting'],
                'adventurous': ['adventurous','exciting','exploration','quest','voyage'],
                'romantic': ['romantic','love','heartfelt','passionate'],
                'calm': ['calm','relaxing','soothing','tranquil','peaceful','serene'],
                'anxious': ['anxious','nervous','uneasy','tense','worry'],
                'angry': ['angry','rage','furious','vengeful','wrath'],
                'dark': ['dark','gritty','bleak','noir','grim'],
                'inspiring': ['inspiring','motivational','uplifting','encouraging','empowering'],
                'nostalgic': ['nostalgic','nostalgia','wistful','sentimental']
            }
            terms = [t]
            for k, v in mood_map.items():
                if (k in t) or any(s in t for s in v):
                    terms.extend(v + [k])
            filters = [or_(
                Book.title.ilike(f'%{term}%'),
                Book.author.ilike(f'%{term}%'),
                Book.genres.ilike(f'%{term}%'),
                Book.description.ilike(f'%{term}%')
            ) for term in set(terms)]
            query_obj = Book.query
            if filters:
                query_obj = query_obj.filter(or_(*filters))
            books = query_obj.order_by(Book.avg_rating.desc(), Book.ratings_count.desc()).limit(12).all()
            return jsonify([
                {'id': b.id, 'title': b.title, 'author': b.author, 'genres': b.genres, 'score': b.avg_rating}
                for b in books
            ])
        books = Book.query.order_by(Book.avg_rating.desc()).limit(12).all()
        return jsonify([
            {'id': b.id, 'title': b.title, 'author': b.author, 'genres': b.genres, 'score': b.avg_rating}
            for b in books
        ])

@user_bp.route('/api/explore')
def api_explore():
    count = request.args.get('count', default=12, type=int)
    books = Book.query.order_by(func.random()).limit(count).all()
    return jsonify([
        {
            'id': b.id,
            'title': b.title,
            'author': b.author,
            'genres': b.genres,
            'avg_rating': b.avg_rating,
            'ratings_count': b.ratings_count
        } for b in books
    ])


@user_bp.route('/book/<int:book_id>')
def book_details(book_id):
    """Book details page"""
    book = Book.query.get_or_404(book_id)
    
    # Get user's rating and favorite status if logged in
    user_rating = None
    is_fav = False
    
    if current_user.is_authenticated:
        user_rating = Rating.query.filter_by(user_id=current_user.id, book_id=book_id).first()
        is_fav = Favorite.query.filter_by(user_id=current_user.id, book_id=book_id).first() is not None
    
    return render_template('book_details.html', book=book, user_rating=user_rating, is_fav=is_fav)


@user_bp.route('/rate/<int:book_id>', methods=['POST'])
@login_required
def rate_book(book_id):
    """Rate a book"""
    book = Book.query.get_or_404(book_id)
    rating_value = request.form.get('rating', type=int)
    review = request.form.get('review', '').strip()
    
    if not rating_value or rating_value < 1 or rating_value > 5:
        flash('Invalid rating. Please select 1-5.', 'error')
        return redirect(url_for('user.book_details', book_id=book_id))
    
    # Find existing rating or create new
    rating = Rating.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    
    if rating:
        rating.rating = rating_value
        if review:
            rating.review = review
    else:
        rating = Rating(
            user_id=current_user.id,
            book_id=book_id,
            rating=rating_value,
            review=review if review else None
        )
        db.session.add(rating)
    
    try:
        db.session.commit()
        update_book_rating_stats(book_id)
        flash('Rating saved!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to save rating.', 'error')
    
    return redirect(url_for('user.book_details', book_id=book_id))


@user_bp.route('/favorite/<int:book_id>', methods=['POST'])
@login_required
def toggle_favorite(book_id):
    """Toggle favorite status"""
    book = Book.query.get_or_404(book_id)
    favorite = Favorite.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    
    if favorite:
        db.session.delete(favorite)
        flash('Removed from favorites.', 'info')
    else:
        favorite = Favorite(user_id=current_user.id, book_id=book_id)
        db.session.add(favorite)
        flash('Added to favorites!', 'success')
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash('Failed to update favorite.', 'error')
    
    return redirect(url_for('user.book_details', book_id=book_id))


@user_bp.route('/feedback/<int:book_id>', methods=['POST'])
@login_required
def submit_feedback(book_id):
    """Submit feedback (like/dislike) for a recommendation"""
    book = Book.query.get_or_404(book_id)
    is_like = request.form.get('is_like', '0') == '1'
    
    # Find existing feedback or create new
    feedback = Feedback.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    
    if feedback:
        feedback.is_like = 1 if is_like else 0
    else:
        feedback = Feedback(
            user_id=current_user.id,
            book_id=book_id,
            is_like=1 if is_like else 0
        )
        db.session.add(feedback)
    
    try:
        db.session.commit()
        flash('Feedback saved!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to save feedback.', 'error')
    
    return redirect(url_for('user.book_details', book_id=book_id))


@user_bp.route('/recommendations')
@login_required
def recommendations():
    """Get personalized recommendations"""
    query = request.args.get('q', '').strip()
    
    # Lazy-load recommender
    try:
        from recommender.hybrid_recommender import HybridRecommender
        recommender = HybridRecommender()
        recommender.load_artifacts()
        
        if query:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            query_emb = model.encode([query])[0]
            recommendations = recommender.recommend_by_text(query_emb, top_k=12)
        elif current_user.id:
            recommendations = recommender.recommend_hybrid(user_id=current_user.id, top_k=12)
        else:
            recommendations = []
        
        # Fallback if no recommendations
        if not recommendations:
            recommendations = Book.query.order_by(Book.avg_rating.desc()).limit(12).all()
            recommendations = [{'id': b.id, 'title': b.title, 'author': b.author, 
                              'genres': b.genres, 'score': b.avg_rating} for b in recommendations]
    
    except Exception as e:
        if query:
            q = query.lower()
            mood_map = {
                'cozy': ['cozy','comfort','heartwarming','warm','gentle','wholesome','feel-good'],
                'thrilling': ['thrilling','suspense','fast-paced','tense','gripping','page-turner'],
                'thought-provoking': ['thought','philosophy','reflective','introspective','provocative','contemplative'],
                'light & funny': ['humor','funny','witty','lighthearted','comedy','hilarious','satirical'],
                'sad': ['sad','melancholic','melancholy','grief','poignant','somber','tragic','heartbreaking','tear-jerker'],
                'happy': ['happy','joyful','cheerful','uplifting','feel-good'],
                'hopeful': ['hopeful','optimistic','inspiring','encouraging','uplifting'],
                'adventurous': ['adventurous','exciting','exploration','quest','voyage'],
                'romantic': ['romantic','love','heartfelt','passionate'],
                'calm': ['calm','relaxing','soothing','tranquil','peaceful','serene'],
                'anxious': ['anxious','nervous','uneasy','tense','worry'],
                'angry': ['angry','rage','furious','vengeful','wrath'],
                'dark': ['dark','gritty','bleak','noir','grim'],
                'inspiring': ['inspiring','motivational','uplifting','encouraging','empowering'],
                'nostalgic': ['nostalgic','nostalgia','wistful','sentimental']
            }
            terms = [q]
            for k, v in mood_map.items():
                if (k in q) or any(s in q for s in v):
                    terms.extend(v + [k])
            filters = []
            for t in set(terms):
                filters.append(or_(
                    Book.title.ilike(f'%{t}%'),
                    Book.author.ilike(f'%{t}%'),
                    Book.genres.ilike(f'%{t}%'),
                    Book.description.ilike(f'%{t}%')
                ))
            query_obj = Book.query
            if filters:
                query_obj = query_obj.filter(or_(*filters))
            books = query_obj.order_by(Book.avg_rating.desc(), Book.ratings_count.desc()).limit(12).all()
            recommendations = [{'id': b.id, 'title': b.title, 'author': b.author,
                               'genres': b.genres, 'score': b.avg_rating} for b in books]
        else:
            flash('Recommendation engine unavailable. Showing top-rated books.', 'info')
            books = Book.query.order_by(Book.avg_rating.desc()).limit(12).all()
            recommendations = [{'id': b.id, 'title': b.title, 'author': b.author, 
                              'genres': b.genres, 'score': b.avg_rating} for b in books]
    
    return render_template('recommendations.html', recommendations=recommendations, query=query)


@user_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard - view favorites, ratings, reviews, and feedback"""
    # Get user's favorites with book details
    favorites = db.session.query(Favorite, Book).join(
        Book, Favorite.book_id == Book.id
    ).filter(Favorite.user_id == current_user.id).order_by(
        Favorite.created_at.desc()
    ).all()
    
    # Get user's ratings with book details and reviews
    ratings = db.session.query(Rating, Book).join(
        Book, Rating.book_id == Book.id
    ).filter(Rating.user_id == current_user.id).order_by(
        Rating.created_at.desc()
    ).all()
    
    # Get user's feedback with book details
    feedbacks = db.session.query(Feedback, Book).join(
        Book, Feedback.book_id == Book.id
    ).filter(Feedback.user_id == current_user.id).order_by(
        Feedback.created_at.desc()
    ).all()
    
    # Statistics
    stats = {
        'total_favorites': Favorite.query.filter_by(user_id=current_user.id).count(),
        'total_ratings': Rating.query.filter_by(user_id=current_user.id).count(),
        'total_reviews': Rating.query.filter_by(
            user_id=current_user.id
        ).filter(Rating.review.isnot(None)).count(),
        'total_feedback': Feedback.query.filter_by(user_id=current_user.id).count(),
        'avg_rating_given': db.session.query(func.avg(Rating.rating)).filter_by(
            user_id=current_user.id
        ).scalar() or 0.0
    }
    
    return render_template(
        'user_dashboard.html',
        favorites=favorites,
        ratings=ratings,
        feedbacks=feedbacks,
        stats=stats
    )

