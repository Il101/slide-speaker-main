# План действий по улучшению UX/UI - ИИ-Лектор

## 🚨 Фаза 1: Критические исправления (1-2 дня)

### День 1: Доступность и безопасность

#### 1. Добавить Error Boundaries
```tsx
// src/components/ErrorBoundary.tsx
import React, { Component, ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
    // Отправить в Sentry или другой сервис мониторинга
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="flex flex-col items-center justify-center min-h-[400px] p-8">
          <AlertTriangle className="h-12 w-12 text-destructive mb-4" />
          <h2 className="text-xl font-semibold mb-2">Что-то пошло не так</h2>
          <p className="text-muted-foreground text-center mb-4">
            Произошла ошибка при отображении этого компонента
          </p>
          <Button onClick={() => window.location.reload()}>
            Перезагрузить страницу
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}

// Обернуть критические компоненты
// App.tsx
<ErrorBoundary>
  <Player />
</ErrorBoundary>
```

#### 2. Исправить доступность
```tsx
// src/components/SkipLink.tsx
export const SkipLink = () => (
  <a 
    href="#main-content" 
    className="absolute left-[-9999px] z-50 bg-primary text-primary-foreground px-4 py-2 focus:left-4 focus:top-4"
  >
    Перейти к основному контенту
  </a>
);

// Добавить в App.tsx
<>
  <SkipLink />
  <main id="main-content">
    {/* содержимое */}
  </main>
</>
```

#### 3. ARIA атрибуты для интерактивных элементов
```tsx
// src/components/VirtualizedSlideList.tsx - исправить
<div
  role="button"
  tabIndex={0}
  aria-label={`Слайд ${slide.id}${currentSlide === slide.id ? ' (текущий)' : ''}`}
  aria-pressed={currentSlide === slide.id}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onSlideSelect(slide.id);
    }
  }}
  onClick={() => onSlideSelect(slide.id)}
>
```

### День 2: Мобильная адаптивность

#### 1. Создать мобильную навигацию
```tsx
// src/components/MobileNav.tsx
import { Menu, X } from 'lucide-react';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { useState } from 'react';

export const MobileNav = ({ user, onLogout }) => {
  const [open, setOpen] = useState(false);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="md:hidden">
          <Menu className="h-5 w-5" />
          <span className="sr-only">Открыть меню</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-[300px]">
        <nav className="flex flex-col space-y-4">
          {/* Навигационные элементы */}
        </nav>
      </SheetContent>
    </Sheet>
  );
};
```

#### 2. Адаптировать сайдбар
```tsx
// src/components/MyVideosSidebar.tsx - изменить
<div className="w-full lg:w-[400px] xl:w-[560px] 
  fixed lg:relative 
  inset-y-0 right-0 
  transform lg:transform-none
  transition-transform duration-300
  ${isOpen ? 'translate-x-0' : 'translate-x-full lg:translate-x-0'}
  z-40 lg:z-auto
  bg-background lg:bg-transparent
">
```

## 📈 Фаза 2: Важные улучшения (3-5 дней)

### День 3: Оптимизация производительности

#### 1. Разбить Player на модули
```bash
# Структура папок
src/components/Player/
├── index.tsx                 # Главный компонент-контейнер
├── PlayerProvider.tsx        # Context provider
├── PlayerControls.tsx        # Панель управления
├── SlideViewer.tsx          # Отображение слайдов
├── EffectsRenderer.tsx      # Визуальные эффекты
├── EditPanel.tsx            # Панель редактирования
├── hooks/
│   ├── usePlayerState.ts
│   ├── useAudioSync.ts
│   └── useKeyboardControls.ts
└── utils/
    ├── calculateScale.ts
    └── formatTime.ts
```

#### 2. Добавить lazy loading
```tsx
// src/App.tsx
import { lazy, Suspense } from 'react';
import { Loader2 } from 'lucide-react';

const Player = lazy(() => import('./components/Player'));
const SubscriptionManager = lazy(() => import('./components/SubscriptionManager'));

const LoadingFallback = () => (
  <div className="flex items-center justify-center h-64">
    <Loader2 className="h-8 w-8 animate-spin" />
  </div>
);

// Использование
<Suspense fallback={<LoadingFallback />}>
  <Player lessonId={lessonId} />
</Suspense>
```

### День 4: UI улучшения

#### 1. Skeleton loaders
```tsx
// src/components/ui/skeleton-variants.tsx
export const VideoCardSkeleton = () => (
  <Card className="p-4">
    <div className="flex space-x-4">
      <Skeleton className="h-20 w-32 rounded" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
        <Skeleton className="h-3 w-1/4" />
      </div>
    </div>
  </Card>
);

export const SlideListSkeleton = () => (
  <div className="space-y-2">
    {[...Array(5)].map((_, i) => (
      <div key={i} className="flex items-center space-x-3 p-2">
        <Skeleton className="h-12 w-16 rounded" />
        <div className="flex-1 space-y-1">
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-2 w-32" />
        </div>
      </div>
    ))}
  </div>
);
```

#### 2. Empty states
```tsx
// src/components/EmptyStates.tsx
export const EmptyVideos = ({ onAction }) => (
  <div className="flex flex-col items-center justify-center py-12 px-4">
    <FileVideo className="h-16 w-16 text-muted-foreground mb-4" />
    <h3 className="text-lg font-semibold mb-2">Нет загруженных лекций</h3>
    <p className="text-muted-foreground text-center mb-6 max-w-md">
      Начните с загрузки вашей первой презентации. 
      ИИ превратит её в интерактивную лекцию с озвучкой.
    </p>
    <Button onClick={onAction} size="lg">
      <Upload className="mr-2 h-4 w-4" />
      Загрузить презентацию
    </Button>
  </div>
);
```

### День 5: Формы и валидация

#### 1. Улучшить обработку форм
```tsx
// src/hooks/useFormValidation.ts
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const loginSchema = z.object({
  email: z.string()
    .email('Неверный формат email')
    .min(1, 'Email обязателен'),
  password: z.string()
    .min(8, 'Пароль должен быть минимум 8 символов')
    .regex(/[A-Z]/, 'Пароль должен содержать заглавную букву')
    .regex(/[0-9]/, 'Пароль должен содержать цифру'),
});

export const useLoginForm = () => {
  const form = useForm({
    resolver: zodResolver(loginSchema),
    mode: 'onChange', // Валидация при изменении
  });

  return form;
};
```

#### 2. Debounced поиск
```tsx
// src/hooks/useDebounce.ts
import { useState, useEffect } from 'react';

export const useDebounce = <T,>(value: T, delay: number = 500): T => {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
};

// Использование в поиске
const SearchVideos = () => {
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 300);

  useEffect(() => {
    if (debouncedSearch) {
      // Выполнить поиск
    }
  }, [debouncedSearch]);
};
```

## 🎨 Фаза 3: UX улучшения (1 неделя)

### Неделя 2: Продвинутые функции

#### 1. Drag & Drop для загрузки
```tsx
// src/components/DragDropUploader.tsx
import { useDropzone } from 'react-dropzone';

export const DragDropUploader = ({ onUpload }) => {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.ms-powerpoint': ['.ppt'],
      'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
    },
    maxFiles: 1,
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        onUpload(acceptedFiles[0]);
      }
    },
  });

  return (
    <div
      {...getRootProps()}
      className={`
        border-2 border-dashed rounded-lg p-8
        transition-colors cursor-pointer
        ${isDragActive 
          ? 'border-primary bg-primary/5' 
          : 'border-muted-foreground/25 hover:border-primary/50'
        }
      `}
    >
      <input {...getInputProps()} />
      <div className="flex flex-col items-center justify-center space-y-4">
        <Upload className={`h-12 w-12 ${isDragActive ? 'text-primary' : 'text-muted-foreground'}`} />
        <div className="text-center">
          <p className="text-lg font-medium">
            {isDragActive ? 'Отпустите файл здесь' : 'Перетащите файл сюда'}
          </p>
          <p className="text-sm text-muted-foreground mt-1">
            или нажмите для выбора файла
          </p>
        </div>
      </div>
    </div>
  );
};
```

#### 2. Keyboard shortcuts
```tsx
// src/hooks/useKeyboardShortcuts.ts
import { useEffect } from 'react';

const shortcuts = {
  'space': 'playPause',
  'arrowleft': 'prevSlide',
  'arrowright': 'nextSlide',
  'f': 'fullscreen',
  'm': 'mute',
  '?': 'showHelp',
};

export const useKeyboardShortcuts = (handlers) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Не обрабатывать, если фокус на input
      if (e.target instanceof HTMLInputElement || 
          e.target instanceof HTMLTextAreaElement) {
        return;
      }

      const key = e.key.toLowerCase();
      const action = shortcuts[key];
      
      if (action && handlers[action]) {
        e.preventDefault();
        handlers[action]();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handlers]);
};
```

#### 3. Onboarding для новых пользователей
```tsx
// src/components/Onboarding.tsx
import { useState } from 'react';
import { Dialog, DialogContent } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

const steps = [
  {
    title: 'Добро пожаловать в ИИ-Лектор!',
    description: 'Превращайте презентации в интерактивные лекции',
    image: '/onboarding/step1.svg',
  },
  {
    title: 'Загрузите презентацию',
    description: 'Поддерживаются форматы PPTX и PDF',
    image: '/onboarding/step2.svg',
  },
  {
    title: 'ИИ создаст лекцию',
    description: 'С озвучкой и визуальными эффектами',
    image: '/onboarding/step3.svg',
  },
];

export const Onboarding = ({ isOpen, onComplete }) => {
  const [currentStep, setCurrentStep] = useState(0);

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      onComplete();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={() => onComplete()}>
      <DialogContent className="sm:max-w-md">
        <div className="text-center">
          <img 
            src={steps[currentStep].image} 
            alt={steps[currentStep].title}
            className="w-48 h-48 mx-auto mb-4"
          />
          <h3 className="text-xl font-semibold mb-2">
            {steps[currentStep].title}
          </h3>
          <p className="text-muted-foreground mb-6">
            {steps[currentStep].description}
          </p>
          
          <div className="flex items-center justify-between">
            <div className="flex space-x-1">
              {steps.map((_, i) => (
                <div
                  key={i}
                  className={`h-2 w-2 rounded-full ${
                    i === currentStep ? 'bg-primary' : 'bg-muted'
                  }`}
                />
              ))}
            </div>
            
            <div className="flex space-x-2">
              {currentStep > 0 && (
                <Button
                  variant="outline"
                  onClick={() => setCurrentStep(currentStep - 1)}
                >
                  Назад
                </Button>
              )}
              <Button onClick={handleNext}>
                {currentStep === steps.length - 1 ? 'Начать' : 'Далее'}
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
```

## 📊 Метрики и мониторинг

### Настройка Web Vitals
```tsx
// src/utils/webVitals.ts
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

export const reportWebVitals = (onPerfEntry?: (metric: any) => void) => {
  if (onPerfEntry && onPerfEntry instanceof Function) {
    getCLS(onPerfEntry);
    getFID(onPerfEntry);
    getFCP(onPerfEntry);
    getLCP(onPerfEntry);
    getTTFB(onPerfEntry);
  }
};

// main.tsx
reportWebVitals((metric) => {
  // Отправка в Google Analytics или другую систему
  console.log(metric);
  // gtag('event', metric.name, {
  //   value: Math.round(metric.value),
  //   metric_id: metric.id,
  //   metric_value: metric.value,
  //   metric_delta: metric.delta,
  // });
});
```

## ✅ Чек-лист для проверки

### Доступность
- [ ] Все изображения имеют alt тексты
- [ ] Все интерактивные элементы доступны с клавиатуры
- [ ] ARIA атрибуты добавлены где нужно
- [ ] Skip links работают
- [ ] Focus indicators видны
- [ ] Lighthouse Accessibility Score > 90

### Производительность
- [ ] LCP < 2.5s
- [ ] FID < 100ms  
- [ ] CLS < 0.1
- [ ] Bundle size < 200KB (gzipped)
- [ ] Code splitting работает
- [ ] Изображения оптимизированы

### Мобильная версия
- [ ] Все страницы адаптивны
- [ ] Touch targets минимум 44x44px
- [ ] Текст читаем без зума
- [ ] Горизонтальный скролл отсутствует
- [ ] Мобильная навигация работает

### UX
- [ ] Loading states везде где нужно
- [ ] Error states информативны
- [ ] Empty states помогают пользователю
- [ ] Формы валидируются на лету
- [ ] Обратная связь консистентна

## 🎯 Ожидаемые результаты

После внедрения всех улучшений:
- **Bounce rate**: -15%
- **Time to action**: -30%
- **User satisfaction**: +25%
- **Accessibility score**: 95+
- **Performance score**: 90+

Начните с Фазы 1 (критические исправления) и двигайтесь последовательно!
