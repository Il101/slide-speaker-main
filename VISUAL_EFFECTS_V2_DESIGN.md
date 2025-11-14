# 🎨 Visual Effects System V2 - Complete Redesign

**Дата:** 2 ноября 2025  
**Статус:** 🚧 В разработке  
**Цель:** Создать современную, точно синхронизированную систему визуальных эффектов

---

## 🎯 Проблемы текущей системы V1

### Синхронизация:
- ❌ Сложная многоуровневая логика с 4 fallback механизмами
- ❌ Неточная синхронизация (±0.5-1 сек)
- ❌ Эффекты "залипают" на несвязанных сегментах
- ❌ Нет предсказуемости timing
- ❌ Сложно отлаживать из-за множества путей исполнения

### Визуальное качество:
- ❌ Примитивные CSS-анимации
- ❌ Нет плавных transitions
- ❌ Отсутствие современных эффектов (morph, particle physics, 3D)
- ❌ Нет GPU acceleration
- ❌ Базовое выделение рамками
- ❌ Не впечатляет для продукта

### Архитектура:
- ❌ 1936 строк в одном файле
- ❌ Смешанная логика синхронизации и рендеринга
- ❌ Сложно поддерживать и расширять

---

## 🚀 Новая архитектура V2

### Принципы:
1. **Timeline-First** - всё основано на точном timeline из манифеста
2. **Separation of Concerns** - раздельные модули для генерации, рендеринга, синхронизации
3. **GPU Acceleration** - Canvas/WebGL для плавных эффектов
4. **Predictable Timing** - детерминированная синхронизация
5. **Modern Effects** - впечатляющие визуальные эффекты

---

## 📊 Архитектура модулей

### Backend:

```
backend/app/services/visual_effects/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── timing_engine.py        # ⭐ Точный timing из TTS
│   ├── effect_types.py         # Определения эффектов
│   └── validators.py           # Валидация timings
├── generators/
│   ├── __init__.py
│   ├── base_generator.py       # Базовый класс
│   ├── semantic_generator.py   # Эффекты из semantic_map
│   └── timeline_builder.py     # ⭐ Timeline-based подход
└── effects/
    ├── __init__.py
    ├── spotlight.py            # Spotlight эффекты
    ├── particles.py            # Particle system
    ├── morphing.py             # Morphing анимации
    └── advanced.py             # Продвинутые эффекты
```

### Frontend:

```
src/components/VisualEffects/
├── index.ts
├── core/
│   ├── EffectsTimeline.ts      # ⭐ Timeline синхронизация
│   ├── EffectsRenderer.ts      # Canvas/WebGL рендерер
│   └── EffectsBuffer.ts        # Предзагрузка эффектов
├── effects/
│   ├── SpotlightEffect.ts      # Динамический spotlight
│   ├── ParticleEffect.ts       # GPU particles
│   ├── MorphEffect.ts          # Плавный морфинг
│   ├── GlitchEffect.ts         # Glitch эффект
│   ├── RippleEffect.ts         # Волновой эффект
│   └── HologramEffect.ts       # 3D голограмма
└── utils/
    ├── shaders.ts              # WebGL шейдеры
    └── animations.ts           # Easing функции
```

---

## ⏱️ Timeline-Based Синхронизация

### Концепция:

Вместо проверки `currentTime >= t0 && currentTime <= t1` на каждом кадре,
используем **event-driven timeline** с предзагрузкой:

```typescript
class EffectsTimeline {
  private events: TimelineEvent[] = [];
  private activeEffects: Map<string, Effect> = new Map();
  
  // Предзагрузка всех событий
  preload(cues: Cue[]) {
    this.events = cues.flatMap(cue => [
      { time: cue.t0, type: 'START', cue },
      { time: cue.t1, type: 'END', cue }
    ]).sort((a, b) => a.time - b.time);
  }
  
  // Обработка событий с буфером опережения
  update(currentTime: number) {
    const lookAhead = 0.1; // 100ms буфер
    
    while (this.events[0]?.time <= currentTime + lookAhead) {
      const event = this.events.shift()!;
      
      if (event.type === 'START') {
        this.startEffect(event.cue);
      } else {
        this.endEffect(event.cue);
      }
    }
  }
}
```

### Преимущества:
- ✅ Точная синхронизация (±16ms при 60 FPS)
- ✅ Предсказуемый timing
- ✅ Буферизация эффектов
- ✅ Нет проверок на каждом кадре
- ✅ Легко отлаживать

---

## 🎨 Новые эффекты

### 1. Dynamic Spotlight
```typescript
// Динамический spotlight с физикой света
class SpotlightEffect {
  - Мягкие тени (shadow mapping)
  - Динамическое затемнение фона
  - Плавный fade in/out (easing)
  - Анимация луча света
}
```

### 2. Particle Highlight
```typescript
// GPU-ускоренная система частиц
class ParticleEffect {
  - 1000+ частиц без лагов
  - Физика (gravity, wind, collision)
  - Множественные emitter types
  - Trails и glow эффекты
}
```

### 3. Morphing Animation
```typescript
// Плавный морфинг элементов
class MorphEffect {
  - Shape morphing (SVG paths)
  - Size/position interpolation
  - Elastic easing
  - Squash & stretch
}
```

### 4. Glitch Effect
```typescript
// Современный glitch эффект
class GlitchEffect {
  - RGB split
  - Scanlines
  - Digital noise
  - Static distortion
}
```

### 5. Ripple Wave
```typescript
// Волновой эффект распространения
class RippleEffect {
  - Физика волн
  - Interference patterns
  - Затухание
}
```

### 6. Hologram 3D
```typescript
// Псевдо-3D голограмма
class HologramEffect {
  - Parallax layers
  - Scan lines
  - Flicker animation
  - Chromatic aberration
}
```

---

## 🔧 Backend: Timing Engine

### Упрощённая логика синхронизации:

```python
class TimingEngine:
    """
    Единственный источник truth для timing.
    Простая, понятная логика без fallbacks.
    """
    
    def get_timing(self, group_id: str, talk_track: List, tts_words: Dict) -> Timing:
        """
        Приоритет 1: Talk track с calculated timing (из LLM)
        Приоритет 2: TTS sentence timing (из Google TTS)
        Приоритет 3: Equal distribution (fallback)
        
        Всего 3 пути вместо 4+, понятная иерархия
        """
        
        # 1. Talk track segments (MAIN SOURCE)
        timing = self._from_talk_track(group_id, talk_track)
        if timing and timing.confidence > 0.8:
            return timing
        
        # 2. TTS sentences (SECONDARY)
        timing = self._from_tts_sentences(group_id, tts_words)
        if timing and timing.confidence > 0.6:
            return timing
        
        # 3. Fallback (LAST RESORT)
        return self._equal_distribution(group_id)
```

### Структура Timing:

```python
@dataclass
class Timing:
    t0: float                    # Начало (секунды)
    t1: float                    # Конец (секунды)
    confidence: float            # Уверенность (0.0-1.0)
    source: str                  # 'talk_track' | 'tts' | 'fallback'
    precision: str               # 'word' | 'sentence' | 'segment'
    metadata: Dict[str, Any]     # Дополнительные данные
```

---

## 📝 Формат манифеста V2

### Улучшенная структура:

```json
{
  "version": "2.0",
  "slides": [
    {
      "id": "slide_0",
      "timeline": {
        "total_duration": 45.6,
        "events": [
          {
            "time": 0.0,
            "type": "slide_start"
          },
          {
            "time": 0.3,
            "type": "effect_start",
            "effect_id": "effect_001"
          },
          {
            "time": 2.5,
            "type": "effect_end",
            "effect_id": "effect_001"
          }
        ]
      },
      "effects": [
        {
          "id": "effect_001",
          "type": "spotlight",
          "target": {
            "element_id": "title_block",
            "bbox": [100, 50, 600, 80]
          },
          "timing": {
            "t0": 0.3,
            "t1": 2.5,
            "confidence": 0.95,
            "source": "talk_track",
            "precision": "word"
          },
          "params": {
            "intensity": "dramatic",
            "shadow_opacity": 0.7,
            "beam_width": 1.2,
            "ease_in": "cubic-out",
            "ease_out": "cubic-in"
          }
        },
        {
          "id": "effect_002",
          "type": "particle_highlight",
          "target": {
            "element_ids": ["formula_1", "formula_2"],
            "bbox": [150, 200, 400, 100]
          },
          "timing": {
            "t0": 3.0,
            "t1": 5.5,
            "confidence": 0.88,
            "source": "tts",
            "precision": "sentence"
          },
          "params": {
            "particle_count": 500,
            "particle_size": [2, 5],
            "colors": ["#3b82f6", "#60a5fa"],
            "physics": {
              "gravity": 0.1,
              "spread": 2.0
            }
          }
        }
      ]
    }
  ]
}
```

---

## 🎯 Метрики успеха

### Синхронизация:
- ✅ Точность: **±16ms** (1 frame @ 60 FPS)
- ✅ Предсказуемость: **100%** (детерминированный timeline)
- ✅ Confidence score: **>0.9** для 80% эффектов

### Производительность:
- ✅ FPS: **стабильные 60 FPS**
- ✅ CPU: **<10%** нагрузки
- ✅ GPU: WebGL acceleration
- ✅ Memory: **<50MB** для эффектов

### Визуальное качество:
- ✅ Плавные transitions (easing curves)
- ✅ Современные эффекты (particles, morphing, 3D)
- ✅ Профессиональный вид
- ✅ WOW-фактор для пользователей

---

## 🚀 План реализации

### Этап 1: Backend Core (2-3 часа)
- [ ] TimingEngine с упрощённой логикой
- [ ] EffectTypes определения
- [ ] TimelineBuilder для манифеста V2

### Этап 2: Frontend Core (3-4 часа)
- [ ] EffectsTimeline (event-driven)
- [ ] Canvas/WebGL рендерер
- [ ] Базовые эффекты (spotlight, highlight)

### Этап 3: Advanced Effects (4-5 часов)
- [ ] Particle system (GPU)
- [ ] Morphing animations
- [ ] Glitch, Ripple, Hologram эффекты

### Этап 4: Integration (2 часа)
- [ ] Интеграция с pipeline
- [ ] Миграция существующих cues
- [ ] Тестирование

### Этап 5: Polish (2 часа)
- [ ] Оптимизация производительности
- [ ] Тонкая настройка timing
- [ ] Документация

**Итого:** ~15 часов чистой работы

---

## 📚 Технологии

### Backend:
- Python 3.11+
- Pydantic для валидации
- NumPy для расчётов (если нужно)

### Frontend:
- TypeScript (строгая типизация)
- Canvas API + WebGL
- requestAnimationFrame для 60 FPS
- OffscreenCanvas для background rendering

### Библиотеки (опционально):
- Three.js (для 3D эффектов)
- GSAP (для продвинутых easing)
- PixiJS (для 2D GPU acceleration)

---

## ✅ Следующие шаги

1. ✅ Создать документацию (этот файл)
2. 🚧 Реализовать Backend Core
3. ⏳ Реализовать Frontend Core
4. ⏳ Добавить Advanced Effects
5. ⏳ Интеграция и тестирование

---

**Статус:** Готов к реализации! 🚀
