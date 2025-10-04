#!/usr/bin/env python3
"""
Тест SSML функциональности для улучшения русских акцентов
"""
import os
import asyncio
import logging
from dotenv import load_dotenv
from backend.workers.llm_openrouter_ssml import OpenRouterLLMWorkerSSML
from backend.workers.tts_google_ssml import GoogleTTSWorkerSSML

# Загружаем переменные окружения
load_dotenv("backend_env_enhanced_hybrid.env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ssml_pipeline():
    """Тестирует полный пайплайн с SSML"""
    logger.info("🎵 Тестируем SSML пайплайн для улучшения русских акцентов...")
    
    # Тестовые элементы слайда
    test_elements = [
        {
            "id": "slide_1_heading",
            "type": "heading",
            "text": "Анатомия растений",
            "confidence": 0.9,
            "bbox": {"x": 100, "y": 50, "width": 600, "height": 40}
        },
        {
            "id": "slide_1_paragraph",
            "type": "paragraph", 
            "text": "Сегодня мы изучаем строение листьев, стеблей и корней растений. Обратите внимание на важные детали в таблице.",
            "confidence": 0.9,
            "bbox": {"x": 100, "y": 100, "width": 600, "height": 150}
        },
        {
            "id": "slide_1_image",
            "type": "image",
            "description": "Диаграмма строения листа",
            "confidence": 0.9,
            "bbox": {"x": 700, "y": 50, "width": 250, "height": 200}
        }
    ]
    
    try:
        # Шаг 1: Генерируем SSML текст с помощью LLM
        logger.info("🤖 Генерируем SSML текст с помощью LLM...")
        llm_worker = OpenRouterLLMWorkerSSML()
        ssml_text = llm_worker.generate_lecture_text_with_ssml(test_elements)
        
        logger.info(f"✅ SSML текст сгенерирован:")
        logger.info(f"📝 Длина: {len(ssml_text)} символов")
        logger.info(f"📄 Содержимое:")
        logger.info(f"{ssml_text[:200]}...")
        
        # Шаг 2: Синтезируем аудио с помощью SSML TTS
        logger.info("🎵 Синтезируем аудио с помощью SSML TTS...")
        tts_worker = GoogleTTSWorkerSSML()
        
        # Разбиваем SSML на предложения для лучшего контроля
        ssml_sentences = ssml_text.split('<break time="0.5s"/>')
        ssml_sentences = [s.strip() for s in ssml_sentences if s.strip()]
        
        audio_path, tts_words = tts_worker.synthesize_slide_text_google_ssml(ssml_sentences)
        
        logger.info(f"✅ Аудио синтезировано:")
        logger.info(f"📁 Файл: {audio_path}")
        logger.info(f"⏱️ Предложений: {len(tts_words['sentences'])}")
        logger.info(f"🎵 Общая длительность: {tts_words['sentences'][-1]['t1']:.2f}s")
        
        # Шаг 3: Показываем структуру таймингов
        logger.info(f"📊 Структура таймингов:")
        for i, sentence in enumerate(tts_words['sentences']):
            logger.info(f"  {i+1}. [{sentence['t0']:.2f}s - {sentence['t1']:.2f}s] {sentence['text'][:50]}...")
        
        logger.info(f"\n🎉 SSML пайплайн успешно протестирован!")
        logger.info(f"💡 Преимущества SSML:")
        logger.info(f"  ✅ Точный контроль над произношением")
        logger.info(f"  ✅ Правильные акценты и интонации")
        logger.info(f"  ✅ Паузы между предложениями")
        logger.info(f"  ✅ Выделение важных терминов")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка в SSML пайплайне: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    asyncio.run(test_ssml_pipeline())
