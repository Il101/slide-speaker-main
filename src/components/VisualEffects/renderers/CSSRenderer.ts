/**
 * CSSRenderer - Ultra-Lightweight Fallback Renderer
 * 
 * Использует чистый CSS для анимаций (0% JavaScript CPU)
 * Fallback для слабых устройств или когда Canvas не доступен
 * 
 * Преимущества:
 * - 0% CPU (нативные CSS animations)
 * - Hardware accelerated (GPU compositing если доступен)
 * - Очень легковесный
 * - Работает везде (даже IE11)
 * 
 * Недостатки:
 * - Ограниченная гибкость
 * - Меньше визуальных эффектов
 * 
 * @module CSSRenderer
 */

import type { Effect } from '../types';

/**
 * Конфигурация CSS renderer
 */
export interface CSSRendererConfig {
  /** Container для эффектов */
  container: HTMLElement;
  
  /** Использовать hardware acceleration (transform3d) */
  useHardwareAcceleration: boolean;
  
  /** Prefix для CSS классов */
  classPrefix: string;
  
  /** Debug режим */
  debug: boolean;
}

/**
 * CSS Effect element
 */
interface CSSEffectElement {
  effect: Effect;
  element: HTMLDivElement;
  animationName: string;
  startTime: number;
}

/**
 * CSSRenderer - минимальный renderer на CSS
 */
export class CSSRenderer {
  private config: CSSRendererConfig;
  private container: HTMLElement;
  private activeEffects: Map<string, CSSEffectElement> = new Map();
  
  private styleSheet: CSSStyleSheet | null = null;
  private styleElement: HTMLStyleElement | null = null;
  
  private animationCounter: number = 0;

  constructor(config: Partial<CSSRendererConfig> = {}) {
    this.config = {
      container: config.container ?? document.body,
      useHardwareAcceleration: config.useHardwareAcceleration ?? true,
      classPrefix: config.classPrefix ?? 'vfx',
      debug: config.debug ?? false,
    };
    
    this.container = this.config.container;
    
    // Создаём style element для динамических стилей
    this.createStyleElement();
    
    // Добавляем базовые стили
    this.injectBaseStyles();
    
    if (this.config.debug) {
      console.log('[CSSRenderer] Initialized');
    }
  }

  /**
   * Начать рендеринг (не требуется для CSS)
   */
  start(): void {
    if (this.config.debug) {
      console.log('[CSSRenderer] Started (CSS animations are always active)');
    }
  }

  /**
   * Остановить рендеринг
   */
  stop(): void {
    // Удаляем все активные эффекты
    this.activeEffects.forEach((_, effectId) => {
      this.removeEffect(effectId);
    });
    
    if (this.config.debug) {
      console.log('[CSSRenderer] Stopped');
    }
  }

  /**
   * Добавить эффект
   */
  addEffect(effect: Effect): void {
    // Создаём DOM элемент для эффекта
    const element = this.createEffectElement(effect);
    
    // Генерируем CSS animation
    const animationName = this.generateAnimation(effect);
    
    // Применяем animation
    this.applyAnimation(element, animationName, effect);
    
    // Добавляем в container
    this.container.appendChild(element);
    
    // Сохраняем
    this.activeEffects.set(effect.effect_id, {
      effect,
      element,
      animationName,
      startTime: performance.now(),
    });
    
    // Auto-remove после завершения
    setTimeout(() => {
      this.removeEffect(effect.effect_id);
    }, effect.duration * 1000);
    
    if (this.config.debug) {
      console.log('[CSSRenderer] Added effect:', effect.effect_id, effect.type);
    }
  }

  /**
   * Обновить прогресс эффекта (не требуется для CSS)
   */
  updateEffect(_effectId: string, _progress: number): void {
    // CSS animations управляются браузером
    // Обновление не требуется
  }

  /**
   * Удалить эффект
   */
  removeEffect(effectId: string): void {
    const cssEffect = this.activeEffects.get(effectId);
    if (!cssEffect) return;
    
    // Удаляем element
    if (cssEffect.element.parentNode) {
      cssEffect.element.parentNode.removeChild(cssEffect.element);
    }
    
    this.activeEffects.delete(effectId);
    
    if (this.config.debug) {
      console.log('[CSSRenderer] Removed effect:', effectId);
    }
  }

  /**
   * Получить метрики (минимальные для CSS)
   */
  getMetrics() {
    return {
      fps: 60, // CSS animations всегда 60 FPS (если браузер успевает)
      frameTime: 16.67,
      activeEffects: this.activeEffects.size,
      droppedFrames: 0,
      qualityLevel: 'high' as const,
    };
  }

  // ==================== Private Methods ====================

  /**
   * Создать style element
   */
  private createStyleElement(): void {
    this.styleElement = document.createElement('style');
    this.styleElement.setAttribute('data-vfx-renderer', 'css');
    document.head.appendChild(this.styleElement);
    
    if (this.styleElement.sheet) {
      this.styleSheet = this.styleElement.sheet as CSSStyleSheet;
    }
  }

  /**
   * Базовые стили
   */
  private injectBaseStyles(): void {
    const baseCSS = `
      .${this.config.classPrefix}-effect {
        position: absolute;
        pointer-events: none;
        z-index: 9999;
        ${this.config.useHardwareAcceleration ? 'transform: translate3d(0, 0, 0);' : ''}
        will-change: transform, opacity;
      }
      
      .${this.config.classPrefix}-spotlight {
        background: radial-gradient(circle, transparent 40%, rgba(0, 0, 0, 0.7) 100%);
        mix-blend-mode: multiply;
      }
      
      .${this.config.classPrefix}-highlight {
        border: 3px solid #FFD700;
        box-shadow: 0 0 20px #FFD700;
        background: linear-gradient(180deg, rgba(255, 215, 0, 0.2), rgba(255, 215, 0, 0.05));
      }
      
      .${this.config.classPrefix}-fade {
        background: rgba(255, 255, 255, 0.8);
      }
      
      .${this.config.classPrefix}-pulse {
        border: 2px solid #FFD700;
        box-shadow: 0 0 10px #FFD700;
      }
    `;
    
    this.addRule(baseCSS);
  }

  /**
   * Создать DOM элемент для эффекта
   */
  private createEffectElement(effect: Effect): HTMLDivElement {
    const element = document.createElement('div');
    element.className = `${this.config.classPrefix}-effect ${this.config.classPrefix}-${effect.type}`;
    element.setAttribute('data-effect-id', effect.effect_id);
    
    // Позиция и размер из bbox
    const bbox = effect.target.bbox;
    if (bbox) {
      const [x, y, w, h] = bbox;
      element.style.left = `${x}px`;
      element.style.top = `${y}px`;
      element.style.width = `${w}px`;
      element.style.height = `${h}px`;
    }
    
    return element;
  }

  /**
   * Генерировать CSS animation
   */
  private generateAnimation(effect: Effect): string {
    const animationName = `${this.config.classPrefix}-anim-${this.animationCounter++}`;
    
    let keyframes = '';
    
    switch (effect.type) {
      case 'spotlight':
        keyframes = this.generateSpotlightKeyframes(effect);
        break;
      case 'highlight':
        keyframes = this.generateHighlightKeyframes(effect);
        break;
      case 'fade_in':
        keyframes = `
          @keyframes ${animationName} {
            from { opacity: 0; }
            to { opacity: 1; }
          }
        `;
        break;
      case 'fade_out':
        keyframes = `
          @keyframes ${animationName} {
            from { opacity: 1; }
            to { opacity: 0; }
          }
        `;
        break;
      case 'pulse':
        keyframes = `
          @keyframes ${animationName} {
            0%, 100% { transform: scale(1); opacity: 0.5; }
            50% { transform: scale(1.1); opacity: 1; }
          }
        `;
        break;
      case 'particle_highlight':
        // Particles сложно реализовать чистым CSS
        // Используем простой blur + glow эффект
        keyframes = `
          @keyframes ${animationName} {
            from { 
              box-shadow: 0 0 5px ${effect.params.color || '#FFD700'};
              opacity: 1;
            }
            to { 
              box-shadow: 0 0 30px ${effect.params.color || '#FFD700'};
              opacity: 0;
            }
          }
        `;
        break;
      default:
        keyframes = `
          @keyframes ${animationName} {
            from { opacity: 0; }
            to { opacity: 1; }
          }
        `;
    }
    
    this.addRule(keyframes);
    
    return animationName;
  }

  /**
   * Spotlight keyframes
   */
  private generateSpotlightKeyframes(effect: Effect): string {
    const animationName = `${this.config.classPrefix}-anim-${this.animationCounter}`;
    const params = effect.params;
    const opacity = params.shadow_opacity ?? 0.7;
    
    return `
      @keyframes ${animationName} {
        from { 
          opacity: 0;
        }
        to { 
          opacity: ${opacity};
        }
      }
    `;
  }

  /**
   * Highlight keyframes
   */
  private generateHighlightKeyframes(effect: Effect): string {
    const animationName = `${this.config.classPrefix}-anim-${this.animationCounter}`;
    const params = effect.params;
    const color = params.color || '#FFD700';
    
    return `
      @keyframes ${animationName} {
        from { 
          opacity: 0;
          box-shadow: 0 0 0 ${color};
        }
        to { 
          opacity: ${params.opacity ?? 0.5};
          box-shadow: 0 0 20px ${color};
        }
      }
    `;
  }

  /**
   * Применить animation к элементу
   */
  private applyAnimation(element: HTMLDivElement, animationName: string, effect: Effect): void {
    const duration = effect.duration;
    const easing = this.mapEasingToCSS(effect.params.ease_in);
    
    element.style.animation = `${animationName} ${duration}s ${easing} forwards`;
  }

  /**
   * Маппинг easing функций в CSS timing functions
   */
  private mapEasingToCSS(easing: string): string {
    const map: Record<string, string> = {
      'linear': 'linear',
      'ease-in': 'ease-in',
      'ease-out': 'ease-out',
      'ease-in-out': 'ease-in-out',
      'cubic-in': 'cubic-bezier(0.32, 0, 0.67, 0)',
      'cubic-out': 'cubic-bezier(0.33, 1, 0.68, 1)',
      'cubic-in-out': 'cubic-bezier(0.65, 0, 0.35, 1)',
      'elastic': 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
      'bounce': 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
    };
    
    return map[easing] || 'ease-in-out';
  }

  /**
   * Добавить CSS rule
   */
  private addRule(css: string): void {
    if (!this.styleSheet) return;
    
    try {
      this.styleSheet.insertRule(css, this.styleSheet.cssRules.length);
    } catch (error) {
      if (this.config.debug) {
        console.error('[CSSRenderer] Failed to add rule:', error);
      }
    }
  }

  /**
   * Cleanup ресурсов
   */
  dispose(): void {
    this.stop();
    
    // Удаляем style element
    if (this.styleElement && this.styleElement.parentNode) {
      this.styleElement.parentNode.removeChild(this.styleElement);
    }
    
    this.styleSheet = null;
    this.styleElement = null;
    this.activeEffects.clear();
    
    if (this.config.debug) {
      console.log('[CSSRenderer] Disposed');
    }
  }
}

export default CSSRenderer;
