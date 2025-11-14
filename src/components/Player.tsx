import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Play, Pause, SkipBack, SkipForward, Volume2, Settings, Download, Edit3, Eye, EyeOff, AlertTriangle, ChevronLeft, ChevronRight } from 'lucide-react';
import { TooltipProvider, Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { PlayerState, EditingState, SlideElement } from '@/types/player';
import { apiClient, Manifest, SlidePatch, LessonPatchRequest } from '@/lib/api';
import { ElementEditor } from '@/components/ElementEditor';

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
    editingElement: null,
    showSubtitles: false,
    dimOthers: false
  });

  // Scale-aware state
  const [scale, setScale] = useState({ x: 1, y: 1 });
  // 🔥 FIX: Get real slide dimensions from manifest metadata instead of hardcoded 1920x1080
  const [slideDimensions, setSlideDimensions] = useState({ width: 1920, height: 1080 });
  const [imageOffset, setImageOffset] = useState({ x: 0, y: 0 });
  
  // Swipe gesture state
  const [touchStart, setTouchStart] = useState<number | null>(null);
  const [touchEnd, setTouchEnd] = useState<number | null>(null);
  const [swipeDirection, setSwipeDirection] = useState<'left' | 'right' | null>(null);

  const audioRef = useRef<HTMLAudioElement>(null);
  const slideRef = useRef<HTMLDivElement>(null);
  const animationRef = useRef<number>();
  
  // Minimum swipe distance (in px)
  const minSwipeDistance = 50;

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

  // Загружаем manifest при монтировании компонента
  useEffect(() => {
    const loadManifest = async () => {
      try {
        setLoading(true);
        const data = await apiClient.getManifest(lessonId);
        setManifest(data);
        
        // 🔥 FIX: Extract real slide dimensions from manifest metadata
        if (data.metadata?.slide_width && data.metadata?.slide_height) {
          const realDimensions = {
            width: data.metadata.slide_width,
            height: data.metadata.slide_height
          };
          setSlideDimensions(realDimensions);
          console.log('[Player] 📐 Using real slide dimensions from manifest:', realDimensions);
        } else {
          console.warn('[Player] ⚠️ No slide dimensions in manifest metadata, using default 1920x1080');
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

  // Event handlers
  const startEditingElement = useCallback((element: SlideElement) => {
    setEditingState(prev => ({
      ...prev,
      isEditing: true,
      editingElement: element
    }));
  }, []);

  const cancelEditing = useCallback(() => {
    setEditingState(prev => ({
      ...prev,
      isEditing: false,
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
        if (currentSlide && currentSlide.duration && currentTime >= currentSlide.duration) {
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

  // Swipe handlers
  const handleTouchStart = (e: React.TouchEvent) => {
    setTouchEnd(null);
    setTouchStart(e.targetTouches[0].clientX);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    setTouchEnd(e.targetTouches[0].clientX);
  };

  const handleTouchEnd = () => {
    if (!touchStart || !touchEnd) return;
    
    const distance = touchStart - touchEnd;
    const isLeftSwipe = distance > minSwipeDistance;
    const isRightSwipe = distance < -minSwipeDistance;

    if (isLeftSwipe) {
      setSwipeDirection('left');
      setTimeout(() => setSwipeDirection(null), 300);
      changeSlide('next');
    } else if (isRightSwipe) {
      setSwipeDirection('right');
      setTimeout(() => setSwipeDirection(null), 300);
      changeSlide('prev');
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
    <TooltipProvider delayDuration={300}>
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
            onTouchStart={handleTouchStart}
            onTouchMove={handleTouchMove}
            onTouchEnd={handleTouchEnd}
          >
          {/* Swipe indicator */}
          {swipeDirection && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/20 pointer-events-none z-20">
              {swipeDirection === 'left' ? (
                <ChevronRight className="h-16 w-16 text-white animate-pulse" />
              ) : (
                <ChevronLeft className="h-16 w-16 text-white animate-pulse" />
              )}
            </div>
          )}
          
          {/* Lazy loading placeholder */}
          {!imageUrl && (
            <div 
              className="absolute inset-0 bg-gray-200 flex items-center justify-center"
              aria-label="Loading slide"
            >
            <div className="text-gray-500">Loading slide...</div>
          </div>
          )}
          {renderElementOverlays()}
        </div>        {/* Slide Counter */}
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

          {/* Mobile Controls (touch-friendly) */}
          <div className="md:hidden">
            <div className="flex items-center justify-center space-x-4 mb-4">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="outline"
                    className="h-14 w-14 touch-target button-press"
                    onClick={() => changeSlide('prev')}
                    disabled={playerState.currentSlide === 0}
                    aria-label="Предыдущий слайд"
                  >
                    <SkipBack className="h-6 w-6" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Предыдущий слайд</p>
                  <kbd className="ml-2 text-xs">←</kbd>
                </TooltipContent>
              </Tooltip>
              
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    className="h-16 w-16 touch-target button-press"
                    onClick={togglePlayPause}
                    variant="gradient-glow"
                    aria-label={playerState.isPlaying ? "Пауза" : "Воспроизвести"}
                  >
                    {playerState.isPlaying ? <Pause className="h-8 w-8" /> : <Play className="h-8 w-8" />}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>{playerState.isPlaying ? "Пауза" : "Воспроизвести"}</p>
                  <kbd className="ml-2 text-xs">Space</kbd>
                </TooltipContent>
              </Tooltip>
              
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="outline"
                    className="h-14 w-14 touch-target button-press"
                    onClick={() => changeSlide('next')}
                    disabled={playerState.currentSlide === manifest.slides.length - 1}
                    aria-label="Следующий слайд"
                  >
                    <SkipForward className="h-6 w-6" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Следующий слайд</p>
                  <kbd className="ml-2 text-xs">→</kbd>
                </TooltipContent>
              </Tooltip>
            </div>
            <p className="text-xs text-center text-muted-foreground mb-4">
              Свайп влево/вправо для переключения слайдов
            </p>
          </div>

          {/* Desktop Controls */}
          <div className="hidden md:flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="outline"
                    size="icon"
                    className="button-press"
                    onClick={() => changeSlide('prev')}
                    disabled={playerState.currentSlide === 0}
                    aria-label="Previous slide"
                  >
                    <SkipBack className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Предыдущий слайд</p>
                  <kbd className="ml-2 text-xs">←</kbd>
                </TooltipContent>
              </Tooltip>
              
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    size="icon"
                    className="button-press"
                    onClick={togglePlayPause}
                    variant="gradient-glow"
                    aria-label={playerState.isPlaying ? "Pause" : "Play"}
                  >
                    {playerState.isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>{playerState.isPlaying ? "Пауза" : "Воспроизвести"}</p>
                  <kbd className="ml-2 text-xs">Space</kbd>
                </TooltipContent>
              </Tooltip>
              
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="outline"
                    size="icon"
                    className="button-press"
                    onClick={() => changeSlide('next')}
                    disabled={playerState.currentSlide === manifest.slides.length - 1}
                    aria-label="Next slide"
                  >
                    <SkipForward className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Следующий слайд</p>
                  <kbd className="ml-2 text-xs">→</kbd>
                </TooltipContent>
              </Tooltip>
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
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant={editingState.isEditing ? "default" : "outline"}
                    onClick={() => setEditingState(prev => ({ ...prev, isEditing: !prev.isEditing }))}
                    className="flex items-center space-x-2 button-press"
                    aria-label={editingState.isEditing ? "Exit edit mode" : "Enter edit mode"}
                    aria-pressed={editingState.isEditing}
                  >
                    <Edit3 className="h-4 w-4" aria-hidden="true" />
                    <span className="hidden lg:inline">{editingState.isEditing ? 'Exit Edit' : 'Edit'}</span>
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>{editingState.isEditing ? "Выйти из режима редактирования" : "Редактировать синхронизацию"}</p>
                  <kbd className="ml-2 text-xs">E</kbd>
                </TooltipContent>
              </Tooltip>

              {/* Subtitles Toggle */}
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant={editingState.showSubtitles ? "default" : "outline"}
                    onClick={() => setEditingState(prev => ({ ...prev, showSubtitles: !prev.showSubtitles }))}
                    className="flex items-center space-x-2 button-press"
                    aria-label={editingState.showSubtitles ? "Hide subtitles" : "Show subtitles"}
                    aria-pressed={editingState.showSubtitles}
                  >
                    {editingState.showSubtitles ? <EyeOff className="h-4 w-4" aria-hidden="true" /> : <Eye className="h-4 w-4" aria-hidden="true" />}
                    <span className="hidden lg:inline">Subtitles</span>
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>{editingState.showSubtitles ? "Скрыть субтитры" : "Показать субтитры"}</p>
                </TooltipContent>
              </Tooltip>

              {/* Dim Others Toggle */}
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant={editingState.dimOthers ? "default" : "outline"}
                    onClick={() => setEditingState(prev => ({ ...prev, dimOthers: !prev.dimOthers }))}
                    className="flex items-center space-x-2 button-press"
                    aria-label={editingState.dimOthers ? "Show all elements" : "Dim other elements"}
                    aria-pressed={editingState.dimOthers}
                  >
                    <Settings className="h-4 w-4" aria-hidden="true" />
                    <span className="hidden lg:inline">Dim Others</span>
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>{editingState.dimOthers ? "Показать все элементы" : "Затемнить другие элементы"}</p>
                </TooltipContent>
              </Tooltip>

              {/* Export Button */}
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button 
                    variant="outline"
                    onClick={onExportMP4}
                    className="flex items-center space-x-2 button-press"
                    aria-label="Export lesson as MP4 video"
                  >
                    <Download className="h-4 w-4" aria-hidden="true" />
                    <span className="hidden lg:inline">Export MP4</span>
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Экспортировать как MP4 видео</p>
                </TooltipContent>
              </Tooltip>
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

      {/* Element Editor */}
      {editingState.editingElement && (
        <ElementEditor
          element={editingState.editingElement}
          onSave={saveElementEdit}
          onCancel={cancelEditing}
        />
      )}
      </div>
    </TooltipProvider>
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