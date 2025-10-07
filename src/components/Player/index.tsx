import React from 'react';
import { Loader2, AlertTriangle, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { PlayerProvider, usePlayer } from './PlayerContext';
import { usePlayerData } from './hooks/usePlayerData';
import { useAudioSync } from './hooks/useAudioSync';
import { useKeyboardControls } from './hooks/useKeyboardControls';
import { PlayerControls } from './PlayerControls';
import { SlideViewer } from './SlideViewer';

interface PlayerProps {
  lessonId: string;
  onExportMP4?: () => void;
}

const PlayerContent: React.FC<PlayerProps> = ({ lessonId, onExportMP4 }) => {
  const { manifest, loading, error, audioRef } = usePlayer();
  
  // Load player data
  usePlayerData(lessonId);
  
  // Setup audio synchronization
  useAudioSync();
  
  // Setup keyboard controls
  useKeyboardControls();

  // Calculate total duration
  const totalDuration = manifest?.slides.reduce((total, slide) => {
    const lastCue = slide.cues[slide.cues.length - 1];
    return Math.max(total, lastCue?.t1 || 0);
  }, 0) || 0;

  // Get audio URL from first slide (assuming combined audio)
  const audioUrl = manifest?.slides[0]?.audio
    ? `${import.meta.env.VITE_API_BASE || 'http://localhost:8000'}${manifest.slides[0].audio}`
    : '';

  if (loading) {
    return (
      <Card className="flex flex-col items-center justify-center h-96 p-8">
        <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
        <p className="text-muted-foreground">Загрузка лекции...</p>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="flex flex-col items-center justify-center h-96 p-8">
        <AlertTriangle className="h-12 w-12 text-destructive mb-4" />
        <h3 className="text-lg font-semibold mb-2">Ошибка загрузки</h3>
        <p className="text-muted-foreground text-center mb-4">{error}</p>
        <Button onClick={() => window.location.reload()}>
          Попробовать снова
        </Button>
      </Card>
    );
  }

  if (!manifest) {
    return (
      <Card className="flex flex-col items-center justify-center h-96 p-8">
        <AlertTriangle className="h-12 w-12 text-muted-foreground mb-4" />
        <p className="text-muted-foreground">Данные лекции не найдены</p>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Hidden audio element */}
      <audio
        ref={audioRef}
        src={audioUrl}
        preload="auto"
        className="hidden"
      />

      {/* Slide viewer */}
      <SlideViewer />

      {/* Player controls */}
      <PlayerControls totalDuration={totalDuration} />

      {/* Export button */}
      {onExportMP4 && (
        <div className="flex justify-end">
          <Button
            variant="outline"
            onClick={onExportMP4}
            className="flex items-center space-x-2"
          >
            <Download className="h-4 w-4" />
            <span>Экспорт в MP4</span>
          </Button>
        </div>
      )}

      {/* Slide list - можно добавить позже */}
      {/* <div className="hidden lg:block">
        <VirtualizedSlideList
          slides={manifest.slides}
          currentSlide={playerState.currentSlide}
          onSlideSelect={goToSlide}
        />
      </div> */}
    </div>
  );
};

export const Player: React.FC<PlayerProps> = (props) => {
  return (
    <PlayerProvider lessonId={props.lessonId}>
      <PlayerContent {...props} />
    </PlayerProvider>
  );
};

// Export for backward compatibility
export default Player;
