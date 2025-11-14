/**
 * Visual Effects V2 - Main Export
 * 
 * @module VisualEffects
 */

// Main Component
export { VisualEffectsEngine, type VisualEffectsEngineProps } from './VisualEffectsEngine';

// Core Systems
export { EffectsTimeline, AudioSyncedTimeline, createTimelineFromEffects } from './core/EffectsTimeline';
export { CapabilityDetector } from './core/CapabilityDetector';
export { easingFunctions, interpolate, interpolateColor } from './core/easing';

// Renderers
export { Canvas2DRenderer, type Canvas2DConfig } from './renderers/Canvas2DRenderer';
export { CSSRenderer, type CSSRendererConfig } from './renderers/CSSRenderer';

// Types
export type {
  Effect,
  EffectType,
  EffectTiming,
  EffectTarget,
  EffectParams,
  Timeline,
  TimelineEvent,
  TimelineStats,
  SlideManifest,
  RenderCapabilities,
  RendererType,
  RendererConfig,
  EasingFunction,
  EasingFunc,
  IntensityLevel,
} from './types';
