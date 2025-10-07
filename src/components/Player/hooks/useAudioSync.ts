import { useEffect, useCallback } from 'react';
import { usePlayer } from '../PlayerContext';

export const useAudioSync = () => {
  const { 
    audioRef, 
    manifest, 
    playerState, 
    setPlayerState, 
    animationRef 
  } = usePlayer();

  // Update current time and slide based on audio position
  const updateCurrentSlide = useCallback((currentTime: number) => {
    if (!manifest) return;

    let newSlide = playerState.currentSlide;
    
    // Find the slide that should be displayed at current time
    for (let i = 0; i < manifest.slides.length; i++) {
      const slide = manifest.slides[i];
      const slideStartTime = slide.cues[0]?.t0 || 0;
      const slideEndTime = slide.cues[slide.cues.length - 1]?.t1 || 0;
      
      if (currentTime >= slideStartTime && currentTime <= slideEndTime) {
        newSlide = i;
        break;
      }
    }

    if (newSlide !== playerState.currentSlide) {
      setPlayerState(prev => ({ ...prev, currentSlide: newSlide }));
    }
  }, [manifest, playerState.currentSlide, setPlayerState]);

  // Animation loop for syncing
  const syncLoop = useCallback(() => {
    if (audioRef.current && playerState.isPlaying) {
      const currentTime = audioRef.current.currentTime;
      setPlayerState(prev => ({ ...prev, currentTime }));
      updateCurrentSlide(currentTime);
    }
    
    if (playerState.isPlaying) {
      animationRef.current = requestAnimationFrame(syncLoop);
    }
  }, [audioRef, playerState.isPlaying, setPlayerState, updateCurrentSlide, animationRef]);

  // Start/stop sync loop
  useEffect(() => {
    if (playerState.isPlaying) {
      animationRef.current = requestAnimationFrame(syncLoop);
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
  }, [playerState.isPlaying, syncLoop, animationRef]);

  // Audio event handlers
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handlePlay = () => {
      setPlayerState(prev => ({ ...prev, isPlaying: true }));
    };

    const handlePause = () => {
      setPlayerState(prev => ({ ...prev, isPlaying: false }));
    };

    const handleTimeUpdate = () => {
      const currentTime = audio.currentTime;
      setPlayerState(prev => ({ ...prev, currentTime }));
      updateCurrentSlide(currentTime);
    };

    const handleEnded = () => {
      setPlayerState(prev => ({ ...prev, isPlaying: false, currentTime: 0 }));
    };

    audio.addEventListener('play', handlePlay);
    audio.addEventListener('pause', handlePause);
    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('ended', handleEnded);

    return () => {
      audio.removeEventListener('play', handlePlay);
      audio.removeEventListener('pause', handlePause);
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('ended', handleEnded);
    };
  }, [audioRef, setPlayerState, updateCurrentSlide]);
};
