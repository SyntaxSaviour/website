from typing import Generator
from sqlalchemy.orm import Session
from app.core.database import SessionLocal

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Mock admin user dependency until Ashutosh merges JWT auth
def get_current_admin_user():
    return {"id": 1, "email": "admin@brainmint.com", "role": "admin"}