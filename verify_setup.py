"""
Quick verification script to check if the project setup is correct
"""
import sys
from pathlib import Path

print("Verifying AI-Book-Recommender setup...")
print("=" * 50)

# Check critical files
critical_files = [
    'app.py',
    'config.py',
    'extensions.py',
    'create_admin.py',
    'seed_books.py',
    'requirements.txt',
    'models/__init__.py',
    'models/user_model.py',
    'models/book_model.py',
    'models/rating_model.py',
    'user/__init__.py',
    'user/routes.py',
    'admin/__init__.py',
    'admin/routes.py',
    'recommender/__init__.py',
    'recommender/build_embeddings.py',
    'recommender/hybrid_recommender.py',
    'recommender/retrain_model.py',
]

missing_files = []
for file in critical_files:
    if not Path(file).exists():
        missing_files.append(file)

if missing_files:
    print("❌ Missing files:")
    for f in missing_files:
        print(f"   - {f}")
else:
    print("✅ All critical files present")

# Check templates
templates = [
    'templates/index.html',
    'templates/login.html',
    'templates/register.html',
    'templates/book_details.html',
    'templates/recommendations.html',
    'templates/admin_base.html',
    'templates/admin_dashboard.html',
    'templates/admin_edit_book.html',
    'templates/admin_upload.html',
]

missing_templates = []
for template in templates:
    if not Path(template).exists():
        missing_templates.append(template)

if missing_templates:
    print("❌ Missing templates:")
    for t in missing_templates:
        print(f"   - {t}")
else:
    print("✅ All templates present")

# Check AdminLTE assets
adminlte_files = [
    'static/adminlte/css/adminlte.min.css',
    'static/adminlte/js/adminlte.min.js',
    'static/adminlte/plugins/jquery/jquery.min.js',
    'static/adminlte/plugins/bootstrap/js/bootstrap.bundle.min.js',
    'static/adminlte/plugins/fontawesome-free/css/all.min.css',
]

missing_adminlte = []
for file in adminlte_files:
    if not Path(file).exists():
        missing_adminlte.append(file)

if missing_adminlte:
    print("❌ Missing AdminLTE files:")
    for f in missing_adminlte:
        print(f"   - {f}")
else:
    print("✅ AdminLTE assets present")

# Try importing app
print("\nTesting imports...")
try:
    from app import create_app
    app = create_app()
    print("✅ App factory works correctly")
    print(f"   App type: {type(app)}")
except Exception as e:
    print(f"❌ Error creating app: {e}")
    sys.exit(1)

# Check directories
directories = ['instance', 'data/raw', 'static', 'templates', 'models', 'user', 'admin', 'recommender']
missing_dirs = []
for dir_path in directories:
    if not Path(dir_path).exists():
        missing_dirs.append(dir_path)

if missing_dirs:
    print("❌ Missing directories:")
    for d in missing_dirs:
        print(f"   - {d}")
else:
    print("✅ All directories present")

print("\n" + "=" * 50)
print("Verification complete!")
print("\nNext steps:")
print("1. Create virtual environment: python -m venv .venv")
print("2. Activate: .venv\\Scripts\\Activate.ps1")
print("3. Install dependencies: pip install -r requirements.txt")
print("4. Create .env file from .env.example")
print("5. Run: python create_admin.py")
print("6. Run: python seed_books.py")
print("7. Start: python app.py")

