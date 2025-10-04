#!/usr/bin/env python3
"""
Быстрая очистка блокировок для конкретного урока
"""
import redis
import sys

# Конфигурация Redis
REDIS_URL = "redis://redis:6379/0"

def clear_lesson_lock(lesson_id: str):
    """Очистить блокировку для конкретного урока"""
    try:
        redis_client = redis.Redis.from_url(REDIS_URL)
        redis_client.ping()  # Проверка соединения
        
        lock_key = f"lock:lesson:{lesson_id}"
        
        if redis_client.exists(lock_key):
            redis_client.delete(lock_key)
            print(f"✅ Блокировка для урока {lesson_id} успешно удалена")
            return True
        else:
            print(f"ℹ️  Блокировка для урока {lesson_id} не найдена")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Использование: python clear_lesson_lock.py <lesson_id>")
        print("Пример: python clear_lesson_lock.py 9fbbfd09-d0f8-435a-9b3f-96182bcf9fa8")
        sys.exit(1)
    
    lesson_id = sys.argv[1]
    print(f"🔍 Очистка блокировки для урока: {lesson_id}")
    
    success = clear_lesson_lock(lesson_id)
    
    if success:
        print("🎉 Готово! Теперь можно повторно запустить обработку урока.")
    else:
        print("⚠️  Блокировка не была найдена или уже была очищена.")

if __name__ == "__main__":
    main()
