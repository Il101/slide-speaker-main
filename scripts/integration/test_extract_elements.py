#!/usr/bin/env python3
"""
Тест extract_elements_from_pages для проверки работы OCR
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Добавляем путь к backend
sys.path.append('/Users/iliazarikov/Documents/Python_crypto/Barahlo/slide-speaker-main/backend')

# Загружаем переменные окружения
load_dotenv('/Users/iliazarikov/Documents/Python_crypto/Barahlo/slide-speaker-main/backend_env_enhanced_hybrid.env')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_extract_elements():
    """Тестируем extract_elements_from_pages напрямую"""
    
    try:
        from app.services.provider_factory import extract_elements_from_pages
        
        print('🔍 Тестируем extract_elements_from_pages...')
        
        # Тестируем на слайдах из kurs10_images_test
        test_slides = [
            'kurs10_images_test/slide_001.png',
            'kurs10_images_test/slide_002.png'
        ]
        
        # Проверяем, что файлы существуют
        existing_slides = []
        for slide in test_slides:
            if os.path.exists(slide):
                existing_slides.append(slide)
                print(f'✅ Найден: {slide}')
            else:
                print(f'❌ Не найден: {slide}')
        
        if not existing_slides:
            print('❌ Нет доступных слайдов для тестирования')
            return
        
        print(f'\\n📄 Тестируем {len(existing_slides)} слайдов...')
        
        # Извлекаем элементы
        elements_per_page = extract_elements_from_pages(existing_slides)
        
        print(f'\\n📊 Результаты:')
        print(f'  Получено результатов: {len(elements_per_page)}')
        
        for i, elements in enumerate(elements_per_page):
            slide_name = existing_slides[i]
            print(f'\\n📊 Слайд {i+1} ({slide_name}):')
            print(f'  Элементов: {len(elements)}')
            
            if elements:
                print(f'  ✅ Элементы извлечены:')
                for j, elem in enumerate(elements[:3]):  # Показываем первые 3
                    elem_type = elem.get('type', 'unknown')
                    elem_text = elem.get('text', elem.get('description', 'No text'))[:40]
                    print(f'    {j+1}. {elem_type}: {elem_text}...')
            else:
                print(f'  ⚠️ Элементы не найдены')
        
        print('\\n🎉 Тест extract_elements_from_pages завершен!')
        
    except Exception as e:
        print(f'❌ Ошибка теста: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_extract_elements()
