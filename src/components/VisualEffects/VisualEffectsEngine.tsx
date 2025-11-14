/**
 * VisualEffectsEngine - Main React Component
 * 
 * Объединяет все системы Visual Effects V2:
 * - EffectsTimeline (синхронизация)
 * - Canvas2DRenderer / CSSRenderer (рендеринг)
 * - CapabilityDetector (автовыбор renderer)
 * - Integration с audio sync
 * 
 * @module VisualEffectsEngine
 */

import React, { useEffect, useRef, useState } from 'react';
import { EffectsTimeline, AudioSyncedTimeline } from './core/EffectsTimeline';
import { Canvas2DRenderer } from './renderers/Canvas2DRenderer';
import { CSSRenderer } from './renderers/CSSRenderer';
import { CapabilityDetector } from './core/CapabilityDetector';
import type { SlideManifest, RendererType, RenderCapabilities, Effect } from './types';

/**
 * Props для VisualEffectsEngine
 */
export interface VisualEffectsEngineProps {
  /** Manifest с эффектами (из Backend V2) */
  manifest: SlideManifest | null;
  
  /** Audio элемент для синхронизации */
  audioElement?: HTMLAudioElement | null;
  
  /** Предпочитаемый renderer (auto = автовыбор) */
  preferredRenderer?: RendererType | 'auto';
  
  /** Включить debug режим */
  debug?: boolean;
  
  /** Callback при изменении производительности */
  onPerformanceChange?: (metrics: any) => void;
  
  /** Container style */
  style?: React.CSSProperties;
  
  /** CSS class */
  className?: string;
  
  /** Масштаб слайда (для координат эффектов) - соотношение canvasSize / originalSlideSize */
  slideScale?: { x: number; y: number };
  
  /** Смещение слайда - используется только для отображения изображения, НЕ для canvas координат */
  slideOffset?: { x: number; y: number };
  
  /** Размеры оригинального слайда (из PPT/PDF) */
  slideDimensions?: { width: number; height: number };
}

/**
 * VisualEffectsEngine Component
 */
export const VisualEffectsEngine: React.FC<VisualEffectsEngineProps> = ({
  manifest,
  audioElement,
  preferredRenderer = 'auto',
  debug = false,
  onPerformanceChange,
  style,
  className,
  slideScale = { x: 1, y: 1 },
  slideOffset = { x: 0, y: 0 },
  slideDimensions = { width: 1920, height: 1080 },
}) => {
  // 🔍 DEBUG: Log что приходит в компонент
  console.log('[VisualEffectsEngine] Component render:', {
    hasManifest: !!manifest,
    manifestType: typeof manifest,
    manifestPreview: manifest ? {
      version: manifest.version,
      id: manifest.id,
      effectsCount: manifest.effects?.length,
      timelineEventsCount: manifest.timeline?.events?.length
    } : null,
    hasAudio: !!audioElement,
    debug
  });
  
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  
  const [capabilities, setCapabilities] = useState<RenderCapabilities | null>(null);
  const [selectedRenderer, setSelectedRenderer] = useState<RendererType>('canvas2d');
  const [isReady, setIsReady] = useState(false);
  
  // Refs для объектов (не вызывают re-render)
  const timelineRef = useRef<EffectsTimeline | AudioSyncedTimeline | null>(null);
  const rendererRef = useRef<Canvas2DRenderer | CSSRenderer | null>(null);
  
  // 🔥 FIX: Prevent infinite re-initialization
  const timelineInitialized = useRef(false);
  const lastManifestId = useRef<string | null>(null);

  /**
   * Инициализация capabilities
   */
  useEffect(() => {
    const detector = new CapabilityDetector();
    const caps = detector.detect();
    setCapabilities(caps);
    
    // Выбираем renderer
    let renderer: RendererType;
    if (preferredRenderer === 'auto') {
      renderer = caps.recommendedRenderer;
    } else {
      renderer = preferredRenderer;
    }
    
    // Fallback если выбранный renderer не поддерживается
    if (renderer === 'webgl' && !caps.webgl) {
      renderer = 'canvas2d';
    }
    
    setSelectedRenderer(renderer);
    
    if (debug) {
      console.log('[VisualEffectsEngine] Capabilities:', caps);
      console.log('[VisualEffectsEngine] Selected renderer:', renderer);
    }
  }, [preferredRenderer, debug]);

  /**
   * Инициализация renderer
   */
  useEffect(() => {
    if (!capabilities) return;
    
    // Cleanup предыдущего renderer
    if (rendererRef.current) {
      rendererRef.current.dispose();
      rendererRef.current = null;
    }
    
    // Создаём новый renderer
    try {
      if (selectedRenderer === 'canvas2d') {
        if (!canvasRef.current || !containerRef.current) return;
        
        const rect = containerRef.current.getBoundingClientRect();
        
        rendererRef.current = new Canvas2DRenderer(canvasRef.current, {
          targetFPS: 60,
          maxParticles: capabilities.hardwareConcurrency > 4 ? 200 : 100,
          quality: capabilities.hardwareConcurrency > 4 ? 'high' : 'medium',
          debug,
          slideScale,
          slideOffset,
          slideDimensions,
        });
        
        // ✅ Устанавливаем размеры canvas
        if (rect.width > 0 && rect.height > 0) {
          rendererRef.current.resize(rect.width, rect.height);
          console.log(`🔍 [DEBUG] Canvas resized: ${rect.width}x${rect.height}`);
          console.log(`🔍 [DEBUG] Canvas element: width=${canvasRef.current.width}, height=${canvasRef.current.height}`);
        } else {
          console.error('❌ [ERROR] Container has ZERO dimensions!', rect);
          
          // 🔥 RETRY: Wait for container to get dimensions
          setTimeout(() => {
            const retryRect = containerRef.current?.getBoundingClientRect();
            if (retryRect && retryRect.width > 0 && retryRect.height > 0 && rendererRef.current) {
              if ('resize' in rendererRef.current) {
                rendererRef.current.resize(retryRect.width, retryRect.height);
                console.log('✅ [RETRY SUCCESS] Canvas resized:', retryRect.width, 'x', retryRect.height);
              }
            } else {
              console.error('❌ [RETRY FAILED] Container still has zero dimensions');
            }
          }, 100);
        }
        
        // 🔥 DEBUG: Прямой тест canvas рендеринга
        const ctx = canvasRef.current.getContext('2d');
        if (ctx) {
          ctx.fillStyle = 'rgba(255, 0, 0, 0.5)';
          ctx.fillRect(100, 100, 200, 200);
          console.log('🔥 [DEBUG] Canvas DIRECT test draw: RED SQUARE at 100,100,200x200');
          console.log('🔍 [DEBUG] Canvas style:', canvasRef.current.style.cssText);
          console.log('🔍 [DEBUG] Canvas computed style:', window.getComputedStyle(canvasRef.current).cssText);
        }
        
        // ✅ Запускаем рендеринг
        rendererRef.current.start();
      } else if (selectedRenderer === 'css') {
        if (!containerRef.current) return;
        
        rendererRef.current = new CSSRenderer({
          container: containerRef.current,
          debug,
        });
      }
      
      setIsReady(true);
      
      if (debug) {
        console.log('[VisualEffectsEngine] Renderer initialized:', selectedRenderer);
      }
    } catch (error) {
      console.error('[VisualEffectsEngine] Failed to initialize renderer:', error);
      
      // Fallback на CSS renderer
      if (selectedRenderer !== 'css' && containerRef.current) {
        rendererRef.current = new CSSRenderer({
          container: containerRef.current,
          debug,
        });
        setSelectedRenderer('css');
      }
    }
    
    return () => {
      if (rendererRef.current) {
        rendererRef.current.dispose();
        rendererRef.current = null;
      }
    };
  }, [capabilities, selectedRenderer, debug, slideScale, slideOffset, slideDimensions]);

  /**
   * Обновление трансформации слайда при изменении масштаба/offset
   */
  useEffect(() => {
    if (rendererRef.current && 'updateSlideTransform' in rendererRef.current) {
      (rendererRef.current as Canvas2DRenderer).updateSlideTransform(
        slideScale,
        slideOffset,
        slideDimensions
      );
    }
  }, [slideScale, slideOffset, slideDimensions]);

  /**
   * Инициализация timeline
   */
  useEffect(() => {
    console.log('[VisualEffectsEngine] Timeline init check:', {
      hasManifest: !!manifest,
      isReady,
      manifestType: typeof manifest,
      manifestKeys: manifest ? Object.keys(manifest) : null,
      effectsCount: manifest?.effects?.length,
      timelineEventsCount: manifest?.timeline?.events?.length,
      alreadyInitialized: timelineInitialized.current,
      manifestId: manifest?.id
    });
    
    // 🔥 FIX: Skip if already initialized with same manifest
    if (timelineInitialized.current && lastManifestId.current === manifest?.id) {
      console.log('[VisualEffectsEngine] ⏩ Timeline already initialized, skipping...');
      return;
    }
    
    if (!manifest || !isReady) {
      if (!manifest) {
        console.warn('[VisualEffectsEngine] ⚠️ NO MANIFEST - skipping timeline init');
      }
      if (!isReady) {
        console.warn('[VisualEffectsEngine] ⚠️ NOT READY - waiting for renderer');
      }
      return;
    }
    
    // ✅ Проверяем структуру manifest
    if (!manifest.timeline || !manifest.effects) {
      console.error('[VisualEffectsEngine] ❌ INVALID MANIFEST STRUCTURE:', {
        hasTimeline: !!manifest.timeline,
        hasEffects: !!manifest.effects,
        manifestKeys: Object.keys(manifest)
      });
      return;
    }
    
    console.log('[VisualEffectsEngine] ✅ Valid manifest, initializing timeline...');
    
    // Cleanup предыдущего timeline
    if (timelineRef.current) {
      timelineRef.current.dispose();
      timelineRef.current = null;
    }
    
    // 🔥 FIX: Transform ALL effects first - flatten timing object
    const transformedEffects = manifest.effects?.map(rawEffect => ({
      ...rawEffect,
      effect_id: rawEffect.id || rawEffect.effect_id,
      id: rawEffect.id || rawEffect.effect_id,
      t0: rawEffect.timing?.t0 ?? rawEffect.t0 ?? 0,
      t1: rawEffect.timing?.t1 ?? rawEffect.t1 ?? 0,
      duration: rawEffect.timing?.duration ?? rawEffect.duration ?? 0,
      confidence: rawEffect.timing?.confidence ?? rawEffect.confidence ?? 1,
      source: rawEffect.timing?.source ?? rawEffect.source ?? 'fallback',
      precision: rawEffect.timing?.precision ?? rawEffect.precision ?? 'segment',
    })) ?? [];
    
    console.log('[VisualEffectsEngine] 🔧 Transformed effects:', {
      original: manifest.effects?.length,
      transformed: transformedEffects.length,
      sample: transformedEffects[0]
    });
    
    // Создаём timeline
    const callbacks = {
      onPreload: (effect: Effect) => {
        if (debug) {
          console.log('[VisualEffectsEngine] Preload effect:', effect.effect_id);
        }
      },
      
      onStart: (effect: Effect) => {
        if (rendererRef.current) {
          console.log('[VisualEffectsEngine] ✅ Adding effect to renderer:', effect.effect_id, effect.type);
          rendererRef.current.addEffect(effect);
        }
        if (debug) {
          console.log('[VisualEffectsEngine] Start effect:', effect.effect_id, effect.type);
        }
      },
      
      onUpdate: (effect: Effect, progress: number) => {
        if (rendererRef.current) {
          rendererRef.current.updateEffect(effect.effect_id, progress);
        }
      },
      
      onEnd: (effect: Effect) => {
        if (rendererRef.current) {
          console.log('[VisualEffectsEngine] ✅ Removing effect from renderer:', effect.effect_id);
          rendererRef.current.removeEffect(effect.effect_id);
        }
        if (debug) {
          console.log('[VisualEffectsEngine] End effect:', effect.effect_id);
        }
      },
    };
    
    // 🔧 FIX: Use transformed effects for timeline enrichment
    const enrichedTimeline = {
      ...manifest.timeline,
      events: manifest.timeline.events.map(event => {
        if (event.effect_id && (event.type === 'START' || event.type === 'END')) {
          // Находим уже трансформированный effect по ID
          const effect = transformedEffects.find(e => e.id === event.effect_id);
          if (effect) {
            return { ...event, effect };
          }
        }
        return event;
      })
    };
    
    // 🔍 Debug: Count enriched events
    const enrichedCount = enrichedTimeline.events.filter(e => e.effect).length;
    if (debug) {
      console.log('[VisualEffectsEngine] Enriched timeline:', {
        totalEvents: enrichedTimeline.events.length,
        enrichedEvents: enrichedCount,
        unenrichedEvents: enrichedTimeline.events.length - enrichedCount,
      });
    }
    
    // Выбираем тип timeline
    if (audioElement) {
      console.log('[VisualEffectsEngine] Creating AudioSyncedTimeline with:', {
        timelineEvents: enrichedTimeline.events.length,
        effectsCount: manifest.effects?.length,
        hasAudio: !!audioElement,
        audioSrc: audioElement?.src,
        audioPaused: audioElement?.paused,
      });
      
      const audioTimeline = new AudioSyncedTimeline({
        preloadBuffer: 100,
        tickInterval: 16,
        syncTolerance: 150, // 🔥 Increased from 50ms to 150ms to reduce false drift warnings
        debug,
      }, callbacks);
      
      audioTimeline.loadTimeline(enrichedTimeline);
      
      // � DON'T attach audio here - it's done in separate useEffect
      // This prevents timeline recreation when audio changes
      // console.log('[VisualEffectsEngine] 🔊 Attaching audio to timeline:', ...);
      // audioTimeline.attachAudio(audioElement);
      
      audioTimeline.start();
      
      timelineRef.current = audioTimeline;
      
      // 🔥 Mark as initialized
      timelineInitialized.current = true;
      lastManifestId.current = manifest.id;
      
      if (debug) {
        console.log('[VisualEffectsEngine] AudioSyncedTimeline initialized');
      }
    } else {
      const timeline = new EffectsTimeline({
        preloadBuffer: 100,
        tickInterval: 16,
        debug,
      }, callbacks);
      
      timeline.loadTimeline(enrichedTimeline);
      timeline.start();
      
      timelineRef.current = timeline;
      
      // 🔥 Mark as initialized
      timelineInitialized.current = true;
      lastManifestId.current = manifest.id;
      
      if (debug) {
        console.log('[VisualEffectsEngine] Manual timeline initialized');
      }
    }
    
    return () => {
      // 🔥 Reset initialization flag on cleanup
      timelineInitialized.current = false;
      lastManifestId.current = null;
      
      if (timelineRef.current) {
        timelineRef.current.dispose();
        timelineRef.current = null;
      }
    };
  }, [manifest, isReady, debug]); // 🔥 REMOVED audioElement - causes infinite loop

  /**
   * Separate effect to attach/detach audio without recreating timeline
   */
  useEffect(() => {
    if (!timelineRef.current || !audioElement) return;
    
    // Only attach audio if timeline is AudioSyncedTimeline
    if ('attachAudio' in timelineRef.current) {
      console.log('[VisualEffectsEngine] 🔊 Attaching audio to existing timeline');
      (timelineRef.current as AudioSyncedTimeline).attachAudio(audioElement);
    }
    
    return () => {
      if (timelineRef.current && 'detachAudio' in timelineRef.current) {
        console.log('[VisualEffectsEngine] 🔇 Detaching audio from timeline');
        (timelineRef.current as AudioSyncedTimeline).detachAudio();
      }
    };
  }, [audioElement]); // 🔥 Only re-run when audio element changes

  /**
   * Performance monitoring
   */
  useEffect(() => {
    if (!onPerformanceChange || !isReady) return;
    
    const interval = setInterval(() => {
      if (rendererRef.current) {
        const metrics = rendererRef.current.getMetrics();
        onPerformanceChange(metrics);
      }
    }, 1000);
    
    return () => clearInterval(interval);
  }, [onPerformanceChange, isReady]);

  /**
   * Resize canvas to match container
   */
  useEffect(() => {
    if (!canvasRef.current || selectedRenderer !== 'canvas2d') return;
    
    const updateSize = () => {
      if (!canvasRef.current || !containerRef.current) return;
      
      const { width, height } = containerRef.current.getBoundingClientRect();
      canvasRef.current.width = width;
      canvasRef.current.height = height;
      
      if (debug) {
        console.log('[VisualEffectsEngine] Canvas resized:', width, 'x', height);
      }
    };
    
    updateSize();
    
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, [selectedRenderer, debug]);

  /**
   * Public API methods are handled by the timeline directly through timelineRef
   * No need for wrapper methods as they're not used externally
   */

  return (
    <div
      ref={containerRef}
      className={className}
      style={{
        position: 'relative',
        width: '100%',
        height: '100%',
        overflow: 'hidden',
        pointerEvents: 'none',
        ...style,
      }}
      data-renderer={selectedRenderer}
      data-ready={isReady}
    >
      {selectedRenderer === 'canvas2d' && (
        <canvas
          ref={canvasRef}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            pointerEvents: 'none',
            zIndex: 10,
          }}
        />
      )}
      
      {debug && (
        <div
          style={{
            position: 'absolute',
            top: 10,
            right: 10,
            background: 'rgba(0, 0, 0, 0.8)',
            color: '#fff',
            padding: '8px 12px',
            borderRadius: 4,
            fontSize: 12,
            fontFamily: 'monospace',
            pointerEvents: 'auto',
            zIndex: 10000,
          }}
        >
          <div>Renderer: {selectedRenderer}</div>
          <div>Effects: {manifest?.effects.length ?? 0}</div>
          <div>Ready: {isReady ? 'Yes' : 'No'}</div>
          {capabilities && (
            <>
              <div>WebGL: {capabilities.webgl ? 'Yes' : 'No'}</div>
              <div>CPU Cores: {capabilities.hardwareConcurrency}</div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default VisualEffectsEngine;
