#!/usr/bin/env python3
"""
Создание тестового изображения с текстом для Vision API
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_test_image():
    """Создаем тестовое изображение с русским текстом"""
    
    # Создаем изображение
    width, height = 800, 600
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Пытаемся загрузить шрифт
    try:
        # Пробуем разные шрифты
        font_paths = [
            '/System/Library/Fonts/Arial.ttf',
            '/System/Library/Fonts/Helvetica.ttc',
            '/Library/Fonts/Arial.ttf'
        ]
        
        font = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, 24)
                break
        
        if not font:
            font = ImageFont.load_default()
            
    except Exception:
        font = ImageFont.load_default()
    
    # Добавляем текст
    texts = [
        "Анатомия листа растения",
        "Строение листа включает:",
        "• Эпидермис",
        "• Мезофилл", 
        "• Проводящие пучки",
        "• Устьица"
    ]
    
    y_position = 50
    for text in texts:
        draw.text((50, y_position), text, fill='black', font=font)
        y_position += 40
    
    # Сохраняем изображение
    image.save('test_leaf_anatomy.png')
    print("✅ Тестовое изображение создано: test_leaf_anatomy.png")

if __name__ == "__main__":
    create_test_image()
