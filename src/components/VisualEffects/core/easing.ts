/**
 * Easing Functions - плавные переходы для анимаций
 * 
 * Все функции принимают t от 0 до 1 и возвращают значение от 0 до 1
 */

import type { EasingFunc, EasingFunctions, EasingFunction } from '../types';

export const easingFunctions: EasingFunctions = {
  linear: (t: number): number => t,
  
  'ease-in': (t: number): number => t * t,
  
  'ease-out': (t: number): number => t * (2 - t),
  
  'ease-in-out': (t: number): number => 
    t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t,
  
  'cubic-in': (t: number): number => t * t * t,
  
  'cubic-out': (t: number): number => 
    (--t) * t * t + 1,
  
  'cubic-in-out': (t: number): number =>
    t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1,
  
  elastic: (t: number): number => {
    if (t === 0 || t === 1) return t;
    const p = 0.3;
    const s = p / 4;
    return Math.pow(2, -10 * t) * Math.sin((t - s) * (2 * Math.PI) / p) + 1;
  },
  
  bounce: (t: number): number => {
    if (t < 1 / 2.75) {
      return 7.5625 * t * t;
    } else if (t < 2 / 2.75) {
      return 7.5625 * (t -= 1.5 / 2.75) * t + 0.75;
    } else if (t < 2.5 / 2.75) {
      return 7.5625 * (t -= 2.25 / 2.75) * t + 0.9375;
    } else {
      return 7.5625 * (t -= 2.625 / 2.75) * t + 0.984375;
    }
  }
};

/**
 * Получить easing функцию по имени
 */
export function getEasingFunction(name: EasingFunction): EasingFunc {
  return easingFunctions[name] || easingFunctions.linear;
}

/**
 * Применить easing к значению
 */
export function applyEasing(
  progress: number,
  easingName: EasingFunction
): number {
  const easing = getEasingFunction(easingName);
  return easing(Math.max(0, Math.min(1, progress)));
}

/**
 * Интерполяция между двумя значениями с easing
 */
export function interpolate(
  from: number,
  to: number,
  progress: number,
  easingName: EasingFunction = 'linear'
): number {
  const t = applyEasing(progress, easingName);
  return from + (to - from) * t;
}

/**
 * Интерполяция цвета (hex)
 */
export function interpolateColor(
  from: string,
  to: string,
  progress: number,
  easingName: EasingFunction = 'linear'
): string {
  const t = applyEasing(progress, easingName);
  
  // Parse hex colors
  const fromRgb = hexToRgb(from);
  const toRgb = hexToRgb(to);
  
  if (!fromRgb || !toRgb) return from;
  
  const r = Math.round(fromRgb.r + (toRgb.r - fromRgb.r) * t);
  const g = Math.round(fromRgb.g + (toRgb.g - fromRgb.g) * t);
  const b = Math.round(fromRgb.b + (toRgb.b - fromRgb.b) * t);
  
  return rgbToHex(r, g, b);
}

/**
 * Hex to RGB
 */
function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : null;
}

/**
 * RGB to Hex
 */
function rgbToHex(r: number, g: number, b: number): string {
  return '#' + [r, g, b].map(x => {
    const hex = x.toString(16);
    return hex.length === 1 ? '0' + hex : hex;
  }).join('');
}
