# 🔧 План осторожного рефакторинга пайплайна

**Дата начала:** 2025-01-15  
**Стратегия:** Conservative, incremental improvements  
**Принцип:** "Сначала не навреди" (Hippocratic oath для кода)

---

## 📋 Оглавление

1. [Подготовка (Phase 0)](#phase-0-подготовка-1-2-дня)
2. [Baseline и защита (Phase 1)](#phase-1-baseline-и-защита-2-3-дня)
3. [Константы и типизация (Phase 2)](#phase-2-константы-и-типизация-3-4-дня)
4. [Извлечение утилит (Phase 3)](#phase-3-извлечение-утилит-1-неделя)
5. [Разделение на модули (Phase 4)](#phase-4-разделение-на-модули-2-недели)
6. [Оптимизация (Phase 5)](#phase-5-оптимизация-1-неделя)

**Общее время:** 4-6 недель (в зависимости от загруженности)

---

## Phase 0: Подготовка (1-2 дня)

### День 1: Анализ и документирование

#### Шаг 1.1: Создать baseline metrics

```bash
# Запустить все тесты и зафиксировать результаты
cd backend
pytest tests/ -v --tb=short > baseline_test_results.txt 2>&1

# Проверить coverage
pytest tests/ --cov=app --cov-report=html --cov-report=term > baseline_coverage.txt 2>&1

# Зафиксировать метрики
echo "=== Baseline Metrics ===" > BASELINE_METRICS.md
echo "Date: $(date)" >> BASELINE_METRICS.md
echo "" >> BASELINE_METRICS.md
echo "Test Results:" >> BASELINE_METRICS.md
grep -E "(passed|failed|error)" baseline_test_results.txt >> BASELINE_METRICS.md
echo "" >> BASELINE_METRICS.md
echo "Coverage:" >> BASELINE_METRICS.md
tail -20 baseline_coverage.txt >> BASELINE_METRICS.md
```

#### Шаг 1.2: Зафиксировать текущее поведение

```bash
# Создать snapshot тестов производительности
cat > tests/baseline/test_performance_snapshot.py << 'EOF'
"""
Baseline performance tests - DO NOT MODIFY
These tests capture current behavior before refactoring
"""
import pytest
import time
from pathlib import Path

@pytest.mark.baseline
class TestPerformanceBaseline:
    """Snapshot of current performance characteristics"""
    
    def test_ingest_speed_baseline(self, sample_pptx):
        """Baseline: ingest stage timing"""
        from app.pipeline import get_pipeline
        pipeline = get_pipeline("intelligent_optimized")()
        
        start = time.time()
        pipeline.ingest(str(sample_pptx))
        elapsed = time.time() - start
        
        # Document current performance (не assert!)
        print(f"\nBaseline ingest time: {elapsed:.2f}s")
        
    def test_full_pipeline_baseline(self, sample_lesson_dir):
        """Baseline: full pipeline timing"""
        from app.pipeline import get_pipeline
        pipeline = get_pipeline("intelligent_optimized")()
        
        start = time.time()
        result = pipeline.process_full_pipeline(str(sample_lesson_dir))
        elapsed = time.time() - start
        
        print(f"\nBaseline full pipeline time: {elapsed:.2f}s")
        print(f"Status: {result.get('status')}")
        
    def test_memory_baseline(self, sample_lesson_dir):
        """Baseline: memory usage"""
        import tracemalloc
        from app.pipeline import get_pipeline
        
        tracemalloc.start()
        pipeline = get_pipeline("intelligent_optimized")()
        pipeline.process_full_pipeline(str(sample_lesson_dir))
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        print(f"\nBaseline peak memory: {peak / (1024**3):.2f}GB")
EOF

# Запустить baseline тесты
pytest tests/baseline/test_performance_snapshot.py -v -s
```

#### Шаг 1.3: Документировать известные проблемы

```bash
cat > KNOWN_ISSUES.md << 'EOF'
# Известные проблемы и ограничения

## Критичные (НЕ ТРОГАТЬ без понимания):
- [ ] Sequential TTS (max_parallel_tts=1) - защита от OOM
- [ ] word_count > 400 ограничение - защита от длинных скриптов
- [ ] Aggressive gc.collect() после каждого слайда - необходимо для стабильности

## Некритичные (можно улучшать):
- [ ] Monolithic intelligent_optimized.py (1439 строк)
- [ ] Избыточное логирование в production
- [ ] Magic numbers (400, 300, 0.35, etc.)
- [ ] Отсутствие type hints в некоторых функциях

## Технический долг:
- [ ] Дублирование логики расчёта duration (3 места)
- [ ] Повторяющаяся логика загрузки/сохранения manifest
- [ ] SSML cleaning логика разбросана

## Production constraints (ВАЖНО!):
- Docker memory limit: 3.8GB (peak usage ~3.7GB)
- Max concurrent slides: 5
- Average processing time: 30-60s per slide
- LLM timeout: 30s (может быть недостаточно для сложных слайдов)
EOF
```

### День 2: Создание защитной сетки

#### Шаг 2.1: Добавить regression тесты

```bash
cat > tests/regression/test_regression_suite.py << 'EOF'
"""
Regression tests to prevent breaking existing functionality
Run before and after each refactoring step
"""
import pytest
from pathlib import Path

class TestRegressionSuite:
    """Critical functionality that must not break"""
    
    def test_pipeline_stages_order(self):
        """Ensure pipeline stages execute in correct order"""
        from app.pipeline.base import BasePipeline
        
        pipeline = BasePipeline.__subclasses__()[0]()
        
        # Verify method existence
        assert hasattr(pipeline, 'ingest')
        assert hasattr(pipeline, 'plan')
        assert hasattr(pipeline, 'tts')
        assert hasattr(pipeline, 'build_manifest')
        
    def test_manifest_structure(self, sample_manifest):
        """Ensure manifest structure remains compatible"""
        required_fields = ['slides', 'metadata']
        assert all(field in sample_manifest for field in required_fields)
        
        # Verify slide structure
        if sample_manifest['slides']:
            slide = sample_manifest['slides'][0]
            required_slide_fields = ['id', 'image', 'elements']
            assert all(field in slide for field in required_slide_fields)
    
    def test_error_handling_preserved(self):
        """Ensure error handling mechanisms work"""
        from app.core.error_handler import error_handler, ErrorCategory
        
        # Verify error handler exists and works
        assert error_handler is not None
        
        # Test categorization
        from app.core.error_handler import RateLimitError
        error = RateLimitError("Test")
        category = error_handler.categorize_error(error)
        assert category == ErrorCategory.TRANSIENT
    
    def test_fallback_mechanisms(self):
        """Ensure graceful degradation works"""
        from app.pipeline import get_pipeline
        
        pipeline = get_pipeline("intelligent_optimized")()
        
        # Verify fallback methods exist
        assert hasattr(pipeline, '_create_fallback_slide_data')
        
    @pytest.mark.asyncio
    async def test_parallel_processing_safe(self):
        """Ensure parallel processing doesn't cause race conditions"""
        import asyncio
        from app.pipeline import get_pipeline
        
        pipeline = get_pipeline("intelligent_optimized")()
        
        # Test that semaphore exists and works
        assert pipeline.max_parallel_slides > 0
        assert pipeline.max_parallel_tts == 1  # Critical: must be 1!
EOF

# Запустить regression suite
pytest tests/regression/ -v
```

#### Шаг 2.2: Настроить pre-commit hooks

```bash
cat > .pre-commit-config.yaml << 'EOF'
# Pre-commit hooks для безопасного рефакторинга
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-yaml
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: check-added-large-files
        args: ['--maxkb=1000']
      
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11
        
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--ignore-missing-imports]
        
  - repo: local
    hooks:
      - id: pytest-regression
        name: Run regression tests
        entry: pytest tests/regression/ -v --tb=short
        language: system
        pass_filenames: false
        always_run: true
EOF

# Установить pre-commit
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

---

## Phase 1: Baseline и защита (2-3 дня)

### День 3: Добавить константы (самое безопасное изменение)

#### Шаг 3.1: Создать файл констант

```bash
cat > backend/app/pipeline/constants.py << 'EOF'
"""
Pipeline constants - extracted from magic numbers
Centralized for easy tuning and documentation
"""

# === LLM Generation Limits ===
MAX_WORDS_PER_SLIDE = 400
"""
Maximum words in generated talk track per slide.
Rationale: Prevents overly long scripts (>2.5 min per slide).
History: Added to fix issue with 5-minute scripts for single slides.
"""

MAX_TOKENS_PER_SLIDE = 600
"""
Maximum tokens for LLM generation per slide.
Calculated: ~400 words * 1.5 tokens/word
"""

REASONABLE_WORD_COUNT_MIN = 200
REASONABLE_WORD_COUNT_MAX = 300
"""
Target word count range for optimal slide duration (60-90 seconds).
"""

# === Anti-Reading Thresholds ===
ANTI_READING_OVERLAP_THRESHOLD = 0.35
"""
Maximum text overlap between generated script and slide text.
Below this threshold = good (not just reading the slide).
Above this threshold = bad (reading the slide verbatim).
"""

# === Timeouts ===
LLM_REQUEST_TIMEOUT_SECONDS = 30.0
"""
Timeout for LLM API calls (Gemini, OpenRouter).
May need adjustment for complex slides.
"""

LLM_RETRY_TIMEOUT_SECONDS = 90.0
"""
Timeout for retry attempts on failed LLM calls.
Longer timeout to give slow requests a chance.
"""

TTS_REQUEST_TIMEOUT_SECONDS = 60.0
"""
Timeout for TTS generation per slide.
"""

TTS_RETRY_TIMEOUT_SECONDS = 90.0
"""
Timeout for TTS retry attempts.
"""

# === Parallelism Limits ===
DEFAULT_MAX_PARALLEL_SLIDES = 5
"""
Default maximum concurrent slides during plan() stage.
Can be overridden by PIPELINE_MAX_PARALLEL_SLIDES env var.
"""

DEFAULT_MAX_PARALLEL_TTS = 1
"""
⚠️ CRITICAL: Must be 1 to prevent OOM!
Silero TTS model + Whisper use ~1.5GB per concurrent request.
Docker limit is 3.8GB, so only 1 concurrent TTS is safe.
"""

# === Memory Management ===
MEMORY_PRESSURE_THRESHOLD_GB = 3.0
"""
Trigger aggressive cleanup when memory exceeds this threshold.
Docker limit: 3.8GB, so 3.0GB = ~80% usage.
"""

# === Duration Calculation ===
WORDS_PER_MINUTE_SPEECH_RATE = 150
"""
Average speech rate for Russian language.
Used to estimate audio duration from word count.
"""

TARGET_SLIDE_DURATION_SECONDS = 60
"""
Target duration per slide (60 seconds = 1 minute).
Used as baseline for adaptive duration calculation.
"""

MIN_SLIDE_DURATION_SECONDS = 30
MAX_SLIDE_DURATION_SECONDS = 120
"""
Min/max bounds for slide duration.
Prevents too-short or too-long slides.
"""

# === Complexity Thresholds ===
HIGH_COMPLEXITY_THRESHOLD = 0.7
MEDIUM_COMPLEXITY_THRESHOLD = 0.4
"""
Content complexity thresholds for adaptive duration.
complexity > 0.7 = high (add 50% time)
complexity > 0.4 = medium (normal time)
complexity <= 0.4 = low (reduce 20% time)
"""

# === Visual Density ===
VISUAL_DENSITY_HIGH_THRESHOLD = 20
VISUAL_DENSITY_MEDIUM_THRESHOLD = 10
"""
Number of visual elements that define density.
> 20 elements = high density
> 10 elements = medium density
<= 10 elements = low density
"""
EOF

git add backend/app/pipeline/constants.py
git commit -m "refactor(pipeline): extract magic numbers to constants.py

- Centralized all magic numbers from intelligent_optimized.py
- Added documentation for each constant with rationale
- No logic changes, pure extraction
- Part of Phase 1: Safe refactoring

Refs: #REFACTOR-PHASE-1"
```

#### Шаг 3.2: Заменить магические числа (один файл за раз)

```bash
# Создать ветку для изменений
git checkout -b refactor/phase1-constants

# Пример замены в smart_script_generator.py
cat > /tmp/refactor_constants.patch << 'EOF'
--- a/backend/app/services/smart_script_generator.py
+++ b/backend/app/services/smart_script_generator.py
@@ -5,6 +5,7 @@
 import logging
 from typing import List, Dict, Any, Optional
 import os
+from app.pipeline.constants import *
 
 class SmartScriptGenerator:
     def __init__(self):
-        self.anti_reading_threshold = 0.35
+        self.anti_reading_threshold = ANTI_READING_OVERLAP_THRESHOLD
         
     async def generate_script(...):
-        max_tokens=600  # Reduced from 2000
+        max_tokens=MAX_TOKENS_PER_SLIDE
         
-        if word_count > 400:
+        if word_count > MAX_WORDS_PER_SLIDE:
             logger.warning(...)
EOF

# НЕ применяем патч автоматически! Делаем вручную и проверяем
```

**Процесс для КАЖДОГО файла:**

```bash
# 1. Открыть файл
code backend/app/services/smart_script_generator.py

# 2. Найти магические числа
grep -n "0.35\|400\|600\|30.0" backend/app/services/smart_script_generator.py

# 3. Заменить ВРУЧНУЮ (не автоматически!)
# Перед:
if word_count > 400:

# После:
from app.pipeline.constants import MAX_WORDS_PER_SLIDE
if word_count > MAX_WORDS_PER_SLIDE:

# 4. Запустить тесты для ЭТОГО файла
pytest tests/unit/test_script_generator*.py -v

# 5. Если тесты прошли - commit
git add backend/app/services/smart_script_generator.py
git commit -m "refactor(services): use constants in smart_script_generator

- Replace magic number 400 with MAX_WORDS_PER_SLIDE
- Replace magic number 600 with MAX_TOKENS_PER_SLIDE  
- Replace magic number 0.35 with ANTI_READING_OVERLAP_THRESHOLD
- Tests: pytest tests/unit/test_script_generator*.py ✅

Part of Phase 1: Extract constants"

# 6. Повторить для следующего файла
```

### День 4-5: Добавить type hints (безопасно и полезно)

#### Шаг 4.1: Установить mypy и настроить

```bash
# mypy уже установлен, настроить конфигурацию
cat > mypy.ini << 'EOF'
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = False  # Начинаем мягко
check_untyped_defs = True
ignore_missing_imports = True

# Gradually increase strictness
[mypy-app.pipeline.*]
disallow_untyped_defs = True  # Строже для pipeline

[mypy-app.services.*]
warn_return_any = True

[mypy-tests.*]
ignore_errors = True  # Тесты пока пропускаем
EOF
```

#### Шаг 4.2: Добавить типы постепенно

```bash
# Начать с самых простых функций
cat > /tmp/add_types_example.py << 'EOF'
# BEFORE (без типов):
def _calculate_overlap(self, generated_text, slide_text):
    generated_words = set(generated_text.lower().split())
    slide_words = set(slide_text.lower().split())
    overlap = len(generated_words & slide_words) / len(generated_words)
    return overlap

# AFTER (с типами):
def _calculate_overlap(
    self,
    generated_text: str,
    slide_text: str
) -> float:
    """
    Calculate text overlap ratio between generated and slide text.
    
    Args:
        generated_text: Generated script text
        slide_text: Original slide text
        
    Returns:
        Overlap ratio (0.0 to 1.0)
    """
    generated_words = set(generated_text.lower().split())
    slide_words = set(slide_text.lower().split())
    
    if not generated_words:
        return 0.0
        
    overlap = len(generated_words & slide_words) / len(generated_words)
    return overlap
EOF

# План по добавлению типов (приоритет):
# 1. Публичные методы пайплайна
# 2. Utility функции
# 3. Private методы
# 4. Внутренние helper функции
```

**Процесс:**

```bash
# 1. Добавить типы к одной функции
# 2. Запустить mypy
mypy backend/app/services/smart_script_generator.py

# 3. Исправить ошибки (если есть)
# 4. Commit
git commit -m "refactor(services): add type hints to _calculate_overlap

- Added type hints for parameters and return value
- Added docstring with Args/Returns
- mypy check: ✅ No errors

Part of Phase 1: Type safety improvements"
```

---

## Phase 2: Константы и типизация (3-4 дня)

### Чеклист файлов для добавления констант:

```bash
cat > PHASE2_CHECKLIST.md << 'EOF'
# Phase 2: Константы и типизация - Checklist

## Файлы для рефакторинга (приоритет HIGH → LOW):

### HIGH Priority (критичные для пайплайна):
- [x] backend/app/pipeline/constants.py - создан
- [ ] backend/app/pipeline/intelligent_optimized.py
  - [ ] Extract timeouts (30.0, 60.0, 90.0)
  - [ ] Extract limits (400, 300, 600)
  - [ ] Extract thresholds (0.35, 0.7, 0.4)
  - [ ] Add type hints to public methods
- [ ] backend/app/services/smart_script_generator.py
  - [ ] Use constants from constants.py
  - [ ] Add type hints to generate_script()
  - [ ] Add type hints to helper methods
- [ ] backend/workers/llm_gemini.py
  - [ ] Extract timeout constants
  - [ ] Add type hints to generate()

### MEDIUM Priority:
- [ ] backend/app/services/semantic_analyzer.py
- [ ] backend/app/services/visual_effects_engine.py
- [ ] backend/app/services/bullet_point_sync.py

### LOW Priority:
- [ ] backend/app/services/adaptive_prompt_builder.py
- [ ] backend/app/services/provider_factory.py

## Прогресс:
- [ ] Phase 2.1: Constants extraction (Day 1-2)
- [ ] Phase 2.2: Type hints addition (Day 3-4)
- [ ] Phase 2.3: Mypy validation (Day 4)
- [ ] Phase 2.4: Documentation update (Day 4)

## Метрики успеха:
- [ ] Все магические числа заменены константами
- [ ] mypy проходит без ошибок для app/pipeline/*
- [ ] Все публичные методы имеют type hints
- [ ] Coverage не упал (должен остаться >= baseline)
- [ ] Все тесты проходят
EOF
```

---

## Phase 3: Извлечение утилит (1 неделя)

### День 6-7: Создать utility модули

```bash
# Создать структуру
mkdir -p backend/app/pipeline/utils
touch backend/app/pipeline/utils/__init__.py

# Создать модули (по одному за раз!)
```

#### Шаг 3.1: Duration calculator

```bash
cat > backend/app/pipeline/utils/duration_calculator.py << 'EOF'
"""
Duration calculation utilities
Extracted from multiple locations in intelligent_optimized.py
"""
from typing import Dict, Any
from app.pipeline.constants import (
    WORDS_PER_MINUTE_SPEECH_RATE,
    MIN_SLIDE_DURATION_SECONDS,
    MAX_SLIDE_DURATION_SECONDS,
    HIGH_COMPLEXITY_THRESHOLD,
    MEDIUM_COMPLEXITY_THRESHOLD
)

class DurationCalculator:
    """Calculate optimal slide duration based on content complexity"""
    
    @staticmethod
    def calculate_from_word_count(word_count: int) -> float:
        """
        Calculate duration from word count using average speech rate.
        
        Args:
            word_count: Number of words in script
            
        Returns:
            Estimated duration in seconds
        """
        duration_seconds = (word_count / WORDS_PER_MINUTE_SPEECH_RATE) * 60
        return max(
            MIN_SLIDE_DURATION_SECONDS,
            min(duration_seconds, MAX_SLIDE_DURATION_SECONDS)
        )
    
    @staticmethod
    def calculate_adaptive(
        word_count: int,
        complexity: float,
        visual_density: str
    ) -> int:
        """
        Calculate adaptive duration based on content characteristics.
        
        Args:
            word_count: Number of words in script
            complexity: Content complexity (0.0 - 1.0)
            visual_density: Visual density level ('low', 'medium', 'high')
            
        Returns:
            Optimal duration in seconds (integer)
        """
        # Base duration from word count
        base_duration = DurationCalculator.calculate_from_word_count(word_count)
        
        # Adjust for complexity
        if complexity > HIGH_COMPLEXITY_THRESHOLD:
            base_duration *= 1.5  # +50% for high complexity
        elif complexity > MEDIUM_COMPLEXITY_THRESHOLD:
            base_duration *= 1.2  # +20% for medium complexity
        else:
            base_duration *= 0.9  # -10% for low complexity
        
        # Adjust for visual density
        density_multiplier = {
            'low': 0.9,
            'medium': 1.0,
            'high': 1.3
        }.get(visual_density, 1.0)
        
        final_duration = base_duration * density_multiplier
        
        return int(max(
            MIN_SLIDE_DURATION_SECONDS,
            min(final_duration, MAX_SLIDE_DURATION_SECONDS)
        ))
    
    @staticmethod
    def calculate_hybrid(
        slide_duration: int,
        persona_duration: float,
        slide_weight: float = 0.6
    ) -> int:
        """
        Calculate hybrid duration from slide-based and persona-based estimates.
        
        Args:
            slide_duration: Duration calculated from slide characteristics
            persona_duration: Duration calculated from persona style
            slide_weight: Weight for slide duration (0.0 - 1.0)
            
        Returns:
            Weighted average duration in seconds
        """
        persona_weight = 1.0 - slide_weight
        hybrid = (slide_duration * slide_weight) + (persona_duration * persona_weight)
        return int(hybrid)


# Unit tests for duration calculator
if __name__ == "__main__":
    calc = DurationCalculator()
    
    # Test basic calculation
    assert calc.calculate_from_word_count(150) == 60  # 150 words = ~60 seconds
    assert calc.calculate_from_word_count(300) == 120  # 300 words = ~120 seconds
    
    # Test adaptive calculation
    duration = calc.calculate_adaptive(200, 0.5, 'medium')
    assert MIN_SLIDE_DURATION_SECONDS <= duration <= MAX_SLIDE_DURATION_SECONDS
    
    print("✅ All tests passed")
EOF

# Тестировать утилиту
python backend/app/pipeline/utils/duration_calculator.py

# Создать unit тесты
cat > backend/tests/unit/test_duration_calculator.py << 'EOF'
import pytest
from app.pipeline.utils.duration_calculator import DurationCalculator

class TestDurationCalculator:
    def test_calculate_from_word_count_normal(self):
        """Test normal word count calculation"""
        calc = DurationCalculator()
        
        # 150 words at 150 wpm = 60 seconds
        assert calc.calculate_from_word_count(150) == pytest.approx(60, abs=5)
        
        # 300 words at 150 wpm = 120 seconds
        assert calc.calculate_from_word_count(300) == pytest.approx(120, abs=5)
    
    def test_calculate_from_word_count_bounds(self):
        """Test min/max bounds are respected"""
        calc = DurationCalculator()
        
        # Very short
        assert calc.calculate_from_word_count(10) == 30  # Min bound
        
        # Very long
        assert calc.calculate_from_word_count(1000) == 120  # Max bound
    
    def test_calculate_adaptive_complexity(self):
        """Test complexity adjustment"""
        calc = DurationCalculator()
        
        low_complex = calc.calculate_adaptive(200, 0.3, 'medium')
        high_complex = calc.calculate_adaptive(200, 0.8, 'medium')
        
        # High complexity should be longer
        assert high_complex > low_complex
    
    def test_calculate_hybrid(self):
        """Test hybrid calculation"""
        calc = DurationCalculator()
        
        result = calc.calculate_hybrid(60, 90, slide_weight=0.6)
        expected = int(60 * 0.6 + 90 * 0.4)  # 78
        
        assert result == expected
EOF

pytest backend/tests/unit/test_duration_calculator.py -v

# Если тесты прошли - commit
git add backend/app/pipeline/utils/duration_calculator.py
git add backend/tests/unit/test_duration_calculator.py
git commit -m "refactor(pipeline): extract DurationCalculator utility

- Extracted duration calculation logic from 3 different places
- Centralized in utils/duration_calculator.py
- Added comprehensive unit tests (100% coverage)
- No logic changes, pure extraction

Tests: pytest backend/tests/unit/test_duration_calculator.py ✅
Part of Phase 3: Extract utilities"
```

#### Шаг 3.2: SSML cleaner

```bash
cat > backend/app/pipeline/utils/ssml_cleaner.py << 'EOF'
"""
SSML marker cleaning utilities
Remove SSML markers for display (subtitles) while keeping them for TTS
"""
import re
from typing import List, Dict, Any

class SSMLCleaner:
    """Clean SSML markers from text for display purposes"""
    
    # Patterns that remove completely
    VISUAL_PATTERN = re.compile(r'\[visual:[a-z]{2}\].*?\[/visual\]')
    PAUSE_PATTERN = re.compile(r'\[pause:\d+ms\]')
    
    # Patterns that extract text
    LANG_PATTERN = re.compile(r'\[lang:[a-z]{2}\](.*?)\[/lang\]')
    PHONEME_PATTERN = re.compile(r'\[phoneme:ipa:.*?\](.*?)\[/phoneme\]')
    EMPHASIS_PATTERN = re.compile(r'\[emphasis:(?:strong|moderate|reduced)\](.*?)\[/emphasis\]')
    PITCH_PATTERN = re.compile(r'\[pitch:[\+\-]?\d+%\](.*?)\[/pitch\]')
    RATE_PATTERN = re.compile(r'\[rate:\d+%\](.*?)\[/rate\]')
    
    @classmethod
    def clean_text(cls, text: str) -> str:
        """
        Remove SSML markers from text for display.
        
        Args:
            text: Text with SSML markers
            
        Returns:
            Clean text without markers
            
        Example:
            >>> SSMLCleaner.clean_text("[visual:ru]term[/visual] normal text")
            'normal text'
        """
        if not text:
            return text
        
        # Remove completely
        text = cls.VISUAL_PATTERN.sub('', text)
        text = cls.PAUSE_PATTERN.sub('', text)
        
        # Extract text from markers
        text = cls.PHONEME_PATTERN.sub(r'\1', text)
        text = cls.LANG_PATTERN.sub(r'\1', text)
        text = cls.EMPHASIS_PATTERN.sub(r'\1', text)
        text = cls.PITCH_PATTERN.sub(r'\1', text)
        text = cls.RATE_PATTERN.sub(r'\1', text)
        
        # Clean up multiple spaces
        text = ' '.join(text.split())
        
        return text
    
    @classmethod
    def clean_talk_track(cls, talk_track: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean all text segments in talk track.
        
        Args:
            talk_track: List of segments with 'text' field
            
        Returns:
            Cleaned talk track with markers removed
        """
        cleaned = []
        
        for segment in talk_track:
            cleaned_segment = segment.copy()
            if 'text' in cleaned_segment:
                cleaned_segment['text'] = cls.clean_text(cleaned_segment['text'])
            cleaned.append(cleaned_segment)
        
        return cleaned


# Tests
if __name__ == "__main__":
    cleaner = SSMLCleaner()
    
    # Test visual marker removal
    assert cleaner.clean_text("[visual:ru]term[/visual] text") == "text"
    
    # Test pause removal
    assert cleaner.clean_text("text [pause:500ms] more") == "text more"
    
    # Test lang extraction
    assert cleaner.clean_text("[lang:ru]текст[/lang]") == "текст"
    
    # Test mixed markers
    mixed = "[visual:ru]hidden[/visual] [lang:ru]visible[/lang] [pause:500ms] text"
    expected = "visible text"
    assert cleaner.clean_text(mixed) == expected
    
    print("✅ All tests passed")
EOF

python backend/app/pipeline/utils/ssml_cleaner.py
```

#### Шаг 3.3: Manifest handler

```bash
cat > backend/app/pipeline/utils/manifest_handler.py << 'EOF'
"""
Manifest loading/saving utilities
Extracted from BasePipeline and OptimizedIntelligentPipeline
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ManifestHandler:
    """Handle manifest.json loading and saving operations"""
    
    @staticmethod
    def load(lesson_dir: str | Path) -> Dict[str, Any]:
        """
        Load manifest.json from lesson directory.
        
        Args:
            lesson_dir: Path to lesson directory
            
        Returns:
            Parsed manifest data
            
        Raises:
            FileNotFoundError: If manifest.json doesn't exist
            json.JSONDecodeError: If manifest is invalid JSON
        """
        lesson_path = Path(lesson_dir)
        manifest_path = lesson_path / "manifest.json"
        
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")
        
        logger.debug(f"Loading manifest from {manifest_path}")
        
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        
        logger.debug(f"Loaded manifest with {len(manifest.get('slides', []))} slides")
        return manifest
    
    @staticmethod
    def save(lesson_dir: str | Path, manifest: Dict[str, Any]) -> None:
        """
        Save manifest.json to lesson directory.
        
        Args:
            lesson_dir: Path to lesson directory
            manifest: Manifest data to save
        """
        lesson_path = Path(lesson_dir)
        manifest_path = lesson_path / "manifest.json"
        
        logger.debug(f"Saving manifest to {manifest_path}")
        
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Saved manifest with {len(manifest.get('slides', []))} slides")
    
    @staticmethod
    def update_slide(
        lesson_dir: str | Path,
        slide_id: int,
        updates: Dict[str, Any]
    ) -> None:
        """
        Update specific slide in manifest.
        
        Args:
            lesson_dir: Path to lesson directory
            slide_id: ID of slide to update
            updates: Fields to update
        """
        manifest = ManifestHandler.load(lesson_dir)
        
        for slide in manifest.get('slides', []):
            if slide.get('id') == slide_id:
                slide.update(updates)
                logger.debug(f"Updated slide {slide_id} with {list(updates.keys())}")
                break
        
        ManifestHandler.save(lesson_dir, manifest)
    
    @staticmethod
    def validate(manifest: Dict[str, Any]) -> bool:
        """
        Validate manifest structure.
        
        Args:
            manifest: Manifest to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['slides', 'metadata']
        
        if not all(field in manifest for field in required_fields):
            logger.error(f"Missing required fields: {required_fields}")
            return False
        
        if not isinstance(manifest['slides'], list):
            logger.error("'slides' must be a list")
            return False
        
        # Validate each slide
        for i, slide in enumerate(manifest['slides']):
            if not isinstance(slide, dict):
                logger.error(f"Slide {i} is not a dict")
                return False
            
            if 'id' not in slide:
                logger.error(f"Slide {i} missing 'id'")
                return False
        
        return True
EOF
```

### День 8-10: Постепенная замена на утилиты

```bash
# Заменять ПОСТЕПЕННО (по одному месту за раз)

# 1. Найти все места использования
grep -rn "self.load_manifest\|self.save_manifest" backend/app/pipeline/

# 2. Заменить в одном месте
# BEFORE:
manifest = self.load_manifest(lesson_dir)

# AFTER:
from app.pipeline.utils.manifest_handler import ManifestHandler
manifest = ManifestHandler.load(lesson_dir)

# 3. Запустить тесты
pytest tests/unit/test_pipeline*.py -v -k "manifest"

# 4. Если OK - commit
git commit -m "refactor(pipeline): use ManifestHandler in ingest()

- Replace self.load_manifest() with ManifestHandler.load()
- Replace self.save_manifest() with ManifestHandler.save()
- Tests: pytest tests/unit/test_pipeline*.py ✅

Part of Phase 3: Migrate to utility modules
Progress: 1/8 locations migrated"

# 5. Повторить для следующего места
```

---

## Phase 4: Разделение на модули (2 недели)

**⚠️ ЭТО САМАЯ РИСКОВАННАЯ ЧАСТЬ - ДЕЛАЕМ КРАЙНЕ ОСТОРОЖНО!**

### Неделя 3: Подготовка к разделению

#### День 11-12: Создать структуру модулей

```bash
# Создать структуру БЕЗ переноса кода
mkdir -p backend/app/pipeline/stages
touch backend/app/pipeline/stages/__init__.py

# Создать пустые заглушки
for stage in ingest ocr translation planning tts manifest; do
    cat > backend/app/pipeline/stages/${stage}_stage.py << EOF
"""
${stage^} stage implementation
TODO: Extract from intelligent_optimized.py
"""
from typing import Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ${stage^}Stage:
    """${stage^} stage of the pipeline"""
    
    def __init__(self):
        self.logger = logger
    
    async def process(self, lesson_dir: str | Path) -> Dict[str, Any]:
        """
        Process ${stage} stage.
        
        Args:
            lesson_dir: Path to lesson directory
            
        Returns:
            Stage result
        """
        raise NotImplementedError("TODO: Extract from intelligent_optimized.py")
EOF
done

git add backend/app/pipeline/stages/
git commit -m "refactor(pipeline): create stage module structure

- Created stages/ directory with stage modules
- Added stub classes for each stage
- No logic moved yet (stubs only)
- Preparation for Phase 4: Module splitting"
```

#### День 13-15: Извлечь ОДНУ стадию (начнём с самой простой)

**Выбираем `ingest` - самая изолированная стадия**

```bash
# Шаг 1: Копировать код (НЕ удалять из оригинала!)
# Открыть intelligent_optimized.py и скопировать метод ingest()
# в stages/ingest_stage.py

# Шаг 2: Адаптировать под новый модуль
cat > backend/app/pipeline/stages/ingest_stage.py << 'EOF'
"""
Ingest stage: PPTX/PDF → PNG conversion
Extracted from OptimizedIntelligentPipeline.ingest()
"""
from typing import Dict, Any, List, Tuple
from pathlib import Path
import logging

from app.pipeline.utils.manifest_handler import ManifestHandler

logger = logging.getLogger(__name__)

class IngestStage:
    """Stage 1: Convert presentation to PNG images"""
    
    def __init__(self):
        self.logger = logger
    
    async def process(self, lesson_dir: str | Path) -> Dict[str, Any]:
        """
        Convert PPTX or PDF to PNG images.
        
        Args:
            lesson_dir: Path to lesson directory
            
        Returns:
            Stage result with slide count
        """
        self.logger.info(f"🔄 Stage 1: Converting presentation to PNG for {lesson_dir}")
        
        lesson_path = Path(lesson_dir)
        
        # Find presentation file
        presentation_file, file_type = self._find_presentation_file(lesson_dir)
        self.logger.info(f"Found {file_type.upper()} file: {presentation_file.name}")
        
        # Create slides directory
        slides_dir = lesson_path / "slides"
        slides_dir.mkdir(exist_ok=True)
        
        # Convert to PNG
        if file_type == 'pptx':
            png_files = self._convert_pptx_to_png(presentation_file, slides_dir)
        else:  # pdf
            png_files = self._convert_pdf_to_png(presentation_file, slides_dir)
        
        # Get slide dimensions
        slide_width, slide_height = self._get_slide_dimensions(png_files)
        
        # Create initial manifest
        manifest = self._create_initial_manifest(
            lesson_path.name,
            presentation_file.name,
            file_type,
            len(png_files),
            slide_width,
            slide_height
        )
        
        # Save manifest
        ManifestHandler.save(lesson_dir, manifest)
        
        self.logger.info(f"✅ Stage 1: Converted {len(png_files)} slides to PNG")
        
        return {
            'status': 'success',
            'stage': 'ingest',
            'slides_count': len(png_files)
        }
    
    # ... (скопировать helper методы из OptimizedIntelligentPipeline)
    # _find_presentation_file()
    # _convert_pptx_to_png()
    # _convert_pdf_to_png()
    # etc.
EOF

# Шаг 3: Создать тесты для новой стадии
cat > backend/tests/unit/test_ingest_stage.py << 'EOF'
import pytest
from pathlib import Path
from app.pipeline.stages.ingest_stage import IngestStage

@pytest.mark.asyncio
class TestIngestStage:
    async def test_ingest_pptx(self, tmp_path, sample_pptx_file):
        """Test PPTX ingestion"""
        stage = IngestStage()
        
        # Copy sample PPTX to temp dir
        lesson_dir = tmp_path / "test_lesson"
        lesson_dir.mkdir()
        import shutil
        shutil.copy(sample_pptx_file, lesson_dir / "presentation.pptx")
        
        # Process
        result = await stage.process(str(lesson_dir))
        
        # Verify
        assert result['status'] == 'success'
        assert result['stage'] == 'ingest'
        assert result['slides_count'] > 0
        
        # Verify PNG files created
        slides_dir = lesson_dir / "slides"
        assert slides_dir.exists()
        png_files = list(slides_dir.glob("*.png"))
        assert len(png_files) == result['slides_count']
        
        # Verify manifest created
        manifest_file = lesson_dir / "manifest.json"
        assert manifest_file.exists()
EOF

# Шаг 4: Запустить тесты
pytest backend/tests/unit/test_ingest_stage.py -v

# Шаг 5: Интегрировать в пайплайн (feature flag!)
# Добавить в OptimizedIntelligentPipeline:
class OptimizedIntelligentPipeline(BasePipeline):
    def __init__(self, use_modular_stages: bool = False):
        super().__init__()
        self.use_modular_stages = use_modular_stages
        
        if use_modular_stages:
            from app.pipeline.stages.ingest_stage import IngestStage
            self.ingest_stage = IngestStage()
    
    async def ingest(self, lesson_dir: str) -> None:
        """Stage 1: Ingest with optional modular implementation"""
        if self.use_modular_stages:
            # Use new modular stage
            result = await self.ingest_stage.process(lesson_dir)
            self.logger.info(f"Modular ingest: {result}")
        else:
            # Use old monolithic implementation
            # ... (keep existing code)

# Шаг 6: Тестировать обе реализации
pytest tests/ -v -k "ingest"

# Шаг 7: Commit
git commit -m "refactor(pipeline): extract IngestStage (modular version)

- Created stages/ingest_stage.py with PPTX/PDF conversion
- Added feature flag use_modular_stages for safe testing
- Both old and new implementations work in parallel
- Added comprehensive tests
- Tests: pytest backend/tests/unit/test_ingest_stage.py ✅

Part of Phase 4: Module extraction (1/6 stages)
Status: OLD CODE KEPT, NEW CODE TESTED"
```

### Неделя 4: Миграция остальных стадий

**Повторить процесс для каждой стадии:**

```bash
# Порядок извлечения (от простого к сложному):
1. ingest     ✅ (сделали выше)
2. ocr        → День 16-17
3. translation → День 18
4. tts        → День 19-20
5. planning   → День 21-23 (самая сложная!)
6. manifest   → День 24-25
```

**ВАЖНО:** Каждую стадию:
- Извлекаем с feature flag
- Тестируем отдельно
- Тестируем в пайплайне
- Запускаем regression tests
- Только потом commit

---

## Phase 5: Оптимизация (1 неделя)

### День 26-27: Memory monitoring

```bash
cat > backend/app/core/memory_monitor.py << 'EOF'
"""
Memory monitoring and management
Critical for preventing OOM in Docker environment
"""
import psutil
import logging
import gc
from typing import Optional
import os

logger = logging.getLogger(__name__)

class MemoryMonitor:
    """Monitor and manage memory usage"""
    
    def __init__(
        self,
        max_memory_gb: float = None,
        warning_threshold: float = 0.8,
        critical_threshold: float = 0.9
    ):
        """
        Initialize memory monitor.
        
        Args:
            max_memory_gb: Maximum allowed memory in GB (default: from env or 7.0)
            warning_threshold: Trigger warning at this % of max
            critical_threshold: Trigger aggressive cleanup at this % of max
        """
        self.max_memory_gb = max_memory_gb or float(
            os.getenv('MAX_MEMORY_GB', '7.0')
        )
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        
    def get_current_usage_gb(self) -> float:
        """Get current memory usage in GB"""
        process = psutil.Process()
        return process.memory_info().rss / (1024 ** 3)
    
    def get_usage_ratio(self) -> float:
        """Get memory usage as ratio of maximum (0.0 - 1.0)"""
        current = self.get_current_usage_gb()
        return current / self.max_memory_gb
    
    def check_memory_pressure(self) -> Optional[str]:
        """
        Check if memory pressure exists.
        
        Returns:
            'critical', 'warning', or None
        """
        ratio = self.get_usage_ratio()
        
        if ratio >= self.critical_threshold:
            logger.error(
                f"🔴 CRITICAL memory pressure: {ratio*100:.1f}% "
                f"({self.get_current_usage_gb():.2f}GB / {self.max_memory_gb}GB)"
            )
            return 'critical'
        elif ratio >= self.warning_threshold:
            logger.warning(
                f"🟡 Memory warning: {ratio*100:.1f}% "
                f"({self.get_current_usage_gb():.2f}GB / {self.max_memory_gb}GB)"
            )
            return 'warning'
        
        return None
    
    def force_cleanup(self, aggressive: bool = False):
        """
        Force garbage collection.
        
        Args:
            aggressive: If True, run multiple GC cycles
        """
        before = self.get_current_usage_gb()
        
        if aggressive:
            # Multiple GC cycles
            for _ in range(3):
                gc.collect()
        else:
            gc.collect()
        
        after = self.get_current_usage_gb()
        freed = before - after
        
        if freed > 0.1:  # More than 100MB freed
            logger.info(f"♻️ Garbage collection freed {freed:.2f}GB")
    
    def auto_cleanup_if_needed(self):
        """Automatically cleanup if memory pressure detected"""
        pressure = self.check_memory_pressure()
        
        if pressure == 'critical':
            logger.warning("🔄 Forcing aggressive garbage collection...")
            self.force_cleanup(aggressive=True)
            
            # Check if it helped
            if self.get_usage_ratio() >= self.critical_threshold:
                logger.error(
                    "❌ Memory still critical after cleanup! "
                    "Consider increasing Docker memory limit."
                )
        elif pressure == 'warning':
            self.force_cleanup(aggressive=False)


# Global instance
memory_monitor = MemoryMonitor()


# Decorator for memory-sensitive operations
def with_memory_check(func):
    """Decorator to check memory before/after operation"""
    from functools import wraps
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Check before
        memory_monitor.auto_cleanup_if_needed()
        before = memory_monitor.get_current_usage_gb()
        
        # Execute
        result = await func(*args, **kwargs)
        
        # Check after
        after = memory_monitor.get_current_usage_gb()
        delta = after - before
        
        if delta > 0.5:  # More than 500MB increase
            logger.warning(
                f"⚠️ {func.__name__} increased memory by {delta:.2f}GB"
            )
        
        memory_monitor.auto_cleanup_if_needed()
        
        return result
    
    return wrapper
EOF

# Использовать в пайплайне:
from app.core.memory_monitor import memory_monitor, with_memory_check

class OptimizedIntelligentPipeline:
    @with_memory_check
    async def plan(self, lesson_dir: str):
        # ... existing code
        
        # Check memory after each slide
        for i, slide in enumerate(slides):
            result = await process_slide(slide)
            
            # Auto-cleanup if needed
            memory_monitor.auto_cleanup_if_needed()
```

### День 28-30: LLM Caching

```bash
cat > backend/app/core/llm_cache.py << 'EOF'
"""
LLM response caching to reduce API calls and cost
"""
import hashlib
import pickle
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class LLMCache:
    """Cache LLM responses to reduce API calls"""
    
    def __init__(
        self,
        cache_dir: Path = None,
        ttl_hours: int = 24,
        enabled: bool = None
    ):
        """
        Initialize LLM cache.
        
        Args:
            cache_dir: Directory for cache files
            ttl_hours: Time-to-live for cache entries
            enabled: Enable caching (default: from env)
        """
        self.cache_dir = cache_dir or Path(".data/llm_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.ttl = timedelta(hours=ttl_hours)
        self.enabled = enabled if enabled is not None else (
            os.getenv('LLM_CACHE_ENABLED', 'true').lower() == 'true'
        )
        
        if self.enabled:
            logger.info(f"✅ LLM cache enabled (TTL: {ttl_hours}h)")
        else:
            logger.info("⚠️ LLM cache disabled")
    
    def _get_cache_key(self, slide_content: str, prompt: str) -> str:
        """Generate cache key from content hash"""
        combined = f"{slide_content}|{prompt}"
        hash_obj = hashlib.sha256(combined.encode())
        return hash_obj.hexdigest()[:16]
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path"""
        return self.cache_dir / f"{cache_key}.pkl"
    
    def get(self, slide_content: str, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Get cached result.
        
        Args:
            slide_content: Slide content string
            prompt: Prompt used for generation
            
        Returns:
            Cached result or None
        """
        if not self.enabled:
            return None
        
        cache_key = self._get_cache_key(slide_content, prompt)
        cache_path = self._get_cache_path(cache_key)
        
        if not cache_path.exists():
            logger.debug(f"Cache MISS: {cache_key}")
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                cached_data = pickle.load(f)
            
            # Check TTL
            cached_time = cached_data.get('timestamp')
            if cached_time:
                age = datetime.now() - cached_time
                if age > self.ttl:
                    logger.debug(f"Cache EXPIRED: {cache_key} (age: {age})")
                    cache_path.unlink()  # Delete expired
                    return None
            
            logger.info(f"✨ Cache HIT: {cache_key}")
            return cached_data.get('result')
            
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
            return None
    
    def set(
        self,
        slide_content: str,
        prompt: str,
        result: Dict[str, Any]
    ):
        """
        Save result to cache.
        
        Args:
            slide_content: Slide content string
            prompt: Prompt used for generation
            result: Result to cache
        """
        if not self.enabled:
            return
        
        cache_key = self._get_cache_key(slide_content, prompt)
        cache_path = self._get_cache_path(cache_key)
        
        try:
            cached_data = {
                'timestamp': datetime.now(),
                'result': result
            }
            
            with open(cache_path, 'wb') as f:
                pickle.dump(cached_data, f)
            
            logger.debug(f"Cache SET: {cache_key}")
            
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
    
    def clear_expired(self):
        """Clear all expired cache entries"""
        if not self.cache_dir.exists():
            return
        
        cleared_count = 0
        for cache_file in self.cache_dir.glob("*.pkl"):
            try:
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                
                cached_time = cached_data.get('timestamp')
                if cached_time:
                    age = datetime.now() - cached_time
                    if age > self.ttl:
                        cache_file.unlink()
                        cleared_count += 1
            except Exception as e:
                logger.warning(f"Error checking {cache_file}: {e}")
        
        if cleared_count > 0:
            logger.info(f"🧹 Cleared {cleared_count} expired cache entries")
    
    def clear_all(self):
        """Clear all cache entries"""
        if not self.cache_dir.exists():
            return
        
        count = 0
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()
            count += 1
        
        logger.info(f"🧹 Cleared {count} cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.cache_dir.exists():
            return {'total': 0, 'size_mb': 0}
        
        cache_files = list(self.cache_dir.glob("*.pkl"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            'total_entries': len(cache_files),
            'size_mb': total_size / (1024 * 1024),
            'cache_dir': str(self.cache_dir)
        }


# Global cache instance
llm_cache = LLMCache()


# Decorator for caching LLM calls
def cached_llm_call(func):
    """Decorator to cache LLM generation calls"""
    from functools import wraps
    
    @wraps(func)
    async def wrapper(self, slide_content: str, prompt: str, **kwargs):
        # Try cache first
        cached = llm_cache.get(slide_content, prompt)
        if cached:
            return cached
        
        # Cache miss - call function
        result = await func(self, slide_content, prompt, **kwargs)
        
        # Save to cache
        llm_cache.set(slide_content, prompt, result)
        
        return result
    
    return wrapper
EOF

# Использовать в SmartScriptGenerator:
from app.core.llm_cache import cached_llm_call, llm_cache

class SmartScriptGenerator:
    @cached_llm_call
    async def generate_script(self, semantic_map, ocr_elements, ...):
        # ... existing code
        pass
```

---

## ✅ Checklist для каждого изменения

Перед каждым commit проверяй:

```bash
# 1. Тесты проходят
pytest tests/ -v --tb=short

# 2. Regression тесты проходят
pytest tests/regression/ -v

# 3. Coverage не упал
pytest tests/ --cov=app --cov-report=term | grep "TOTAL"

# 4. Mypy проходит (если добавляли типы)
mypy backend/app/pipeline --ignore-missing-imports

# 5. Pre-commit hooks проходят
pre-commit run --all-files

# 6. Code review готов
# - Понятное commit message
# - Изолированное изменение
# - Тесты включены
# - Документация обновлена (если нужно)
```

---

## 🚨 Что делать если что-то пошло не так

### Откат изменений:

```bash
# Если изменение в отдельной ветке:
git checkout main
git branch -D refactor/broken-change

# Если уже в main:
git revert <commit-hash>

# Если много изменений:
git reset --hard origin/main  # ОСТОРОЖНО! Потеряешь локальные изменения
```

### Если тесты падают:

```bash
# 1. Запустить с verbose для деталей
pytest tests/test_failed.py -vv --tb=long

# 2. Запустить отдельный тест
pytest tests/test_failed.py::TestClass::test_method -s

# 3. Проверить baseline
diff baseline_test_results.txt current_test_results.txt

# 4. Если не можешь починить - откатывай!
```

### Если production упал:

```bash
# 1. Немедленный откат на последнюю рабочую версию
git revert <bad-commit>
git push origin main

# 2. Deploy старой версии
docker-compose down
docker-compose up -d

# 3. Проверить логи
docker-compose logs -f backend | grep ERROR

# 4. Расследование после восстановления сервиса!
```

---

## 📊 Метрики успеха рефакторинга

Отслеживай эти метрики каждую неделю:

```bash
cat > track_metrics.sh << 'EOF'
#!/bin/bash
# Track refactoring metrics

echo "=== Refactoring Metrics $(date) ===" >> REFACTORING_METRICS.md

# Code metrics
echo "## Code Metrics" >> REFACTORING_METRICS.md
echo "- Total Python files: $(find backend/app -name '*.py' | wc -l)" >> REFACTORING_METRICS.md
echo "- Lines of code: $(find backend/app -name '*.py' -exec wc -l {} + | tail -1)" >> REFACTORING_METRICS.md
echo "- Largest file: $(find backend/app -name '*.py' -exec wc -l {} + | sort -rn | head -2 | tail -1)" >> REFACTORING_METRICS.md

# Test metrics
echo "## Test Metrics" >> REFACTORING_METRICS.md
pytest tests/ --co -q | grep "test session" >> REFACTORING_METRICS.md
pytest tests/ --cov=app --cov-report=term | grep "TOTAL" >> REFACTORING_METRICS.md

# Type coverage
echo "## Type Coverage" >> REFACTORING_METRICS.md
mypy backend/app --ignore-missing-imports 2>&1 | tail -1 >> REFACTORING_METRICS.md

echo "" >> REFACTORING_METRICS.md
EOF

chmod +x track_metrics.sh
./track_metrics.sh
```

**Целевые метрики:**
- ✅ Самый большой файл: < 500 строк (сейчас 1439)
- ✅ Test coverage: >= 70% (текущий baseline)
- ✅ Mypy success rate: 100% для app/pipeline/*
- ✅ Константы: 100% магических чисел заменены
- ✅ Memory peak: < 3.5GB (сейчас ~3.7GB)

---

## 📝 Финальный чеклист

Перед завершением рефакторинга проверь:

- [ ] Все тесты проходят (включая regression)
- [ ] Coverage не упал (>= baseline)
- [ ] Production работает стабильно минимум 1 неделю
- [ ] Нет новых ошибок в Sentry
- [ ] Memory usage стабилен
- [ ] Документация обновлена
- [ ] KNOWN_ISSUES.md актуален
- [ ] REFACTORING_METRICS.md показывает улучшения
- [ ] Team знает о изменениях (если есть team)

---

**ПОМНИ:** Лучше медленно и безопасно, чем быстро и с падением production! 🛡️
