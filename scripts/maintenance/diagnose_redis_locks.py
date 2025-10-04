#!/usr/bin/env python3
"""
Скрипт для диагностики и очистки блокировок Redis в пайплайне Slide Speaker
"""
import redis
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Конфигурация Redis (из docker-compose.yml)
REDIS_URL = "redis://redis:6379/0"

class LockDiagnostic:
    def __init__(self, redis_url: str = REDIS_URL):
        """Инициализация подключения к Redis"""
        try:
            self.redis_client = redis.Redis.from_url(redis_url)
            self.redis_client.ping()  # Проверка соединения
            print(f"✅ Подключение к Redis установлено: {redis_url}")
        except Exception as e:
            print(f"❌ Ошибка подключения к Redis: {e}")
            sys.exit(1)
    
    def get_all_locks(self) -> Dict[str, Dict]:
        """Получить все активные блокировки"""
        locks = {}
        try:
            # Ищем все ключи с префиксом "lock:"
            lock_keys = self.redis_client.keys("lock:*")
            
            for key in lock_keys:
                key_str = key.decode('utf-8')
                value = self.redis_client.get(key)
                ttl = self.redis_client.ttl(key)
                
                locks[key_str] = {
                    'value': value.decode('utf-8') if value else None,
                    'ttl': ttl,
                    'expires_at': datetime.now().timestamp() + ttl if ttl > 0 else None
                }
            
            return locks
        except Exception as e:
            print(f"❌ Ошибка получения блокировок: {e}")
            return {}
    
    def analyze_locks(self, locks: Dict[str, Dict]) -> None:
        """Анализ блокировок"""
        print(f"\n📊 Анализ блокировок ({len(locks)} найдено):")
        print("=" * 60)
        
        if not locks:
            print("✅ Активных блокировок не найдено")
            return
        
        for lock_key, lock_info in locks.items():
            resource = lock_key.replace("lock:", "")
            ttl = lock_info['ttl']
            expires_at = lock_info['expires_at']
            
            print(f"\n🔒 Блокировка: {resource}")
            print(f"   Значение: {lock_info['value']}")
            print(f"   TTL: {ttl} секунд")
            
            if ttl > 0:
                expires_time = datetime.fromtimestamp(expires_at)
                print(f"   Истекает: {expires_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Проверяем, не слишком ли долго висит блокировка
                if ttl > 1800:  # Больше 30 минут
                    print(f"   ⚠️  ВНИМАНИЕ: Блокировка висит слишком долго!")
            else:
                print(f"   ⚠️  ВНИМАНИЕ: Блокировка без TTL!")
    
    def cleanup_expired_locks(self, locks: Dict[str, Dict]) -> int:
        """Очистка истекших блокировок"""
        cleaned_count = 0
        
        print(f"\n🧹 Очистка истекших блокировок:")
        print("=" * 40)
        
        for lock_key, lock_info in locks.items():
            ttl = lock_info['ttl']
            
            # Удаляем блокировки без TTL или с отрицательным TTL
            if ttl <= 0:
                try:
                    self.redis_client.delete(lock_key)
                    resource = lock_key.replace("lock:", "")
                    print(f"✅ Удалена истекшая блокировка: {resource}")
                    cleaned_count += 1
                except Exception as e:
                    print(f"❌ Ошибка удаления {lock_key}: {e}")
        
        return cleaned_count
    
    def cleanup_lesson_locks(self, lesson_id: Optional[str] = None) -> int:
        """Очистка блокировок для конкретного урока"""
        cleaned_count = 0
        
        if lesson_id:
            lock_key = f"lock:lesson:{lesson_id}"
            try:
                if self.redis_client.exists(lock_key):
                    self.redis_client.delete(lock_key)
                    print(f"✅ Удалена блокировка для урока: {lesson_id}")
                    cleaned_count += 1
                else:
                    print(f"ℹ️  Блокировка для урока {lesson_id} не найдена")
            except Exception as e:
                print(f"❌ Ошибка удаления блокировки для урока {lesson_id}: {e}")
        else:
            # Удаляем все блокировки уроков
            lesson_locks = self.redis_client.keys("lock:lesson:*")
            for lock_key in lesson_locks:
                try:
                    self.redis_client.delete(lock_key)
                    resource = lock_key.decode('utf-8').replace("lock:", "")
                    print(f"✅ Удалена блокировка урока: {resource}")
                    cleaned_count += 1
                except Exception as e:
                    print(f"❌ Ошибка удаления {lock_key}: {e}")
        
        return cleaned_count
    
    def get_redis_info(self) -> None:
        """Получить информацию о Redis"""
        try:
            info = self.redis_client.info()
            print(f"\n📈 Информация о Redis:")
            print("=" * 30)
            print(f"Версия: {info.get('redis_version', 'Unknown')}")
            print(f"Подключения: {info.get('connected_clients', 'Unknown')}")
            print(f"Использование памяти: {info.get('used_memory_human', 'Unknown')}")
            print(f"Ключей в базе: {info.get('db0', {}).get('keys', 'Unknown')}")
        except Exception as e:
            print(f"❌ Ошибка получения информации о Redis: {e}")

def main():
    """Основная функция"""
    print("🔍 Диагностика блокировок Redis для Slide Speaker")
    print("=" * 50)
    
    # Инициализация
    diagnostic = LockDiagnostic()
    
    # Получение информации о Redis
    diagnostic.get_redis_info()
    
    # Получение всех блокировок
    locks = diagnostic.get_all_locks()
    
    # Анализ блокировок
    diagnostic.analyze_locks(locks)
    
    # Интерактивное меню
    while True:
        print(f"\n🎯 Выберите действие:")
        print("1. Очистить все истекшие блокировки")
        print("2. Очистить блокировки для конкретного урока")
        print("3. Очистить все блокировки уроков")
        print("4. Обновить анализ")
        print("5. Выход")
        
        choice = input("\nВведите номер действия (1-5): ").strip()
        
        if choice == "1":
            cleaned = diagnostic.cleanup_expired_locks(locks)
            print(f"\n✅ Очищено {cleaned} истекших блокировок")
            locks = diagnostic.get_all_locks()  # Обновляем список
            
        elif choice == "2":
            lesson_id = input("Введите ID урока: ").strip()
            if lesson_id:
                cleaned = diagnostic.cleanup_lesson_locks(lesson_id)
                print(f"\n✅ Очищено {cleaned} блокировок для урока {lesson_id}")
                locks = diagnostic.get_all_locks()
            
        elif choice == "3":
            confirm = input("Удалить ВСЕ блокировки уроков? (yes/no): ").strip().lower()
            if confirm == "yes":
                cleaned = diagnostic.cleanup_lesson_locks()
                print(f"\n✅ Очищено {cleaned} блокировок уроков")
                locks = diagnostic.get_all_locks()
            
        elif choice == "4":
            locks = diagnostic.get_all_locks()
            diagnostic.analyze_locks(locks)
            
        elif choice == "5":
            print("👋 До свидания!")
            break
            
        else:
            print("❌ Неверный выбор. Попробуйте снова.")

if __name__ == "__main__":
    main()
