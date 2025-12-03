#Booksynapse: AI-Powered-Sementic-Book-Recommender

A complete Flask-based book recommendation system with hybrid recommendation engine (content-based filtering + collaborative filtering) using SentenceTransformers.

## Features

- **User Authentication**: Registration, login, and session management
- **Book Search**: Search books by title, author, or genre
- **Rating System**: Users can rate books (1-5 stars) and write reviews
- **Favorites**: Bookmark favorite books
- **Hybrid Recommendations**: 
  - Content-based filtering using SentenceTransformers embeddings
  - Collaborative filtering based on user ratings
  - Hybrid scoring (60% CBF + 40% CF)
- **Admin Panel**: Full admin interface with AdminLTE 3
  - Dashboard with statistics
  - Add/Edit/Delete books
  - CSV import (Goodreads-compatible)
  - Model retraining
- **CSV Import**: Robust import system that handles various column formats

## Requirements

- Python 3.10-3.12
- Virtual environment (venv)

## Installation

### 1. Create Virtual Environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

**Note**: On first run, SentenceTransformers will download the `all-MiniLM-L6-v2` model (~90MB). This requires an internet connection.

### 3. Configure Environment

Copy `.env.example` to `.env` and update values:

```powershell
copy .env.example .env
```

Edit `.env` and set:
- `SECRET_KEY`: Change to a secure random string
- `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`: Admin credentials

### 4. Create Admin User

```powershell
python create_admin.py
```

This creates an admin user from the `.env` variables.

### 5. Seed Demo Books (Optional)

```powershell
python seed_books.py
```

Adds 5 demo books if the database is empty.

## Running the Application

### Start the Flask Server

```powershell
python app.py
```

The application will:
- Start on `http://127.0.0.1:5000`
- Automatically open your browser
- Create the database in `instance/ai_book_recommender.db`

### Access Points

- **Homepage**: http://127.0.0.1:5000/
- **Admin Dashboard**: http://127.0.0.1:5000/admin/dashboard (requires admin login)
- **Health Check**: http://127.0.0.1:5000/health

## Building Recommendations

### 1. Build Embeddings

After adding books (via admin panel or CSV import), build embeddings:

```powershell
python recommender/build_embeddings.py
```

This creates:
- `data/embeddings.pkl`: Book embeddings
- `data/books_index.pkl`: Book ID to index mapping

### 2. Retrain Model (Full)

Rebuilds embeddings and collaborative filtering matrix:

```powershell
python recommender/retrain_model.py
```

Creates:
- `data/embeddings.pkl`
- `data/books_index.pkl`
- `data/cf_matrix.pkl`: Collaborative filtering matrix

**Note**: Retraining may take several minutes for large datasets.

## CSV Import Format

The CSV import is flexible and supports various column names:

### Required Columns
- **Title**: `title`, `book_title`, `name`, `book_name`
- **Author**: `author`, `authors`, `author_name`, `writer`

### Optional Columns
- **Description**: `description`, `desc`
- **Genres**: `genres`, `tags`, `genre` (semicolon-separated)
- **Rating**: `average_rating`, `avg_rating`
- **Year**: `publication_year`, `year`, `publication_date`
- **Language**: `language_code`, `language`

### Example CSV

```csv
title,author,average_rating,publication_year,language_code,genres
The Great Gatsby,F. Scott Fitzgerald,4.2,1925,en,"Fiction;Classic"
1984,George Orwell,4.5,1949,en,"Fiction;Dystopian"
```

## Project Structure

```
AI-Book-Recommender/
├── app.py                 # Flask app factory
├── config.py              # Configuration
├── extensions.py          # Flask extensions
├── create_admin.py        # CLI: Create admin user
├── seed_books.py          # CLI: Seed demo books
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── README.md             # This file
├── instance/             # Database (created automatically)
├── data/                 # Data files
│   ├── raw/             # CSV uploads
│   ├── embeddings.pkl   # Generated embeddings
│   ├── books_index.pkl   # Book index
│   └── cf_matrix.pkl    # CF matrix
├── models/              # Database models
│   ├── user_model.py
│   ├── book_model.py
│   └── rating_model.py
├── user/                # User routes
│   └── routes.py
├── admin/                # Admin routes
│   └── routes.py
├── recommender/          # Recommendation engine
│   ├── build_embeddings.py
│   ├── hybrid_recommender.py
│   └── retrain_model.py
├── templates/           # Jinja2 templates
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── book_details.html
│   ├── recommendations.html
│   ├── admin_base.html
│   ├── admin_dashboard.html
│   ├── admin_edit_book.html
│   └── admin_upload.html
└── static/              # Static files
    ├── style.css
    └── adminlte/        # AdminLTE assets
```

## Usage Workflow

1. **Setup**: Install dependencies, create admin user
2. **Add Books**: Use admin panel to add books or upload CSV
3. **Build Embeddings**: Run `build_embeddings.py` after adding books
4. **Users Register**: Users can register and rate books
5. **Get Recommendations**: Users see personalized recommendations
6. **Retrain**: Periodically retrain model as more ratings are added

## Troubleshooting

### Import Errors

If you see circular import errors:
- Ensure blueprints are imported inside `create_app()` function
- Check that all `__init__.py` files exist

### Missing Embeddings

If recommendations show fallback books:
- Run `python recommender/build_embeddings.py`
- Ensure books exist in database

### AdminLTE Not Loading

- Verify `static/adminlte/` contains CSS/JS files
- Check browser console for 404 errors
- Ensure AdminLTE assets were copied correctly

### SentenceTransformers Download

On first run, the model downloads automatically. If it fails:
- Check internet connection
- The model is cached in `~/.cache/torch/sentence_transformers/`

## Development

### Database Migrations

```powershell
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### Testing

Run basic tests:

```powershell
python -c "from app import create_app; a=create_app(); print('OK', type(a))"
```

## License

This project is provided as-is for educational purposes.

## Notes

- The recommender uses a simple hybrid approach. For production, consider more sophisticated CF algorithms.
- FAISS is optional but recommended for faster similarity search on large datasets.
- The first model download may take a few minutes depending on internet speed.

