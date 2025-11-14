# 🎨 Frontend Integration Guide

**Дата:** 2024-01-15  
**Статус:** ✅ Компоненты созданы и готовы к интеграции

---

## 📦 Созданные Компоненты

### 1. WebSocket Hook (`src/hooks/useWebSocket.ts`)

Real-time прогресс обработки презентаций через WebSocket.

**Возможности:**
- ✅ Автоматическое переподключение
- ✅ Keepalive ping каждые 30 секунд
- ✅ Typed сообщения (TypeScript)
- ✅ Callbacks для разных типов событий
- ✅ Обработка ошибок

**Использование:**
```typescript
import { useWebSocket } from '@/hooks/useWebSocket';

const { isConnected, lastMessage } = useWebSocket({
  lessonId: 'abc-123',
  token: authToken,
  onProgress: (data) => {
    console.log(`Progress: ${data.percent}%`);
  },
  onCompletion: (data) => {
    console.log('Processing complete!', data.result);
  },
  autoConnect: true,
});
```

---

### 2. Real-Time Progress Component (`src/components/RealTimeProgress.tsx`)

Визуальный компонент для отображения прогресса обработки.

**Возможности:**
- ✅ Progress bar с процентами
- ✅ Отображение текущего этапа
- ✅ ETA (estimated time)
- ✅ Статус каждого слайда (grid visualization)
- ✅ Индикатор подключения
- ✅ Обработка ошибок

**Использование:**
```typescript
import { RealTimeProgress } from '@/components/RealTimeProgress';

<RealTimeProgress
  lessonId={lessonId}
  token={authToken}
  onComplete={(success, result) => {
    if (success) {
      // Redirect to player or show success message
      router.push(`/lessons/${lessonId}`);
    }
  }}
/>
```

**Скриншот:**
```
┌─────────────────────────────────────────────────┐
│ Обработка презентации              [●] Live    │
│ Отслеживание прогресса в реальном времени       │
├─────────────────────────────────────────────────┤
│ ⚡ Генерация скриптов              45%         │
│ ████████████░░░░░░░░░░░░░░░░                   │
│ Generating scripts for slides...                │
│                                                 │
│ Слайд: [5 / 10]                                │
│ ⏱ Осталось: 2m 15s                             │
│                                                 │
│ Статус слайдов:                                │
│ [✓][✓][✓][✓][●][░][░][░][░][░]                │
└─────────────────────────────────────────────────┘
```

---

### 3. Content Editor (`src/components/ContentEditor.tsx`)

Редактор для изменения и регенерации скриптов слайдов.

**Возможности:**
- ✅ Ручное редактирование текста
- ✅ AI регенерация сегментов (intro/main/conclusion/full)
- ✅ Выбор стиля (casual/formal/technical)
- ✅ Кастомные промпты
- ✅ Сохранение с/без регенерации аудио
- ✅ Отслеживание изменений
- ✅ 2 вкладки: Редактирование | Регенерация

**Использование:**
```typescript
import { ContentEditor } from '@/components/ContentEditor';

<ContentEditor
  lessonId={lessonId}
  slideNumber={currentSlide}
  initialScript={slide.lecture_text}
  onSave={(newScript) => {
    // Update local state
    updateSlideScript(newScript);
  }}
  onClose={() => setEditorOpen(false)}
/>
```

**Tabs:**

**Tab 1: Редактирование**
```
┌─────────────────────────────────────────────────┐
│ [Редактирование] | Регенерация                  │
├─────────────────────────────────────────────────┤
│ ┌───────────────────────────────────────────┐  │
│ │ В этом слайде мы рассмотрим...           │  │
│ │ Основные концепции включают:              │  │
│ │ 1. Архитектуру системы                    │  │
│ │ 2. Компоненты и их взаимодействие        │  │
│ │ ...                                       │  │
│ └───────────────────────────────────────────┘  │
│                                                 │
│ [💾 Сохранить и регенерировать аудио]          │
│ [Сохранить без аудио] [✕]                     │
└─────────────────────────────────────────────────┘
```

**Tab 2: Регенерация**
```
┌─────────────────────────────────────────────────┐
│ Редактирование | [Регенерация]                  │
├─────────────────────────────────────────────────┤
│ Сегмент: [Вступление ▼]                        │
│ Стиль:   [Неформальный ▼]                      │
│                                                 │
│ Дополнительные инструкции:                     │
│ ┌───────────────────────────────────────────┐  │
│ │ Добавить больше примеров...               │  │
│ └───────────────────────────────────────────┘  │
│                                                 │
│ [✨ Регенерировать с помощью AI]               │
└─────────────────────────────────────────────────┘
```

---

### 4. Subscription Manager (`src/components/SubscriptionManager.tsx`)

Управление подпиской пользователя.

**Возможности:**
- ✅ Отображение текущего тарифа
- ✅ Usage tracking (presentations used)
- ✅ Список возможностей тарифа
- ✅ Карточки для upgrade (PRO/ENTERPRISE)
- ✅ Предупреждения при приближении к лимиту
- ✅ Цветовая кодировка тарифов

**Использование:**
```typescript
import { SubscriptionManager } from '@/components/SubscriptionManager';

// В профиле пользователя или отдельной странице
<SubscriptionManager />
```

**Визуализация:**
```
┌─────────────────────────────────────────────────┐
│ ⚡ Free                              [FREE]     │
│ Ваш текущий тариф                              │
├─────────────────────────────────────────────────┤
│ Использовано презентаций                       │
│ 2 / 3                                           │
│ ████████████████████░░░░░░░░ 67%               │
│                                                 │
│ Макс. слайдов:   10  │  Макс. размер:   10MB  │
│ Качество AI:   basic │  Приоритет:       low  │
│                                                 │
│ Возможности:                                    │
│ ✓ 3 presentations per month                    │
│ ✓ Up to 10 slides per presentation             │
│ ✓ Basic AI quality                             │
│ ✓ MP4 export only                              │
└─────────────────────────────────────────────────┘

Обновить тариф
┌──────────────────────┐ ┌───────────────────────┐
│ 📈 Professional      │ │ 👑 Enterprise         │
│ $29.99/месяц         │ │ $99.99/месяц          │
├──────────────────────┤ ├───────────────────────┤
│ ✓ 50 presentations   │ │ ✓ Unlimited           │
│ ✓ 100 slides         │ │ ✓ 500 slides          │
│ ✓ Premium AI         │ │ ✓ API access          │
│ ✓ Custom voices      │ │ ✓ Dedicated support   │
│                      │ │                       │
│ [Обновить до PRO]    │ │ [Обновить до ENTERP.] │
└──────────────────────┘ └───────────────────────┘
```

---

## 🔌 Интеграция в Существующий UI

### 1. Добавить в Upload Flow

Замените `ProcessingProgress` на `RealTimeProgress`:

```typescript
// src/pages/Upload.tsx или где происходит загрузка

import { RealTimeProgress } from '@/components/RealTimeProgress';

function UploadPage() {
  const [processingLessonId, setProcessingLessonId] = useState<string | null>(null);

  const handleUpload = async (file: File) => {
    const response = await apiClient.uploadPresentation(file);
    setProcessingLessonId(response.lesson_id);
  };

  return (
    <div>
      {!processingLessonId ? (
        <FileUploader onUpload={handleUpload} />
      ) : (
        <RealTimeProgress
          lessonId={processingLessonId}
          token={authToken}
          onComplete={(success) => {
            if (success) {
              router.push(`/lessons/${processingLessonId}`);
            }
          }}
        />
      )}
    </div>
  );
}
```

---

### 2. Добавить Content Editor в Player

Добавьте кнопку редактирования в плеер:

```typescript
// src/components/Player.tsx

import { ContentEditor } from '@/components/ContentEditor';
import { Dialog, DialogContent } from '@/components/ui/dialog';

function Player({ lessonId }: PlayerProps) {
  const [editorOpen, setEditorOpen] = useState(false);
  const [editingSlide, setEditingSlide] = useState<number | null>(null);

  const handleEditSlide = (slideNumber: number) => {
    setEditingSlide(slideNumber);
    setEditorOpen(true);
  };

  return (
    <>
      {/* Existing player UI */}
      <div className="player-controls">
        <Button onClick={() => handleEditSlide(currentSlide)}>
          <Edit3 className="h-4 w-4" />
          Редактировать скрипт
        </Button>
      </div>

      {/* Content Editor Dialog */}
      <Dialog open={editorOpen} onOpenChange={setEditorOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          {editingSlide && (
            <ContentEditor
              lessonId={lessonId}
              slideNumber={editingSlide}
              initialScript={slides[editingSlide - 1]?.lecture_text}
              onSave={(newScript) => {
                // Update slide script in state
                updateSlide(editingSlide, newScript);
                setEditorOpen(false);
              }}
              onClose={() => setEditorOpen(false)}
            />
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
```

---

### 3. Добавить Subscription Page

Создайте отдельную страницу или вкладку в профиле:

```typescript
// src/pages/Subscription.tsx

import { SubscriptionManager } from '@/components/SubscriptionManager';

export function SubscriptionPage() {
  return (
    <div className="container max-w-6xl py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Управление подпиской</h1>
        <p className="text-muted-foreground">
          Просмотр и управление вашим тарифным планом
        </p>
      </div>

      <SubscriptionManager />
    </div>
  );
}
```

Добавьте в роутинг:
```typescript
// src/App.tsx или routes

import { SubscriptionPage } from '@/pages/Subscription';

<Route path="/subscription" element={<SubscriptionPage />} />
```

---

## 🔧 Конфигурация

### Environment Variables

Добавьте в `.env`:

```bash
# WebSocket URL
VITE_WS_URL=ws://localhost:8000

# API Base URL (if not already set)
VITE_API_URL=http://localhost:8000
```

---

### API Client Updates

Убедитесь что `src/lib/api.ts` поддерживает новые endpoints:

```typescript
// src/lib/api.ts

export const apiClient = {
  // ... existing methods

  // Content Editor
  async getSlideScript(lessonId: string, slideNumber: number) {
    return fetch(`/api/content/slide-script/${lessonId}/${slideNumber}`, {
      headers: { 'Authorization': `Bearer ${getToken()}` },
    }).then(r => r.json());
  },

  async regenerateSegment(data: RegenerateSegmentRequest) {
    return fetch('/api/content/regenerate-segment', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`,
      },
      body: JSON.stringify(data),
    }).then(r => r.json());
  },

  async editScript(data: EditScriptRequest) {
    return fetch('/api/content/edit-script', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`,
      },
      body: JSON.stringify(data),
    }).then(r => r.json());
  },

  // Subscription
  async getSubscriptionInfo() {
    return fetch('/api/subscription/info', {
      headers: { 'Authorization': `Bearer ${getToken()}` },
    }).then(r => r.json());
  },

  async getAllPlans() {
    return fetch('/api/subscription/plans').then(r => r.json());
  },
};
```

---

## 🎨 Styling

Все компоненты используют shadcn/ui, который уже установлен в проекте.

Если нужны дополнительные стили, добавьте в `tailwind.config.ts`:

```typescript
// tailwind.config.ts

export default {
  // ... existing config
  theme: {
    extend: {
      // Add custom animations for progress indicators
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
};
```

---

## 🧪 Testing

### Manual Testing Checklist

#### WebSocket / Progress
- [ ] Загрузить презентацию
- [ ] Проверить что WebSocket подключается
- [ ] Progress bar обновляется в реальном времени
- [ ] ETA отображается корректно
- [ ] Grid статуса слайдов обновляется
- [ ] При completion показывается success message
- [ ] При ошибке показывается error alert

#### Content Editor
- [ ] Открыть Content Editor для слайда
- [ ] Отредактировать текст вручную
- [ ] Сохранить изменения
- [ ] Регенерировать сегмент (intro)
- [ ] Проверить что AI генерирует новый текст
- [ ] Сменить стиль и регенерировать
- [ ] Проверить кастомный промпт

#### Subscription Manager
- [ ] Открыть страницу подписки
- [ ] Проверить отображение текущего тарифа
- [ ] Usage bar показывает правильный процент
- [ ] Upgrade карточки отображаются
- [ ] При приближении к лимиту показывается warning

---

## 📦 TypeScript Types

Все компоненты полностью типизированы. Основные типы:

```typescript
// Progress Message
interface ProgressMessage {
  type: 'progress' | 'completion' | 'error' | 'slide_update' | 'connected';
  lesson_id: string;
  stage?: string;
  percent?: number;
  message?: string;
  // ... more fields
}

// Subscription Info
interface SubscriptionInfo {
  user_id: string;
  tier: 'free' | 'pro' | 'enterprise';
  plan: SubscriptionPlan;
  usage: {
    presentations_this_month: number;
    current_concurrent: number;
  };
}

// Content Editor Request
interface RegenerateSegmentRequest {
  lesson_id: string;
  slide_number: number;
  segment_type: 'intro' | 'main' | 'conclusion' | 'full';
  style?: 'casual' | 'formal' | 'technical';
  custom_prompt?: string;
}
```

---

## 🚀 Deployment

### Build

```bash
# Development
npm run dev

# Production build
npm run build

# Preview production build
npm run preview
```

### Docker

Если используете Docker, убедитесь что frontend контейнер rebuilded:

```bash
docker-compose down
docker-compose up -d --build frontend
```

---

## 📊 Monitoring

### Console Logs

Все компоненты логируют важные события в console:

```javascript
// WebSocket
console.log('WebSocket connected');
console.log('WebSocket message:', data);

// Content Editor
console.log('Script saved successfully');
console.log('Regeneration started');
```

### Network Tab

Проверьте в DevTools:
- **WS:** `ws://localhost:8000/api/ws/progress/{lesson_id}`
- **API:** `/api/content/*` endpoints
- **API:** `/api/subscription/*` endpoints

---

## 🔍 Troubleshooting

### WebSocket не подключается

1. Проверить что backend запущен: `curl http://localhost:8000/health`
2. Проверить VITE_WS_URL в `.env`
3. Проверить CORS настройки в backend
4. Проверить в Network tab DevTools

### Content Editor не сохраняет

1. Проверить что token валиден
2. Проверить в Network tab response
3. Проверить backend logs
4. Убедиться что lesson_id существует

### Subscription не загружается

1. Проверить что пользователь авторизован
2. Проверить что /api/subscription/info endpoint доступен
3. Проверить backend logs
4. Миграция БД применена (subscription_tier column exists)

---

## ✅ Summary

**Созданные файлы:**
- `src/hooks/useWebSocket.ts` - WebSocket hook
- `src/components/RealTimeProgress.tsx` - Progress UI
- `src/components/ContentEditor.tsx` - Script editor
- `src/components/SubscriptionManager.tsx` - Subscription UI

**Следующие шаги:**
1. ✅ Компоненты созданы
2. ⏳ Интегрировать в существующий UI
3. ⏳ Протестировать end-to-end
4. ⏳ Deploy

**Статус:** ✅ Ready for Integration

---

Все frontend компоненты готовы к использованию! Интегрируйте их в существующий UI согласно инструкциям выше.
