#!/usr/bin/env python3
"""
Тест Enhanced Vision API на реальных слайдах Kurs_10.pdf
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

def test_kurs10_slides():
    """Тестируем Enhanced Vision API на слайдах Kurs_10.pdf"""
    
    try:
        from workers.ocr_vision_enhanced import EnhancedVisionOCRWorker
        
        print('🔍 Тестируем Enhanced Vision API на слайдах Kurs_10.pdf...')
        
        # Инициализируем worker
        worker = EnhancedVisionOCRWorker()
        print('✅ Enhanced Vision OCR Worker инициализирован')
        
        # Ищем PNG файлы слайдов
        slides_dir = 'kurs10_images_test'
        if not os.path.exists(slides_dir):
            print(f'❌ Директория не найдена: {slides_dir}')
            return
        
        png_files = [f for f in os.listdir(slides_dir) if f.endswith('.png')]
        png_files.sort()
        
        if not png_files:
            print(f'❌ PNG файлы не найдены в {slides_dir}')
            return
        
        print(f'📄 Найдено {len(png_files)} PNG файлов')
        
        # Тестируем первые 3 слайда
        test_files = png_files[:3]
        full_paths = [os.path.join(slides_dir, f) for f in test_files]
        
        print(f'🔍 Тестируем слайды: {test_files}')
        
        # Обрабатываем слайды
        elements_per_page = worker.extract_elements_from_pages(full_paths)
        
        for i, elements in enumerate(elements_per_page):
            slide_name = test_files[i]
            print(f'\\n📊 Слайд {slide_name}:')
            
            if elements:
                print(f'  ✅ Извлечено {len(elements)} элементов:')
                
                # Группируем по типам
                text_elements = [e for e in elements if e.get('type') == 'text']
                image_elements = [e for e in elements if e.get('type') == 'image']
                object_elements = [e for e in elements if e.get('type') == 'object']
                
                print(f'    📝 Текстовых элементов: {len(text_elements)}')
                print(f'    🖼️ Изображений: {len(image_elements)}')
                print(f'    🎯 Объектов: {len(object_elements)}')
                
                # Показываем примеры текста
                if text_elements:
                    print(f'    📝 Примеры текста:')
                    for j, elem in enumerate(text_elements[:3]):  # Показываем первые 3
                        text = elem.get('text', 'No text')[:50]
                        print(f'      {j+1}. {text}...')
                
                # Показываем примеры изображений
                if image_elements:
                    print(f'    🖼️ Примеры изображений:')
                    for j, elem in enumerate(image_elements[:3]):  # Показываем первые 3
                        desc = elem.get('description', 'No description')
                        confidence = elem.get('confidence', 0)
                        print(f'      {j+1}. {desc} (уверенность: {confidence:.2f})')
                
                # Показываем примеры объектов
                if object_elements:
                    print(f'    🎯 Примеры объектов:')
                    for j, elem in enumerate(object_elements[:3]):  # Показываем первые 3
                        desc = elem.get('description', 'No description')
                        confidence = elem.get('confidence', 0)
                        bbox = elem.get('bbox', {})
                        print(f'      {j+1}. {desc} (уверенность: {confidence:.2f})')
                        if bbox:
                            print(f'         Координаты: x={bbox.get("x")}, y={bbox.get("y")}, w={bbox.get("width")}, h={bbox.get("height")}')
            else:
                print(f'  ⚠️ Элементы не найдены')
        
        print('\\n🎉 Тест Enhanced Vision API на Kurs_10.pdf завершен!')
        
    except Exception as e:
        print(f'❌ Ошибка теста: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_kurs10_slides()
