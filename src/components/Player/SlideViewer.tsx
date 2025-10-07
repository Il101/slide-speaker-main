import React, { useEffect, useCallback } from 'react';
import { usePlayer } from './PlayerContext';
import { calculateScale } from './utils/scaleCalculations';
import { AdvancedEffectRenderer } from '@/components/AdvancedEffects';

export const SlideViewer: React.FC = () => {
  const {
    manifest,
    playerState,
    slideRef,
    scale,
    setScale,
    slideDimensions,
    imageOffset,
    setImageOffset,
  } = usePlayer();

  const currentSlide = manifest?.slides[playerState.currentSlide];
  const imageUrl = currentSlide?.image 
    ? `${import.meta.env.VITE_API_BASE || 'http://localhost:8000'}${currentSlide.image}`
    : '';

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

  return (
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
      <div className="absolute inset-0 pointer-events-none">
        <AdvancedEffectRenderer
          cues={currentSlide.cues}
          elements={currentSlide.elements}
          currentTime={playerState.currentTime}
          scale={scale}
          offset={imageOffset}
        />
      </div>

      {/* Slide number indicator */}
      <div className="absolute bottom-4 right-4 bg-black/70 text-white px-3 py-1 rounded-md text-sm font-medium">
        {playerState.currentSlide + 1} / {manifest?.slides.length || 0}
      </div>
    </div>
  );
};
