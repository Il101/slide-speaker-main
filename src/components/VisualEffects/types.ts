/**
 * Visual Effects V2 - Type Definitions
 * 
 * Типы для системы визуальных эффектов
 */

export type EffectType =
  | 'spotlight'
  | 'highlight'
  | 'fade_in'
  | 'fade_out'
  | 'particle_highlight'
  | 'morph'
  | 'glitch'
  | 'ripple'
  | 'hologram'
  | 'pulse'
  | 'blur_others';

export type EasingFunction =
  | 'linear'
  | 'ease-in'
  | 'ease-out'
  | 'ease-in-out'
  | 'cubic-in'
  | 'cubic-out'
  | 'cubic-in-out'
  | 'elastic'
  | 'bounce';

export type IntensityLevel = 'subtle' | 'normal' | 'dramatic';

export interface EffectTiming {
  t0: number;            // Start time (seconds)
  t1: number;            // End time (seconds)
  duration: number;      // Duration (seconds)
  confidence: number;    // 0.0 - 1.0
  source: 'talk_track' | 'tts' | 'fallback';
  precision: 'word' | 'sentence' | 'segment';
}

export interface EffectTarget {
  element_id?: string;
  element_ids?: string[];
  bbox?: [number, number, number, number]; // [x, y, width, height]
  group_id?: string;
}

export interface EffectParams {
  ease_in: EasingFunction;
  ease_out: EasingFunction;
  intensity: IntensityLevel;
  opacity: number;
  color: string;
  secondary_color?: string;
  
  // Spotlight specific
  shadow_opacity?: number;
  beam_width?: number;
  
  // Particle specific
  particle_count?: number;
  particle_size?: [number, number];
  gravity?: number;
  spread?: number;
  
  // Custom params
  [key: string]: any;
}

export interface Effect {
  effect_id: string;  // Unified ID field
  id: string;         // Alias for compatibility
  type: EffectType;
  target: EffectTarget;
  
  // Timing fields (flattened from timing object)
  t0: number;        // Start time (seconds)
  t1: number;        // End time (seconds)
  duration: number;  // Duration (seconds)
  confidence: number;
  source: 'talk_track' | 'tts' | 'fallback';
  precision: 'word' | 'sentence' | 'segment';
  
  // Legacy timing object support
  timing?: EffectTiming;
  
  params: EffectParams;
  metadata?: {
    group_id?: string;
    group_type?: string;
    priority?: string;
    [key: string]: any;
  };
}

export interface TimelineEvent {
  t: number;          // Event time (seconds)
  time: number;       // Alias for compatibility
  event_type: 'START' | 'END' | 'SLIDE_START' | 'SLIDE_END';
  type: 'START' | 'END' | 'SLIDE_START' | 'SLIDE_END';  // Alias
  effect_id?: string;
  effect_type?: string;
  effect?: Effect;    // Full effect object for convenience
  metadata?: Record<string, any>;
}

export interface TimelineStats {
  total_effects: number;
  effects_by_type: Record<string, number>;
  max_concurrent: number;
  avg_concurrent: number;
  total_duration: number;
}

export interface Timeline {
  total_duration: number;
  events: TimelineEvent[];
  stats: TimelineStats;
  
  // Legacy fields
  effects_count?: number;
  statistics?: {
    total_effects: number;
    confidence: {
      high: number;
      medium: number;
      low: number;
    };
    sources: Record<string, number>;
    types: Record<string, number>;
  };
}

export interface SlideManifest {
  version: string;
  id: string;
  timeline: Timeline;
  effects: Effect[];
  quality?: {
    score: number;
    confidence_avg: number;
    high_confidence_count: number;
    total_effects: number;
  };
}

export interface RenderCapabilities {
  webgl: boolean;
  webgl2: boolean;
  offscreenCanvas: boolean;
  hardwareConcurrency: number;
  deviceMemory: number;
  pixelRatio: number;
  isHeadless: boolean;
  recommendedRenderer: RendererType;
}

export type RendererType = 'webgl' | 'canvas2d' | 'css';

export interface RendererConfig {
  preferredRenderer?: RendererType;
  maxParticles?: number;
  disableWebGL?: boolean;
  quality?: 'low' | 'medium' | 'high';
  enablePerformanceMonitoring?: boolean;
}

// Easing functions (mathematical)
export type EasingFunc = (t: number) => number;

export interface EasingFunctions {
  linear: EasingFunc;
  'ease-in': EasingFunc;
  'ease-out': EasingFunc;
  'ease-in-out': EasingFunc;
  'cubic-in': EasingFunc;
  'cubic-out': EasingFunc;
  'cubic-in-out': EasingFunc;
  elastic: EasingFunc;
  bounce: EasingFunc;
}
