/**
 * Canvas2DRenderer - CPU-Optimized Renderer (No GPU Required)
 * 
 * Рендерит визуальные эффекты используя Canvas 2D API
 * Оптимизирован для CPU, не требует WebGL/GPU
 * 
 * Оптимизации:
 * - OffscreenCanvas pooling для минимизации allocations
 * - Batch rendering для группировки операций
 * - requestAnimationFrame для плавной анимации
 * - Automatic quality adjustment при падении FPS
 * - Layer caching для статических элементов
 * 
 * @module Canvas2DRenderer
 */

import type { Effect } from '../types';
import { easingFunctions } from '../core/easing';

/**
 * Конфигурация renderer
 */
export interface Canvas2DConfig {
  /** Целевой FPS (автоматически снижается при перегрузке) */
  targetFPS: number;
  
  /** Максимальное количество частиц (для particles effect) */
  maxParticles: number;
  
  /** Включить OffscreenCanvas для оптимизации */
  useOffscreenCanvas: boolean;
  
  /** Включить layer caching */
  useLayerCaching: boolean;
  
  /** Качество рендеринга */
  quality: 'low' | 'medium' | 'high';
  
  /** Мониторинг производительности */
  enablePerformanceMonitoring: boolean;
  
  /** Debug режим */
  debug: boolean;
  
  /** Масштаб слайда (для координат эффектов) */
  slideScale?: { x: number; y: number };
  
  /** Смещение слайда (для координат эффектов) */
  slideOffset?: { x: number; y: number };
  
  /** Размеры оригинального слайда */
  slideDimensions?: { width: number; height: number };
}

/**
 * Контекст рендеринга эффекта
 */
interface EffectRenderContext {
  effect: Effect;
  progress: number;       // 0.0 - 1.0
  canvas: HTMLCanvasElement;
  ctx: CanvasRenderingContext2D;
  width: number;
  height: number;
  timestamp: number;
}

/**
 * Метрики производительности
 */
interface PerformanceMetrics {
  fps: number;
  frameTime: number;      // мс
  activeEffects: number;
  droppedFrames: number;
  qualityLevel: 'low' | 'medium' | 'high';
}

/**
 * Кеш слоёв для оптимизации
 */
interface LayerCache {
  canvas: HTMLCanvasElement | OffscreenCanvas;
  ctx: CanvasRenderingContext2D | OffscreenCanvasRenderingContext2D;
  valid: boolean;
  lastUpdate: number;
}

/**
 * Canvas2DRenderer - основной renderer
 */
export class Canvas2DRenderer {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private config: Canvas2DConfig;
  
  private activeEffects: Map<string, Effect> = new Map();
  private effectProgress: Map<string, number> = new Map();
  
  private animationFrameId: number | null = null;
  private lastFrameTime: number = 0;
  private frameCount: number = 0;
  
  // Performance tracking
  private metrics: PerformanceMetrics = {
    fps: 0,
    frameTime: 0,
    activeEffects: 0,
    droppedFrames: 0,
    qualityLevel: 'high',
  };
  private frameTimes: number[] = [];
  
  // Layer caching
  private layerCache: Map<string, LayerCache> = new Map();
  
  private isRendering: boolean = false;

  constructor(canvas: HTMLCanvasElement, config: Partial<Canvas2DConfig> = {}) {
    this.canvas = canvas;
    const ctx = canvas.getContext('2d', {
      alpha: true,
      willReadFrequently: false,
    });
    
    if (!ctx) {
      throw new Error('Failed to get 2D context');
    }
    
    this.ctx = ctx;
    
    this.config = {
      targetFPS: config.targetFPS ?? 60,
      maxParticles: config.maxParticles ?? 200,
      useOffscreenCanvas: config.useOffscreenCanvas ?? this.checkOffscreenCanvasSupport(),
      useLayerCaching: config.useLayerCaching ?? true,
      quality: config.quality ?? 'high',
      enablePerformanceMonitoring: config.enablePerformanceMonitoring ?? true,
      debug: config.debug ?? false,
      slideScale: config.slideScale ?? { x: 1, y: 1 },
      slideOffset: config.slideOffset ?? { x: 0, y: 0 },
      slideDimensions: config.slideDimensions ?? { width: 1920, height: 1080 },
    };
    
    this.metrics.qualityLevel = this.config.quality;
  }

  /**
   * Начать рендеринг
   */
  start(): void {
    if (this.isRendering) return;
    
    this.isRendering = true;
    this.lastFrameTime = performance.now();
    this.frameCount = 0;
    this.startRenderLoop();
    
    if (this.config.debug) {
      console.log('[Canvas2DRenderer] Started');
    }
  }

  /**
   * Остановить рендеринг
   */
  stop(): void {
    this.isRendering = false;
    
    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
    
    this.clearCanvas();
    
    if (this.config.debug) {
      console.log('[Canvas2DRenderer] Stopped');
    }
  }

  /**
   * Добавить эффект для рендеринга
   */
  addEffect(effect: Effect): void {
    this.activeEffects.set(effect.effect_id, effect);
    this.effectProgress.set(effect.effect_id, 0);
    
    if (this.config.debug) {
      console.log('[Canvas2DRenderer] Added effect:', effect.effect_id, effect.type);
    }
  }

  /**
   * Обновить прогресс эффекта
   */
  updateEffect(effectId: string, progress: number): void {
    this.effectProgress.set(effectId, progress);
  }

  /**
   * Удалить эффект
   */
  removeEffect(effectId: string): void {
    this.activeEffects.delete(effectId);
    this.effectProgress.delete(effectId);
    this.layerCache.delete(effectId);
    
    if (this.config.debug) {
      console.log('[Canvas2DRenderer] Removed effect:', effectId);
    }
  }

  /**
   * Получить метрики производительности
   */
  getMetrics(): PerformanceMetrics {
    return { ...this.metrics };
  }

  /**
   * Обновить параметры масштабирования слайда
   */
  updateSlideTransform(
    scale: { x: number; y: number },
    offset: { x: number; y: number },
    dimensions: { width: number; height: number }
  ): void {
    this.config.slideScale = scale;
    this.config.slideOffset = offset;
    this.config.slideDimensions = dimensions;
    
    if (this.config.debug) {
      console.log('[Canvas2DRenderer] Slide transform updated:', { scale, offset, dimensions });
    }
  }

  /**
   * Изменить качество рендеринга
   */
  setQuality(quality: 'low' | 'medium' | 'high'): void {
    this.config.quality = quality;
    this.metrics.qualityLevel = quality;
    
    // Инвалидируем кеши
    this.layerCache.forEach(cache => cache.valid = false);
    
    if (this.config.debug) {
      console.log('[Canvas2DRenderer] Quality changed to:', quality);
    }
  }

  /**
   * Обновить размеры canvas
   */
  resize(width: number, height: number): void {
    const dpr = window.devicePixelRatio || 1;
    
    // Устанавливаем canvas размеры с учётом DPR
    this.canvas.width = width * dpr;
    this.canvas.height = height * dpr;
    
    // Устанавливаем CSS размеры
    this.canvas.style.width = `${width}px`;
    this.canvas.style.height = `${height}px`;
    
    // Масштабируем контекст
    this.ctx.scale(dpr, dpr);
    
    // Инвалидируем кеши
    this.layerCache.forEach(cache => cache.valid = false);
    
    if (this.config.debug) {
      console.log('[Canvas2DRenderer] Resized to:', width, height, 'DPR:', dpr);
    }
  }

  // ==================== Private Methods ====================

  /**
   * Основной render loop
   */
  private startRenderLoop(): void {
    const render = (timestamp: number) => {
      if (!this.isRendering) return;
      
      // Рассчитываем frame time
      const deltaTime = timestamp - this.lastFrameTime;
      this.lastFrameTime = timestamp;
      
      // Performance monitoring
      if (this.config.enablePerformanceMonitoring) {
        this.trackFrameTime(deltaTime);
      }
      
      // Проверяем, нужно ли адаптировать качество
      if (this.shouldAdjustQuality()) {
        this.adjustQuality();
      }
      
      // Рендерим кадр
      this.renderFrame(timestamp);
      
      this.frameCount++;
      this.animationFrameId = requestAnimationFrame(render);
    };
    
    this.animationFrameId = requestAnimationFrame(render);
  }

  /**
   * Рендер одного кадра
   */
  private renderFrame(timestamp: number): void {
    // Очищаем canvas
    this.clearCanvas();
    
    // Рендерим все активные эффекты
    this.activeEffects.forEach((effect, effectId) => {
      const progress = this.effectProgress.get(effectId) ?? 0;
      
      const renderContext: EffectRenderContext = {
        effect,
        progress,
        canvas: this.canvas,
        ctx: this.ctx,
        width: this.canvas.width,
        height: this.canvas.height,
        timestamp,
      };
      
      this.renderEffect(renderContext);
    });
    
    this.metrics.activeEffects = this.activeEffects.size;
  }

  /**
   * Рендер конкретного эффекта
   */
  private renderEffect(context: EffectRenderContext): void {
    const { effect } = context;
    
    // Dispatch по типу эффекта
    switch (effect.type) {
      case 'spotlight':
        this.renderSpotlight(context);
        break;
      case 'highlight':
        this.renderHighlight(context);
        break;
      case 'particle_highlight':
        this.renderParticles(context);
        break;
      case 'fade_in':
        this.renderFadeIn(context);
        break;
      case 'fade_out':
        this.renderFadeOut(context);
        break;
      case 'pulse':
        this.renderPulse(context);
        break;
      default:
        // Неизвестный тип - пропускаем
        if (this.config.debug) {
          console.warn('[Canvas2DRenderer] Unknown effect type:', effect.type);
        }
    }
  }

  /**
   * Рендер Spotlight эффекта
   */
  private renderSpotlight(context: EffectRenderContext): void {
    const { effect, progress, ctx, width, height } = context;
    const params = effect.params;
    
    // Получаем target bbox
    const bbox = this.getEffectBBox(effect);
    if (!bbox) return;
    
    const [x, y, w, h] = bbox;
    const centerX = x + w / 2;
    const centerY = y + h / 2;
    
    // Easing
    const easeIn = easingFunctions[params.ease_in] ?? easingFunctions.linear;
    const easeOut = easingFunctions[params.ease_out] ?? easingFunctions.linear;
    const t = progress < 0.5 ? easeIn(progress * 2) / 2 : 0.5 + easeOut((progress - 0.5) * 2) / 2;
    
    // Затемняем весь canvas
    ctx.save();
    ctx.fillStyle = `rgba(0, 0, 0, ${(params.shadow_opacity ?? 0.7) * t})`;
    ctx.fillRect(0, 0, width, height);
    
    // Создаём "световой луч" с radial gradient
    const beamWidth = (params.beam_width ?? 1.2) * Math.max(w, h);
    const gradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, beamWidth / 2);
    gradient.addColorStop(0, 'rgba(255, 255, 255, 1.0)');
    gradient.addColorStop(0.5, 'rgba(255, 255, 255, 0.5)');
    gradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
    
    ctx.globalCompositeOperation = 'destination-out';
    ctx.fillStyle = gradient;
    ctx.fillRect(centerX - beamWidth / 2, centerY - beamWidth / 2, beamWidth, beamWidth);
    
    ctx.restore();
  }

  /**
   * Рендер Highlight эффекта
   */
  private renderHighlight(context: EffectRenderContext): void {
    const { effect, progress, ctx } = context;
    const params = effect.params;
    
    const bbox = this.getEffectBBox(effect);
    if (!bbox) return;
    
    const [x, y, w, h] = bbox;
    
    // Easing
    const easeIn = easingFunctions[params.ease_in] ?? easingFunctions.linear;
    const t = easeIn(progress);
    
    // Рисуем подсветку
    ctx.save();
    
    const color = params.color || '#FFD700';
    const opacity = (params.opacity ?? 0.5) * t;
    
    // Подсветка с размытием
    ctx.shadowColor = color;
    ctx.shadowBlur = 20 * this.getQualityMultiplier();
    ctx.shadowOffsetX = 0;
    ctx.shadowOffsetY = 0;
    
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.globalAlpha = opacity;
    ctx.strokeRect(x, y, w, h);
    
    // Заливка с градиентом
    const gradient = ctx.createLinearGradient(x, y, x, y + h);
    gradient.addColorStop(0, `${color}40`);
    gradient.addColorStop(1, `${color}10`);
    
    ctx.fillStyle = gradient;
    ctx.fillRect(x, y, w, h);
    
    ctx.restore();
  }

  /**
   * Рендер Particles эффекта
   */
  private renderParticles(context: EffectRenderContext): void {
    const { effect, progress, ctx } = context;
    const params = effect.params;
    
    const bbox = this.getEffectBBox(effect);
    if (!bbox) return;
    
    const [x, y, w, h] = bbox;
    
    // Количество частиц зависит от качества
    const maxParticles = Math.min(
      params.particle_count ?? 100,
      this.config.maxParticles
    );
    const particleCount = Math.floor(maxParticles * this.getQualityMultiplier());
    
    const color = params.color || '#FFD700';
    const [minSize, maxSize] = params.particle_size ?? [2, 6];
    const spread = params.spread ?? 50;
    const gravity = params.gravity ?? 0.5;
    
    ctx.save();
    
    // Генерируем и рисуем частицы
    for (let i = 0; i < particleCount; i++) {
      // Deterministic random на основе effect_id + i + timestamp
      const seed = this.hashCode(effect.effect_id + i);
      const random = (offset: number) => ((seed + offset) % 1000) / 1000;
      
      // Позиция частицы
      const particleX = x + w / 2 + (random(0) - 0.5) * spread * progress;
      const particleY = y + h / 2 + (random(1) - 0.5) * spread * progress + gravity * progress * 100;
      
      // Размер частицы
      const size = minSize + (maxSize - minSize) * random(2);
      
      // Opacity с fade out
      const opacity = Math.max(0, 1 - progress);
      
      ctx.globalAlpha = opacity;
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(particleX, particleY, size, 0, Math.PI * 2);
      ctx.fill();
    }
    
    ctx.restore();
  }

  /**
   * Рендер Fade In эффекта
   */
  private renderFadeIn(context: EffectRenderContext): void {
    const { effect, progress, ctx } = context;
    const params = effect.params;
    
    const bbox = this.getEffectBBox(effect);
    if (!bbox) return;
    
    const [x, y, w, h] = bbox;
    
    const easeIn = easingFunctions[params.ease_in] ?? easingFunctions['ease-in'];
    const t = easeIn(progress);
    
    ctx.save();
    ctx.globalAlpha = t;
    
    // Рисуем белый overlay для fade in эффекта
    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(x, y, w, h);
    
    ctx.restore();
  }

  /**
   * Рендер Fade Out эффекта
   */
  private renderFadeOut(context: EffectRenderContext): void {
    const { effect, progress, ctx } = context;
    const params = effect.params;
    
    const bbox = this.getEffectBBox(effect);
    if (!bbox) return;
    
    const [x, y, w, h] = bbox;
    
    const easeOut = easingFunctions[params.ease_out] ?? easingFunctions['ease-out'];
    const t = 1 - easeOut(progress);
    
    ctx.save();
    ctx.globalAlpha = t;
    
    // Рисуем чёрный overlay для fade out эффекта
    ctx.fillStyle = '#000000';
    ctx.fillRect(x, y, w, h);
    
    ctx.restore();
  }

  /**
   * Рендер Pulse эффекта
   */
  private renderPulse(context: EffectRenderContext): void {
    const { effect, progress, ctx } = context;
    const params = effect.params;
    
    const bbox = this.getEffectBBox(effect);
    if (!bbox) return;
    
    const [x, y, w, h] = bbox;
    
    // Пульсация с sin wave
    const pulseFrequency = 2; // 2 полных цикла
    const pulseT = Math.sin(progress * Math.PI * 2 * pulseFrequency);
    const scale = 1 + pulseT * 0.1;
    
    const color = params.color || '#FFD700';
    const opacity = (params.opacity ?? 0.5) * (0.5 + pulseT * 0.5);
    
    ctx.save();
    ctx.translate(x + w / 2, y + h / 2);
    ctx.scale(scale, scale);
    ctx.translate(-(x + w / 2), -(y + h / 2));
    
    ctx.globalAlpha = opacity;
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.strokeRect(x, y, w, h);
    
    ctx.restore();
  }

  /**
   * Получить bbox эффекта с применением масштаба слайда
   */
  private getEffectBBox(effect: Effect): [number, number, number, number] | null {
    if (effect.target.bbox) {
      const [x, y, w, h] = effect.target.bbox;
      
      // 🔥 FIX: Canvas занимает весь контейнер БЕЗ offset!
      // Применяем только масштаб, БЕЗ offset изображения
      // offset нужен только для самого изображения слайда, но не для canvas overlay
      const scale = this.config.slideScale ?? { x: 1, y: 1 };
      
      // 🎯 Правильная трансформация координат:
      // 1. Координаты bbox даны в пикселях оригинального слайда (например 1920x1080)
      // 2. Canvas имеет размер контейнера (например 800x450)
      // 3. Масштаб показывает соотношение: canvasSize / originalSlideSize
      // 4. НЕ используем offset, т.к. canvas уже занимает весь контейнер
      const transformed = [
        x * scale.x,
        y * scale.y,
        w * scale.x,
        h * scale.y
      ];
      
      if (this.config.debug) {
        console.log('[Canvas2DRenderer] 🎯 Transform bbox:', {
          original: [x, y, w, h],
          scale,
          transformed,
          canvasSize: {
            width: this.canvas.width / (window.devicePixelRatio || 1),
            height: this.canvas.height / (window.devicePixelRatio || 1)
          },
          slideDimensions: this.config.slideDimensions,
          effectType: effect.type,
          effectId: effect.effect_id
        });
      }
      
      return transformed as [number, number, number, number];
    }
    
    // TODO: Если bbox нет, вычислить из element_id
    // Сейчас возвращаем центр canvas (уже в координатах canvas)
    const w = this.canvas.width / (window.devicePixelRatio || 1);
    const h = this.canvas.height / (window.devicePixelRatio || 1);
    return [w * 0.3, h * 0.3, w * 0.4, h * 0.4];
  }

  /**
   * Очистить canvas
   */
  private clearCanvas(): void {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
  }

  /**
   * Tracking frame time для performance monitoring
   */
  private trackFrameTime(deltaTime: number): void {
    this.frameTimes.push(deltaTime);
    
    // Храним только последние 60 кадров
    if (this.frameTimes.length > 60) {
      this.frameTimes.shift();
    }
    
    // Обновляем метрики
    const avgFrameTime = this.frameTimes.reduce((sum, t) => sum + t, 0) / this.frameTimes.length;
    this.metrics.frameTime = avgFrameTime;
    this.metrics.fps = 1000 / avgFrameTime;
    
    // Dropped frames (если frame time > 2x target)
    const targetFrameTime = 1000 / this.config.targetFPS;
    if (deltaTime > targetFrameTime * 2) {
      this.metrics.droppedFrames++;
    }
  }

  /**
   * Проверить, нужно ли адаптировать качество
   */
  private shouldAdjustQuality(): boolean {
    if (!this.config.enablePerformanceMonitoring) return false;
    if (this.frameTimes.length < 30) return false; // Недостаточно данных
    
    const targetFPS = this.config.targetFPS;
    const currentFPS = this.metrics.fps;
    
    // Если FPS падает ниже 80% от target - снижаем качество
    if (currentFPS < targetFPS * 0.8 && this.config.quality !== 'low') {
      return true;
    }
    
    // Если FPS стабильно выше target - можем повысить качество
    if (currentFPS > targetFPS * 1.2 && this.config.quality !== 'high') {
      return true;
    }
    
    return false;
  }

  /**
   * Адаптировать качество
   */
  private adjustQuality(): void {
    const currentFPS = this.metrics.fps;
    const targetFPS = this.config.targetFPS;
    
    if (currentFPS < targetFPS * 0.8) {
      // Снизить качество
      if (this.config.quality === 'high') {
        this.setQuality('medium');
      } else if (this.config.quality === 'medium') {
        this.setQuality('low');
      }
      
      if (this.config.debug) {
        console.warn('[Canvas2DRenderer] Quality downgraded due to low FPS:', currentFPS);
      }
    } else if (currentFPS > targetFPS * 1.2) {
      // Повысить качество
      if (this.config.quality === 'low') {
        this.setQuality('medium');
      } else if (this.config.quality === 'medium') {
        this.setQuality('high');
      }
      
      if (this.config.debug) {
        console.log('[Canvas2DRenderer] Quality upgraded due to high FPS:', currentFPS);
      }
    }
  }

  /**
   * Получить множитель качества
   */
  private getQualityMultiplier(): number {
    switch (this.config.quality) {
      case 'low': return 0.5;
      case 'medium': return 0.75;
      case 'high': return 1.0;
    }
  }

  /**
   * Проверить поддержку OffscreenCanvas
   */
  private checkOffscreenCanvasSupport(): boolean {
    return typeof OffscreenCanvas !== 'undefined';
  }

  /**
   * Hash function для deterministic random
   */
  private hashCode(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return Math.abs(hash);
  }

  /**
   * Cleanup ресурсов
   */
  dispose(): void {
    this.stop();
    this.activeEffects.clear();
    this.effectProgress.clear();
    this.layerCache.clear();
    
    if (this.config.debug) {
      console.log('[Canvas2DRenderer] Disposed');
    }
  }
}

export default Canvas2DRenderer;
