"""Script to create initial users in the database"""
import uuid
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from app.core.auth import AuthManager
from app.core.database import User

def create_initial_users():
    """Create initial admin and user accounts"""
    # Create synchronous engine for this script
    engine = create_engine("postgresql+psycopg2://postgres:postgres@postgres:5432/slide_speaker")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with SessionLocal() as session:
        # Удаляем существующих пользователей
        session.execute(text("DELETE FROM users WHERE email IN ('admin@example.com', 'user@example.com')"))
        
        # Создаем админа
        admin_user = User(
            id=str(uuid.uuid4()),
            email="admin@example.com",
            hashed_password=AuthManager.get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        session.add(admin_user)
        print("Created admin user: admin@example.com / admin123")
        
        # Создаем обычного пользователя
        regular_user = User(
            id=str(uuid.uuid4()),
            email="user@example.com",
            hashed_password=AuthManager.get_password_hash("user123"),
            role="user",
            is_active=True
        )
        session.add(regular_user)
        print("Created regular user: user@example.com / user123")
        
        session.commit()
        print("Initial users created successfully!")

if __name__ == "__main__":
    create_initial_users()
