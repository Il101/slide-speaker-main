import React from 'react';
import { Play, Pause, SkipBack, SkipForward, Volume2, VolumeX, Settings } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { usePlayer } from './PlayerContext';
import { formatTime } from './utils/timeFormatting';

interface PlayerControlsProps {
  totalDuration?: number;
}

export const PlayerControls: React.FC<PlayerControlsProps> = ({ totalDuration = 0 }) => {
  const {
    playerState,
    manifest,
    togglePlayPause,
    nextSlide,
    prevSlide,
    setVolume,
    setPlaybackRate,
    audioRef,
  } = usePlayer();

  // Get duration from audio element or use totalDuration prop
  const duration = audioRef.current?.duration || totalDuration || 0;
  const currentSlideNumber = playerState.currentSlide + 1;
  const totalSlides = manifest?.slides.length || 0;

  const handleSeek = (value: number[]) => {
    if (audioRef.current) {
      audioRef.current.currentTime = value[0];
    }
  };

  const handleVolumeChange = (value: number[]) => {
    setVolume(value[0]);
  };

  const toggleMute = () => {
    setVolume(playerState.volume > 0 ? 0 : 1);
  };

  return (
    <div className="bg-card border border-border rounded-lg p-4 sm:p-6 space-y-4">
      {/* Progress bar */}
      <div className="space-y-2">
        <Slider
          value={[playerState.currentTime]}
          max={duration || 100}
          step={0.1}
          onValueChange={handleSeek}
          className="w-full"
          aria-label="Прогресс воспроизведения"
        />
        <div className="flex justify-between text-sm text-muted-foreground">
          <span>{formatTime(playerState.currentTime)}</span>
          <span>{formatTime(duration)}</span>
        </div>
      </div>

      {/* Main controls */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Playback buttons */}
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="icon"
            onClick={prevSlide}
            aria-label="Предыдущий слайд"
          >
            <SkipBack className="h-4 w-4" />
          </Button>
          
          <Button
            variant="default"
            size="icon"
            className="h-12 w-12"
            onClick={togglePlayPause}
            aria-label={playerState.isPlaying ? 'Пауза' : 'Воспроизвести'}
          >
            {playerState.isPlaying ? (
              <Pause className="h-5 w-5" />
            ) : (
              <Play className="h-5 w-5" />
            )}
          </Button>
          
          <Button
            variant="outline"
            size="icon"
            onClick={nextSlide}
            aria-label="Следующий слайд"
          >
            <SkipForward className="h-4 w-4" />
          </Button>
        </div>

        {/* Volume control */}
        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleMute}
            aria-label={playerState.volume === 0 ? 'Включить звук' : 'Выключить звук'}
          >
            {playerState.volume === 0 ? (
              <VolumeX className="h-4 w-4" />
            ) : (
              <Volume2 className="h-4 w-4" />
            )}
          </Button>
          
          <div className="w-24 hidden sm:block">
            <Slider
              value={[playerState.volume]}
              max={1}
              step={0.01}
              onValueChange={handleVolumeChange}
              aria-label="Громкость"
            />
          </div>

          {/* Playback speed */}
          <Select
            value={playerState.playbackRate.toString()}
            onValueChange={(value) => setPlaybackRate(parseFloat(value))}
          >
            <SelectTrigger className="w-20">
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
        </div>
      </div>

      {/* Keyboard shortcuts hint */}
      <div className="text-xs text-muted-foreground text-center pt-2 border-t">
        <kbd className="px-2 py-1 bg-muted rounded">Space</kbd> - Пауза/Воспроизведение
        {' • '}
        <kbd className="px-2 py-1 bg-muted rounded">←</kbd>
        <kbd className="px-2 py-1 bg-muted rounded">→</kbd> - Навигация
        {' • '}
        <kbd className="px-2 py-1 bg-muted rounded">M</kbd> - Звук
      </div>
    </div>
  );
};
