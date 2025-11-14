/**
 * Capability Detector - определение возможностей браузера
 * 
 * Автоматически определяет:
 * - Доступность WebGL
 * - Canvas2D оптимизации
 * - Performance характеристики
 * - Headless режим
 * - Рекомендуемый рендерер
 */

import type { RenderCapabilities, RendererType } from '../types';

export class CapabilityDetector {
  detect(): RenderCapabilities {
    const capabilities: RenderCapabilities = {
      webgl: this.detectWebGL(),
      webgl2: this.detectWebGL2(),
      offscreenCanvas: this.detectOffscreenCanvas(),
      hardwareConcurrency: this.getHardwareConcurrency(),
      deviceMemory: this.getDeviceMemory(),
      pixelRatio: this.getPixelRatio(),
      isHeadless: this.detectHeadless(),
      recommendedRenderer: 'css' // Будет установлен ниже
    };
    
    // Определяем рекомендуемый рендерер
    capabilities.recommendedRenderer = this.getRecommendedRenderer(capabilities);
    
    return capabilities;
  }
  
  private detectWebGL(): boolean {
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || 
                 canvas.getContext('experimental-webgl');
      return !!gl;
    } catch (e) {
      return false;
    }
  }
  
  private detectWebGL2(): boolean {
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl2');
      return !!gl;
    } catch (e) {
      return false;
    }
  }
  
  private detectOffscreenCanvas(): boolean {
    return typeof OffscreenCanvas !== 'undefined';
  }
  
  private getHardwareConcurrency(): number {
    return navigator.hardwareConcurrency || 1;
  }
  
  private getDeviceMemory(): number {
    // @ts-ignore - experimental API
    return (navigator as any).deviceMemory || 2;
  }
  
  private getPixelRatio(): number {
    return window.devicePixelRatio || 1;
  }
  
  private detectHeadless(): boolean {
    // Различные эвристики для определения headless режима
    
    // 1. Puppeteer/Playwright detection
    if ((navigator as any).webdriver) {
      return true;
    }
    
    // 2. Chrome headless detection
    if (/HeadlessChrome/.test(navigator.userAgent)) {
      return true;
    }
    
    // 3. PhantomJS
    if ((window as any).callPhantom || (window as any)._phantom) {
      return true;
    }
    
    // 4. Проверка доступности некоторых API
    if (!(window as any).chrome && /Chrome/.test(navigator.userAgent)) {
      return true; // Chrome без window.chrome - подозрительно
    }
    
    return false;
  }
  
  private getRecommendedRenderer(cap: RenderCapabilities): RendererType {
    // Логика выбора оптимального рендерера
    
    // Headless mode - только CSS
    if (cap.isHeadless) {
      console.log('🔍 Headless mode detected → CSS renderer');
      return 'css';
    }
    
    // Слабое железо - CSS
    if (cap.hardwareConcurrency < 2 || cap.deviceMemory < 2) {
      console.log('🔍 Low-end device detected → CSS renderer');
      return 'css';
    }
    
    // WebGL доступен и хорошее железо - WebGL
    if (cap.webgl && cap.hardwareConcurrency >= 4 && cap.deviceMemory >= 4) {
      console.log('🔍 High-end device + WebGL → WebGL renderer');
      return 'webgl';
    }
    
    // Среднее железо - Canvas2D
    if (cap.hardwareConcurrency >= 2 || cap.deviceMemory >= 2) {
      console.log('🔍 Mid-range device → Canvas2D renderer');
      return 'canvas2d';
    }
    
    // Fallback - CSS
    console.log('🔍 Fallback → CSS renderer');
    return 'css';
  }
  
  /**
   * Получить читаемое описание возможностей
   */
  getCapabilitiesDescription(cap: RenderCapabilities): string {
    const parts = [];
    
    if (cap.webgl) {
      parts.push(`WebGL${cap.webgl2 ? '2' : ''}`);
    }
    
    if (cap.offscreenCanvas) {
      parts.push('OffscreenCanvas');
    }
    
    parts.push(`${cap.hardwareConcurrency} cores`);
    parts.push(`${cap.deviceMemory}GB RAM`);
    parts.push(`${cap.pixelRatio}x DPI`);
    
    if (cap.isHeadless) {
      parts.push('Headless');
    }
    
    return parts.join(', ');
  }
}
