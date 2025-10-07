import React, { createContext, useContext, useState, useRef, ReactNode } from 'react';
import { Manifest } from '@/lib/api';

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
  // State management
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

  const [scale, setScale] = useState({ x: 1, y: 1 });
  const [slideDimensions, setSlideDimensions] = useState({ width: 1920, height: 1080 });
  const [imageOffset, setImageOffset] = useState({ x: 0, y: 0 });

  // Refs
  const audioRef = useRef<HTMLAudioElement>(null);
  const slideRef = useRef<HTMLDivElement>(null);
  const animationRef = useRef<number>();

  // Player control methods
  const play = () => {
    if (audioRef.current) {
      audioRef.current.play();
      setPlayerState(prev => ({ ...prev, isPlaying: true }));
    }
  };

  const pause = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      setPlayerState(prev => ({ ...prev, isPlaying: false }));
    }
  };

  const togglePlayPause = () => {
    if (playerState.isPlaying) {
      pause();
    } else {
      play();
    }
  };

  const nextSlide = () => {
    if (!manifest) return;
    const nextIndex = Math.min(playerState.currentSlide + 1, manifest.slides.length - 1);
    goToSlide(nextIndex);
  };

  const prevSlide = () => {
    const prevIndex = Math.max(playerState.currentSlide - 1, 0);
    goToSlide(prevIndex);
  };

  const goToSlide = (slideIndex: number) => {
    if (!manifest || !audioRef.current) return;
    
    const slide = manifest.slides[slideIndex];
    if (!slide) return;

    // Find first cue of the slide
    const firstCue = slide.cues[0];
    if (firstCue) {
      audioRef.current.currentTime = firstCue.start;
    }
    
    setPlayerState(prev => ({ 
      ...prev, 
      currentSlide: slideIndex,
      currentTime: firstCue?.start || 0
    }));
  };

  const setVolumeControl = (volume: number) => {
    if (audioRef.current) {
      audioRef.current.volume = volume;
      setPlayerState(prev => ({ ...prev, volume }));
    }
  };

  const setPlaybackRateControl = (rate: number) => {
    if (audioRef.current) {
      audioRef.current.playbackRate = rate;
      setPlayerState(prev => ({ ...prev, playbackRate: rate }));
    }
  };

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
