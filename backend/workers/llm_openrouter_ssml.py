"""
OpenRouter LLM Worker with SSML support for better Russian pronunciation
"""
import asyncio
import json
import logging
import os
import re
from typing import Dict, List, Optional, Any
from pathlib import Path
import uuid

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI client not available. Install openai")

logger = logging.getLogger(__name__)

class OpenRouterLLMWorkerSSML:
    """Worker for generating speaker notes with SSML support for better Russian pronunciation"""
    
    def __init__(self, api_key: str = None, model: str = None, base_url: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = model or os.getenv("OPENROUTER_MODEL", "x-ai/grok-4-fast:free")
        self.base_url = base_url or os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))
        self.language = os.getenv("LLM_LANGUAGE", "ru")
        
        if not self.api_key or not OPENAI_AVAILABLE:
            logger.warning("OpenRouter API key not provided or OpenAI client not available, will use mock mode")
            self.use_mock = True
        else:
            self.use_mock = False
            # Initialize OpenAI client with OpenRouter configuration
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def generate_lecture_text_with_ssml(self, elements: List[Dict], model: str = None, 
                                       location: str = None, temperature: float = 0.3) -> str:
        """
        Генерирует текст лекции с SSML-разметкой для правильных русских акцентов.
        
        Args:
            elements: Список элементов слайда
            model: Модель для использования (игнорируется для OpenRouter)
            location: Локация (игнорируется для OpenRouter)
            temperature: Температура генерации
            
        Returns:
            Текст лекции с SSML-разметкой для произнесения
        """
        try:
            if self.use_mock:
                return self._generate_lecture_text_ssml_mock(elements)
            
            # Use provided temperature or fallback to instance settings
            temperature = temperature or self.temperature
            
            # Prepare prompt for SSML lecture text generation
            prompt = self._create_ssml_lecture_text_prompt(elements)
            
            # Generate with OpenRouter
            response = self._generate_with_openrouter(prompt, temperature)
            
            # Clean and validate SSML response
            lecture_text = self._clean_ssml_lecture_text(response)
            
            logger.info(f"Generated SSML lecture text: {len(lecture_text)} characters")
            return lecture_text
            
        except Exception as e:
            logger.error(f"Error generating SSML lecture text with OpenRouter: {e}")
            # Fallback to mock mode
            logger.info("Falling back to mock SSML lecture text")
            return self._generate_lecture_text_ssml_mock(elements)
    
    def _create_ssml_lecture_text_prompt(self, elements: List[Dict]) -> str:
        """Create prompt for SSML lecture text generation with Russian accent guidance"""
        
        # Extract text content from elements
        text_content = []
        image_content = []
        
        for element in elements:
            if element.get('text') and element.get('text').strip():
                text_content.append(element['text'].strip())
            elif element.get('type') == 'image' or element.get('type') == 'object':
                # Handle image elements
                img_desc = element.get('description', element.get('text', 'Unknown image'))
                img_type = element.get('subtype', 'image')
                img_details = element.get('details', '')
                img_significance = element.get('scientific_significance', '')

                image_info = f"- {img_desc}"
                if img_type and img_type != 'image':
                    image_info += f" ({img_type})"
                if img_details:
                    image_info += f": {img_details}"
                if img_significance:
                    image_info += f" [Научное значение: {img_significance}]"

                image_content.append(image_info)

        slide_text = ' '.join(text_content)
        slide_images = '\n'.join(image_content) if image_content else ""

        # Language-specific prompts with SSML guidance
        language_prompts = {
            "ru": f"""
Ты - опытный преподаватель биологии, который ведет лекцию по анатомии растений для студентов университета.

Содержание слайда:
{slide_text}

{("Изображения на слайде:" + chr(10) + slide_images) if slide_images else ""}

Твоя лекция должна:
1. Объясняет содержание слайда простым и понятным языком
2. Использует научную терминологию с правильными ударениями
3. Связывает информацию логически и последовательно
4. Упоминает изображения, если они есть на слайде
5. НЕ содержит приветствий - сразу переходи к содержанию
6. Использует естественную речь преподавателя
7. ЗАМЕНЯЕТ иностранные слова на русские аналоги с правильными ударениями
8. НЕ переводит термины на другие языки - использует только русские термины

Стиль речи: профессиональный, но доступный для студентов.

ВАЖНО: 
- Заменяй иностранные слова на русские аналоги!
- НЕ переводи термины на другие языки
- НЕ используй фразы типа "по-немецки это называется..."
- Используй только русские термины и объяснения

Словарь замен:
- "universität innsbruck" → "университет инсбрук"
- "Das Blatt" → "лист"
- "Monokotyle Pflanzen" → "однодольные растения"
- "Dikotyle Pflanzen" → "двудольные растения"
- "parallelnervig" → "параллельнонервные"
- "netznervig" → "сетчатонервные"
- "carnivore Pflanzen" → "плотоядные растения"
- "Blütenbestandteile" → "части цветка"
- "Fruchtblätter" → "плодолистики"
- "Staubblätter" → "тычинки"
- "Kronblätter" → "лепестки"
- "Kelchblätter" → "чашелистики"
- "Hochblätter" → "прицветники"

Используй SSML-теги для улучшения произношения:
- <prosody rate="1.0"> - для основного текста
- <emphasis level="strong"> - для важных терминов и ударных слогов
- <break time="0.5s"/> - для пауз между предложениями
- <prosody rate="0.9"> - для медленного произношения сложных терминов
- <say-as interpret-as="characters"> - для латинских названий
- <mark name="слово_оригинал"/> - ОБЯЗАТЕЛЬНО добавляй перед каждым ключевым термином для синхронизации с визуальными подсказками

КРИТИЧЕСКИ ВАЖНО О MARK ТЕГАХ:
- Используй <mark name="original_word"/> где original_word - это слово С СЛАЙДА в ОРИГИНАЛЬНОМ НАПИСАНИИ (немецком/латинском)
- Если на слайде "Das Blatt" - используй <mark name="blatt"/>, а НЕ <mark name="лист"/>
- Если на слайде "universität innsbruck" - используй <mark name="universitat"/> и <mark name="innsbruck"/>
- Если на слайде "Monokotyle" - используй <mark name="monokotyle"/>, а НЕ <mark name="однодольные"/>
- Mark теги ДОЛЖНЫ совпадать с текстом на слайде для правильной синхронизации визуальных подсветок
- Используй латиницу и нижний регистр для mark names (без умлаутов: ä→a, ö→o, ü→u)

Примеры правильного использования MARK:
НЕПРАВИЛЬНО: <mark name="лист"/>лист
ПРАВИЛЬНО: <mark name="blatt"/>лист

НЕПРАВИЛЬНО: <mark name="университет"/>университет инсбрук
ПРАВИЛЬНО: <mark name="universitat"/><mark name="innsbruck"/>университет инсбрук

НЕПРАВИЛЬНО: <mark name="однодольные"/>однодольные растения
ПРАВИЛЬНО: <mark name="monokotyle"/>однодольные растения

Примеры правильных ударений в биологических терминах:
- "анатОмия" (не "анатомия")
- "растЕний" (не "растений") 
- "архитЕктура" (не "архитектура")
- "органИзм" (не "организм")
- "клЕточный" (не "клеточный")
- "ткАни" (не "ткани")

Примеры правильного использования С MARK ТЕГАМИ:
<prosody rate="1.0">На этом <mark name="slajde"/>слайде мы видим <mark name="anatomija"/><emphasis level="strong">анатОмию</emphasis> <mark name="lista"/>листа.</prosody> <break time="0.5s"/>
<prosody rate="0.9">Обратите <mark name="vnimanie"/>внимание</prosody> на различные <mark name="tkani"/><emphasis level="strong">ткАни</emphasis>, которые формируют <mark name="strukturu"/>структуру листа. <break time="0.5s"/>
<prosody rate="1.0"><mark name="universitat"/>Университет <mark name="innsbruck"/>инсбрук представляет <mark name="kurs"/>курс по <mark name="blatt"/><emphasis level="strong">листу</emphasis>.</prosody> <break time="0.5s"/>
<prosody rate="1.0"><mark name="monokotyle"/><emphasis level="strong">Однодольные растения</emphasis> имеют <mark name="parallelnervig"/>параллельное жилкование, а <mark name="dikotyle"/><emphasis level="strong">двудольные растения</emphasis> - <mark name="netznervig"/>сетчатое.</prosody> <break time="0.5s"/>
<prosody rate="1.0">Это важное <mark name="razlichie"/>различие между <mark name="tipami"/>типами растений, которое помогает в их <mark name="klassifikacija"/>классификации.</prosody>

Отвечай только SSML-разметкой, без дополнительных комментариев.
""",
            "en": f"""
You are an experienced English teacher creating lecture text with SSML markup for proper pronunciation.

Slide Content:
{slide_text}

{("Images on slide:" + chr(10) + slide_images) if slide_images else ""}

Create lecture text in SSML format that:
1. Contains natural English speech for students
2. Uses proper accents and intonations
3. Includes SSML tags for improved pronunciation
4. Mentions images if they are present on the slide

Use these SSML tags for improved pronunciation:
- <prosody rate="0.95"> - for main text
- <emphasis level="strong"> - for important terms
- <break time="0.5s"/> - for pauses between sentences
- <prosody rate="0.9"> - for slow pronunciation of complex words
- <say-as interpret-as="characters"> - for abbreviations
- <mark name="word_N"/> - REQUIRED: add before each noun, verb, adjective and important term for visual cue synchronization

IMPORTANT ABOUT MARK TAGS:
- Add <mark name="term"/> before each key word that appears on the slide
- Name the mark by word content (e.g., <mark name="leaf"/>, <mark name="university"/>, <mark name="plants"/>)
- Mark tags help synchronize speech with visual highlights on slides
- DON'T forget mark tags - they are critical!

Example with MARK TAGS:
<prosody rate="0.95">On this <mark name="slide"/>slide we see the <mark name="anatomy"/><emphasis level="strong">anatomy</emphasis> of a <mark name="leaf"/>leaf.</prosody> <break time="0.5s"/>
<prosody rate="0.9">Pay <mark name="attention"/>attention</prosody> to various <mark name="tissues"/><emphasis level="strong">tissues</emphasis> that form the <mark name="structure"/>structure of the leaf. <break time="0.5s"/>

Respond only with SSML markup, no additional comments.
"""
        }

        prompt = language_prompts.get(self.language, language_prompts["en"])
        return prompt
    
    def _clean_ssml_lecture_text(self, response: str) -> str:
        """Clean and validate SSML lecture text"""
        # Remove any markdown formatting
        text = re.sub(r'```ssml\s*\n?', '', response)
        text = re.sub(r'```\s*$', '', text)
        
        # Remove any leading/trailing whitespace
        text = text.strip()
        
        # Ensure it starts with proper SSML
        if not text.startswith('<speak>'):
            text = f'<speak>{text}</speak>'
        
        # Validate basic SSML structure
        if not text.endswith('</speak>'):
            text = f'{text}</speak>'
        
        return text
    
    def _generate_lecture_text_ssml_mock(self, elements: List[Dict]) -> str:
        """Mock SSML lecture text generation"""
        # Extract some text from elements for mock
        text_parts = []
        for element in elements[:3]:  # Take first 3 elements
            if element.get('text'):
                text_parts.append(element['text'][:50])  # First 50 chars
        
        mock_text = ' '.join(text_parts) if text_parts else "Это тестовый текст лекции."
        
        return f'''<speak>
<prosody rate="1.0">На этом слайде мы рассматриваем <emphasis level="strong">{mock_text}</emphasis>.</prosody> <break time="0.5s"/>
<prosody rate="0.9">Обратите внимание</prosody> на важные детали структуры. <break time="0.5s"/>
</speak>'''
    
    def _generate_with_openrouter(self, prompt: str, temperature: float) -> str:
        """Generate response using OpenRouter API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=temperature,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            raise e

# Convenience function
def generate_lecture_text_with_ssml(elements: List[Dict], model: str = None,
                                   location: str = None, temperature: float = 0.3) -> str:
    """Convenience function for generating SSML lecture text"""
    worker = OpenRouterLLMWorkerSSML()
    return worker.generate_lecture_text_with_ssml(elements, model, location, temperature)
