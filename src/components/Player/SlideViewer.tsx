import React, { useEffect, useCallback, useMemo } from 'react';
import { usePlayer } from './PlayerContext';
import { calculateScale } from './utils/scaleCalculations';
import { VisualEffectsEngine } from '@/components/VisualEffects';

export const SlideViewer: React.FC = () => {
  const {
    manifest,
    playerState,
    setPlayerState,
    slideRef,
    scale,
    setScale,
    slideDimensions,
    setSlideDimensions,
    imageOffset,
    setImageOffset,
    audioRef,
  } = usePlayer();

  const currentSlide = manifest?.slides[playerState.currentSlide];
  
  // 🔥 Memoize VFX manifest to prevent re-initialization on every render
  const vfxManifest = useMemo(() => {
    return currentSlide?.visual_effects_manifest;
  }, [playerState.currentSlide, manifest]);
  const imageUrl = currentSlide?.image 
    ? `${import.meta.env.VITE_API_BASE || 'http://localhost:8000'}${currentSlide.image}`
    : '';

  // 🔥 Load actual image dimensions
  useEffect(() => {
    if (!imageUrl) return;
    
    const img = new Image();
    img.onload = () => {
      if (img.naturalWidth && img.naturalHeight) {
        setSlideDimensions({
          width: img.naturalWidth,
          height: img.naturalHeight
        });
        console.log('[SlideViewer] 📐 Image dimensions loaded:', {
          width: img.naturalWidth,
          height: img.naturalHeight
        });
      }
    };
    img.src = imageUrl;
  }, [imageUrl, setSlideDimensions]);

  // 🔍 DEBUG: Log slide data
  useEffect(() => {
    if (currentSlide) {
      console.log('[SlideViewer] Current slide:', {
        slideIndex: playerState.currentSlide,
        slideId: currentSlide.id,
        hasVisualEffects: !!currentSlide.visual_effects_manifest,
        vfxType: typeof currentSlide.visual_effects_manifest,
        vfxKeys: currentSlide.visual_effects_manifest ? Object.keys(currentSlide.visual_effects_manifest) : null,
        vfxManifest: currentSlide.visual_effects_manifest // 🔥 Full manifest
      });
      
      // 🔥 Extra debug for VFX
      if (currentSlide.visual_effects_manifest) {
        const vfx = currentSlide.visual_effects_manifest;
        console.log('[SlideViewer] 🎨 VFX Details:', {
          version: vfx.version,
          effects: vfx.effects?.length || 0,
          timeline_events: vfx.timeline?.events?.length || 0,
          quality: vfx.quality
        });
      } else {
        console.warn('[SlideViewer] ⚠️ NO VISUAL EFFECTS MANIFEST!');
      }
    }
  }, [currentSlide, playerState.currentSlide]);

  // Calculate and update scale when container or slide changes
  const updateScale = useCallback(() => {
    if (!slideRef.current) return;
    
    const container = slideRef.current;
    const containerRect = container.getBoundingClientRect();
    
    const result = calculateScale(
      containerRect.width,
      containerRect.height,
      slideDimensions.width,
      slideDimensions.height
    );
    
    setScale({ x: result.uniformScale, y: result.uniformScale });
    setImageOffset(result.offset);
    
    // 🔍 DEBUG: Log scale calculations
    console.log('[SlideViewer] 📐 Scale calculated:', {
      containerSize: { width: containerRect.width, height: containerRect.height },
      slideSize: slideDimensions,
      scale: { x: result.uniformScale, y: result.uniformScale },
      offset: result.offset,
      scaledSlideSize: {
        width: slideDimensions.width * result.uniformScale,
        height: slideDimensions.height * result.uniformScale
      }
    });
  }, [slideRef, slideDimensions, setScale, setImageOffset]);

  // Update scale on mount and window resize
  useEffect(() => {
    updateScale();
    
    const handleResize = () => {
      updateScale();
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [updateScale]);

  if (!currentSlide) {
    return (
      <div className="flex items-center justify-center h-full bg-muted rounded-lg">
        <p className="text-muted-foreground">Слайд не найден</p>
      </div>
    );
  }

  const audioUrl = currentSlide.audio 
    ? `${import.meta.env.VITE_API_BASE || 'http://localhost:8000'}${currentSlide.audio}`
    : '';

  // Handle time update from audio playback
  // 🔥 Memoize to prevent creating new function on every render
  // 🔥 OPTIMIZATION: Throttle currentTime updates to reduce re-renders
  // Update max 15 times per second instead of 60
  const lastUpdateRef = React.useRef<number>(0);
  const THROTTLE_MS = 66; // ~15 updates per second

  const handleTimeUpdate = useCallback(() => {
    if (audioRef.current) {
      const now = Date.now();
      
      // Only update if enough time has passed
      if (now - lastUpdateRef.current < THROTTLE_MS) {
        return;
      }
      
      lastUpdateRef.current = now;
      
      setPlayerState(prev => ({
        ...prev,
        currentTime: audioRef.current!.currentTime,
      }));
    }
  }, [audioRef, setPlayerState]);

  // Handle audio end - go to next slide
  // 🔥 Memoize with dependencies
  const handleAudioEnded = useCallback(() => {
    if (manifest && playerState.currentSlide < manifest.slides.length - 1) {
      // Auto-advance to next slide
      const nextIndex = playerState.currentSlide + 1;
      setPlayerState(prev => ({ ...prev, currentSlide: nextIndex }));
    } else {
      // Last slide - stop playing
      setPlayerState(prev => ({ ...prev, isPlaying: false }));
    }
  }, [manifest, playerState.currentSlide, setPlayerState]);

  // 🔥 Memoize play/pause handlers
  const handlePlay = useCallback(() => {
    setPlayerState(prev => ({ ...prev, isPlaying: true }));
  }, [setPlayerState]);

  const handlePause = useCallback(() => {
    setPlayerState(prev => ({ ...prev, isPlaying: false }));
  }, [setPlayerState]);

  return (
    <>
      <div 
        ref={slideRef}
        className="relative w-full aspect-video bg-black rounded-lg overflow-hidden"
        aria-label={`Слайд ${playerState.currentSlide + 1}`}
      >
        {/* Slide image */}
        {imageUrl && (
          <img
            src={imageUrl}
            alt={`Слайд ${playerState.currentSlide + 1}`}
            className="absolute inset-0 w-full h-full object-contain"
            style={{
              transform: `translate(${imageOffset.x}px, ${imageOffset.y}px) scale(${scale.x})`,
              transformOrigin: 'top left',
            }}
          />
        )}

        {/* Visual effects overlay */}
        <div className="absolute inset-0 pointer-events-none" style={{ width: '100%', height: '100%' }}>
          <VisualEffectsEngine
            manifest={vfxManifest}
            audioElement={audioRef.current}
            preferredRenderer="auto"
            debug={import.meta.env.DEV}
            slideScale={scale}
            slideOffset={imageOffset}
            slideDimensions={slideDimensions}
          />
        </div>

        {/* VFX Debug Info */}
        {import.meta.env.DEV && (
          <div className="absolute top-2 left-2 bg-black/80 text-white p-2 text-xs rounded z-50 font-mono">
            <div>VFX: {vfxManifest ? '✅ OK' : '❌ NO MANIFEST'}</div>
            {vfxManifest && (
              <>
                <div>Effects: {vfxManifest.effects?.length || 0}</div>
                <div>Events: {vfxManifest.timeline?.events?.length || 0}</div>
                <div>Version: {vfxManifest.version || 'N/A'}</div>
              </>
            )}
          </div>
        )}

        {/* Slide number indicator */}
        <div className="absolute bottom-4 right-4 bg-black/70 text-white px-3 py-1 rounded-md text-sm font-medium">
          {playerState.currentSlide + 1} / {manifest?.slides.length || 0}
        </div>
      </div>

      {/* Audio element */}
      {audioUrl && (
        <audio
          ref={audioRef}
          src={audioUrl}
          onTimeUpdate={handleTimeUpdate}
          onEnded={handleAudioEnded}
          onPlay={handlePlay}
          onPause={handlePause}
          className="hidden"
        />
      )}
    </>
  );
};
