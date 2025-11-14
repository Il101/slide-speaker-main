#!/usr/bin/env python3
"""
Скрипт для очистки OCR кэша в Redis
"""
import sys
sys.path.insert(0, '.')

from app.services.ocr_cache import get_ocr_cache

def main():
    print("🗑️  Очистка OCR кэша...")

    cache = get_ocr_cache()

    if not cache.enabled:
        print("❌ OCR Cache не включён (Redis недоступен)")
        return

    # Получить статистику перед очисткой
    stats_before = cache.get_stats()
    print(f"\n📊 До очистки:")
    print(f"   Записей: {stats_before.get('total_entries', 0)}")
    print(f"   Размер: {stats_before.get('total_size_mb', 0)} MB")

    # Очистить весь OCR кэш
    deleted = cache.clear_all()

    # Также очистить processed slides (дедупликация)
    try:
        processed_keys = cache.redis_client.keys("slide_processed:*")
        if processed_keys:
            deleted_processed = cache.redis_client.delete(*processed_keys)
            print(f"\n✅ Удалено OCR записей: {deleted}")
            print(f"✅ Удалено processed slides: {deleted_processed}")
            print(f"✅ Всего удалено: {deleted + deleted_processed}")
        else:
            print(f"\n✅ Удалено OCR записей: {deleted}")
    except Exception as e:
        print(f"\n✅ Удалено OCR записей: {deleted}")
        print(f"⚠️  Ошибка при очистке processed slides: {e}")

    # Статистика после
    stats_after = cache.get_stats()
    print(f"\n📊 После очистки:")
    print(f"   Записей: {stats_after.get('total_entries', 0)}")
    print(f"   Размер: {stats_after.get('total_size_mb', 0)} MB")

    print(f"\n✅ OCR кэш полностью очищен!")

if __name__ == "__main__":
    main()
