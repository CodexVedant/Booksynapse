"""
Flask application factory
"""
from flask import Flask
from config import Config
from extensions import db, migrate, bcrypt, login_manager
from threading import Timer
import os
import webbrowser


def create_app():
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from models.user_model import User
        return User.query.get(int(user_id))
    
    # Register blueprints (import inside to avoid circular imports)
    from user.routes import user_bp
    from admin.routes import admin_bp
    from models.tag_model import Tag, BookTag
    
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Create database tables
    with app.app_context():
        # Ensure instance directory exists before creating tables
        from pathlib import Path
        instance_dir = Path('instance')
        instance_dir.mkdir(exist_ok=True)
        db.create_all()
    
    # Routes
    @app.route('/health')
    def health():
        """Health check endpoint"""
        return {'status': 'ok', 'message': 'AI-Book-Recommender is running'}
    
    return app


if __name__ == '__main__':
    app = create_app()
    
    # Auto-open browser after 1 second
    def open_browser():
        webbrowser.open('http://127.0.0.1:5000')
    
    # Avoid double-opening with reloader
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        Timer(1.0, open_browser).start()
    
    # Run app
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

