import { useEffect } from 'react';
import { usePlayer } from '../PlayerContext';

export const useKeyboardControls = () => {
  const { 
    togglePlayPause, 
    nextSlide, 
    prevSlide, 
    setVolume, 
    playerState 
  } = usePlayer();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't handle if user is typing in an input/textarea
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      switch (e.key.toLowerCase()) {
        case ' ':
        case 'k':
          e.preventDefault();
          togglePlayPause();
          break;
        
        case 'arrowright':
        case 'l':
          e.preventDefault();
          nextSlide();
          break;
        
        case 'arrowleft':
        case 'j':
          e.preventDefault();
          prevSlide();
          break;
        
        case 'arrowup':
          e.preventDefault();
          setVolume(Math.min(playerState.volume + 0.1, 1));
          break;
        
        case 'arrowdown':
          e.preventDefault();
          setVolume(Math.max(playerState.volume - 0.1, 0));
          break;
        
        case 'm':
          e.preventDefault();
          setVolume(playerState.volume > 0 ? 0 : 1);
          break;
        
        default:
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [togglePlayPause, nextSlide, prevSlide, setVolume, playerState.volume]);
};
