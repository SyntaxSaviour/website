import sys
<<<<<<< HEAD
import getpass
import argparse
=======
>>>>>>> dfcbd30b9be2441de778c8562dc6a0327756a581
from pathlib import Path

# Add backend directory to python path if running from root
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.models.admin_user import AdminUser
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_initial_admin():
<<<<<<< HEAD
    parser = argparse.ArgumentParser(description="Create a secure admin user.")
    parser.add_argument("email", type=str, help="Admin email address")
    args = parser.parse_args()

    admin_email = args.email
    password = getpass.getpass("Enter admin password (min 10 characters): ")
    
    if len(password) < 10:
        print("Error: Password must be at least 10 characters long.")
        sys.exit(1)

    db = SessionLocal()
    try:
=======
    db = SessionLocal()
    try:
        admin_email = "admin@brainmint.com"
>>>>>>> dfcbd30b9be2441de778c8562dc6a0327756a581
        existing_admin = db.query(AdminUser).filter(AdminUser.email == admin_email).first()
        
        if existing_admin:
            print(f"Admin user {admin_email} already exists!")
            return

<<<<<<< HEAD
        hashed_password = pwd_context.hash(password)
=======
        hashed_password = pwd_context.hash("Admin@12345")
>>>>>>> dfcbd30b9be2441de778c8562dc6a0327756a581
        new_admin = AdminUser(
            email=admin_email,
            hashed_password=hashed_password,
            is_active=True
        )
        db.add(new_admin)
        db.commit()
<<<<<<< HEAD
        print(f"Successfully created admin user: {admin_email}")
=======
        print(f"Successfully created initial admin user: {admin_email} / Admin@12345")
>>>>>>> dfcbd30b9be2441de778c8562dc6a0327756a581
        
    except Exception as e:
        db.rollback()
        print(f"Error creating admin: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_initial_admin()