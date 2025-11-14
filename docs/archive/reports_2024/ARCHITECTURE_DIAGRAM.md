# Архитектура новой системы генерации лекций

```
Document Upload
       ↓
Document Parser
       ↓
Extract Elements
       ↓
Concept Extractor ←→ Slide Concepts
       ↓
Lecture Outline Generator ←→ Global Outline
       ↓
AI Generator
       ↓
Build Lecture Prompt
       ↓
Call LLM
       ↓
Generate Talk Track
       ↓
Anti-Reading Check
       ↓
Overlap > 0.35? → Yes → Regenerate with Enhanced Prompt
       ↓ No
Accept Talk Track
       ↓
Generate Visual Cues
       ↓
Map to Elements
       ↓
Final Speaker Notes
       ↓
Player Component
       ↓
┌─────────────────┬─────────────────┬─────────────────┐
│ Display Talk    │ Show Visual     │ Sync with       │
│ Track           │ Cues            │ Audio           │
└─────────────────┴─────────────────┴─────────────────┘
```

## Ключевые компоненты:

### 1. Concept Extractor
- Извлекает заголовок, тезисы, визуальные инсайты
- Определяет термины для объяснения
- Структурирует информацию для LLM

### 2. Anti-Reading Check
- Вычисляет Jaccard similarity
- Проверяет порог перекрытия (0.35)
- Инициирует регенерацию при необходимости

### 3. Talk Track Generator
- Создает структурированную речь
- Включает hook, core, example, contrast, takeaway, question
- Обеспечивает объяснение вместо чтения

### 4. Visual Cues Mapper
- Привязывает речь к элементам слайда
- Создает тайминги для подсветки
- Синхронизирует с аудио

### 5. Player Integration
- Отображает talk_track по сегментам
- Показывает visual_cues в нужное время
- Поддерживает редактирование

## Поток данных:

1. **Входные данные:** Элементы слайда (текст, позиции)
2. **Обработка:** Извлечение концептов, генерация плана
3. **Генерация:** Создание talk_track с проверкой анти-чтения
4. **Синхронизация:** Привязка к визуальным элементам
5. **Воспроизведение:** Отображение в плеере

## Преимущества архитектуры:

- **Модульность:** Каждый компонент независим
- **Проверяемость:** Автоматическая валидация качества
- **Расширяемость:** Легко добавлять новые стили
- **Совместимость:** Работает со старой системой