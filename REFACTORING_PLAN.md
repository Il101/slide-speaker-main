# 🔧 Refactoring Plan - Pipeline Services

**Дата:** 2 ноября 2025  
**Приоритет:** MEDIUM (после diagram detection)  
**Статус:** Планирование

---

## 📊 Текущее состояние

### Размеры файлов:
```
backend/app/services/visual_effects_engine.py    1,935 строк  🔴
backend/app/pipeline/intelligent_optimized.py    1,549 строк  🟠
backend/app/services/smart_script_generator.py     749 строк  🟡
backend/app/services/semantic_analyzer_gemini.py   303 строки 🟢
```

### Проблемные методы:
```python
generate_cues_from_semantic_map()     218 строк  # God method
_generate_group_cues()                 154 строки
_find_element_mention_timing()         149 строк
_generate_diagram_cues()               136 строк  # Новый
_generate_smart_element_cues()         133 строки
```

---

## 🎯 Цели рефакторинга

1. ✅ **Single Responsibility Principle** - один класс = одна задача
2. ✅ **DRY** - избавиться от дублирования
3. ✅ **Testability** - легко тестировать отдельные компоненты
4. ✅ **Maintainability** - понятная структура
5. ✅ **Performance** - не ухудшить производительность

---

## 📦 Предлагаемая архитектура

### Phase 1: Visual Effects Engine (High Priority)

#### Текущая структура (плохо):
```
VisualEffectsEngine (1,935 строк)
├─ generate_cues_from_semantic_map()
├─ _generate_diagram_cues()
├─ _generate_group_cues()
├─ _find_element_mention_timing()
├─ _translate_term_to_russian()  ← Не его задача!
├─ _detect_language()             ← Не его задача!
└─ ... ещё 20 методов
```

#### Предлагаемая структура (хорошо):
```
visual_effects/
├─ __init__.py
├─ engine.py                    # Главный оркестратор (~200 строк)
├─ cue_generators/
│  ├─ __init__.py
│  ├─ base_generator.py        # Базовый класс
│  ├─ text_cue_generator.py    # Для текста
│  ├─ diagram_cue_generator.py # Для диаграмм ✨
│  └─ group_cue_generator.py   # Для групп
├─ timing/
│  ├─ __init__.py
│  ├─ timing_finder.py         # Поиск timing
│  ├─ word_matcher.py          # Поиск в словах
│  └─ tts_parser.py            # Парсинг TTS
├─ translation/                 # Вынести в отдельный сервис
│  ├─ __init__.py
│  └─ term_translator.py
└─ validators/
   ├─ __init__.py
   └─ cue_validator.py
```

### Phase 2: Pipeline Orchestration (Medium Priority)

#### Текущая структура:
```
OptimizedIntelligentPipeline (1,549 строк)
├─ extract_from_powerpoint()
├─ extract_elements_ocr()       # Stage 2 + Translation + Diagrams
├─ plan()                       # Stage 3-4 (parallel)
├─ generate()                   # Stage 5-6 (TTS + Effects)
└─ ... много вспомогательных методов
```

#### Предлагаемая структура:
```
pipeline/
├─ __init__.py
├─ orchestrator.py              # Главный Pipeline (~300 строк)
├─ stages/
│  ├─ __init__.py
│  ├─ stage_1_extraction.py    # PowerPoint → PNG
│  ├─ stage_2_ocr.py           # OCR + Diagrams + Translation
│  ├─ stage_3_analysis.py      # Semantic Analysis
│  ├─ stage_4_script.py        # Script Generation
│  ├─ stage_5_tts.py           # TTS Synthesis
│  └─ stage_6_effects.py       # Visual Effects
└─ parallel/
   ├─ __init__.py
   └─ parallel_processor.py    # Параллельная обработка
```

---

## 🔨 Implementation Plan

### Week 1: Visual Effects Refactoring

#### Day 1-2: Extract Timing Logic
```bash
# Создать timing модуль
mkdir -p backend/app/services/visual_effects/timing

# Переместить методы:
- _extract_word_timings()
- _find_group_timing()
- _find_element_mention_timing()
- _find_timing_by_first_words()
- _find_text_timing_from_sentences()
→ timing/timing_finder.py
```

#### Day 3: Extract Translation Logic
```bash
# Создать translation сервис (или использовать существующий)
mkdir -p backend/app/services/translation

# Переместить:
- _translate_term_to_russian()
- _detect_language()
→ translation/term_translator.py (или использовать TranslationService)
```

#### Day 4-5: Refactor Cue Generators
```bash
# Создать иерархию генераторов
mkdir -p backend/app/services/visual_effects/cue_generators

# Разбить:
- _generate_diagram_cues() → diagram_cue_generator.py (136 строк)
- _generate_group_cues() → group_cue_generator.py (154 строки)
- _generate_smart_element_cues() → smart_element_generator.py
- _generate_sequential_element_cues() → sequential_generator.py
```

### Week 2: Pipeline Refactoring

#### Day 1-2: Extract Stages
```bash
# Создать stage модули
mkdir -p backend/app/pipeline/stages

# Переместить логику:
- extract_elements_ocr() → stage_2_ocr.py
- plan() → stage_3_analysis.py + stage_4_script.py
- generate() → stage_5_tts.py + stage_6_effects.py
```

#### Day 3-4: Orchestrator
```python
# Упростить главный Pipeline
class OptimizedIntelligentPipeline(BasePipeline):
    def __init__(self):
        self.stages = {
            1: Stage1Extraction(),
            2: Stage2OCR(),
            3: Stage3Analysis(),
            4: Stage4Script(),
            5: Stage5TTS(),
            6: Stage6Effects()
        }
    
    async def process(self, lesson_dir: str):
        for stage_num, stage in self.stages.items():
            logger.info(f"🔄 Stage {stage_num}: {stage.name}")
            await stage.execute(lesson_dir)
```

#### Day 5: Testing & Integration
```bash
# Запустить все тесты
pytest backend/tests/ -v

# Интеграционные тесты
python test_pipeline_detailed.py
```

---

## 📏 Success Metrics

### Code Quality:
- ✅ Максимальный размер файла: 500 строк
- ✅ Максимальный размер метода: 50 строк
- ✅ Cyclomatic complexity: < 10
- ✅ Test coverage: > 80%

### Performance:
- ✅ Время обработки: не хуже текущего
- ✅ Memory usage: не больше текущего
- ✅ API calls: не больше текущего

### Maintainability:
- ✅ Понятная структура директорий
- ✅ Документация для каждого модуля
- ✅ Примеры использования

---

## 🚨 Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Регрессия в функциональности | HIGH | MEDIUM | Comprehensive tests before refactoring |
| Увеличение времени обработки | MEDIUM | LOW | Benchmark на каждом этапе |
| Сломать существующий API | HIGH | LOW | Сохранить обратную совместимость |
| Конфликты при мерже | MEDIUM | MEDIUM | Создать отдельную ветку `refactoring` |

---

## 🎯 Priority Refactorings

### Must Have (Priority 1):
1. ✅ **Extract TimingFinder** - используется везде
2. ✅ **Split CueGenerators** - самая большая часть
3. ✅ **Separate Diagram Logic** - новая функциональность

### Should Have (Priority 2):
4. ⚡ Pipeline stages extraction
5. ⚡ Translation service separation
6. ⚡ Validator extraction

### Nice to Have (Priority 3):
7. 💡 Add type hints везде
8. 💡 Add docstrings для всех методов
9. 💡 Create architecture diagram

---

## 🔄 Migration Strategy

### Option 1: Big Bang (Not Recommended)
- Сделать всё сразу
- ❌ Высокий риск
- ❌ Долго без feedback

### Option 2: Strangler Pattern (Recommended)
- Постепенная миграция
- ✅ Старый и новый код работают параллельно
- ✅ Можно откатить в любой момент

```python
# Example:
class VisualEffectsEngine:
    def __init__(self):
        self.use_new_generators = os.getenv('USE_NEW_CUE_GENERATORS', 'false') == 'true'
        
        if self.use_new_generators:
            from .cue_generators import DiagramCueGenerator
            self.diagram_generator = DiagramCueGenerator()
    
    def _generate_diagram_cues(self, ...):
        if self.use_new_generators:
            return self.diagram_generator.generate(...)
        else:
            # Legacy code
            return self._generate_diagram_cues_legacy(...)
```

---

## 📝 Example: DiagramCueGenerator Extraction

### Before (in visual_effects_engine.py):
```python
class VisualEffectsEngine:
    def _generate_diagram_cues(self, diagram_element, talk_track, tts_words):
        """136 строк кода здесь"""
        cues = []
        # ... 136 lines of logic ...
        return cues
```

### After (new structure):
```python
# backend/app/services/visual_effects/cue_generators/diagram_cue_generator.py

class DiagramCueGenerator(BaseCueGenerator):
    """Generates visual cues for diagrams with progressive reveal"""
    
    def generate(self, diagram_element, talk_track, tts_words):
        """Main entry point"""
        cues = []
        cues.extend(self._generate_overview_cue(diagram_element, talk_track))
        cues.extend(self._generate_walkthrough_cues(diagram_element, talk_track))
        cues.extend(self._generate_conclusion_cue(diagram_element, talk_track))
        return cues
    
    def _generate_overview_cue(self, diagram_element, talk_track):
        """~30 lines"""
        ...
    
    def _generate_walkthrough_cues(self, diagram_element, talk_track):
        """~50 lines"""
        ...
    
    def _generate_conclusion_cue(self, diagram_element, talk_track):
        """~20 lines"""
        ...
```

---

## 🧪 Testing Strategy

### Unit Tests:
```bash
# Тесты для каждого нового модуля
tests/
├─ visual_effects/
│  ├─ test_diagram_cue_generator.py
│  ├─ test_timing_finder.py
│  └─ test_group_cue_generator.py
└─ pipeline/
   └─ stages/
      ├─ test_stage_2_ocr.py
      └─ test_stage_6_effects.py
```

### Integration Tests:
```bash
# Убедиться что всё работает вместе
pytest tests/integration/test_full_pipeline.py -v
```

---

## 📅 Timeline

| Week | Tasks | Deliverables |
|------|-------|--------------|
| **Week 1** | Visual Effects Refactoring | New cue_generators module |
| **Week 2** | Pipeline Refactoring | New stages module |
| **Week 3** | Testing & Documentation | All tests passing, docs updated |
| **Week 4** | Performance optimization | Benchmarks, cleanup |

**Total:** ~4 weeks (при 1 разработчике, part-time)

---

## 💰 Cost-Benefit Analysis

### Costs:
- 👨‍💻 Development time: 4 weeks
- 🧪 Testing time: 1 week
- 📝 Documentation: 2 days
- **Total:** ~5 weeks effort

### Benefits:
- ✅ Easier to maintain (+50% faster bug fixes)
- ✅ Easier to test (+80% coverage possible)
- ✅ Easier to extend (+30% faster new features)
- ✅ Better code quality (Reduced complexity)
- ✅ Onboarding new developers faster

**ROI:** Положительный после 3-4 месяцев

---

## 🚀 Quick Wins (Can Start Now)

### 1. Extract TimingFinder (1 day):
```bash
# Immediate benefit, low risk
mkdir -p backend/app/services/visual_effects/timing
# Move timing methods → timing_finder.py
```

### 2. Extract DiagramCueGenerator (1 day):
```bash
# Already isolated, easy to extract
mkdir -p backend/app/services/visual_effects/cue_generators
# Move _generate_diagram_cues() → diagram_cue_generator.py
```

### 3. Add type hints to public methods (2 days):
```python
# Improves IDE support and catches bugs
def generate_cues_from_semantic_map(
    self,
    semantic_map: Dict[str, Any],
    elements: List[Dict[str, Any]],
    audio_duration: float,
    tts_words: Optional[Dict[str, Any]] = None,
    talk_track: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
```

---

## 🎓 Lessons Learned

### Why files grow:
1. ✅ Feature creep - добавляем функции без рефакторинга
2. ✅ "Quick fixes" - временные решения становятся постоянными
3. ✅ Lack of architecture review - не планируем структуру заранее
4. ✅ Fear of breaking - боимся трогать работающий код

### Prevention:
1. ✅ Regular code reviews
2. ✅ Set file size limits (500 lines max)
3. ✅ Refactor as you go (Boy Scout Rule)
4. ✅ Architecture discussions before big features

---

_Plan created: 2 ноября 2025_  
_Status: Ready for approval_ 📋
