#!/usr/bin/env python3
"""
Скрипт для исправления критических проблем безопасности аутентификации
"""
import secrets
import os
from pathlib import Path


def generate_secrets():
    """Сгенерировать криптографически безопасные секреты"""
    jwt_secret = secrets.token_urlsafe(64)
    csrf_secret = secrets.token_urlsafe(32)
    
    return jwt_secret, csrf_secret


def update_env_file():
    """Обновить .env файл с новыми секретами"""
    env_path = Path(__file__).parent / ".env"
    
    if not env_path.exists():
        print(f"❌ .env file not found at {env_path}")
        return False
    
    # Прочитать текущий .env
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Проверить есть ли уже секреты
    has_jwt_secret = any('JWT_SECRET_KEY=' in line for line in lines)
    has_csrf_secret = any('CSRF_SECRET_KEY=' in line for line in lines)
    
    if has_jwt_secret and has_csrf_secret:
        print("⚠️  Security keys already exist in .env")
        response = input("Do you want to regenerate them? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Aborting. No changes made.")
            return False
    
    # Сгенерировать новые секреты
    print("🔐 Generating cryptographically secure secrets...")
    jwt_secret, csrf_secret = generate_secrets()
    
    # Обновить или добавить секреты
    new_lines = []
    jwt_updated = False
    csrf_updated = False
    
    for line in lines:
        if line.startswith('JWT_SECRET_KEY='):
            new_lines.append(f'JWT_SECRET_KEY={jwt_secret}\n')
            jwt_updated = True
        elif line.startswith('CSRF_SECRET_KEY='):
            new_lines.append(f'CSRF_SECRET_KEY={csrf_secret}\n')
            csrf_updated = True
        else:
            new_lines.append(line)
    
    # Если секретов не было, добавить в конец
    if not jwt_updated or not csrf_updated:
        new_lines.append('\n# Security Keys (GENERATED - DO NOT COMMIT TO GIT)\n')
        if not jwt_updated:
            new_lines.append(f'JWT_SECRET_KEY={jwt_secret}\n')
        if not csrf_updated:
            new_lines.append(f'CSRF_SECRET_KEY={csrf_secret}\n')
    
    # Записать обновлённый .env
    with open(env_path, 'w') as f:
        f.writelines(new_lines)
    
    print(f"✅ Security keys updated in {env_path}")
    print("\n" + "="*60)
    print("⚠️  IMPORTANT: Add .env to .gitignore if not already!")
    print("="*60 + "\n")
    
    return True


def update_auth_py():
    """Обновить auth.py для обязательной проверки секретов"""
    auth_path = Path(__file__).parent / "app" / "core" / "auth.py"
    
    if not auth_path.exists():
        print(f"❌ auth.py not found at {auth_path}")
        return False
    
    with open(auth_path, 'r') as f:
        content = f.read()
    
    # Проверить нужно ли обновление
    if 'raise ValueError("JWT_SECRET_KEY must be set' in content:
        print("✅ auth.py already has security checks")
        return True
    
    # Заменить строку с SECRET_KEY
    old_line = 'SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")'
    
    new_code = '''SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY or SECRET_KEY == "your-secret-key-change-in-production":
    raise ValueError(
        "JWT_SECRET_KEY must be set in .env and cannot be default value. "
        "Generate with: python -c 'import secrets; print(secrets.token_urlsafe(64))'"
    )'''
    
    if old_line in content:
        content = content.replace(old_line, new_code)
        
        with open(auth_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Updated {auth_path} with mandatory secret check")
        return True
    else:
        print(f"⚠️  Could not find expected SECRET_KEY line in {auth_path}")
        return False


def update_csrf_py():
    """Обновить csrf.py для обязательной проверки секретов"""
    csrf_path = Path(__file__).parent / "app" / "core" / "csrf.py"
    
    if not csrf_path.exists():
        print(f"❌ csrf.py not found at {csrf_path}")
        return False
    
    with open(csrf_path, 'r') as f:
        content = f.read()
    
    # Проверить нужно ли обновление
    if 'raise ValueError("CSRF_SECRET_KEY must be set' in content:
        print("✅ csrf.py already has security checks")
        return True
    
    # Заменить секцию с csrf_protection
    old_code = '''# Global CSRF instance
csrf_protection = CSRFProtection(
    secret_key=os.getenv("CSRF_SECRET_KEY", "your-csrf-secret-key-change-in-production"),
    cookie_name="csrf_token",
    header_name="X-CSRF-Token"
)'''
    
    new_code = '''# Global CSRF instance
CSRF_SECRET_KEY = os.getenv("CSRF_SECRET_KEY")
if not CSRF_SECRET_KEY or CSRF_SECRET_KEY == "your-csrf-secret-key-change-in-production":
    raise ValueError(
        "CSRF_SECRET_KEY must be set in .env and cannot be default value. "
        "Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
    )

csrf_protection = CSRFProtection(
    secret_key=CSRF_SECRET_KEY,
    cookie_name="csrf_token",
    header_name="X-CSRF-Token"
)'''
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        
        with open(csrf_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Updated {csrf_path} with mandatory secret check")
        return True
    else:
        print(f"⚠️  Could not find expected csrf_protection code in {csrf_path}")
        return False


def check_gitignore():
    """Проверить что .env в .gitignore"""
    gitignore_path = Path(__file__).parent.parent / ".gitignore"
    
    if not gitignore_path.exists():
        print("⚠️  .gitignore not found in project root")
        return False
    
    with open(gitignore_path, 'r') as f:
        content = f.read()
    
    if '.env' in content or '*.env' in content:
        print("✅ .env is in .gitignore")
        return True
    else:
        print("❌ .env is NOT in .gitignore!")
        print("\n" + "="*60)
        print("⚠️  CRITICAL: Add 'backend/.env' to .gitignore NOW!")
        print("="*60 + "\n")
        return False


def main():
    print("="*60)
    print("🔒 Authentication Security Fix Script")
    print("="*60 + "\n")
    
    print("This script will:")
    print("1. Generate strong JWT and CSRF secret keys")
    print("2. Update backend/.env with new secrets")
    print("3. Update auth.py and csrf.py to enforce secrets")
    print("4. Check .gitignore for .env")
    print()
    
    response = input("Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Aborted by user")
        return
    
    print()
    
    # Шаг 1: Обновить .env
    success = update_env_file()
    if not success:
        print("❌ Failed to update .env file")
        return
    
    # Шаг 2: Обновить auth.py
    update_auth_py()
    
    # Шаг 3: Обновить csrf.py
    update_csrf_py()
    
    # Шаг 4: Проверить .gitignore
    check_gitignore()
    
    print("\n" + "="*60)
    print("✅ Security fixes completed!")
    print("="*60)
    print("\nNext steps:")
    print("1. Restart your backend server")
    print("2. Verify that authentication works")
    print("3. NEVER commit backend/.env to git")
    print("4. In production, use environment variables or secrets manager")
    print()


if __name__ == "__main__":
    main()
