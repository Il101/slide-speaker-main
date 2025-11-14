# 🎨 Visual Effects V2 - Frontend Design (Adaptive)

**Дата:** 2 ноября 2025  
**Статус:** 🎯 Design Ready  
**Фокус:** Работает везде - от слабых серверов до мощных GPU

---

## 🎯 Принципиальное решение: Adaptive Rendering

### Проблема:
- ❌ WebGL требует GPU
- ❌ Серверы часто без GPU
- ❌ Не все браузеры поддерживают WebGL
- ❌ Headless режим (скриншоты/видео) без GPU

### Решение: 3-уровневая система

```
Level 3: WebGL Renderer (GPU)
  ↓ fallback если недоступен
Level 2: Canvas2D Renderer (CPU, оптимизированный)
  ↓ fallback если проблемы
Level 1: CSS/DOM Renderer (базовый, везде работает)
```

---

## 🏗️ Архитектура Frontend

```
src/components/VisualEffects/
├── core/
│   ├── EffectsTimeline.ts          # Event-driven sync (универсальный)
│   ├── CapabilityDetector.ts       # Определение возможностей
│   └── EffectsCoordinator.ts       # Выбор рендерера
│
├── renderers/
│   ├── BaseRenderer.ts             # Базовый интерфейс
│   ├── WebGLRenderer.ts            # Level 3: GPU (если есть)
│   ├── Canvas2DRenderer.ts         # Level 2: Canvas (оптимизированный)
│   └── CSSRenderer.ts              # Level 1: CSS/DOM (fallback)
│
├── effects/
│   ├── spotlight/
│   │   ├── SpotlightWebGL.ts      # GPU версия
│   │   ├── SpotlightCanvas.ts     # Canvas версия
│   │   └── SpotlightCSS.ts        # CSS версия
│   │
│   ├── particles/
│   │   ├── ParticlesWebGL.ts      # GPU: 1000+ частиц
│   │   ├── ParticlesCanvas.ts     # Canvas: 100-200 частиц
│   │   └── ParticlesCSS.ts        # CSS: эмуляция (10-20 частиц)
│   │
│   └── highlight/
│       └── HighlightCSS.ts         # Простой, везде работает
│
└── utils/
    ├── performance.ts               # Мониторинг FPS
    └── shaders.ts                   # WebGL шейдеры (опционально)
```

---

## 🔍 Capability Detection

### Автоматическое определение:

```typescript
class CapabilityDetector {
  private capabilities: RenderCapabilities;
  
  detect(): RenderCapabilities {
    return {
      // WebGL доступен?
      webgl: this.detectWebGL(),
      webgl2: this.detectWebGL2(),
      
      // Canvas2D оптимизации
      offscreenCanvas: 'OffscreenCanvas' in window,
      
      // Performance
      hardwareConcurrency: navigator.hardwareConcurrency || 1,
      deviceMemory: (navigator as any).deviceMemory || 2,
      
      // Display
      pixelRatio: window.devicePixelRatio || 1,
      
      // Режим работы
      isHeadless: this.detectHeadless(),
      
      // Рекомендуемый рендерер
      recommendedRenderer: this.getRecommendedRenderer()
    };
  }
  
  private detectWebGL(): boolean {
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || 
                 canvas.getContext('experimental-webgl');
      return !!gl;
    } catch {
      return false;
    }
  }
  
  private getRecommendedRenderer(): RendererType {
    // Логика выбора оптимального рендерера
    if (this.detectWebGL() && !this.detectHeadless()) {
      return 'webgl';  // GPU доступен
    } else if (!this.detectHeadless()) {
      return 'canvas2d';  // CPU Canvas
    } else {
      return 'css';  // Fallback для headless/серверов
    }
  }
}
```

---

## 🎨 Renderer Implementation

### 1. WebGL Renderer (Level 3 - Best Quality)

**Когда:** GPU доступен, современный браузер, desktop  
**Эффекты:** Все (particles, spotlight, morph, glitch)  
**FPS:** 60 стабильно  

```typescript
class WebGLRenderer extends BaseRenderer {
  private gl: WebGLRenderingContext;
  private shaderProgram: WebGLProgram;
  
  async render(effect: Effect, currentTime: number) {
    // GPU-accelerated rendering
    // - Vertex/Fragment shaders
    // - Texture sampling
    // - Blend modes
  }
}
```

**Преимущества:**
- ✅ 1000+ частиц без лагов
- ✅ Сложные шейдеры (glitch, ripple)
- ✅ Реальные тени и освещение

**Недостатки:**
- ❌ Требует GPU
- ❌ Не работает headless без хаков

---

### 2. Canvas2D Renderer (Level 2 - Good Quality)

**Когда:** GPU недоступен, но Canvas2D работает  
**Эффекты:** Большинство (упрощённые)  
**FPS:** 30-60  

```typescript
class Canvas2DRenderer extends BaseRenderer {
  private ctx: CanvasRenderingContext2D;
  private offscreenCanvas?: OffscreenCanvas;
  
  async render(effect: Effect, currentTime: number) {
    // Оптимизированный Canvas2D
    // - OffscreenCanvas для pre-rendering
    // - Batch drawing
    // - Cached gradients/patterns
    // - Layer compositing
    
    switch (effect.type) {
      case 'spotlight':
        this.renderSpotlightCanvas(effect, currentTime);
        break;
      case 'particles':
        this.renderParticlesCanvas(effect, currentTime);
        break;
      case 'highlight':
        this.renderHighlightCanvas(effect, currentTime);
        break;
    }
  }
  
  private renderSpotlightCanvas(effect: Effect, time: number) {
    const progress = this.calculateProgress(effect, time);
    
    // Радиальный градиент для spotlight
    const gradient = this.ctx.createRadialGradient(
      centerX, centerY, 0,
      centerX, centerY, radius
    );
    
    gradient.addColorStop(0, 'rgba(255, 255, 255, 0.9)');
    gradient.addColorStop(0.7, 'rgba(255, 255, 255, 0.3)');
    gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
    
    // Применяем с easing
    this.ctx.globalAlpha = this.easing(progress);
    this.ctx.fillStyle = gradient;
    this.ctx.fillRect(bbox[0], bbox[1], bbox[2], bbox[3]);
  }
  
  private renderParticlesCanvas(effect: Effect, time: number) {
    const params = effect.params;
    const particleCount = Math.min(params.particle_count, 200); // Limit на CPU
    
    // Генерируем частицы (кэшируем при первом вызове)
    if (!this.particlesCache.has(effect.id)) {
      this.particlesCache.set(effect.id, 
        this.generateParticles(particleCount, bbox)
      );
    }
    
    const particles = this.particlesCache.get(effect.id)!;
    const progress = this.calculateProgress(effect, time);
    
    // Рисуем каждую частицу (оптимизировано)
    this.ctx.save();
    particles.forEach(p => {
      const age = progress * p.lifetime;
      const opacity = 1 - age;
      
      this.ctx.globalAlpha = opacity;
      this.ctx.fillStyle = params.color;
      this.ctx.fillRect(
        p.x + p.vx * age,
        p.y + p.vy * age,
        p.size,
        p.size
      );
    });
    this.ctx.restore();
  }
}
```

**Преимущества:**
- ✅ Работает без GPU
- ✅ Хорошее качество
- ✅ 100-200 частиц нормально
- ✅ Поддержка везде

**Недостатки:**
- ⚠️ Меньше частиц чем WebGL
- ⚠️ Простые эффекты

---

### 3. CSS Renderer (Level 1 - Basic Quality)

**Когда:** Headless, старые браузеры, fallback  
**Эффекты:** Базовые (highlight, fade, border)  
**FPS:** 60 (CSS animations)  

```typescript
class CSSRenderer extends BaseRenderer {
  private container: HTMLElement;
  
  async render(effect: Effect, currentTime: number) {
    // DOM-based с CSS animations
    // - CSS transitions/animations
    // - Transform/opacity
    // - Box-shadow для эффектов
    
    const element = this.createEffectElement(effect);
    
    switch (effect.type) {
      case 'spotlight':
        this.applySpotlightCSS(element, effect);
        break;
      case 'highlight':
        this.applyHighlightCSS(element, effect);
        break;
      case 'particles':
        this.applyParticlesCSS(element, effect); // Эмуляция
        break;
    }
    
    this.container.appendChild(element);
  }
  
  private applySpotlightCSS(element: HTMLElement, effect: Effect) {
    const bbox = effect.target.bbox!;
    
    element.style.cssText = `
      position: absolute;
      left: ${bbox[0]}px;
      top: ${bbox[1]}px;
      width: ${bbox[2]}px;
      height: ${bbox[3]}px;
      background: radial-gradient(
        circle,
        rgba(255, 255, 255, 0.9) 0%,
        rgba(255, 255, 255, 0.3) 70%,
        rgba(0, 0, 0, 0) 100%
      );
      box-shadow: 0 0 50px rgba(255, 255, 255, 0.5);
      animation: spotlightFade ${effect.duration}s ${effect.params.ease_in};
      pointer-events: none;
      z-index: 1000;
    `;
  }
  
  private applyParticlesCSS(element: HTMLElement, effect: Effect) {
    // Эмуляция particles через CSS (10-20 элементов)
    const count = Math.min(effect.params.particle_count, 20);
    
    for (let i = 0; i < count; i++) {
      const particle = document.createElement('div');
      const angle = (Math.PI * 2 * i) / count;
      
      particle.style.cssText = `
        position: absolute;
        width: 4px;
        height: 4px;
        background: ${effect.params.color};
        border-radius: 50%;
        animation: particleFloat ${effect.duration}s ease-out;
        animation-delay: ${i * 0.05}s;
        --angle: ${angle}rad;
        --distance: 100px;
      `;
      
      element.appendChild(particle);
    }
  }
}
```

**Преимущества:**
- ✅ Работает ВЕЗДЕ
- ✅ Headless совместимо
- ✅ Нативные CSS animations (smooth)
- ✅ Низкая нагрузка

**Недостатки:**
- ⚠️ Базовые эффекты только
- ⚠️ Мало частиц (10-20)
- ⚠️ Нет сложных шейдеров

---

## 🎬 Effects Timeline (Универсальный)

**Работает с любым рендерером!**

```typescript
class EffectsTimeline {
  private events: TimelineEvent[] = [];
  private activeEffects: Map<string, Effect> = new Map();
  private renderer: BaseRenderer;
  
  constructor(renderer: BaseRenderer) {
    this.renderer = renderer;
  }
  
  // Загрузка timeline из manifest V2
  load(timeline: TimelineData) {
    this.events = timeline.events.sort((a, b) => a.time - b.time);
  }
  
  // Обновление на каждом кадре
  update(currentTime: number) {
    const lookAhead = 0.1; // 100ms буфер
    
    // Обработка событий с опережением
    while (this.events[0]?.time <= currentTime + lookAhead) {
      const event = this.events.shift()!;
      
      if (event.type === 'START') {
        this.startEffect(event.effect);
      } else if (event.type === 'END') {
        this.endEffect(event.effect.id);
      }
    }
    
    // Рендеринг активных эффектов
    this.activeEffects.forEach((effect, id) => {
      this.renderer.render(effect, currentTime);
    });
  }
  
  private startEffect(effect: Effect) {
    console.log(`▶️ Starting effect: ${effect.id} (${effect.type})`);
    this.activeEffects.set(effect.id, effect);
  }
  
  private endEffect(effectId: string) {
    console.log(`⏹️ Ending effect: ${effectId}`);
    this.activeEffects.delete(effectId);
    this.renderer.cleanup(effectId);
  }
}
```

---

## 🎯 Adaptive Strategy

### Автоматический выбор:

```typescript
class EffectsCoordinator {
  private detector: CapabilityDetector;
  private renderer: BaseRenderer;
  private timeline: EffectsTimeline;
  
  async initialize() {
    // 1. Определяем возможности
    const capabilities = this.detector.detect();
    
    console.log('🔍 Detected capabilities:', capabilities);
    
    // 2. Выбираем рендерер
    this.renderer = this.selectRenderer(capabilities);
    
    console.log(`🎨 Using renderer: ${this.renderer.name}`);
    
    // 3. Создаём timeline
    this.timeline = new EffectsTimeline(this.renderer);
  }
  
  private selectRenderer(cap: RenderCapabilities): BaseRenderer {
    // Приоритет: WebGL > Canvas2D > CSS
    
    if (cap.webgl && !cap.isHeadless) {
      return new WebGLRenderer(cap);
    }
    
    if (!cap.isHeadless) {
      return new Canvas2DRenderer(cap);
    }
    
    // Fallback для серверов/headless
    return new CSSRenderer(cap);
  }
}
```

---

## 📊 Performance Monitoring

```typescript
class PerformanceMonitor {
  private fps = 60;
  private frameCount = 0;
  private lastCheck = performance.now();
  
  update() {
    this.frameCount++;
    const now = performance.now();
    
    if (now - this.lastCheck >= 1000) {
      this.fps = this.frameCount;
      this.frameCount = 0;
      this.lastCheck = now;
      
      // Если FPS падает, понижаем качество
      if (this.fps < 30) {
        this.downgradQuality();
      }
    }
  }
  
  private downgradQuality() {
    // Автоматическое снижение качества при лагах
    console.warn('⚠️ Low FPS detected, reducing quality');
    
    // Уменьшаем количество частиц
    // Упрощаем шейдеры
    // Переключаемся на более простой рендерер
  }
}
```

---

## 🚀 Для вашего случая (сервер без GPU)

### Рекомендация: Canvas2D + CSS

```typescript
// В production на сервере:
const config = {
  preferredRenderer: 'canvas2d',  // Или 'css' если совсем слабо
  maxParticles: 100,               // Ограничение для производительности
  disableWebGL: true,              // Явно отключаем WebGL
  quality: 'medium'                // Средее качество
};

const coordinator = new EffectsCoordinator(config);
await coordinator.initialize();
```

### Результат:
- ✅ Работает на сервере без GPU
- ✅ Хорошее качество (Canvas2D оптимизированный)
- ✅ 30-60 FPS стабильно
- ✅ Graceful degradation при нагрузке
- ✅ Fallback на CSS если проблемы

---

## 📝 Реализация Priority

### Фаза 1: Core (обязательно)
- [x] CapabilityDetector
- [x] EffectsTimeline (event-driven)
- [x] BaseRenderer interface
- [x] EffectsCoordinator

### Фаза 2: Canvas2D (рекомендую для вас!)
- [ ] Canvas2DRenderer
- [ ] SpotlightCanvas
- [ ] HighlightCanvas
- [ ] ParticlesCanvas (100-200 частиц)
- [ ] FadeCanvas

### Фаза 3: CSS Fallback
- [ ] CSSRenderer
- [ ] SpotlightCSS
- [ ] HighlightCSS
- [ ] ParticlesCSS (эмуляция)

### Фаза 4: WebGL (опционально)
- [ ] WebGLRenderer
- [ ] Advanced effects (только если нужно)

---

## ✅ Итого для вашего сервера

**Без GPU? Не проблема!**

1. **Canvas2D Renderer** - основной для вас
   - Хорошее качество
   - 100-200 частиц
   - 30-60 FPS
   - CPU-based, работает везде

2. **CSS Renderer** - fallback
   - Базовые эффекты
   - Всегда работает
   - Низкая нагрузка

3. **WebGL** - можно не делать
   - Только для мощных клиентов
   - Опционально в будущем

**Фокус:** Canvas2D + CSS = работает везде, хорошее качество! 🎯

---

Начать с Canvas2D реализации? Это даст вам 80% качества WebGL при 0% требований к GPU! 🚀
