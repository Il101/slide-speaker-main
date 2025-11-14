/**
 * EffectsTimeline - Event-Driven Synchronization System
 * 
 * Обеспечивает точную синхронизацию визуальных эффектов с аудио (±16ms)
 * Заменяет polling на event-driven подход с preloading
 * 
 * Архитектура:
 * - События START/END для каждого эффекта
 * - Preloading за 100ms до старта
 * - Automatic cleanup завершённых эффектов
 * - Интеграция с audio.currentTime
 * 
 * @module EffectsTimeline
 */

import type { Timeline, TimelineEvent, Effect, TimelineStats } from '../types';

/**
 * Состояние активного эффекта
 */
interface ActiveEffect {
  effect: Effect;
  startTime: number;
  endTime: number;
  isPreloaded: boolean;
  onStart?: () => void;
  onEnd?: () => void;
}

/**
 * Конфигурация Timeline
 */
interface TimelineConfig {
  /** Время preloading эффектов перед стартом (мс) */
  preloadBuffer: number;
  
  /** Интервал проверки событий (мс) */
  tickInterval: number;
  
  /** Допустимая погрешность синхронизации (мс) */
  syncTolerance: number;
  
  /** Логировать события? */
  debug: boolean;
}

/**
 * Callback для событий lifecycle
 */
interface EffectCallbacks {
  onPreload?: (effect: Effect) => void;
  onStart?: (effect: Effect) => void;
  onUpdate?: (effect: Effect, progress: number) => void;
  onEnd?: (effect: Effect) => void;
}

/**
 * Метрики производительности
 */
interface PerformanceMetrics {
  totalEffects: number;
  activeEffects: number;
  preloadedEffects: number;
  averageSyncError: number; // мс
  maxSyncError: number; // мс
  missedStarts: number;
  frameDrops: number;
}

/**
 * EffectsTimeline - главный контроллер синхронизации
 */
export class EffectsTimeline {
  private timeline: Timeline | null = null;
  private activeEffects: Map<string, ActiveEffect> = new Map();
  private preloadedEffects: Set<string> = new Set();
  
  private config: TimelineConfig;
  private callbacks: EffectCallbacks;
  
  private tickTimer: number | null = null;
  private animationFrameId: number | null = null;
  private lastTickTime: number = 0;
  
  private isPlaying: boolean = false;
  private currentTime: number = 0; // секунды
  
  // Performance tracking
  private metrics: PerformanceMetrics = {
    totalEffects: 0,
    activeEffects: 0,
    preloadedEffects: 0,
    averageSyncError: 0,
    maxSyncError: 0,
    missedStarts: 0,
    frameDrops: 0,
  };
  private syncErrors: number[] = [];

  constructor(
    config: Partial<TimelineConfig> = {},
    callbacks: EffectCallbacks = {}
  ) {
    this.config = {
      preloadBuffer: config.preloadBuffer ?? 100, // 100ms заранее
      tickInterval: config.tickInterval ?? 16, // ~60 FPS
      syncTolerance: config.syncTolerance ?? 50, // 50ms допуск
      debug: config.debug ?? false,
    };
    this.callbacks = callbacks;
  }

  /**
   * Загрузить timeline
   */
  loadTimeline(timeline: Timeline): void {
    this.stop();
    this.timeline = timeline;
    this.activeEffects.clear();
    this.preloadedEffects.clear();
    this.currentTime = 0;
    
    this.metrics.totalEffects = timeline.events.length;
    this.metrics.activeEffects = 0;
    this.metrics.preloadedEffects = 0;
    
    if (this.config.debug) {
      console.log('[EffectsTimeline] Loaded timeline:', {
        events: timeline.events.length,
        duration: timeline.total_duration,
        stats: timeline.stats,
      });
    }
  }

  /**
   * Начать воспроизведение
   */
  start(): void {
    if (!this.timeline) {
      console.warn('[EffectsTimeline] No timeline loaded');
      return;
    }

    this.isPlaying = true;
    this.lastTickTime = performance.now();
    this.startTicker();

    if (this.config.debug) {
      console.log('[EffectsTimeline] Started');
    }
  }

  /**
   * Остановить воспроизведение
   */
  stop(): void {
    this.isPlaying = false;
    this.stopTicker();
    
    // Cleanup всех активных эффектов
    this.activeEffects.forEach((activeEffect) => {
      this.endEffect(activeEffect.effect);
    });
    this.activeEffects.clear();
    this.preloadedEffects.clear();

    if (this.config.debug) {
      console.log('[EffectsTimeline] Stopped');
    }
  }

  /**
   * Пауза
   */
  pause(): void {
    this.isPlaying = false;
    this.stopTicker();

    if (this.config.debug) {
      console.log('[EffectsTimeline] Paused at', this.currentTime);
    }
  }

  /**
   * Возобновить
   */
  resume(): void {
    if (!this.timeline) return;
    
    this.isPlaying = true;
    this.lastTickTime = performance.now();
    this.startTicker();

    if (this.config.debug) {
      console.log('[EffectsTimeline] Resumed from', this.currentTime);
    }
  }

  /**
   * Перемотка (seek)
   */
  seek(timeSeconds: number): void {
    this.currentTime = timeSeconds;
    
    // Cleanup эффектов, которые уже должны были закончиться
    this.activeEffects.forEach((activeEffect, effectId) => {
      if (timeSeconds < activeEffect.startTime || timeSeconds > activeEffect.endTime) {
        this.endEffect(activeEffect.effect);
        this.activeEffects.delete(effectId);
      }
    });
    
    // Preload эффектов, которые скоро начнутся
    this.preloadedEffects.clear();
    this.checkPreloading(timeSeconds);

    if (this.config.debug) {
      console.log('[EffectsTimeline] Seeked to', timeSeconds);
    }
  }

  /**
   * Синхронизация с внешним временем (например, audio.currentTime)
   */
  sync(audioTimeSeconds: number): void {
    const drift = Math.abs(audioTimeSeconds - this.currentTime);
    
    // Если drift больше tolerance - корректируем
    if (drift > this.config.syncTolerance / 1000) {
      if (this.config.debug) {
        console.warn('[EffectsTimeline] Sync drift detected:', drift * 1000, 'ms');
      }
      
      this.seek(audioTimeSeconds);
      this.trackSyncError(drift * 1000);
    }
  }

  /**
   * Получить текущие активные эффекты
   */
  getActiveEffects(): Effect[] {
    return Array.from(this.activeEffects.values()).map(ae => ae.effect);
  }

  /**
   * Получить метрики производительности
   */
  getMetrics(): PerformanceMetrics {
    return { ...this.metrics };
  }

  /**
   * Получить статистику timeline
   */
  getStats(): TimelineStats | null {
    return this.timeline?.stats ?? null;
  }

  // ==================== Private Methods ====================

  /**
   * Запуск основного ticker
   */
  private startTicker(): void {
    this.stopTicker();
    
    // Используем requestAnimationFrame для плавной анимации
    const tick = () => {
      if (!this.isPlaying) return;
      
      const now = performance.now();
      const deltaMs = now - this.lastTickTime;
      this.lastTickTime = now;
      
      // Обновляем currentTime
      this.currentTime += deltaMs / 1000;
      
      // Проверяем события
      this.processTick(this.currentTime);
      
      // Следующий кадр
      this.animationFrameId = requestAnimationFrame(tick);
    };
    
    this.animationFrameId = requestAnimationFrame(tick);
  }

  /**
   * Остановка ticker
   */
  private stopTicker(): void {
    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
    if (this.tickTimer !== null) {
      clearInterval(this.tickTimer);
      this.tickTimer = null;
    }
  }

  /**
   * Обработка tick - проверка событий
   */
  private processTick(currentTime: number): void {
    if (!this.timeline) return;

    // 1. Preload эффектов, которые скоро начнутся
    this.checkPreloading(currentTime);

    // 2. Запуск новых эффектов
    this.checkStarts(currentTime);

    // 3. Обновление активных эффектов
    this.updateActiveEffects(currentTime);

    // 4. Завершение эффектов
    this.checkEnds(currentTime);

    // 5. Обновляем метрики
    this.metrics.activeEffects = this.activeEffects.size;
    this.metrics.preloadedEffects = this.preloadedEffects.size;
  }

  /**
   * Проверка preloading
   */
  private checkPreloading(currentTime: number): void {
    if (!this.timeline) return;

    const preloadTime = currentTime + this.config.preloadBuffer / 1000;

    this.timeline.events.forEach((event) => {
      if (event.event_type !== 'START') return;
      if (!event.effect_id || !event.effect) return; // Guard clause
      
      const effectId = event.effect_id;
      const startTime = event.t;

      // Если эффект скоро начнётся и ещё не preloaded
      if (
        startTime <= preloadTime &&
        startTime > currentTime &&
        !this.preloadedEffects.has(effectId)
      ) {
        this.preloadEffect(event.effect);
        this.preloadedEffects.add(effectId);
      }
    });
  }

  /**
   * Проверка стартов эффектов
   */
  private checkStarts(currentTime: number): void {
    if (!this.timeline) return;

    this.timeline.events.forEach((event) => {
      if (event.event_type !== 'START') return;
      if (!event.effect_id || !event.effect) return; // Guard clause
      
      const effectId = event.effect_id;
      const startTime = event.t;

      // Если эффект должен стартовать и ещё не активен
      if (
        startTime <= currentTime &&
        !this.activeEffects.has(effectId)
      ) {
        // Проверяем, не пропустили ли мы старт
        const latency = (currentTime - startTime) * 1000;
        if (latency > this.config.syncTolerance) {
          this.metrics.missedStarts++;
          if (this.config.debug) {
            console.warn('[EffectsTimeline] Missed start:', effectId, 'latency:', latency, 'ms');
          }
        }

        this.startEffect(event.effect, startTime);
      }
    });
  }

  /**
   * Обновление активных эффектов
   */
  private updateActiveEffects(currentTime: number): void {
    this.activeEffects.forEach((activeEffect) => {
      const duration = activeEffect.endTime - activeEffect.startTime;
      const elapsed = currentTime - activeEffect.startTime;
      const progress = Math.min(Math.max(elapsed / duration, 0), 1);

      if (this.callbacks.onUpdate) {
        this.callbacks.onUpdate(activeEffect.effect, progress);
      }
    });
  }

  /**
   * Проверка завершений эффектов
   */
  private checkEnds(currentTime: number): void {
    const toRemove: string[] = [];

    this.activeEffects.forEach((activeEffect, effectId) => {
      if (currentTime >= activeEffect.endTime) {
        this.endEffect(activeEffect.effect);
        toRemove.push(effectId);
      }
    });

    toRemove.forEach(id => this.activeEffects.delete(id));
  }

  /**
   * Preload эффекта
   */
  private preloadEffect(effect: Effect): void {
    if (this.callbacks.onPreload) {
      this.callbacks.onPreload(effect);
    }

    if (this.config.debug) {
      console.log('[EffectsTimeline] Preloaded:', effect.effect_id, effect.type);
    }
  }

  /**
   * Старт эффекта
   */
  private startEffect(effect: Effect, startTime: number): void {
    const endTime = startTime + (effect.duration ?? 1.0);

    const activeEffect: ActiveEffect = {
      effect,
      startTime,
      endTime,
      isPreloaded: this.preloadedEffects.has(effect.effect_id),
    };

    this.activeEffects.set(effect.effect_id, activeEffect);

    // 🔥 DEBUG: Always log effect start
    console.log('[EffectsTimeline] 🎬 Starting effect:', {
      effect_id: effect.effect_id,
      type: effect.type,
      startTime,
      endTime,
      duration: effect.duration,
      hasCallback: !!this.callbacks.onStart
    });

    if (this.callbacks.onStart) {
      this.callbacks.onStart(effect);
    }

    if (this.config.debug) {
      console.log('[EffectsTimeline] Started:', effect.effect_id, effect.type, '@', startTime);
    }
  }

  /**
   * Завершение эффекта
   */
  private endEffect(effect: Effect): void {
    if (this.callbacks.onEnd) {
      this.callbacks.onEnd(effect);
    }

    this.preloadedEffects.delete(effect.effect_id);

    if (this.config.debug) {
      console.log('[EffectsTimeline] Ended:', effect.effect_id);
    }
  }

  /**
   * Трекинг ошибок синхронизации
   */
  private trackSyncError(errorMs: number): void {
    this.syncErrors.push(errorMs);
    
    // Храним только последние 100 ошибок
    if (this.syncErrors.length > 100) {
      this.syncErrors.shift();
    }

    // Обновляем метрики
    this.metrics.averageSyncError = 
      this.syncErrors.reduce((sum, err) => sum + err, 0) / this.syncErrors.length;
    this.metrics.maxSyncError = Math.max(...this.syncErrors);
  }

  /**
   * Cleanup ресурсов
   */
  dispose(): void {
    this.stop();
    this.timeline = null;
    this.activeEffects.clear();
    this.preloadedEffects.clear();
    this.callbacks = {};

    if (this.config.debug) {
      console.log('[EffectsTimeline] Disposed');
    }
  }
}

/**
 * Hook для интеграции с audio элементом
 */
export class AudioSyncedTimeline extends EffectsTimeline {
  private audioElement: HTMLAudioElement | null = null;
  private syncInterval: number | null = null;
  private syncFrequency: number = 100; // Проверяем sync каждые 100ms

  /**
   * Подключить audio элемент
   */
  attachAudio(audio: HTMLAudioElement): void {
    this.detachAudio();
    
    this.audioElement = audio;
    
    // Слушаем события audio
    audio.addEventListener('play', this.handleAudioPlay);
    audio.addEventListener('pause', this.handleAudioPause);
    audio.addEventListener('seeked', this.handleAudioSeeked);
    audio.addEventListener('ended', this.handleAudioEnded);
    
    // Запускаем периодическую синхронизацию
    this.startSync();
  }

  /**
   * Отключить audio элемент
   */
  detachAudio(): void {
    if (this.audioElement) {
      this.audioElement.removeEventListener('play', this.handleAudioPlay);
      this.audioElement.removeEventListener('pause', this.handleAudioPause);
      this.audioElement.removeEventListener('seeked', this.handleAudioSeeked);
      this.audioElement.removeEventListener('ended', this.handleAudioEnded);
      this.audioElement = null;
    }
    
    this.stopSync();
  }

  private handleAudioPlay = (): void => {
    this.resume();
  };

  private handleAudioPause = (): void => {
    this.pause();
  };

  private handleAudioSeeked = (): void => {
    if (this.audioElement) {
      this.seek(this.audioElement.currentTime);
    }
  };

  private handleAudioEnded = (): void => {
    this.stop();
  };

  /**
   * Запуск периодической синхронизации
   */
  private startSync(): void {
    this.stopSync();
    
    this.syncInterval = window.setInterval(() => {
      if (this.audioElement && !this.audioElement.paused) {
        this.sync(this.audioElement.currentTime);
      }
    }, this.syncFrequency);
  }

  /**
   * Остановка синхронизации
   */
  private stopSync(): void {
    if (this.syncInterval !== null) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
    }
  }

  /**
   * Cleanup
   */
  dispose(): void {
    this.detachAudio();
    super.dispose();
  }
}

/**
 * Utility: создание timeline из массива эффектов
 */
export function createTimelineFromEffects(effects: Effect[]): Timeline {
  const events: TimelineEvent[] = [];
  let maxTime = 0;

  effects.forEach((effect) => {
    const startTime = effect.t0;
    const endTime = effect.t1;
    
    // START event (with aliases for compatibility)
    events.push({
      t: startTime,
      time: startTime,
      effect_id: effect.effect_id,
      effect_type: effect.type,
      event_type: 'START',
      type: 'START',
      effect: effect,
    });

    // END event (with aliases for compatibility)
    events.push({
      t: endTime,
      time: endTime,
      effect_id: effect.effect_id,
      effect_type: effect.type,
      event_type: 'END',
      type: 'END',
      effect: effect,
    });

    maxTime = Math.max(maxTime, endTime);
  });

  // Сортируем события по времени
  events.sort((a, b) => a.t - b.t);

  // Статистика
  const stats: TimelineStats = {
    total_effects: effects.length,
    effects_by_type: {},
    max_concurrent: 0,
    avg_concurrent: 0,
    total_duration: maxTime,
  };

  // Подсчёт по типам
  effects.forEach(effect => {
    stats.effects_by_type[effect.type] = (stats.effects_by_type[effect.type] || 0) + 1;
  });

  // Расчёт concurrent effects
  const timeline: Timeline = {
    events,
    total_duration: maxTime,
    stats,
  };

  return timeline;
}

export default EffectsTimeline;
