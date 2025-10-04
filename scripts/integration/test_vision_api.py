#!/usr/bin/env python3
"""
Тест Vision API на реальной презентации
"""

import os
import sys
import json
from dotenv import load_dotenv

# Добавляем путь к backend
sys.path.append('/Users/iliazarikov/Documents/Python_crypto/Barahlo/slide-speaker-main/backend')

# Загружаем переменные окружения
load_dotenv('/Users/iliazarikov/Documents/Python_crypto/Barahlo/slide-speaker-main/backend_env_vision_api.env')

def test_vision_api():
    """Тестируем Vision API на реальных слайдах"""
    
    try:
        from workers.ocr_vision import VisionOCRWorker
        
        print("🔍 Тестируем Vision API...")
        
        # Инициализируем Vision API
        worker = VisionOCRWorker()
        print("✅ Vision API инициализирован")
        
        # Тестируем на слайдах из существующей презентации
        slides_dir = "/Users/iliazarikov/Documents/Python_crypto/Barahlo/slide-speaker-main/.data/4171a65f-89cd-41b6-9cc4-2e8f21d107e5/slides"
        
        if not os.path.exists(slides_dir):
            print(f"❌ Директория слайдов не найдена: {slides_dir}")
            return
        
        # Получаем список PNG файлов
        png_files = [f for f in os.listdir(slides_dir) if f.endswith('.png')]
        png_files.sort()
        
        print(f"📄 Найдено {len(png_files)} слайдов")
        
        # Тестируем первые 3 слайда
        for i, png_file in enumerate(png_files[:3]):
            slide_path = os.path.join(slides_dir, png_file)
            print(f"\n🔍 Обрабатываем слайд {i+1}: {png_file}")
            
            try:
                # Извлекаем элементы
                elements = worker.extract_elements_from_pages([slide_path])
                
                if elements and elements[0]:
                    print(f"✅ Извлечено {len(elements[0])} элементов:")
                    for j, element in enumerate(elements[0]):
                        print(f"  {j+1}. {element['type']}: {element['text'][:100]}...")
                else:
                    print("⚠️ Элементы не найдены")
                    
            except Exception as e:
                print(f"❌ Ошибка обработки слайда {i+1}: {e}")
        
        print("\n🎉 Тест Vision API завершен!")
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vision_api()
