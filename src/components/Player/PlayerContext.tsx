import React, { createContext, useContext, useState, useRef, ReactNode, useEffect, useCallback } from 'react';
import { Manifest, apiClient } from '@/lib/api';
import { toast } from 'sonner';

export interface PlayerState {
  isPlaying: boolean;
  currentSlide: number;
  currentTime: number;
  playbackRate: number;
  volume: number;
}

export interface EditingState {
  isEditing: boolean;
  editingCue: any | null;
  editingElement: any | null;
  showSubtitles: boolean;
  dimOthers: boolean;
}

interface PlayerContextType {
  // State
  manifest: Manifest | null;
  setManifest: (manifest: Manifest | null) => void;
  loading: boolean;
  setLoading: (loading: boolean) => void;
  error: string | null;
  setError: (error: string | null) => void;
  
  // Player state
  playerState: PlayerState;
  setPlayerState: React.Dispatch<React.SetStateAction<PlayerState>>;
  
  // Editing state
  editingState: EditingState;
  setEditingState: React.Dispatch<React.SetStateAction<EditingState>>;
  
  // Scale and dimensions
  scale: { x: number; y: number };
  setScale: React.Dispatch<React.SetStateAction<{ x: number; y: number }>>;
  slideDimensions: { width: number; height: number };
  setSlideDimensions: React.Dispatch<React.SetStateAction<{ width: number; height: number }>>;
  imageOffset: { x: number; y: number };
  setImageOffset: React.Dispatch<React.SetStateAction<{ x: number; y: number }>>;
  
  // Refs
  audioRef: React.RefObject<HTMLAudioElement>;
  slideRef: React.RefObject<HTMLDivElement>;
  animationRef: React.MutableRefObject<number | undefined>;
  
  // Methods
  play: () => void;
  pause: () => void;
  togglePlayPause: () => void;
  nextSlide: () => void;
  prevSlide: () => void;
  goToSlide: (slideIndex: number) => void;
  setVolume: (volume: number) => void;
  setPlaybackRate: (rate: number) => void;
}

const PlayerContext = createContext<PlayerContextType | undefined>(undefined);

interface PlayerProviderProps {
  children: ReactNode;
  lessonId: string;
}

export const PlayerProvider: React.FC<PlayerProviderProps> = ({ children, lessonId }) => {
  // 🔥 DEBUG: Log provider initialization
  console.log('[PlayerProvider] Initializing with lessonId:', lessonId);

  // State management
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [playerState, setPlayerStateInternal] = useState<PlayerState>({
    isPlaying: false,
    currentSlide: 0,
    currentTime: 0,
    playbackRate: 1,
    volume: 1
  });

  // 🔥 DEBUG: Wrap setPlayerState to track who's calling it
  // IMPORTANT: Don't use useCallback here - it creates a new function on every render!
  const setPlayerStateRef = useRef<React.Dispatch<React.SetStateAction<PlayerState>>>();
  const playerStateRef = useRef<PlayerState>(playerState);
  playerStateRef.current = playerState;
  setPlayerStateRef.current = setPlayerStateInternal;
  
  const setPlayerState: React.Dispatch<React.SetStateAction<PlayerState>> = useCallback((update) => {
    const stack = new Error().stack;
    const caller = stack?.split('\n')[2]?.trim();
    
    // Calculate what actually changed
    const prevState = playerStateRef.current;
    const nextState = typeof update === 'function' ? update(prevState) : update;
    
    console.log('[PlayerContext] 🔄 setPlayerState called from:', caller, {
      changes: {
        isPlaying: prevState.isPlaying !== nextState.isPlaying ? `${prevState.isPlaying} → ${nextState.isPlaying}` : 'unchanged',
        currentSlide: prevState.currentSlide !== nextState.currentSlide ? `${prevState.currentSlide} → ${nextState.currentSlide}` : 'unchanged',
        currentTime: prevState.currentTime !== nextState.currentTime ? `${prevState.currentTime.toFixed(2)} → ${nextState.currentTime.toFixed(2)}` : 'unchanged',
        playbackRate: prevState.playbackRate !== nextState.playbackRate ? `${prevState.playbackRate} → ${nextState.playbackRate}` : 'unchanged',
        volume: prevState.volume !== nextState.volume ? `${prevState.volume} → ${nextState.volume}` : 'unchanged',
      }
    });
    
    setPlayerStateRef.current?.(update);
  }, []); // ✅ Empty deps - function never recreated

  const [editingState, setEditingState] = useState<EditingState>({
    isEditing: false,
    editingCue: null,
    editingElement: null,
    showSubtitles: false,
    dimOthers: false
  });

  const [scale, setScale] = useState({ x: 1, y: 1 });
  const [slideDimensions, setSlideDimensions] = useState({ width: 1920, height: 1080 });
  const [imageOffset, setImageOffset] = useState({ x: 0, y: 0 });

  // Refs
  const audioRef = useRef<HTMLAudioElement>(null);
  const slideRef = useRef<HTMLDivElement>(null);
  const animationRef = useRef<number>();

  // 🔥 Load manifest on mount
  useEffect(() => {
    console.log('[PlayerProvider] useEffect triggered - loading manifest for:', lessonId);
    
    const loadManifest = async () => {
      try {
        setLoading(true);
        setError(null);
        console.log('[PlayerProvider] Fetching manifest from API...');
        
        const data = await apiClient.getManifest(lessonId);
        
        console.log('[PlayerProvider] ✅ Manifest loaded:', {
          slides: data.slides?.length || 0,
          hasVFX: data.slides?.[0]?.visual_effects_manifest ? 'YES' : 'NO'
        });
        
        setManifest(data);
        toast.success('Презентация загружена');
      } catch (err) {
        console.error('[PlayerProvider] ❌ Failed to load manifest:', err);
        const errorMessage = err instanceof Error ? err.message : 'Не удалось загрузить презентацию';
        setError(errorMessage);
        toast.error(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    loadManifest();
  }, [lessonId]);

  // Player control functions
  const play = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.play().catch(err => {
        console.error('Failed to play audio:', err);
        toast.error('Ошибка воспроизведения аудио');
      });
      setPlayerState(prev => ({ ...prev, isPlaying: true }));
    }
  }, []);

  const pause = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      setPlayerState(prev => ({ ...prev, isPlaying: false }));
    }
  }, []);

  const togglePlayPause = useCallback(() => {
    if (playerState.isPlaying) {
      pause();
    } else {
      play();
    }
  }, [playerState.isPlaying, pause, play]);  const goToSlide = useCallback((slideIndex: number) => {
    if (!manifest) return;
    
    const slide = manifest.slides[slideIndex];
    if (!slide) return;

    // Find first cue of the slide and get its start time
    const firstCue = slide.cues[0];
    const targetTime = firstCue?.t0 ?? 0;

    // Safely set audio time (fix race condition)
    if (audioRef.current) {
      try {
        audioRef.current.currentTime = targetTime;
      } catch (err) {
        console.error('Failed to seek audio:', err);
      }
    }
    
    setPlayerState(prev => ({ 
      ...prev, 
      currentSlide: slideIndex,
      currentTime: targetTime
    }));
  }, [manifest]);

  const nextSlide = useCallback(() => {
    if (!manifest) return;
    const nextIndex = Math.min(playerState.currentSlide + 1, manifest.slides.length - 1);
    goToSlide(nextIndex);
  }, [manifest, playerState.currentSlide, goToSlide]);

  const prevSlide = useCallback(() => {
    const prevIndex = Math.max(playerState.currentSlide - 1, 0);
    goToSlide(prevIndex);
  }, [playerState.currentSlide, goToSlide]);

  const setVolumeControl = useCallback((volume: number) => {
    if (audioRef.current) {
      audioRef.current.volume = volume;
      setPlayerState(prev => ({ ...prev, volume }));
    }
  }, []);

  const setPlaybackRateControl = useCallback((rate: number) => {
    if (audioRef.current) {
      audioRef.current.playbackRate = rate;
      setPlayerState(prev => ({ ...prev, playbackRate: rate }));
    }
  }, []);

  // 🔥 FIX: Don't memoize the context value - let it update naturally
  // Memoization with frequently changing state creates more problems than it solves
  // React Context will only trigger re-renders in components that actually USE the context
  const value: PlayerContextType = {
    manifest,
    setManifest,
    loading,
    setLoading,
    error,
    setError,
    playerState,
    setPlayerState,
    editingState,
    setEditingState,
    scale,
    setScale,
    slideDimensions,
    setSlideDimensions,
    imageOffset,
    setImageOffset,
    audioRef,
    slideRef,
    animationRef,
    play,
    pause,
    togglePlayPause,
    nextSlide,
    prevSlide,
    goToSlide,
    setVolume: setVolumeControl,
    setPlaybackRate: setPlaybackRateControl,
  };

  return (
    <PlayerContext.Provider value={value}>
      {children}
    </PlayerContext.Provider>
  );
};

export const usePlayer = (): PlayerContextType => {
  const context = useContext(PlayerContext);
  if (context === undefined) {
    throw new Error('usePlayer must be used within a PlayerProvider');
  }
  return context;
};
