import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { Play, Pause, SkipBack, SkipForward, Volume2, Settings, Download, Edit3, Eye, EyeOff, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { PlayerState, EditingState, Cue, SlideElement } from '@/types/player';
import { apiClient, Manifest, Slide, CuePatch, ElementPatch, SlidePatch, LessonPatchRequest } from '@/lib/api';
import { CueEditor } from '@/components/CueEditor';
import { ElementEditor } from '@/components/ElementEditor';
import { AdvancedEffectRenderer } from '@/components/AdvancedEffects';

// Simplified lazy loading hook
const useLazyImage = (src: string) => {
  const [imageSrc, setImageSrc] = useState<string | null>(null);
  const [imageRef, setImageRef] = useState<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!imageRef || !src) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setImageSrc(src);
          observer.unobserve(entry.target);
        }
      },
      { rootMargin: '50px' }
    );

    observer.observe(imageRef);

    return () => {
      if (imageRef) {
        observer.unobserve(imageRef);
      }
    };
  }, [imageRef, src]);

  return [imageSrc, setImageRef] as const;
};

interface PlayerProps {
  lessonId: string;
  onExportMP4: () => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

class PlayerErrorBoundary extends React.Component<
  React.PropsWithChildren<{}>,
  ErrorBoundaryState
> {
  constructor(props: React.PropsWithChildren<{}>) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Player Error Boundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
            <h2 className="text-lg font-semibold text-destructive mb-2">
              Ошибка воспроизведения
            </h2>
            <p className="text-muted-foreground text-sm mb-4">
              Произошла ошибка при загрузке плеера. Попробуйте обновить страницу.
            </p>
            <Button
              onClick={() => window.location.reload()}
              variant="outline"
            >
              Обновить страницу
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export const Player: React.FC<PlayerProps> = ({ lessonId, onExportMP4 }) => {
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [playerState, setPlayerState] = useState<PlayerState>({
    isPlaying: false,
    currentSlide: 0,
    currentTime: 0,
    playbackRate: 1,
    volume: 1
  });

  const [editingState, setEditingState] = useState<EditingState>({
    isEditing: false,
    editingCue: null,
    editingElement: null,
    showSubtitles: false,
    dimOthers: false
  });

  // Scale-aware state
  const [scale, setScale] = useState({ x: 1, y: 1 });
  const [slideDimensions, setSlideDimensions] = useState({ width: 1920, height: 1080 });
  const [imageOffset, setImageOffset] = useState({ x: 0, y: 0 });

  const audioRef = useRef<HTMLAudioElement>(null);
  const slideRef = useRef<HTMLDivElement>(null);
  const animationRef = useRef<number>();

  // Simplified image loading without lazy loading for now
  const currentSlideImageSrc = manifest?.slides[playerState.currentSlide]?.image || '';
  const imageUrl = currentSlideImageSrc ? `${import.meta.env.VITE_API_BASE || 'http://localhost:8000'}${currentSlideImageSrc}` : '';

  // Calculate scale and offset based on container and slide dimensions
  const calculateScale = useCallback(() => {
    if (!slideRef.current) return { x: 1, y: 1 };
    
    const container = slideRef.current;
    const containerRect = container.getBoundingClientRect();
    
    // Get container dimensions (aspect-video = 16:9)
    const containerWidth = containerRect.width;
    const containerHeight = containerRect.height;
    
    // Calculate scale factors maintaining aspect ratio
    const scaleX = containerWidth / slideDimensions.width;
    const scaleY = containerHeight / slideDimensions.height;
    
    // Use uniform scaling to maintain aspect ratio (like background-size: contain)
    const uniformScale = Math.min(scaleX, scaleY);
    
    // Ensure minimum scale to prevent elements from becoming too small
    const minScale = 0.1;
    const finalScale = Math.max(uniformScale, minScale);
    
    // Calculate image dimensions after scaling
    const scaledImageWidth = slideDimensions.width * finalScale;
    const scaledImageHeight = slideDimensions.height * finalScale;
    
    // Calculate offset for centering (like background-position: center)
    const offsetX = (containerWidth - scaledImageWidth) / 2;
    const offsetY = (containerHeight - scaledImageHeight) / 2;
    
    // Update offset state
    setImageOffset({ x: Math.max(0, offsetX), y: Math.max(0, offsetY) });
    
    return { x: finalScale, y: finalScale };
  }, [slideDimensions]);

  // Update scale when container size changes
  useEffect(() => {
    let timeoutId: NodeJS.Timeout;
    
    const updateScale = () => {
      // Debounce scale updates to avoid excessive recalculations
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        const newScale = calculateScale();
        setScale(newScale);
      }, 100);
    };

    // Initial calculation
    updateScale();

    // Listen for window resize
    const handleResize = () => {
      updateScale();
    };

    window.addEventListener('resize', handleResize);
    
    // Also listen for container size changes
    const resizeObserver = new ResizeObserver(updateScale);
    if (slideRef.current) {
      resizeObserver.observe(slideRef.current);
    }

    return () => {
      clearTimeout(timeoutId);
      window.removeEventListener('resize', handleResize);
      resizeObserver.disconnect();
    };
  }, [slideDimensions, calculateScale]);

  // Easing function for smooth laser movement
  const easeInOutQuad = (t: number): number => {
    return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
  };

  // Загружаем manifest при монтировании компонента
  useEffect(() => {
    const loadManifest = async () => {
      try {
        setLoading(true);
        const data = await apiClient.getManifest(lessonId);
        setManifest(data);
        
        // Load slide dimensions from manifest
        const currentSlide = data.slides[playerState.currentSlide];
        if (currentSlide && currentSlide.width && currentSlide.height) {
          setSlideDimensions({ width: currentSlide.width, height: currentSlide.height });
        } else if (data.metadata?.slide_width && data.metadata?.slide_height) {
          setSlideDimensions({ width: data.metadata.slide_width, height: data.metadata.slide_height });
        }
        
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load lesson');
      } finally {
        setLoading(false);
      }
    };

    loadManifest();
  }, [lessonId]);

  // Animation effect for playing state
  useEffect(() => {
    if (playerState.isPlaying) {
      const updateTime = () => {
        if (audioRef.current) {
          setPlayerState(prev => ({
            ...prev,
            currentTime: audioRef.current!.currentTime
          }));
        }
        animationRef.current = requestAnimationFrame(updateTime);
      };
      animationRef.current = requestAnimationFrame(updateTime);
    } else {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [playerState.isPlaying]);

  // Memoized slide effects calculation with support for both old cues and new visual_cues
  const renderSlideEffects = useMemo(() => {
    if (!manifest || !manifest.slides[playerState.currentSlide] || !slideRef.current) return null;
    
    const currentSlide = manifest.slides[playerState.currentSlide];
    const effects = [];
    
    // Render traditional cues (for backward compatibility)
    if (currentSlide.cues) {
      currentSlide.cues.forEach((cue, index) => {
        const isActive = playerState.currentTime >= cue.t0 && playerState.currentTime <= cue.t1;
        const isEditing = editingState.editingCue?.cue_id === cue.cue_id;
        
        // Show all cues when editing, active cues when playing
        if (!isActive && !isEditing && !editingState.isEditing) return;

        if (cue.action === 'highlight' && cue.bbox) {
          const [x, y, width, height] = cue.bbox;
          const scaledX = x * scale.x + imageOffset.x;
          const scaledY = y * scale.y + imageOffset.y;
          const scaledWidth = width * scale.x;
          const scaledHeight = height * scale.y;
          
          effects.push(
            <div
              key={`highlight-${index}`}
              className={`absolute border-2 rounded transition-all duration-300 ${
                isActive 
                  ? 'bg-yellow-300 bg-opacity-50 border-yellow-500' 
                  : isEditing 
                  ? 'bg-blue-300 bg-opacity-50 border-blue-500' 
                  : 'bg-gray-300 bg-opacity-30 border-gray-400'
              } ${editingState.isEditing ? 'cursor-pointer hover:bg-opacity-70' : ''}`}
              style={{
                left: `${scaledX}px`,
                top: `${scaledY}px`,
                width: `${scaledWidth}px`,
                height: `${scaledHeight}px`
              }}
              onClick={() => editingState.isEditing && startEditingCue(cue)}
              data-testid="highlight"
            >
              {editingState.isEditing && (
                <div className="absolute -top-6 left-0 bg-blue-500 text-white text-xs px-1 rounded">
                  {cue.t0.toFixed(1)}s - {cue.t1.toFixed(1)}s
                </div>
              )}
            </div>
          );
        }

        if (cue.action === 'underline' && cue.bbox) {
          const [x, y, width, height] = cue.bbox;
          const scaledX = x * scale.x + imageOffset.x;
          const scaledY = y * scale.y + imageOffset.y;
          const scaledWidth = width * scale.x;
          const scaledHeight = height * scale.y;
          
          effects.push(
            <div
              key={`underline-${index}`}
              className={`absolute border-b-2 transition-all duration-300 ${
                isActive 
                  ? 'border-red-500' 
                  : isEditing 
                  ? 'border-blue-500' 
                  : 'border-gray-400'
              } ${editingState.isEditing ? 'cursor-pointer' : ''}`}
              style={{
                left: `${scaledX}px`,
                top: `${scaledY + scaledHeight - 2}px`,
                width: `${scaledWidth}px`,
                height: '2px'
              }}
              onClick={() => editingState.isEditing && startEditingCue(cue)}
            >
              {editingState.isEditing && (
                <div className="absolute -top-6 left-0 bg-blue-500 text-white text-xs px-1 rounded">
                  {cue.t0.toFixed(1)}s - {cue.t1.toFixed(1)}s
                </div>
              )}
            </div>
          );
        }

        if (cue.action === 'laser_move' && cue.to) {
          const [x, y] = cue.to;
          const scaledX = x * scale.x + imageOffset.x;
          const scaledY = y * scale.y + imageOffset.y;
          
          effects.push(
            <div
              key={`laser-${index}`}
              className={`absolute w-2 h-2 rounded-full transition-all duration-300 ${
                isActive 
                  ? 'bg-red-500 shadow-lg shadow-red-500' 
                  : isEditing 
                  ? 'bg-blue-500' 
                  : 'bg-gray-400'
              } ${editingState.isEditing ? 'cursor-pointer' : ''}`}
              style={{
                left: `${scaledX - 4}px`,
                top: `${scaledY - 4}px`,
                transform: isActive ? 'scale(1.5)' : 'scale(1)'
              }}
              onClick={() => editingState.isEditing && startEditingCue(cue)}
            >
              {editingState.isEditing && (
                <div className="absolute -top-6 left-0 bg-blue-500 text-white text-xs px-1 rounded">
                  {cue.t0.toFixed(1)}s - {cue.t1.toFixed(1)}s
                </div>
              )}
            </div>
          );
        }
      });
    }
    
    // Render new visual_cues based on talk_track timing
    if (currentSlide.visual_cues && currentSlide.talk_track) {
      currentSlide.visual_cues.forEach((visualCue, index) => {
        const targetElement = currentSlide.elements.find(el => el.id === visualCue.targetId);
        if (!targetElement) {
          console.warn(`Target element ${visualCue.targetId} not found for visual cue`);
          return;
        }
        
        // Find corresponding talk track segment
        const talkSegment = currentSlide.talk_track.find(segment => segment.kind === visualCue.at);
        if (!talkSegment) return;
        
        // Estimate timing based on talk track position (simplified)
        const segmentIndex = currentSlide.talk_track.indexOf(talkSegment);
        const estimatedStartTime = segmentIndex * 10; // 10 seconds per segment
        const estimatedEndTime = estimatedStartTime + 8; // 8 seconds duration
        
        const isActive = playerState.currentTime >= estimatedStartTime && playerState.currentTime <= estimatedEndTime;
        
        if (isActive || editingState.isEditing) {
          const [x, y, width, height] = targetElement.bbox;
          const scaledX = x * scale.x + imageOffset.x;
          const scaledY = y * scale.y + imageOffset.y;
          const scaledWidth = width * scale.x;
          const scaledHeight = height * scale.y;
          
          effects.push(
            <div
              key={`visual-cue-${index}`}
              className={`absolute border-2 rounded transition-all duration-300 ${
                isActive 
                  ? 'bg-green-300 bg-opacity-50 border-green-500' 
                  : 'bg-gray-300 bg-opacity-30 border-gray-400'
              }`}
              style={{
                left: `${scaledX}px`,
                top: `${scaledY}px`,
                width: `${scaledWidth}px`,
                height: `${scaledHeight}px`
              }}
            >
              {editingState.isEditing && (
                <div className="absolute -top-6 left-0 bg-green-500 text-white text-xs px-1 rounded">
                  {visualCue.at} ({estimatedStartTime.toFixed(1)}s)
                </div>
              )}
            </div>
          );
        }
      });
    }
    
    // ✅ Render advanced effects (ken_burns, typewriter, particle_highlight, etc.)
    if (currentSlide.cues) {
      const advancedEffectTypes = [
        'ken_burns', 'typewriter', 'particle_highlight', 'slide_in',
        'fade_in', 'pulse', 'circle_draw', 'arrow_point', 'shake', 'morph'
      ];
      
      currentSlide.cues.forEach((cue, index) => {
        const isActive = playerState.currentTime >= cue.t0 && playerState.currentTime <= cue.t1;
        const effectType = cue.effect_type || cue.action;
        
        if (advancedEffectTypes.includes(effectType) && (isActive || editingState.isEditing)) {
          // Get slide text for typewriter effect
          const slideText = currentSlide.elements
            .map(el => el.text)
            .join(' ');
          
          effects.push(
            <AdvancedEffectRenderer
              key={`advanced-effect-${index}`}
              cue={cue}
              active={isActive}
              text={slideText}
            />
          );
        }
      });
    }
    
    return effects;
  }, [manifest, playerState.currentSlide, playerState.currentTime, editingState, scale]);

  // Event handlers
  const startEditingCue = useCallback((cue: Cue) => {
    setEditingState(prev => ({
      ...prev,
      isEditing: true,
      editingCue: cue,
      editingElement: null
    }));
  }, []);

  const startEditingElement = useCallback((element: SlideElement) => {
    setEditingState(prev => ({
      ...prev,
      isEditing: true,
      editingCue: null,
      editingElement: element
    }));
  }, []);

  const cancelEditing = useCallback(() => {
    setEditingState(prev => ({
      ...prev,
      isEditing: false,
      editingCue: null,
      editingElement: null
    }));
  }, []);

  const togglePlayPause = useCallback(() => {
    if (audioRef.current) {
      if (playerState.isPlaying) {
        audioRef.current.pause();
        setPlayerState(prev => ({ ...prev, isPlaying: false }));
      } else {
        audioRef.current.play();
        setPlayerState(prev => ({ ...prev, isPlaying: true }));
      }
    }
  }, [playerState.isPlaying]);

  const handleTimeUpdate = useCallback(() => {
    if (audioRef.current) {
      const currentTime = audioRef.current.currentTime;
      setPlayerState(prev => ({ ...prev, currentTime }));
      
      // Check if we need to move to next slide
      if (manifest) {
        const currentSlide = manifest.slides[playerState.currentSlide];
        if (currentSlide && currentTime >= currentSlide.duration) {
          const nextSlide = playerState.currentSlide + 1;
          if (nextSlide < manifest.slides.length) {
            setPlayerState(prev => ({ ...prev, currentSlide: nextSlide }));
          } else {
            // End of presentation
            audioRef.current.pause();
            setPlayerState(prev => ({ ...prev, isPlaying: false }));
          }
        }
      }
    }
  }, [manifest, playerState.currentSlide]);

  const handleVolumeChange = useCallback((volume: number[]) => {
    const newVolume = volume[0];
    setPlayerState(prev => ({ ...prev, volume: newVolume }));
    if (audioRef.current) {
      audioRef.current.volume = newVolume;
    }
  }, []);

  const handlePlaybackRateChange = useCallback((rate: string) => {
    const newRate = parseFloat(rate);
    setPlayerState(prev => ({ ...prev, playbackRate: newRate }));
    if (audioRef.current) {
      audioRef.current.playbackRate = newRate;
    }
  }, []);

  const handleSlideChange = useCallback((slideIndex: number) => {
    if (manifest && slideIndex >= 0 && slideIndex < manifest.slides.length) {
      setPlayerState(prev => ({ ...prev, currentSlide: slideIndex }));
      if (audioRef.current) {
        audioRef.current.currentTime = 0;
      }
    }
  }, [manifest]);

  const handleExportMP4 = useCallback(() => {
    onExportMP4();
  }, [onExportMP4]);

  // Handle loading and error states
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Загрузка лекции...</p>
        </div>
      </div>
    );
  }

  if (error || !manifest) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-destructive mb-4">Ошибка загрузки лекции</p>
          <p className="text-muted-foreground text-sm">{error}</p>
        </div>
      </div>
    );
  }

  const currentSlide = manifest?.slides[playerState.currentSlide];


  const changeSlide = (direction: 'next' | 'prev') => {
    if (!manifest) return;
    
    const newIndex = direction === 'next' 
      ? Math.min(playerState.currentSlide + 1, manifest.slides.length - 1)
      : Math.max(playerState.currentSlide - 1, 0);
    
    setPlayerState(prev => ({ 
      ...prev, 
      currentSlide: newIndex,
      currentTime: 0,
      isPlaying: false
    }));
    
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
  };


  const saveCueEdit = async (editedCue: Cue) => {
    if (!manifest) return;

    try {
      const slidePatch: SlidePatch = {
        slide_id: currentSlide.id,
        cues: [{
          cue_id: editedCue.cue_id,
          t0: editedCue.t0,
          t1: editedCue.t1,
          action: editedCue.action,
          bbox: editedCue.bbox,
          to: editedCue.to,
          element_id: editedCue.element_id
        }]
      };

      const patchRequest: LessonPatchRequest = {
        lesson_id: lessonId,
        slides: [slidePatch]
      };

      await apiClient.patchLesson(lessonId, patchRequest);
      
      // Update local manifest
      setManifest(prev => {
        if (!prev) return prev;
        const updatedSlides = prev.slides.map(slide => {
          if (slide.id === currentSlide.id) {
            const updatedCues = slide.cues.map(cue => 
              cue.cue_id === editedCue.cue_id ? editedCue : cue
            );
            return { ...slide, cues: updatedCues };
          }
          return slide;
        });
        return { ...prev, slides: updatedSlides };
      });

      cancelEditing();
    } catch (error) {
      console.error('Failed to save cue edit:', error);
      alert('Failed to save changes');
    }
  };

  const saveElementEdit = async (editedElement: SlideElement) => {
    if (!manifest) return;

    try {
      const slidePatch: SlidePatch = {
        slide_id: currentSlide.id,
        elements: [{
          element_id: editedElement.id,
          bbox: editedElement.bbox,
          text: editedElement.text,
          confidence: editedElement.confidence
        }]
      };

      const patchRequest: LessonPatchRequest = {
        lesson_id: lessonId,
        slides: [slidePatch]
      };

      await apiClient.patchLesson(lessonId, patchRequest);
      
      // Update local manifest
      setManifest(prev => {
        if (!prev) return prev;
        const updatedSlides = prev.slides.map(slide => {
          if (slide.id === currentSlide.id) {
            const updatedElements = slide.elements.map(element => 
              element.id === editedElement.id ? editedElement : element
            );
            return { ...slide, elements: updatedElements };
          }
          return slide;
        });
        return { ...prev, slides: updatedSlides };
      });

      cancelEditing();
    } catch (error) {
      console.error('Failed to save element edit:', error);
      alert('Failed to save changes');
    }
  };

  const previewCue = (t0: number, t1: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = t0;
      audioRef.current.play();
      
      // Stop at t1
      const stopTime = t1;
      const checkTime = () => {
        if (audioRef.current && audioRef.current.currentTime >= stopTime) {
          audioRef.current.pause();
        } else {
          requestAnimationFrame(checkTime);
        }
      };
      checkTime();
    }
  };


  const renderElementOverlays = () => {
    if (!currentSlide || !editingState.isEditing) return null;

    return currentSlide.elements.map((element, index) => {
      const [x, y, width, height] = element.bbox;
      // Apply scale and offset to coordinates
      const scaledX = x * scale.x + imageOffset.x;
      const scaledY = y * scale.y + imageOffset.y;
      const scaledWidth = width * scale.x;
      const scaledHeight = height * scale.y;
      
      return (
        <div
          key={`element-${index}`}
          className="absolute border-2 border-dashed border-green-500 bg-green-100 bg-opacity-20 cursor-pointer hover:bg-opacity-40 transition-all duration-200"
          style={{
            left: `${scaledX}px`,
            top: `${scaledY}px`,
            width: `${scaledWidth}px`,
            height: `${scaledHeight}px`
          }}
          onClick={() => startEditingElement(element)}
        >
          <div className="absolute -top-6 left-0 bg-green-500 text-white text-xs px-1 rounded">
            {element.text || element.id}
          </div>
        </div>
      );
    });
  };

  return (
    <div className="space-y-6">
      {/* Slide Display */}
      <Card className="relative overflow-hidden card-gradient card-shadow">
        <div 
          ref={slideRef}
          className={`relative w-full aspect-video bg-white rounded-lg ${editingState.dimOthers ? 'opacity-50' : ''}`}
          style={{ 
            backgroundImage: imageUrl ? `url(${imageUrl})` : 'none',
            backgroundSize: 'contain', 
            backgroundRepeat: 'no-repeat', 
            backgroundPosition: 'center' 
          }}
          role="img"
          aria-label={`Slide ${playerState.currentSlide + 1} of ${manifest.slides.length}`}
          aria-live="polite"
          aria-describedby="slide-description"
        >
          {/* Lazy loading placeholder */}
          {!imageUrl && (
            <div 
              className="absolute inset-0 bg-gray-200 flex items-center justify-center"
              aria-label="Loading slide"
            >
              <div className="text-gray-500">Loading slide...</div>
            </div>
          )}
          {renderSlideEffects}
          {renderElementOverlays()}
        </div>
        
        {/* Slide Counter */}
        <div 
          className="absolute top-4 right-4 bg-background/80 backdrop-blur-sm rounded-lg px-3 py-1 text-sm"
          aria-label={`Current slide ${playerState.currentSlide + 1} of ${manifest.slides.length}`}
        >
          {playerState.currentSlide + 1} / {manifest.slides.length}
        </div>
        
        {/* Hidden description for screen readers */}
        <div id="slide-description" className="sr-only">
          {(() => {
            try {
              console.log('Speaker notes type:', typeof currentSlide.speaker_notes, currentSlide.speaker_notes);
              console.log('Speaker notes isArray:', Array.isArray(currentSlide.speaker_notes));
              console.log('Speaker notes constructor:', currentSlide.speaker_notes?.constructor?.name);
              
              if (!currentSlide.speaker_notes) {
                return `Slide ${playerState.currentSlide + 1} content`;
              }
              
              if (Array.isArray(currentSlide.speaker_notes)) {
                // Безопасный вызов map с дополнительной проверкой
                if (currentSlide.speaker_notes.length > 0 && currentSlide.speaker_notes[0] && typeof currentSlide.speaker_notes[0] === 'object' && 'text' in currentSlide.speaker_notes[0]) {
                  return currentSlide.speaker_notes.map(note => note.text).join(' ');
                } else {
                  // Если элементы массива не являются объектами с полем text, преобразуем их в строки
                  return currentSlide.speaker_notes.map(note => String(note)).join(' ');
                }
              }
              
              if (typeof currentSlide.speaker_notes === 'string') {
                return currentSlide.speaker_notes;
              }
              
              return `Slide ${playerState.currentSlide + 1} content`;
            } catch (error) {
              console.error('Error processing speaker notes:', error);
              return `Slide ${playerState.currentSlide + 1} content`;
            }
          })()}
        </div>
      </Card>

      {/* Audio Element */}
      <audio
        ref={audioRef}
        src={`${import.meta.env.VITE_API_BASE || 'http://localhost:8000'}${currentSlide.audio}`}
        onPlay={() => setPlayerState(prev => ({ ...prev, isPlaying: true }))}
        onPause={() => setPlayerState(prev => ({ ...prev, isPlaying: false }))}
        onTimeUpdate={handleTimeUpdate}
        onEnded={() => {
          if (manifest && playerState.currentSlide < manifest.slides.length - 1) {
            changeSlide('next');
          } else {
            setPlayerState(prev => ({ ...prev, isPlaying: false }));
          }
        }}
      />

      {/* Controls */}
      <Card className="p-6 card-gradient">
        <div className="space-y-4">
          {/* Progress Bar */}
          <div className="space-y-2">
            <Slider
              value={[playerState.currentTime]}
              max={audioRef.current?.duration || 0}
              step={0.1}
              onValueChange={([value]) => {
                if (audioRef.current) {
                  audioRef.current.currentTime = value;
                  setPlayerState(prev => ({ ...prev, currentTime: value }));
                }
              }}
              className="w-full"
            />
            <div className="flex justify-between text-sm text-muted-foreground">
              <span>{Math.floor(playerState.currentTime)}s</span>
              <span>{Math.floor(audioRef.current?.duration || 0)}s</span>
            </div>
          </div>

          {/* Main Controls */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button
                variant="outline"
                size="icon"
                onClick={() => changeSlide('prev')}
                disabled={playerState.currentSlide === 0}
                aria-label="Previous slide"
                title="Previous slide"
              >
                <SkipBack className="h-4 w-4" />
              </Button>
              
              <Button
                size="icon"
                onClick={togglePlayPause}
                variant="gradient-glow"
                aria-label={playerState.isPlaying ? "Pause" : "Play"}
                title={playerState.isPlaying ? "Pause" : "Play"}
              >
                {playerState.isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              </Button>
              
              <Button
                variant="outline"
                size="icon"
                onClick={() => changeSlide('next')}
                disabled={playerState.currentSlide === manifest.slides.length - 1}
                aria-label="Next slide"
                title="Next slide"
              >
                <SkipForward className="h-4 w-4" />
              </Button>
            </div>

            <div className="flex items-center space-x-4">
              {/* Volume */}
              <div className="flex items-center space-x-2">
                <Volume2 className="h-4 w-4" aria-hidden="true" />
                <Slider
                  value={[playerState.volume * 100]}
                  max={100}
                  step={1}
                  onValueChange={([value]) => {
                    const volume = value / 100;
                    setPlayerState(prev => ({ ...prev, volume }));
                    if (audioRef.current) {
                      audioRef.current.volume = volume;
                    }
                  }}
                  className="w-20"
                  aria-label="Volume control"
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={playerState.volume * 100}
                />
              </div>

              {/* Playback Speed */}
              <Select
                value={playerState.playbackRate.toString()}
                onValueChange={(value) => {
                  const rate = parseFloat(value);
                  setPlayerState(prev => ({ ...prev, playbackRate: rate }));
                  if (audioRef.current) {
                    audioRef.current.playbackRate = rate;
                  }
                }}
              >
                <SelectTrigger className="w-20" aria-label="Playback speed">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="0.5">0.5x</SelectItem>
                  <SelectItem value="0.75">0.75x</SelectItem>
                  <SelectItem value="1">1x</SelectItem>
                  <SelectItem value="1.25">1.25x</SelectItem>
                  <SelectItem value="1.5">1.5x</SelectItem>
                  <SelectItem value="2">2x</SelectItem>
                </SelectContent>
              </Select>

              {/* Edit Mode Toggle */}
              <Button
                variant={editingState.isEditing ? "default" : "outline"}
                onClick={() => setEditingState(prev => ({ ...prev, isEditing: !prev.isEditing }))}
                className="flex items-center space-x-2"
                aria-label={editingState.isEditing ? "Exit edit mode" : "Enter edit mode"}
                aria-pressed={editingState.isEditing}
              >
                <Edit3 className="h-4 w-4" aria-hidden="true" />
                <span>{editingState.isEditing ? 'Exit Edit' : 'Edit'}</span>
              </Button>

              {/* Subtitles Toggle */}
              <Button
                variant={editingState.showSubtitles ? "default" : "outline"}
                onClick={() => setEditingState(prev => ({ ...prev, showSubtitles: !prev.showSubtitles }))}
                className="flex items-center space-x-2"
                aria-label={editingState.showSubtitles ? "Hide subtitles" : "Show subtitles"}
                aria-pressed={editingState.showSubtitles}
              >
                {editingState.showSubtitles ? <EyeOff className="h-4 w-4" aria-hidden="true" /> : <Eye className="h-4 w-4" aria-hidden="true" />}
                <span>Subtitles</span>
              </Button>

              {/* Dim Others Toggle */}
              <Button
                variant={editingState.dimOthers ? "default" : "outline"}
                onClick={() => setEditingState(prev => ({ ...prev, dimOthers: !prev.dimOthers }))}
                className="flex items-center space-x-2"
                aria-label={editingState.dimOthers ? "Show all elements" : "Dim other elements"}
                aria-pressed={editingState.dimOthers}
              >
                <Settings className="h-4 w-4" aria-hidden="true" />
                <span>Dim Others</span>
              </Button>

              {/* Export Button */}
              <Button 
                variant="outline"
                onClick={onExportMP4}
                className="flex items-center space-x-2"
                aria-label="Export lesson as MP4 video"
              >
                <Download className="h-4 w-4" aria-hidden="true" />
                <span>Export MP4</span>
              </Button>
            </div>
          </div>
        </div>
      </Card>

      {/* Subtitles */}
      {editingState.showSubtitles && (
        <Card className="p-4">
          <div className="text-center">
            <div className="text-lg font-medium text-gray-800">
              {currentSlide.lecture_text ? (
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="text-base leading-relaxed">{currentSlide.lecture_text}</div>
                </div>
              ) : currentSlide.talk_track && currentSlide.talk_track.length > 0 ? (
                <div className="space-y-3">
                  {currentSlide.talk_track.map((segment, index) => (
                    <div key={index} className="p-3 bg-gray-50 rounded-lg">
                      <div className="text-sm text-gray-600 mb-1 font-medium capitalize">
                        {segment.kind}
                      </div>
                      <div className="text-base">{segment.text}</div>
                    </div>
                  ))}
                </div>
              ) : currentSlide.speaker_notes && Array.isArray(currentSlide.speaker_notes) && currentSlide.speaker_notes.length > 0 ? (
                <div className="space-y-2">
                  {currentSlide.speaker_notes.map((note, index) => {
                    // Проверяем, является ли note объектом с полем text
                    if (typeof note === 'object' && note !== null && 'text' in note) {
                      return (
                        <div key={index} className="p-2 bg-gray-50 rounded-lg">
                          <div className="text-sm text-gray-600 mb-1">
                            {note.targetId ? `Target: ${note.targetId}` : 
                             note.target ? `Target: ${note.target.type}` : 'General note'}
                          </div>
                          <div className="text-base">{note.text}</div>
                        </div>
                      );
                    } else {
                      // Если note - это строка или другой тип
                      return (
                        <div key={index} className="p-2 bg-gray-50 rounded-lg">
                          <div className="text-base">{String(note)}</div>
                        </div>
                      );
                    }
                  })}
                </div>
              ) : currentSlide.speaker_notes && typeof currentSlide.speaker_notes === 'string' ? (
                <div className="p-2 bg-gray-50 rounded-lg">
                  <div className="text-base">{currentSlide.speaker_notes}</div>
                </div>
              ) : (
                <div>No lecture text available</div>
              )}
            </div>
          </div>
        </Card>
      )}

      {/* Cue Editor */}
      {editingState.editingCue && (
        <CueEditor
          cue={editingState.editingCue}
          elements={currentSlide.elements}
          audioDuration={audioRef.current?.duration || 0}
          onSave={saveCueEdit}
          onCancel={cancelEditing}
          onPreview={previewCue}
        />
      )}

      {/* Element Editor */}
      {editingState.editingElement && (
        <ElementEditor
          element={editingState.editingElement}
          onSave={saveElementEdit}
          onCancel={cancelEditing}
        />
      )}
    </div>
  );
};

// Export wrapped component with error boundary
export const PlayerWithErrorBoundary: React.FC<PlayerProps> = (props) => {
  return (
    <PlayerErrorBoundary>
      <Player {...props} />
    </PlayerErrorBoundary>
  );
};