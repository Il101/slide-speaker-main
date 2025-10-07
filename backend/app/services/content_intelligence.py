"""
Content Intelligence - детекция типов контента для адаптивной обработки
Распознаёт формулы, код, диаграммы, таблицы и адаптирует стратегию объяснения
"""
import logging
import re
from typing import Dict, Any, List, Tuple, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ContentType(str, Enum):
    """Типы контента на слайде"""
    TEXT = "text"  # Обычный текст
    MATHEMATICAL = "mathematical"  # Математические формулы
    CODE = "code"  # Программный код
    DIAGRAM = "diagram"  # Диаграммы и графики
    TABLE = "table"  # Таблицы
    FORMULA_CHEMICAL = "chemical"  # Химические формулы
    EQUATION = "equation"  # Уравнения
    LIST = "list"  # Списки
    MIXED = "mixed"  # Смешанный контент


class ContentIntelligence:
    """
    Умная детекция типов контента и адаптация стратегии объяснения
    """
    
    # Паттерны для детекции математики
    MATH_PATTERNS = [
        r'[∫∑∏√∂∇∆]',  # Математические символы
        r'[α-ωΑ-Ω]',  # Греческие буквы
        r'\^[\d\w]+',  # Степени
        r'_{[\w\d]+}',  # Индексы
        r'\b\w+\s*[=≈≠<>≤≥]\s*\w+',  # Уравнения
        r'\b(sin|cos|tan|log|ln|exp|lim|dx|dy)\b',  # Математические функции
        r'∈|∉|⊂|⊃|∪|∩|∅',  # Теория множеств
    ]
    
    # Паттерны для детекции кода
    CODE_PATTERNS = [
        r'\b(function|def|class|import|from|return|if|else|for|while)\b',  # Ключевые слова
        r'[{}\[\]();]',  # Синтаксис
        r'=>|->|::|\.\.\.|\|\|',  # Операторы
        r'\b\w+\.\w+\(',  # Вызовы методов
        r'//|/\*|\*/|#.*$',  # Комментарии
        r'<[a-zA-Z]+.*?>',  # HTML теги
    ]
    
    # Паттерны для химии
    CHEMISTRY_PATTERNS = [
        r'\b[A-Z][a-z]?\d*',  # Химические элементы (H2O, CO2)
        r'[→⇌⇄]',  # Стрелки реакций
        r'\b(acid|base|pH|mol|catalyst)\b',
    ]
    
    def __init__(self):
        self.math_regex = re.compile('|'.join(self.MATH_PATTERNS))
        self.code_regex = re.compile('|'.join(self.CODE_PATTERNS))
        self.chemistry_regex = re.compile('|'.join(self.CHEMISTRY_PATTERNS))
    
    def detect_content_type(
        self,
        elements: List[Dict[str, Any]],
        slide_image_path: Optional[str] = None
    ) -> Tuple[ContentType, Dict[str, Any]]:
        """
        Определяет тип контента на слайде
        
        Args:
            elements: OCR элементы с текстом
            slide_image_path: Путь к изображению (для визуального анализа)
            
        Returns:
            (content_type, strategy_config)
        """
        # Собираем весь текст
        all_text = " ".join([elem.get("text", "") for elem in elements])
        
        # Подсчёт совпадений
        math_score = len(self.math_regex.findall(all_text))
        code_score = len(self.code_regex.findall(all_text))
        chemistry_score = len(self.chemistry_regex.findall(all_text))
        
        # Проверяем наличие таблиц
        table_elements = [e for e in elements if e.get("type") in ["table", "table_cell"]]
        has_table = len(table_elements) > 0
        
        # Проверяем наличие списков
        list_elements = [e for e in elements if e.get("type") == "list_item"]
        has_list = len(list_elements) > 3
        
        # Анализируем структуру элементов
        figure_elements = [e for e in elements if e.get("type") == "figure"]
        has_diagram = len(figure_elements) > 0
        
        # Определяем основной тип
        scores = {
            ContentType.MATHEMATICAL: math_score,
            ContentType.CODE: code_score,
            ContentType.FORMULA_CHEMICAL: chemistry_score,
        }
        
        max_score = max(scores.values())
        
        # Логика определения типа
        if max_score > 5:
            content_type = max(scores, key=scores.get)
        elif has_table:
            content_type = ContentType.TABLE
        elif has_list:
            content_type = ContentType.LIST
        elif has_diagram:
            content_type = ContentType.DIAGRAM
        else:
            content_type = ContentType.TEXT
        
        # Создаём стратегию обработки
        strategy = self._create_strategy(content_type, {
            "math_score": math_score,
            "code_score": code_score,
            "has_table": has_table,
            "has_list": has_list,
            "has_diagram": has_diagram,
            "element_count": len(elements),
        })
        
        logger.info(
            f"Detected content type: {content_type.value} "
            f"(math:{math_score}, code:{code_score}, table:{has_table})"
        )
        
        return content_type, strategy
    
    def _create_strategy(
        self,
        content_type: ContentType,
        detection_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Создать стратегию обработки для типа контента"""
        
        strategies = {
            ContentType.MATHEMATICAL: {
                "description": "Математический контент с формулами",
                "needs_step_by_step": True,
                "visual_focus": "formulas",
                "pace": "slow",
                "complexity": 0.8,
                "speaking_rate": 0.9,
                "explanation_style": "sequential",
                "prompt_additions": """
IMPORTANT: This slide contains mathematical formulas.
- Explain each formula step by step
- Define all variables and symbols
- Show the logical progression
- Provide intuition before diving into math
- Use phrases like "let's break this down" or "step by step"
""",
                "visual_effects": ["spotlight_formula", "sequential_reveal"],
                "recommended_duration_multiplier": 1.5,
            },
            
            ContentType.CODE: {
                "description": "Программный код",
                "needs_syntax_highlight": True,
                "explain_line_by_line": True,
                "visual_focus": "code_blocks",
                "pace": "methodical",
                "complexity": 0.7,
                "speaking_rate": 0.95,
                "explanation_style": "line_by_line",
                "prompt_additions": """
IMPORTANT: This slide contains code.
- Explain the code's purpose first
- Walk through line by line
- Highlight key logic and patterns
- Explain what each part does and why
- Use phrases like "this line does..." or "notice how..."
""",
                "visual_effects": ["code_highlight", "line_by_line"],
                "recommended_duration_multiplier": 1.3,
            },
            
            ContentType.DIAGRAM: {
                "description": "Диаграмма или график",
                "needs_pointer": True,
                "explain_relationships": True,
                "visual_focus": "diagram_elements",
                "pace": "moderate",
                "complexity": 0.6,
                "speaking_rate": 1.0,
                "explanation_style": "spatial",
                "prompt_additions": """
IMPORTANT: This slide contains a diagram or chart.
- Start with the big picture/overview
- Explain relationships between elements
- Guide attention spatially (top to bottom, left to right)
- Highlight key connections
- Use phrases like "notice the connection" or "moving to..."
""",
                "visual_effects": ["pointer_animated", "element_connections"],
                "recommended_duration_multiplier": 1.2,
            },
            
            ContentType.TABLE: {
                "description": "Табличные данные",
                "needs_structured_reading": True,
                "visual_focus": "table_cells",
                "pace": "systematic",
                "complexity": 0.5,
                "speaking_rate": 1.0,
                "explanation_style": "structured",
                "prompt_additions": """
IMPORTANT: This slide contains a table.
- Explain what the table shows (rows/columns meaning)
- Highlight key data points or patterns
- Compare important values
- Don't read every cell - focus on insights
- Use phrases like "notice the pattern" or "the key takeaway is..."
""",
                "visual_effects": ["row_highlight", "cell_spotlight"],
                "recommended_duration_multiplier": 1.1,
            },
            
            ContentType.LIST: {
                "description": "Списки и перечисления",
                "needs_sequential_reveal": True,
                "visual_focus": "list_items",
                "pace": "steady",
                "complexity": 0.4,
                "speaking_rate": 1.0,
                "explanation_style": "sequential",
                "prompt_additions": """
IMPORTANT: This slide contains a list.
- Introduce the list's purpose/context
- Explain each point with examples
- Show connections between items
- Provide context for each item
- Use phrases like "first...", "next...", "finally..."
""",
                "visual_effects": ["sequential_cascade", "bullet_reveal"],
                "recommended_duration_multiplier": 1.0,
            },
            
            ContentType.TEXT: {
                "description": "Текстовый контент",
                "visual_focus": "text_blocks",
                "pace": "natural",
                "complexity": 0.5,
                "speaking_rate": 1.0,
                "explanation_style": "narrative",
                "prompt_additions": """
This is a text-heavy slide.
- Don't read the text verbatim
- Explain the concepts in your own words
- Provide context and examples
- Make it engaging and conversational
""",
                "visual_effects": ["highlight", "paragraph_focus"],
                "recommended_duration_multiplier": 1.0,
            },
        }
        
        strategy = strategies.get(content_type, strategies[ContentType.TEXT])
        
        # Добавляем информацию о детекции
        strategy["detection_info"] = detection_info
        strategy["content_type"] = content_type.value
        
        return strategy
    
    def analyze_complexity(
        self,
        elements: List[Dict[str, Any]],
        content_type: ContentType
    ) -> float:
        """
        Анализирует сложность контента (0.0 - 1.0)
        
        Returns:
            Complexity score где 0.0 = простой, 1.0 = очень сложный
        """
        if not elements:
            return 0.5
        
        # Базовые метрики
        total_chars = sum(len(e.get("text", "")) for e in elements)
        avg_word_length = total_chars / max(len(elements), 1) / 5  # Примерно слов
        
        # Количество элементов
        element_count = len(elements)
        
        # Базовая сложность
        complexity = 0.5
        
        # Корректировка на основе типа
        type_complexity = {
            ContentType.MATHEMATICAL: 0.8,
            ContentType.CODE: 0.7,
            ContentType.FORMULA_CHEMICAL: 0.75,
            ContentType.EQUATION: 0.8,
            ContentType.DIAGRAM: 0.6,
            ContentType.TABLE: 0.5,
            ContentType.LIST: 0.4,
            ContentType.TEXT: 0.5,
        }
        
        complexity = type_complexity.get(content_type, 0.5)
        
        # Корректировка на основе объёма
        if element_count > 10:
            complexity += 0.1
        if total_chars > 500:
            complexity += 0.1
        
        # Ограничиваем диапазон
        complexity = max(0.1, min(1.0, complexity))
        
        logger.debug(
            f"Complexity analysis: type={content_type.value}, "
            f"elements={element_count}, chars={total_chars}, score={complexity:.2f}"
        )
        
        return complexity
    
    def get_recommended_effects(
        self,
        content_type: ContentType,
        element_count: int
    ) -> List[str]:
        """Получить рекомендованные визуальные эффекты"""
        strategy = self._create_strategy(content_type, {})
        effects = strategy.get("visual_effects", ["highlight"])
        
        # Адаптируем под количество элементов
        if element_count > 8 and "sequential_cascade" not in effects:
            effects.append("sequential_cascade")
        
        return effects
    
    def get_explanation_instructions(
        self,
        content_type: ContentType,
        elements: List[Dict[str, Any]]
    ) -> str:
        """Получить специальные инструкции для объяснения"""
        strategy = self._create_strategy(content_type, {})
        return strategy.get("prompt_additions", "")
    
    def should_use_step_by_step(self, content_type: ContentType) -> bool:
        """Определить нужно ли пошаговое объяснение"""
        return content_type in [
            ContentType.MATHEMATICAL,
            ContentType.CODE,
            ContentType.EQUATION,
        ]
    
    def get_optimal_speaking_rate(
        self,
        content_type: ContentType,
        complexity: float
    ) -> float:
        """Получить оптимальную скорость речи"""
        strategy = self._create_strategy(content_type, {})
        base_rate = strategy.get("speaking_rate", 1.0)
        
        # Корректируем на основе сложности
        if complexity > 0.7:
            base_rate *= 0.95
        elif complexity < 0.3:
            base_rate *= 1.05
        
        return max(0.8, min(1.2, base_rate))


# Utility функции
def detect_content(elements: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
    """Удобная функция для детекции контента"""
    intelligence = ContentIntelligence()
    content_type, strategy = intelligence.detect_content_type(elements)
    return content_type.value, strategy


def get_complexity(elements: List[Dict[str, Any]], content_type: str = "text") -> float:
    """Удобная функция для анализа сложности"""
    intelligence = ContentIntelligence()
    try:
        ct = ContentType(content_type)
    except ValueError:
        ct = ContentType.TEXT
    return intelligence.analyze_complexity(elements, ct)
