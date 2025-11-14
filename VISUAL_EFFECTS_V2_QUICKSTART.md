# 🚀 Visual Effects V2 - Quick Start Guide

## Быстрый старт (Backend V2)

### 1. Простой пример использования

```python
from backend.app.services.visual_effects import VisualEffectsEngineV2

# Инициализация
engine = VisualEffectsEngineV2()

# Генерация manifest для одного слайда
manifest = engine.generate_slide_manifest(
    semantic_map={
        'groups': [
            {
                'id': 'title_group',
                'type': 'title',
                'priority': 'high',
                'element_ids': ['elem_0']
            }
        ]
    },
    elements=[
        {
            'id': 'elem_0',
            'text': 'Welcome to Presentation',
            'bbox': [100, 50, 600, 80]
        }
    ],
    audio_duration=10.0,
    slide_id='slide_0',
    talk_track=[
        {
            'segment': 'introduction',
            'group_id': 'title_group',
            'text': 'Welcome to our presentation',
            'start': 0.3,
            'end': 2.8
        }
    ]
)

# Результат:
print(f"Эффектов: {len(manifest['effects'])}")
print(f"Качество: {manifest['quality']['score']}/100")
print(f"События timeline: {len(manifest['timeline']['events'])}")
```

### 2. Интеграция в OptimizedIntelligentPipeline

```python
def build_manifest(self, lesson_dir: str):
    """Stage 6-8: Visual effects + validation + final manifest"""
    
    # Импорт нового движка
    from backend.app.services.visual_effects import VisualEffectsEngineV2
    effects_engine = VisualEffectsEngineV2()
    
    for slide in slides:
        # Генерация эффектов V2
        slide_manifest = effects_engine.generate_slide_manifest(
            semantic_map=slide.get('semantic_map', {}),
            elements=slide.get('elements', []),
            audio_duration=slide.get('duration', 0.0),
            slide_id=slide['id'],
            tts_words=slide.get('tts_words'),
            talk_track=slide.get('talk_track'),
            slide_data={
                'image': slide.get('image'),
                'speaker_notes': slide.get('speaker_notes'),
            }
        )
        
        # Добавляем V2 данные в слайд
        slide['effects'] = slide_manifest['effects']
        slide['timeline'] = slide_manifest['timeline']
        slide['quality'] = slide_manifest['quality']
        
        # Для обратной совместимости (если нужно)
        slide['cues'] = self._convert_effects_to_cues(slide_manifest['effects'])
```

### 3. Тестирование

```bash
# Запуск примеров из модулей
cd /Users/iliazarikov/Documents/Python_crypto/Barahlo/slide-speaker-main/backend

# Test Timing Engine
python -m app.services.visual_effects.core.timing_engine

# Test Facade (полный пример)
python -m app.services.visual_effects.facade
```

### 4. Проверка качества

```python
# После генерации manifest
quality = manifest['quality']

if quality['score'] >= 80:
    print("✅ Отличное качество!")
elif quality['score'] >= 60:
    print("⚠️ Среднее качество")
else:
    print("❌ Низкое качество, проверьте данные")

# Детали
print(f"Средняя уверенность: {quality['confidence_avg']}")
print(f"Эффектов с высокой уверенностью: {quality['high_confidence_count']}")
```

---

## Формат данных

### Входные данные:

```python
semantic_map = {
    'groups': [
        {
            'id': 'group_id',           # Уникальный ID
            'type': 'title',            # title|body|bullet_list|diagram|formula
            'priority': 'high',          # critical|high|medium|low|none
            'element_ids': ['elem_0'],   # Список ID элементов
            'highlight_strategy': {      # Опционально
                'effect_type': 'spotlight',
                'intensity': 'dramatic'
            }
        }
    ]
}

elements = [
    {
        'id': 'elem_0',
        'text': 'Element text',
        'bbox': [x, y, width, height]   # Координаты
    }
]

talk_track = [
    {
        'segment': 'introduction',       # Тип сегмента
        'group_id': 'group_id',          # Ссылка на группу
        'text': 'Narration text',        # Текст озвучки
        'start': 0.3,                    # Начало (секунды)
        'end': 2.8                       # Конец (секунды)
    }
]

tts_words = {
    'sentences': [
        {
            'text': 'Sentence text',
            't0': 0.3,
            't1': 2.5
        }
    ]
}
```

### Выходные данные (manifest V2):

```python
{
    'version': '2.0',
    'id': 'slide_0',
    'effects': [
        {
            'id': 'effect_xxx',
            'type': 'spotlight',
            'timing': {
                't0': 0.3,
                't1': 2.5,
                'confidence': 0.95,
                'source': 'talk_track',
                'precision': 'segment'
            },
            'target': {
                'element_id': 'elem_0',
                'bbox': [100, 50, 600, 80]
            },
            'params': {
                'intensity': 'dramatic',
                'ease_in': 'cubic-out',
                'ease_out': 'cubic-in'
            }
        }
    ],
    'timeline': {
        'total_duration': 10.0,
        'events': [
            {'time': 0.0, 'type': 'SLIDE_START'},
            {'time': 0.3, 'type': 'START', 'effect_id': 'effect_xxx'},
            {'time': 2.5, 'type': 'END', 'effect_id': 'effect_xxx'},
            {'time': 10.0, 'type': 'SLIDE_END'}
        ],
        'effects_count': 1
    },
    'quality': {
        'score': 95,
        'confidence_avg': 0.95,
        'high_confidence_count': 1,
        'total_effects': 1
    }
}
```

---

## Типы эффектов

```python
from backend.app.services.visual_effects.core import EffectType

# Базовые
EffectType.SPOTLIGHT         # Драматичный spotlight
EffectType.HIGHLIGHT         # Классическое выделение
EffectType.FADE_IN          # Плавное появление

# Продвинутые (для будущего Frontend)
EffectType.PARTICLE_HIGHLIGHT  # GPU частицы
EffectType.MORPH               # Morphing анимация
EffectType.GLITCH              # Glitch эффект
EffectType.RIPPLE              # Волновой эффект
EffectType.HOLOGRAM            # 3D голограмма
```

---

## FAQ

### Q: Как выбрать тип эффекта?
A: Система автоматически выбирает на основе `group.type` и `priority`:
- `title` + `high` → SPOTLIGHT
- `body` → HIGHLIGHT  
- `diagram` → PARTICLE_HIGHLIGHT
- etc.

Можно переопределить в `highlight_strategy.effect_type`.

### Q: Как повысить точность синхронизации?
A: Обеспечьте качественные входные данные:
1. `talk_track` с точными `start`/`end` (confidence 0.95)
2. `tts_words` с sentences (confidence 0.7-0.9)
3. Fallback даст confidence 0.3

### Q: Что означает confidence?
A:
- **0.9-1.0**: Отлично (talk_track timing)
- **0.7-0.9**: Хорошо (TTS sentences)
- **0.3-0.7**: Средне (частичное совпадение)
- **0.0-0.3**: Плохо (fallback)

### Q: Как отладить проблемы?
A: Проверьте каждый effect:
```python
for effect in manifest['effects']:
    timing = effect['timing']
    print(f"{effect['id']}: source={timing['source']}, conf={timing['confidence']}")
    
    if timing['confidence'] < 0.6:
        print(f"  ⚠️ Низкая уверенность, проверьте talk_track/tts_words")
```

---

## Roadmap

- [x] ✅ Backend Core (Timing, Effects, Timeline)
- [x] ✅ Semantic Generator
- [x] ✅ Facade API
- [ ] ⏳ Frontend Timeline (event-driven)
- [ ] ⏳ Canvas/WebGL Renderer
- [ ] ⏳ Modern Effects (particles, morph, glitch)
- [ ] ⏳ Integration в pipeline
- [ ] ⏳ Testing на реальных презентациях

---

**Статус:** Backend V2 готов к использованию! 🎉
