"""Script to create initial users in the database"""
import uuid
import os
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from app.core.auth import AuthManager
from app.core.database import User

def create_initial_users():
    """Create initial admin and user accounts"""
    # Get database URL from environment
    db_password = os.getenv('POSTGRES_PASSWORD', 'postgres')
    db_url = f"postgresql+psycopg2://postgres:{db_password}@postgres:5432/slide_speaker"
    
    # Create synchronous engine for this script
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with SessionLocal() as session:
        # Проверяем, существуют ли уже пользователи
        existing_admin = session.execute(
            text("SELECT id FROM users WHERE email = 'admin@example.com'")
        ).first()
        
        existing_test = session.execute(
            text("SELECT id FROM users WHERE email = 'test@example.com'")
        ).first()
        
        # Создаем админа только если его нет
        if not existing_admin:
            admin_user = User(
                id=str(uuid.uuid4()),
                email="admin@example.com",
                hashed_password=AuthManager.get_password_hash("admin123"),
                role="admin",
                is_active=True
            )
            session.add(admin_user)
            print("✓ Created admin user: admin@example.com / admin123")
        else:
            print("⊙ Admin user already exists, skipping...")
        
        # Создаем тестового пользователя только если его нет
        if not existing_test:
            test_user = User(
                id=str(uuid.uuid4()),
                email="test@example.com",
                hashed_password=AuthManager.get_password_hash("TestPassword123!"),
                role="user",
                is_active=True
            )
            session.add(test_user)
            print("✓ Created test user: test@example.com / TestPassword123!")
        else:
            print("⊙ Test user already exists, skipping...")
        
        session.commit()
        print("✅ Initial users setup completed!")

if __name__ == "__main__":
    create_initial_users()
