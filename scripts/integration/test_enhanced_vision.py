#!/usr/bin/env python3
"""
Тест Enhanced Vision API для проверки работы OCR
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Добавляем путь к backend
sys.path.append('/Users/iliazarikov/Documents/Python_crypto/Barahlo/slide-speaker-main/backend')

# Загружаем переменные окружения
load_dotenv('backend/.env')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_enhanced_vision_api():
    """Тестируем Enhanced Vision API напрямую"""
    
    try:
        from workers.ocr_vision_enhanced import EnhancedVisionOCRWorker
        
        print('🔍 Тестируем Enhanced Vision API...')
        
        # Инициализируем worker
        worker = EnhancedVisionOCRWorker()
        print('✅ Enhanced Vision OCR Worker инициализирован')
        
        # Создаем тестовое изображение
        from PIL import Image, ImageDraw, ImageFont
        
        test_image_path = 'test_enhanced_vision.png'
        img = Image.new('RGB', (800, 600), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except IOError:
            font = ImageFont.load_default()
            print("⚠️ Arial font not found, using default font.")
        
        # Добавляем текст
        d.text((100, 50), "Анатомия листа растения", fill=(0, 0, 0), font=font)
        d.text((100, 100), "Строение листа включает:", fill=(0, 0, 0), font=font)
        d.text((120, 140), "• Эпидермис", fill=(0, 0, 0), font=font)
        d.text((120, 170), "• Мезофилл", fill=(0, 0, 0), font=font)
        d.text((120, 200), "• Проводящие пучки", fill=(0, 0, 0), font=font)
        d.text((120, 230), "• Устьица", fill=(0, 0, 0), font=font)
        
        # Добавляем простую диаграмму
        d.rectangle([400, 100, 700, 400], outline=(0, 0, 0), width=2)
        d.text((420, 120), "Поперечный срез листа", fill=(0, 0, 0), font=font)
        
        img.save(test_image_path)
        print(f'✅ Тестовое изображение создано: {test_image_path}')
        
        # Тестируем OCR
        print(f'📄 Обрабатываем: {test_image_path}')
        elements_per_page = worker.extract_elements_from_pages([test_image_path])
        
        if elements_per_page and elements_per_page[0]:
            print(f'✅ Извлечено {len(elements_per_page[0])} элементов:')
            for i, element in enumerate(elements_per_page[0]):
                print(f'  {i+1}. {element["type"]}: {element.get("text", element.get("description", "No text"))[:50]}...')
                if 'bbox' in element:
                    bbox = element['bbox']
                    print(f'      Координаты: x={bbox["x"]}, y={bbox["y"]}, w={bbox["width"]}, h={bbox["height"]}')
                if 'confidence' in element:
                    print(f'      Уверенность: {element["confidence"]:.2f}')
        else:
            print('⚠️ Enhanced Vision API не извлек элементы.')
        
        # Удаляем тестовый файл
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
            print(f'🗑️ Тестовый файл удален: {test_image_path}')
        
        print('🎉 Тест Enhanced Vision API завершен!')
        
    except Exception as e:
        print(f'❌ Ошибка теста: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_enhanced_vision_api()
