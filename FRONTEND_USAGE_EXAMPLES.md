# 🎨 Frontend Usage Examples

**Быстрые примеры интеграции новых компонентов**

---

## 1️⃣ Enhanced File Uploader (WebSocket Progress)

### Замена старого FileUploader

**Было (с polling):**
```typescript
// src/pages/UploadPage.tsx
import { FileUploader } from '@/components/FileUploader';

<FileUploader onUploadSuccess={(lessonId) => navigate(`/lessons/${lessonId}`)} />
```

**Стало (с WebSocket):**
```typescript
// src/pages/UploadPage.tsx
import { EnhancedFileUploader } from '@/components/EnhancedFileUploader';

<EnhancedFileUploader onUploadSuccess={(lessonId) => navigate(`/lessons/${lessonId}`)} />
```

**Результат:**
- ✅ Instant progress updates (no 2s delay)
- ✅ Real-time slide status grid
- ✅ ETA calculation
- ✅ Better UX

---

## 2️⃣ Player with Content Editor

### Обновление страницы плеера

**Было:**
```typescript
// src/pages/LessonPage.tsx
import { Player } from '@/components/Player';

<Player 
  lessonId={lessonId}
  onExportMP4={() => handleExport()}
/>
```

**Стало:**
```typescript
// src/pages/LessonPage.tsx
import { PlayerWithEditor } from '@/components/PlayerWithEditor';

<PlayerWithEditor 
  lessonId={lessonId}
  onExportMP4={() => handleExport()}
/>
```

**Результат:**
- ✅ Floating "Редактировать скрипт" button
- ✅ Full-screen editor dialog
- ✅ AI regeneration + manual editing
- ✅ Saves and regenerates audio

---

## 3️⃣ Subscription Page

### Добавление в роутинг

**App.tsx или routes:**
```typescript
import { SubscriptionPage } from '@/pages/SubscriptionPage';

// Add route
<Route path="/subscription" element={<SubscriptionPage />} />
```

### Добавление ссылки в навигацию

**Navigation.tsx:**
```typescript
import { Crown } from 'lucide-react';

<nav>
  <Link to="/subscription">
    <Crown className="h-4 w-4" />
    Подписка
  </Link>
</nav>
```

**Результат:**
- ✅ Full subscription management
- ✅ Usage tracking
- ✅ Upgrade cards
- ✅ Warnings at limit

---

## 4️⃣ Standalone Components

### RealTimeProgress (custom usage)

```typescript
import { RealTimeProgress } from '@/components/RealTimeProgress';

// In любой компонент где нужен прогресс
<RealTimeProgress
  lessonId={lessonId}
  token={authToken}
  onComplete={(success, result) => {
    if (success) {
      console.log('Done!', result);
      router.push(`/lessons/${lessonId}`);
    } else {
      showError('Processing failed');
    }
  }}
/>
```

### ContentEditor (standalone)

```typescript
import { ContentEditor } from '@/components/ContentEditor';

// В модальном окне или на отдельной странице
<ContentEditor
  lessonId={lessonId}
  slideNumber={currentSlide}
  initialScript={slide.lecture_text}
  onSave={(newScript) => {
    updateSlideInState(currentSlide, newScript);
    toast({ title: 'Сохранено!' });
  }}
  onClose={() => setModalOpen(false)}
/>
```

### SubscriptionManager (в профиле)

```typescript
import { SubscriptionManager } from '@/components/SubscriptionManager';

// В профиле пользователя или dashboard
<Tabs defaultValue="profile">
  <TabsList>
    <TabsTrigger value="profile">Профиль</TabsTrigger>
    <TabsTrigger value="subscription">Подписка</TabsTrigger>
  </TabsList>
  
  <TabsContent value="profile">
    {/* Profile content */}
  </TabsContent>
  
  <TabsContent value="subscription">
    <SubscriptionManager />
  </TabsContent>
</Tabs>
```

---

## 5️⃣ useWebSocket Hook (custom usage)

```typescript
import { useWebSocket } from '@/hooks/useWebSocket';

function CustomProgressComponent({ lessonId }: { lessonId: string }) {
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('');

  const { isConnected, error } = useWebSocket({
    lessonId,
    token: localStorage.getItem('token'),
    
    onProgress: (data) => {
      setProgress(data.percent || 0);
      setMessage(data.message || '');
    },
    
    onCompletion: (data) => {
      alert('Done!');
    },
    
    onError: (data) => {
      console.error(data.error_message);
    },
    
    onSlideUpdate: (data) => {
      console.log(`Slide ${data.slide_number}: ${data.status}`);
    },
    
    autoConnect: true,
  });

  return (
    <div>
      <div>Status: {isConnected ? 'Connected' : 'Disconnected'}</div>
      <div>Progress: {progress}%</div>
      <div>Message: {message}</div>
      {error && <div>Error: {error}</div>}
    </div>
  );
}
```

---

## 6️⃣ Complete Integration Example

### Full Upload → Process → View Flow

```typescript
// src/pages/HomePage.tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { EnhancedFileUploader } from '@/components/EnhancedFileUploader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function HomePage() {
  const navigate = useNavigate();

  return (
    <div className="container max-w-4xl py-12">
      <Card>
        <CardHeader>
          <CardTitle>Создать презентацию</CardTitle>
        </CardHeader>
        <CardContent>
          <EnhancedFileUploader
            onUploadSuccess={(lessonId) => {
              // Автоматический redirect после успешной обработки
              navigate(`/lessons/${lessonId}`);
            }}
          />
        </CardContent>
      </Card>
    </div>
  );
}
```

```typescript
// src/pages/LessonPage.tsx
import { useParams } from 'react-router-dom';
import { PlayerWithEditor } from '@/components/PlayerWithEditor';

export function LessonPage() {
  const { lessonId } = useParams<{ lessonId: string }>();

  if (!lessonId) {
    return <div>Lesson not found</div>;
  }

  return (
    <div className="container max-w-7xl py-8">
      <PlayerWithEditor
        lessonId={lessonId}
        onExportMP4={() => {
          // Handle export
          console.log('Exporting...');
        }}
      />
    </div>
  );
}
```

---

## 7️⃣ API Client Updates

### Ensure these methods exist in src/lib/api.ts

```typescript
// src/lib/api.ts

export const apiClient = {
  // Existing methods...
  
  // Content Editor APIs
  async getSlideScript(lessonId: string, slideNumber: number) {
    const response = await fetch(
      `/api/content/slide-script/${lessonId}/${slideNumber}`,
      {
        headers: {
          'Authorization': `Bearer ${getToken()}`,
        },
      }
    );
    if (!response.ok) throw new Error('Failed to get slide script');
    return response.json();
  },

  async regenerateSegment(data: {
    lesson_id: string;
    slide_number: number;
    segment_type: 'intro' | 'main' | 'conclusion' | 'full';
    style?: string;
    custom_prompt?: string;
  }) {
    const response = await fetch('/api/content/regenerate-segment', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`,
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to regenerate segment');
    return response.json();
  },

  async editScript(data: {
    lesson_id: string;
    slide_number: number;
    new_script: string;
    regenerate_audio?: boolean;
  }) {
    const response = await fetch('/api/content/edit-script', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`,
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to edit script');
    return response.json();
  },

  // Subscription APIs
  async getSubscriptionInfo() {
    const response = await fetch('/api/subscription/info', {
      headers: {
        'Authorization': `Bearer ${getToken()}`,
      },
    });
    if (!response.ok) throw new Error('Failed to get subscription');
    return response.json();
  },

  async getAllPlans() {
    const response = await fetch('/api/subscription/plans');
    if (!response.ok) throw new Error('Failed to get plans');
    return response.json();
  },
};

function getToken(): string {
  return localStorage.getItem('token') || '';
}
```

---

## 8️⃣ Environment Variables

### .env or .env.local

```bash
# WebSocket URL
VITE_WS_URL=ws://localhost:8000

# API Base URL
VITE_API_URL=http://localhost:8000

# For production:
# VITE_WS_URL=wss://api.yoursite.com
# VITE_API_URL=https://api.yoursite.com
```

---

## 9️⃣ Testing Checklist

### Before deploying, test:

#### File Upload Flow
- [ ] Drag & drop works
- [ ] File type validation works
- [ ] Upload progress shows correctly
- [ ] WebSocket connects after upload
- [ ] Real-time progress updates
- [ ] ETA displays
- [ ] Slide grid updates
- [ ] Completion message shows
- [ ] Auto-redirect works

#### Content Editor
- [ ] Opens from player
- [ ] Loads current script
- [ ] Manual editing works
- [ ] Save button works
- [ ] AI regeneration works
- [ ] Style selection works
- [ ] Custom prompts work
- [ ] Audio regeneration triggers
- [ ] Changes persist

#### Subscription Manager
- [ ] Current plan displays
- [ ] Usage bar correct
- [ ] Upgrade cards show
- [ ] Limits display correctly
- [ ] Warning at 80% usage
- [ ] Features list correct

---

## 🔟 Troubleshooting

### WebSocket not connecting

```typescript
// Check WebSocket URL in browser console
console.log('WS URL:', import.meta.env.VITE_WS_URL);

// Test WebSocket manually
const ws = new WebSocket('ws://localhost:8000/api/ws/status');
ws.onopen = () => console.log('Connected');
ws.onmessage = (e) => console.log('Message:', e.data);
ws.onerror = (e) => console.error('Error:', e);
```

### API calls failing

```typescript
// Check token
console.log('Token:', localStorage.getItem('token'));

// Test API manually
fetch('http://localhost:8000/api/subscription/info', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  }
})
  .then(r => r.json())
  .then(d => console.log('Subscription:', d))
  .catch(e => console.error('Error:', e));
```

### Components not importing

```bash
# Check file exists
ls -la src/components/RealTimeProgress.tsx
ls -la src/hooks/useWebSocket.ts

# Rebuild
npm run build
```

---

## ✅ Quick Start Commands

```bash
# 1. Install dependencies (if any missing)
npm install

# 2. Start development server
npm run dev

# 3. In another terminal, ensure backend is running
cd backend
docker-compose up -d

# 4. Open browser
open http://localhost:3000

# 5. Test upload flow
# - Upload a presentation
# - Watch real-time progress
# - Open player
# - Click "Редактировать скрипт"
# - Edit and save
# - Check subscription page
```

---

## 📊 Component Sizes

| Component | Lines | Size | Complexity |
|-----------|-------|------|------------|
| EnhancedFileUploader | ~270 | 8KB | Medium |
| PlayerWithEditor | ~60 | 2KB | Low |
| SubscriptionPage | ~50 | 2KB | Low |
| RealTimeProgress | ~250 | 8KB | Medium |
| ContentEditor | ~300 | 10KB | High |
| SubscriptionManager | ~280 | 9KB | Medium |
| useWebSocket | ~220 | 7KB | High |

---

## 🎯 Performance Tips

1. **Lazy load heavy components:**
```typescript
const ContentEditor = lazy(() => import('@/components/ContentEditor'));
const SubscriptionManager = lazy(() => import('@/components/SubscriptionManager'));
```

2. **Memoize WebSocket callbacks:**
```typescript
const onProgress = useCallback((data) => {
  setProgress(data.percent);
}, []);
```

3. **Cleanup WebSocket on unmount:**
```typescript
useEffect(() => {
  return () => {
    disconnect();
  };
}, []);
```

---

**Все компоненты готовы к использованию!** 🚀

Просто замените старые компоненты на новые согласно примерам выше.
