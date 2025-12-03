"""
Create admin user script
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app
from extensions import db
from models.user_model import User
from config import Config


def create_admin():
    """Create admin user from environment variables"""
    # Ensure we're in the project directory
    import os
    from pathlib import Path
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    app = create_app()
    
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Check if admin already exists
        admin = User.query.filter_by(username=Config.ADMIN_USERNAME).first()
        
        if admin:
            print(f"Admin user '{Config.ADMIN_USERNAME}' already exists.")
            if admin.is_admin:
                print("User is already an admin.")
            else:
                admin.is_admin = 1
                db.session.commit()
                print("User promoted to admin.")
            return
        
        # Create new admin user
        admin = User(
            username=Config.ADMIN_USERNAME,
            email=Config.ADMIN_EMAIL,
            is_admin=1
        )
        admin.set_password(Config.ADMIN_PASSWORD)
        
        try:
            db.session.add(admin)
            db.session.commit()
            print(f"Admin user '{Config.ADMIN_USERNAME}' created successfully!")
            print(f"Email: {Config.ADMIN_EMAIL}")
            print(f"Password: {Config.ADMIN_PASSWORD}")
            print("\nPlease change the password after first login.")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin user: {e}")
            sys.exit(1)


if __name__ == '__main__':
    create_admin()

