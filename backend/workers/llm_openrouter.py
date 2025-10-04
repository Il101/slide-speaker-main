"""
OpenRouter LLM Worker
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

class OpenRouterLLMWorker:
    """Worker for generating speaker notes using OpenRouter API"""
    
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
    
    def plan_slide_with_gemini(self, elements: List[Dict], model: str = None, 
                              location: str = None, temperature: float = 0.2) -> List[Dict]:
        """
        Генерирует notes (2–4 коротких фразы) с targetId или table_region (список ячеек).
        
        Args:
            elements: Список элементов слайда (включая table_cell и figure с alt_text)
            model: Модель для использования (игнорируется для OpenRouter)
            location: Локация (игнорируется для OpenRouter)
            temperature: Температура генерации
            
        Returns:
            [
              {"text":"...", "targetId":"b1"}, 
              {"text":"...", "target":{"type":"table_region","tableId":"tbl1","cells":["r2c3","r2c4"]}}
            ]
            Строгий JSON, без постороннего текста. Делай автопочинку JSON при парсинге.
        """
        try:
            if self.use_mock:
                return self._plan_slide_mock(elements)
            
            # Use provided temperature or fallback to instance settings
            temperature = temperature or self.temperature
            
            # Prepare prompt
            prompt = self._create_planning_prompt(elements)
            
            # Generate with OpenRouter
            response = self._generate_with_openrouter(prompt, temperature)
            
            # Parse and validate response
            notes = self._parse_openrouter_response(response)
            
            logger.info(f"Generated {len(notes)} speaker notes for slide")
            return notes
            
        except Exception as e:
            logger.error(f"Error planning slide with OpenRouter: {e}")
            # Fallback to mock mode
            logger.info("Falling back to mock LLM")
            return self._plan_slide_mock(elements)
    
    def _create_planning_prompt(self, elements: List[Dict]) -> str:
        """Create prompt for slide planning"""
        
        # Categorize elements
        headings = [e for e in elements if e.get('type') == 'heading']
        paragraphs = [e for e in elements if e.get('type') == 'paragraph']
        tables = [e for e in elements if e.get('type') == 'table']
        table_cells = [e for e in elements if e.get('type') == 'table_cell']
        figures = [e for e in elements if e.get('type') == 'figure']
        
        # Language-specific instructions
        language_instructions = {
            "ru": "Вы эксперт по презентациям. Проанализируйте содержимое слайда и создайте 2-4 краткие заметки докладчика, которые помогут презентатору эффективно объяснить материал.",
            "en": "You are an expert presentation coach. Analyze this slide content and generate 2-4 concise speaker notes that would help a presenter explain the content effectively.",
            "es": "Eres un experto en presentaciones. Analiza el contenido de esta diapositiva y genera 2-4 notas concisas del presentador que ayuden a explicar el contenido de manera efectiva.",
            "fr": "Vous êtes un expert en présentations. Analysez le contenu de cette diapositive et générez 2-4 notes concises du présentateur qui aideraient à expliquer le contenu efficacement.",
            "de": "Sie sind ein Experte für Präsentationen. Analysieren Sie den Inhalt dieser Folie und erstellen Sie 2-4 prägnante Sprechernotizen, die dem Präsentator helfen, den Inhalt effektiv zu erklären."
        }
        
        base_instruction = language_instructions.get(self.language, language_instructions["en"])
        
        prompt = f"""
{base_instruction}

Slide Elements:
"""
        
        # Add headings
        if headings:
            prompt += "\nHeadings:\n"
            for heading in headings:
                prompt += f"- {heading['text']} (ID: {heading['id']})\n"
        
        # Add paragraphs
        if paragraphs:
            prompt += "\nParagraphs:\n"
            for para in paragraphs:
                prompt += f"- {para['text']} (ID: {para['id']})\n"
        
        # Add tables
        if tables:
            prompt += "\nTables:\n"
            for table in tables:
                prompt += f"- Table {table.get('table_id', 'unknown')} with {table.get('rows', 0)} rows, {table.get('cols', 0)} columns (ID: {table['id']})\n"
        
        # Add table cells
        if table_cells:
            prompt += "\nTable Cells:\n"
            for cell in table_cells:
                prompt += f"- Cell {cell.get('row', '?')},{cell.get('col', '?')}: {cell['text']} (Table: {cell.get('table_id', 'unknown')}, ID: {cell['id']})\n"
        
        # Add figures
        if figures:
            prompt += "\nFigures:\n"
            for figure in figures:
                prompt += f"- {figure.get('alt_text', figure['text'])} (ID: {figure['id']})\n"
        
        # Language-specific rules
        language_rules = {
            "ru": """
Создайте заметки докладчика в формате JSON. Каждая заметка должна:
1. Состоять из 1-2 предложений, объясняющих или подчеркивающих ключевое содержание
2. Ссылаться на конкретные элементы, используя их ID
3. Для табличного контента использовать формат table_region с конкретными ячейками

Верните ТОЛЬКО валидный JSON массив с этой точной структурой:
[
  {
    "text": "Краткое объяснение основной концепции",
    "targetId": "element_id"
  },
  {
    "text": "Объяснение данных таблицы",
    "target": {
      "type": "table_region",
      "tableId": "table_id",
      "cells": ["r1c1", "r2c3"]
    }
  }
]

Правила:
- Используйте "targetId" для отдельных элементов (заголовки, абзацы, рисунки)
- Используйте "target" с "table_region" для табличного контента
- Формат ссылок на ячейки: "r{row}c{col}" (например, "r1c1", "r2c3")
- Создайте максимум 2-4 заметки
- Делайте объяснения краткими, но информативными
- Верните ТОЛЬКО JSON массив, без дополнительного текста
""",
            "en": """
Generate speaker notes in JSON format. Each note should:
1. Be 1-2 sentences that explain or emphasize key content
2. Reference specific elements using their IDs
3. For table content, use table_region format with specific cells

Return ONLY valid JSON array with this exact structure:
[
  {
    "text": "Brief explanation of the main concept",
    "targetId": "element_id"
  },
  {
    "text": "Explanation of table data",
    "target": {
      "type": "table_region",
      "tableId": "table_id",
      "cells": ["r1c1", "r2c3"]
    }
  }
]

Rules:
- Use "targetId" for individual elements (headings, paragraphs, figures)
- Use "target" with "table_region" for table content
- Cell references format: "r{row}c{col}" (e.g., "r1c1", "r2c3")
- Generate 2-4 notes maximum
- Keep explanations concise but informative
- Return ONLY the JSON array, no other text
"""
        }
        
        rules_text = language_rules.get(self.language, language_rules["en"])
        prompt += rules_text
        
        return prompt
    
    def _generate_with_openrouter(self, prompt: str, temperature: float) -> str:
        """Generate response using OpenRouter API via OpenAI client"""
        try:
            completion = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "https://slide-speaker.app",
                    "X-Title": "Slide Speaker"
                },
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=1000,
                top_p=0.9
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating with OpenRouter: {e}")
            raise
    
    def _parse_openrouter_response(self, response: str) -> List[Dict]:
        """Parse and validate OpenRouter response"""
        try:
            # Clean response text
            response = response.strip()
            
            # Try to extract JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response
            
            # Parse JSON
            try:
                notes = json.loads(json_str)
            except json.JSONDecodeError:
                # Try to fix common JSON issues
                json_str = self._fix_json(json_str)
                notes = json.loads(json_str)
            
            # Validate structure
            if not isinstance(notes, list):
                raise ValueError("Response must be a JSON array")
            
            # Validate each note
            validated_notes = []
            for note in notes:
                if not isinstance(note, dict):
                    continue
                
                if 'text' not in note:
                    continue
                
                # Must have either targetId or target
                if 'targetId' not in note and 'target' not in note:
                    continue
                
                validated_notes.append(note)
            
            if not validated_notes:
                raise ValueError("No valid notes found in response")
            
            return validated_notes
            
        except Exception as e:
            logger.error(f"Error parsing OpenRouter response: {e}")
            # Try one retry with instruction
            try:
                retry_prompt = f"""
The previous response was invalid. Please return ONLY a valid JSON array with this exact format:

[
  {{
    "text": "Brief explanation",
    "targetId": "element_id"
  }}
]

Return ONLY the JSON array, no other text.
"""
                retry_response = self._generate_with_openrouter(retry_prompt, 0.1)
                return self._parse_openrouter_response(retry_response)
            except:
                raise ValueError("Failed to parse OpenRouter response after retry")
    
    def _fix_json(self, json_str: str) -> str:
        """Fix common JSON formatting issues"""
        # Remove any text before/after JSON array
        json_str = json_str.strip()
        
        # Fix common issues
        json_str = re.sub(r'```json\s*', '', json_str)
        json_str = re.sub(r'```\s*$', '', json_str)
        
        # Ensure proper array brackets
        if not json_str.startswith('['):
            json_str = '[' + json_str
        if not json_str.endswith(']'):
            json_str = json_str + ']'
        
        return json_str
    
    def _plan_slide_mock(self, elements: List[Dict]) -> List[Dict]:
        """Mock slide planning for testing"""
        notes = []
        
        # Language-specific mock texts
        mock_texts = {
            "ru": {
                "heading": "Давайте обсудим {text}",
                "paragraph": "Этот раздел охватывает {text}...",
                "table": "Давайте изучим данные в этой таблице",
                "generic1": "Этот слайд содержит важную информацию",
                "generic2": "Давайте рассмотрим ключевые моменты"
            },
            "en": {
                "heading": "Let's discuss {text}",
                "paragraph": "This section covers {text}...",
                "table": "Let's examine the data in this table",
                "generic1": "This slide contains important information",
                "generic2": "Let's review the key points"
            }
        }
        
        texts = mock_texts.get(self.language, mock_texts["en"])
        
        # Find headings
        headings = [e for e in elements if e.get('type') == 'heading']
        if headings:
            notes.append({
                "text": texts["heading"].format(text=headings[0]['text']),
                "targetId": headings[0]['id']
            })
        
        # Find paragraphs
        paragraphs = [e for e in elements if e.get('type') == 'paragraph']
        if paragraphs:
            notes.append({
                "text": texts["paragraph"].format(text=paragraphs[0]['text'][:50]),
                "targetId": paragraphs[0]['id']
            })
        
        # Find tables
        tables = [e for e in elements if e.get('type') == 'table']
        if tables:
            table_cells = [e for e in elements if e.get('type') == 'table_cell' and e.get('table_id') == tables[0].get('table_id')]
            if table_cells:
                cell_refs = [f"r{cell.get('row', 0)}c{cell.get('col', 0)}" for cell in table_cells[:4]]  # First 4 cells
                notes.append({
                    "text": texts["table"],
                    "target": {
                        "type": "table_region",
                        "tableId": tables[0].get('table_id', 'table_1'),
                        "cells": cell_refs
                    }
                })
        
        # If no specific elements, create generic notes
        if not notes:
            notes = [
                {
                    "text": texts["generic1"],
                    "targetId": elements[0]['id'] if elements else "slide_area"
                },
                {
                    "text": texts["generic2"],
                    "targetId": elements[1]['id'] if len(elements) > 1 else "slide_area"
                }
            ]
        
        logger.info(f"Mock LLM generated {len(notes)} speaker notes")
        return notes
    
    def generate_lecture_text(self, elements: List[Dict], model: str = None, 
                              location: str = None, temperature: float = 0.3) -> str:
        """
        Генерирует текст лекции на основе содержимого слайда.
        
        Args:
            elements: Список элементов слайда
            model: Модель для использования (игнорируется для OpenRouter)
            location: Локация (игнорируется для OpenRouter)
            temperature: Температура генерации
            
        Returns:
            Текст лекции для произнесения
        """
        try:
            if self.use_mock:
                return self._generate_lecture_text_mock(elements)
            
            # Use provided temperature or fallback to instance settings
            temperature = temperature or self.temperature
            
            # Prepare prompt for lecture text generation
            prompt = self._create_lecture_text_prompt(elements)
            
            # Generate with OpenRouter
            response = self._generate_with_openrouter(prompt, temperature)
            
            # Clean and validate response
            lecture_text = self._clean_lecture_text(response)
            
            logger.info(f"Generated lecture text: {len(lecture_text)} characters")
            return lecture_text
            
        except Exception as e:
            logger.error(f"Error generating lecture text with OpenRouter: {e}")
            # Fallback to mock mode
            logger.info("Falling back to mock lecture text")
            return self._generate_lecture_text_mock(elements)
    
    def _create_lecture_text_prompt(self, elements: List[Dict]) -> str:
        """Create prompt for lecture text generation"""
        
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
        
        # Language-specific prompts
        language_prompts = {
            "ru": f"""
Вы профессиональный лектор, выступающий перед аудиторией. На основе содержания этого слайда создайте естественный, разговорный текст лекции, который звучит как то, что презентатор действительно сказал бы студентам или участникам аудитории.

Содержание слайда:
{slide_text}

{"Изображения на слайде:" + chr(10) + slide_images if slide_images else ""}

Создайте текст лекции, который:
1. Звучит как естественная разговорная речь (не письменные инструкции)
2. Использует первое лицо ("я", "мы", "давайте") и прямое обращение ("вы")
3. Объясняет содержание в разговорной, увлекательной манере
4. Упоминает изображения, если они есть на слайде
5. Использует подходящие переходы и связующие фразы
6. Составляет примерно 100-200 слов (30-60 секунд речи)

Пишите так, как будто вы говорите напрямую с аудиторией. Используйте фразы типа:
- "Давайте посмотрим на это вместе..."
- "Как вы можете видеть здесь..."
- "Это показывает нам, что..."
- "Что интересно в этом..."
- "Я хочу подчеркнуть..."
- "Мы можем видеть, что..."
- "На этом изображении мы видим..."

ИЗБЕГАЙТЕ инструкционного языка типа:
- "Начните с представления..."
- "Начните с..."
- "Сначала выделите..."
- "Затем подчеркните..."

Верните ТОЛЬКО естественный текст лекции, без дополнительного форматирования или объяснений.
""",
            "en": f"""
You are a professional lecturer speaking to an audience. Based on this slide content, generate natural, conversational lecture text that sounds like what a presenter would actually say to students or audience members.

Slide Content:
{slide_text}

{"Images on slide:" + chr(10) + slide_images if slide_images else ""}

Generate lecture text that:
1. Sounds like natural spoken language (not written instructions)
2. Uses first person ("I", "we", "let's") and direct address ("you")
3. Explains the content in a conversational, engaging way
4. Mentions images if they are present on the slide
5. Uses appropriate transitions and connecting phrases
6. Is approximately 100-200 words (30-60 seconds of speech)

Write as if you are speaking directly to an audience. Use phrases like:
- "Let's look at this together..."
- "As you can see here..."
- "This shows us that..."
- "What's interesting about this is..."
- "I want to highlight..."
- "We can see that..."
- "In this image we can see..."

AVOID instructional language like:
- "Start by introducing..."
- "Begin with..."
- "First, highlight..."
- "Next, emphasize..."

Return ONLY the natural lecture text, no additional formatting or explanations.
"""
        }
        
        prompt = language_prompts.get(self.language, language_prompts["en"])
        
        return prompt
    
    def _clean_lecture_text(self, response: str) -> str:
        """Clean and validate lecture text response"""
        # Remove any markdown formatting
        response = response.strip()
        response = re.sub(r'```.*?```', '', response, flags=re.DOTALL)
        response = re.sub(r'`([^`]+)`', r'\1', response)
        
        # Remove any quotes or extra formatting
        response = re.sub(r'^["\']|["\']$', '', response)
        
        # Ensure it ends with proper punctuation
        if not response.endswith(('.', '!', '?')):
            response += '.'
        
        return response.strip()
    
    def _generate_lecture_text_mock(self, elements: List[Dict]) -> str:
        """Mock lecture text generation for testing"""
        # Extract text from elements
        text_parts = []
        for element in elements:
            if element.get('text') and element.get('text').strip():
                text_parts.append(element['text'].strip())
        
        # Language-specific mock texts
        mock_lecture_texts = {
            "ru": {
                "no_content": "Давайте обсудим содержание этого слайда вместе. Этот слайд содержит важную информацию, которую нам нужно рассмотреть.",
                "with_content": "Давайте посмотрим на этот слайд вместе. {content}. Это важный момент, который я хочу подчеркнуть для вас. Как вы можете видеть, эта информация помогает нам лучше понять тему."
            },
            "en": {
                "no_content": "Let's discuss the content of this slide together. This slide contains important information that we need to review.",
                "with_content": "Let's look at this slide together. {content}. This is an important point that I want to highlight for you. As you can see, this information helps us understand the topic better."
            }
        }
        
        texts = mock_lecture_texts.get(self.language, mock_lecture_texts["en"])
        
        if not text_parts:
            return texts["no_content"]
        
        # Create natural lecture text
        slide_content = ' '.join(text_parts)
        
        # Generate mock lecture text that sounds natural
        lecture_text = texts["with_content"].format(content=slide_content)
        
        logger.info(f"Mock LLM generated lecture text: {len(lecture_text)} characters")
        return lecture_text

# Utility functions for integration
def plan_slide_with_gemini(elements: List[Dict], model: str = None, 
                          location: str = None, temperature: float = 0.2) -> List[Dict]:
    """
    Генерирует notes (2–4 коротких фразы) с targetId или table_region (список ячеек).
    
    Args:
        elements: Список элементов слайда (включая table_cell и figure с alt_text)
        model: Модель для использования (игнорируется для OpenRouter)
        location: Локация (игнорируется для OpenRouter)
        temperature: Температура генерации
        
    Returns:
        [
          {"text":"...", "targetId":"b1"}, 
          {"text":"...", "target":{"type":"table_region","tableId":"tbl1","cells":["r2c3","r2c4"]}}
        ]
        Строгий JSON, без постороннего текста. Делай автопочинку JSON при парсинге.
    """
    worker = OpenRouterLLMWorker()
    return worker.plan_slide_with_gemini(elements, model, location, temperature)

def generate_lecture_text(elements: List[Dict], model: str = None, 
                         location: str = None, temperature: float = 0.3) -> str:
    """
    Генерирует текст лекции на основе содержимого слайда.
    
    Args:
        elements: Список элементов слайда
        model: Модель для использования (игнорируется для OpenRouter)
        location: Локация (игнорируется для OpenRouter)
        temperature: Температура генерации
        
    Returns:
        Текст лекции для произнесения
    """
    worker = OpenRouterLLMWorker()
    return worker.generate_lecture_text(elements, model, location, temperature)

if __name__ == "__main__":
    # Test the worker
    async def test_worker():
        test_elements = [
            {
                "id": "elem_1",
                "type": "heading",
                "text": "Machine Learning Fundamentals",
                "bbox": [100, 50, 600, 80],
                "confidence": 0.95
            },
            {
                "id": "elem_2", 
                "type": "paragraph",
                "text": "Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data.",
                "bbox": [100, 150, 600, 100],
                "confidence": 0.90
            },
            {
                "id": "elem_3",
                "type": "table",
                "text": "ML Types Comparison",
                "bbox": [100, 300, 600, 200],
                "table_id": "table_1",
                "rows": 3,
                "cols": 2
            },
            {
                "id": "elem_4",
                "type": "table_cell",
                "text": "Supervised Learning",
                "bbox": [100, 300, 300, 50],
                "table_id": "table_1",
                "row": 0,
                "col": 0
            },
            {
                "id": "elem_5",
                "type": "table_cell", 
                "text": "Uses labeled data",
                "bbox": [400, 300, 300, 50],
                "table_id": "table_1",
                "row": 0,
                "col": 1
            }
        ]
        
        worker = OpenRouterLLMWorker()
        notes = worker.plan_slide_with_gemini(test_elements)
        
        print(f"Generated {len(notes)} speaker notes:")
        for i, note in enumerate(notes):
            print(f"  {i+1}. {note['text']}")
            if 'targetId' in note:
                print(f"     Target: {note['targetId']}")
            elif 'target' in note:
                print(f"     Target: {note['target']}")
    
    asyncio.run(test_worker())
