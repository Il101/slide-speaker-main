#!/usr/bin/env python3
"""
Тест Vision API с координатами
"""

import os
import sys
from dotenv import load_dotenv

# Добавляем путь к backend
sys.path.append('/Users/iliazarikov/Documents/Python_crypto/Barahlo/slide-speaker-main/backend')

# Загружаем переменные окружения
load_dotenv('/Users/iliazarikov/Documents/Python_crypto/Barahlo/slide-speaker-main/backend_env_vision_api.env')

def test_vision_api_with_coordinates():
    """Тестируем Vision API с координатами"""
    
    try:
        from workers.ocr_vision import VisionOCRWorker
        
        print("🔍 Тестируем Vision API с координатами...")
        
        # Инициализируем Vision API
        worker = VisionOCRWorker()
        print("✅ Vision API инициализирован")
        
        # Тестируем на тестовом изображении
        image_path = "/Users/iliazarikov/Documents/Python_crypto/Barahlo/slide-speaker-main/test_leaf_anatomy.png"
        
        if not os.path.exists(image_path):
            print(f"❌ Изображение не найдено: {image_path}")
            return
        
        print(f"📄 Обрабатываем: {image_path}")
        
        # Извлекаем элементы
        elements = worker.extract_elements_from_pages([image_path])
        
        if elements and elements[0]:
            print(f"✅ Извлечено {len(elements[0])} элементов:")
            for i, element in enumerate(elements[0]):
                bbox = element['bbox']
                print(f"  {i+1}. {element['type']}: {element['text'][:50]}...")
                print(f"      Координаты: x={bbox['x']}, y={bbox['y']}, w={bbox['width']}, h={bbox['height']}")
        else:
            print("⚠️ Элементы не найдены")
        
        print("\n🎉 Тест Vision API завершен!")
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vision_api_with_coordinates()
