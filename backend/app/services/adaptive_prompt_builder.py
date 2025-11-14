"""
Adaptive Prompt Builder - умное построение промптов на основе характеристик слайда
Адаптирует детализацию и инструкции в зависимости от плотности информации и сложности
"""
import logging
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)


class AdaptivePromptBuilder:
    """
    Строит контекстно-зависимые промпты для генерации скриптов
    Адаптируется к:
    - Визуальной плотности слайда (visual_density)
    - Когнитивной нагрузке (cognitive_load)
    - Типу контента (content_type)
    - Важности групп (priority + educational_intent)
    """
    
    # Веса для расчёта важности группы
    PRIORITY_WEIGHTS = {
        'high': 10.0,
        'medium': 5.0,
        'low': 2.0,
        'none': 0.0
    }
    
    TYPE_WEIGHTS = {
        'title': 1.5,  # ✅ FIX: Снижен вес - заголовки нужно только НАЗВАТЬ, не разбирать
        'heading': 2.5,
        'key_point': 2.0,
        'example': 1.5,
        'content': 1.0,
        'diagram': 2.0,
        'table': 1.8,
        'footer': 0.1,
        'watermark': 0.0,
        'decorative': 0.0
    }
    
    def __init__(self):
        pass
    
    def build_adaptive_groups_section(
        self,
        semantic_map: Dict[str, Any],
        ocr_elements: List[Dict[str, Any]],
        max_groups: Optional[int] = None
    ) -> Tuple[str, List[Dict[str, Any]], int]:
        """
        Строит адаптивную секцию с группами для промпта
        
        Args:
            semantic_map: Semantic map с группами и метриками
            ocr_elements: OCR элементы для извлечения текста
            max_groups: Максимум групп (если None, определяется автоматически)
            
        Returns:
            (groups_section_text, filtered_groups, optimal_duration)
        """
        groups = semantic_map.get('groups', [])
        visual_density = semantic_map.get('visual_density', 'medium')
        cognitive_load = semantic_map.get('cognitive_load', 'medium')
        
        # 1. Фильтруем и ранжируем группы
        filtered_groups = self._filter_and_rank_groups(
            groups, 
            visual_density, 
            cognitive_load,
            max_groups
        )
        
        # 2. Определяем уровень детализации для каждой группы
        groups_with_depth = self._assign_explanation_depth(
            filtered_groups,
            visual_density,
            cognitive_load
        )
        
        # 3. Строим текст секции
        elements_by_id = {elem.get('id'): elem for elem in ocr_elements}
        groups_text = self._format_groups_section(
            groups_with_depth,
            elements_by_id,
            visual_density,
            cognitive_load
        )
        
        # 4. Рассчитываем оптимальную длительность
        optimal_duration = self._calculate_optimal_duration(
            filtered_groups,
            visual_density,
            cognitive_load
        )
        
        return groups_text, filtered_groups, optimal_duration
    
    def generate_adaptive_instructions(
        self,
        semantic_map: Dict[str, Any],
        content_strategy: Dict[str, Any],
        filtered_groups_count: int
    ) -> str:
        """
        Генерирует адаптивные инструкции на основе характеристик слайда
        
        Returns:
            Текст инструкций для включения в промпт
        """
        visual_density = semantic_map.get('visual_density', 'medium')
        cognitive_load = semantic_map.get('cognitive_load', 'medium')
        content_type = content_strategy.get('content_type', 'text')
        
        instructions = []
        
        # Базовая стратегия на основе плотности
        if visual_density == 'high':
            instructions.append("""
⚡ CRITICAL STRATEGY - HIGH DENSITY SLIDE:
This slide is PACKED with information - you MUST be CONCISE!
- Focus ONLY on the TOP priority groups marked above
- Aim for 20-30 seconds total (NO MORE!)
- Mention key terms but DON'T elaborate on everything
- Skip examples and analogies - get to the point
- Use phrases like "ключевой момент здесь", "главное"
""")
        elif visual_density == 'low':
            instructions.append("""
📖 STRATEGY - LOW DENSITY SLIDE:
This slide has limited information - you can ELABORATE more:
- Take 40-60 seconds
- Add examples and real-world analogies
- Explain WHY concepts matter
- Provide context and connections
- Make it engaging and conversational
""")
        else:  # medium
            instructions.append("""
⚖️ STRATEGY - BALANCED SLIDE:
Standard information density - use balanced approach:
- Aim for 30-45 seconds
- Focus on high-priority groups
- Add brief examples where helpful
- Maintain good pace
""")
        
        # Адаптация к когнитивной нагрузке
        if cognitive_load == 'complex':
            instructions.append("""
🧠 COMPLEXITY HANDLING:
This content is COMPLEX - help students understand:
- Break down concepts step-by-step
- Use simpler language and analogies
- Explain the "why" before the "what"
- Pause between major concepts [pause:500ms]
- Slow down speaking rate [rate:90%] for key definitions
""")
        elif cognitive_load == 'easy':
            instructions.append("""
✅ EASY CONTENT:
This is straightforward - maintain energy:
- Keep good pace
- Be conversational
- Can speak faster [rate:110%] for known concepts
""")
        
        # Специальные инструкции по типу контента
        content_instructions = content_strategy.get('prompt_additions', '')
        if content_instructions:
            instructions.append(f"\n📋 CONTENT-SPECIFIC INSTRUCTIONS:\n{content_instructions}")
        
        return "\n".join(instructions)
    
    def _calculate_group_importance(self, group: Dict[str, Any]) -> float:
        """
        Рассчитывает важность группы для ранжирования
        
        Факторы:
        - priority (high/medium/low/none)
        - type (title/heading/key_point/...)
        - educational_intent (наличие и содержание)
        - размер (количество элементов)
        - позиция в reading_order
        """
        score = 0.0
        
        # Базовый вес от priority
        priority = group.get('priority', 'medium')
        score += self.PRIORITY_WEIGHTS.get(priority, 0.0)
        
        # Вес от типа группы
        group_type = group.get('type', 'content')
        score += self.TYPE_WEIGHTS.get(group_type, 1.0)
        
        # Бонус за наличие educational_intent
        intent = group.get('educational_intent', '')
        if intent and intent.lower() not in ['n/a', 'none', '']:
            score += 2.0
        
        # Бонус за размер группы (больше элементов = важнее)
        element_ids = group.get('element_ids', [])
        score += min(len(element_ids) * 0.3, 2.0)  # Max +2.0
        
        # Бонус за позицию в reading_order (первые элементы важнее)
        reading_order = group.get('reading_order', [])
        if reading_order:
            avg_position = sum(reading_order) / len(reading_order)
            # Первые элементы получают бонус
            position_bonus = max(0, 2.0 - avg_position * 0.2)
            score += position_bonus
        
        # Проверка на highlight_strategy
        highlight = group.get('highlight_strategy', {})
        if highlight.get('when') not in ['never', None]:
            score += 1.0
        
        return score
    
    def _filter_and_rank_groups(
        self,
        groups: List[Dict[str, Any]],
        visual_density: str,
        cognitive_load: str,
        max_groups: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Фильтрует и ранжирует группы по важности
        Адаптирует количество групп к плотности слайда
        """
        if not groups:
            return []
        
        # Рассчитываем importance score для каждой группы
        scored_groups = []
        for group in groups:
            score = self._calculate_group_importance(group)
            scored_groups.append((score, group))
        
        # Сортируем по убыванию важности
        scored_groups.sort(reverse=True, key=lambda x: x[0])
        
        # Определяем максимум групп на основе плотности
        if max_groups is None:
            if visual_density == 'high':
                max_groups = 4  # Только топ-4 для плотных слайдов
            elif visual_density == 'low':
                max_groups = 10  # Можно больше деталей
            else:
                max_groups = 6  # Средний вариант
        
        # Дополнительная фильтрация: убираем группы с priority='none'
        filtered = []
        for score, group in scored_groups:
            if group.get('priority') != 'none' and score > 0:
                filtered.append(group)
        
        # Возвращаем топ-N
        result = filtered[:max_groups]
        
        logger.info(
            f"Filtered groups: {len(result)}/{len(groups)} total "
            f"(density={visual_density}, max={max_groups})"
        )
        
        return result
    
    def _assign_explanation_depth(
        self,
        groups: List[Dict[str, Any]],
        visual_density: str,
        cognitive_load: str
    ) -> List[Tuple[Dict[str, Any], str]]:
        """
        Назначает уровень детализации объяснения для каждой группы
        
        Depth levels:
        - DETAILED: подробное объяснение с примерами
        - BRIEF: краткое объяснение + 1 пример
        - MENTION: только упомянуть
        - SKIP: пропустить
        """
        groups_with_depth = []
        
        for i, group in enumerate(groups):
            priority = group.get('priority', 'medium')
            group_type = group.get('type', 'content')
            
            # Определяем глубину объяснения
            if visual_density == 'high':
                # Для плотных слайдов - минимальная детализация
                if i == 0 and priority == 'high':
                    depth = 'DETAILED'  # Только первая группа подробно
                elif priority == 'high':
                    depth = 'BRIEF'
                else:
                    depth = 'MENTION'
            
            elif visual_density == 'low':
                # Для простых слайдов - больше деталей
                if priority == 'high':
                    depth = 'DETAILED'
                elif priority == 'medium':
                    depth = 'BRIEF'
                else:
                    depth = 'MENTION'
            
            else:  # medium
                # Средний вариант
                if i < 2 and priority == 'high':
                    depth = 'DETAILED'
                elif priority in ['high', 'medium']:
                    depth = 'BRIEF'
                else:
                    depth = 'MENTION'
            
            # Корректировка для когнитивной нагрузки
            if cognitive_load == 'complex' and depth == 'MENTION':
                depth = 'BRIEF'  # Сложные концепты нельзя просто упомянуть
            
            groups_with_depth.append((group, depth))
        
        return groups_with_depth
    
    def _format_groups_section(
        self,
        groups_with_depth: List[Tuple[Dict[str, Any], str]],
        elements_by_id: Dict[str, Any],
        visual_density: str,
        cognitive_load: str
    ) -> str:
        """
        Форматирует секцию с группами для промпта
        """
        if not groups_with_depth:
            return "No significant groups found"
        
        lines = []
        
        # Заголовок с метриками
        lines.append(f"""
SLIDE ANALYSIS:
- Visual Density: {visual_density.upper()}
- Cognitive Load: {cognitive_load.upper()}
- Top Priority Groups: {len(groups_with_depth)}
""")
        
        # Добавляем группы с рекомендациями
        lines.append("\nTOP PRIORITY GROUPS (explain these):")
        
        for i, (group, depth) in enumerate(groups_with_depth):
            group_id = group.get('id', f'group_{i}')
            group_type = group.get('type', 'content')
            priority = group.get('priority', 'medium')
            intent = group.get('educational_intent', 'N/A')
            
            # Извлекаем текст из элементов группы
            # ✅ CRITICAL: Use translated text to avoid mixing languages in TTS
            element_ids = group.get('element_ids', [])
            element_texts = []
            for elem_id in element_ids[:3]:  # Max 3 элемента
                if elem_id in elements_by_id:
                    # Prefer translated text if available, fallback to original
                    elem = elements_by_id[elem_id]
                    text = (elem.get('text_translated') or elem.get('text', '')).strip()
                    if text:
                        element_texts.append(text[:60])
            
            text_summary = ' | '.join(element_texts) if element_texts else 'No text'
            
            # Символы приоритета
            priority_symbols = {
                'high': '⭐⭐⭐',
                'medium': '⭐⭐',
                'low': '⭐'
            }
            stars = priority_symbols.get(priority, '⭐')
            
            # Инструкция по depth
            # ✅ CRITICAL: If group has multiple elements, ALWAYS mention each one
            element_count = len(element_ids)

            depth_instructions = {
                'DETAILED': '📖 Explain in detail with examples',
                'BRIEF': '📝 Brief explanation + 1 example',
                'MENTION': '💬 Just mention key point',
                'SKIP': '⏭️ Skip'
            }
            depth_hint = depth_instructions.get(depth, '')

            # ✅ Add special instruction for groups with multiple elements (lists/bullet points)
            if element_count > 1:
                depth_hint += f' | ⚠️ CRITICAL: This group has {element_count} items - mention EACH ONE separately in different sentences!'
            
            lines.append(f"""
{i+1}. {stars} {group_id} [{priority.upper()}, {group_type}]
   Text on slide: "{text_summary}"
   Intent: {intent}
   → {depth_hint}""")
        
        return "\n".join(lines)
    
    def _calculate_optimal_duration(
        self,
        groups: List[Dict[str, Any]],
        visual_density: str,
        cognitive_load: str
    ) -> int:
        """
        Рассчитывает оптимальную длительность скрипта
        
        Факторы:
        - Количество групп
        - Visual density
        - Cognitive load
        - Priority групп
        """
        if not groups:
            return 20
        
        # Базовая длительность: 10 секунд на группу (разумный темп объяснения)
        base_duration = len(groups) * 10
        
        # Корректировка на основе плотности
        density_multipliers = {
            'high': 0.7,    # 30% короче для плотных слайдов
            'medium': 1.0,
            'low': 1.3      # 30% длиннее для простых слайдов
        }
        multiplier = density_multipliers.get(visual_density, 1.0)
        base_duration *= multiplier
        
        # Корректировка на основе сложности
        complexity_multipliers = {
            'complex': 1.3,  # Сложные концепты требуют больше времени
            'medium': 1.0,
            'easy': 0.9
        }
        complexity_mult = complexity_multipliers.get(cognitive_load, 1.0)
        base_duration *= complexity_mult
        
        # Бонус за high-priority группы (они требуют больше внимания)
        high_priority_count = sum(1 for g in groups if g.get('priority') == 'high')
        if high_priority_count > 2:
            base_duration += (high_priority_count - 2) * 3
        
        # Ограничиваем диапазон (минимум зависит от плотности)
        min_duration = {
            'high': 20,    # Плотные слайды могут быть короче
            'medium': 25,
            'low': 30      # Простые слайды должны быть подробнее
        }.get(visual_density, 25)
        
        duration = int(max(min_duration, min(70, base_duration)))
        
        logger.info(
            f"Calculated optimal duration: {duration}s "
            f"(groups={len(groups)}, density={visual_density}, load={cognitive_load})"
        )
        
        return duration
    
    def build_duration_hint(
        self,
        optimal_duration: int,
        visual_density: str
    ) -> str:
        """
        Создаёт подсказку по длительности для промпта
        """
        if visual_density == 'high':
            return f"""
⏱️ TARGET DURATION: {optimal_duration-5}-{optimal_duration} seconds (STRICT LIMIT!)
This is a DENSE slide - be CONCISE! Every second counts.
"""
        elif visual_density == 'low':
            return f"""
⏱️ TARGET DURATION: {optimal_duration-5}-{optimal_duration+5} seconds
You have time to elaborate - use it wisely.
"""
        else:
            return f"""
⏱️ TARGET DURATION: {optimal_duration-5}-{optimal_duration+5} seconds
Maintain balanced pace.
"""
