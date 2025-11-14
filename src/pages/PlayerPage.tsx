import React from 'react';
import { useParams } from 'react-router-dom';
import { PlayerProvider, usePlayer } from '@/components/Player/PlayerContext';
import { SlideViewer } from '@/components/Player/SlideViewer';
import { PlayerControls } from '@/components/Player/PlayerControls';
import { Card } from '@/components/ui/card';

/**
 * PlayerPage - Individual Lesson Player
 * 
 * This page loads and plays a single lesson with visual effects support.
 * Uses the new PlayerContext system with SlideViewer that includes VisualEffectsEngine.
 */
export const PlayerPage: React.FC = () => {
  const { lessonId } = useParams<{ lessonId: string }>();

  // 🔥 DEBUG: Confirm PlayerPage is loading
  console.log('🎬 [PlayerPage] Component loaded!');
  console.log('🎬 [PlayerPage] Lesson ID from params:', lessonId);

  if (!lessonId) {
    console.error('❌ [PlayerPage] No lesson ID provided!');
    return (
      <div className="container mx-auto p-6">
        <Card className="p-8 text-center">
          <h2 className="text-2xl font-bold text-destructive mb-4">
            Ошибка
          </h2>
          <p className="text-muted-foreground">
            ID урока не указан
          </p>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <PlayerProvider lessonId={lessonId}>
        <PlayerPageContent />
      </PlayerProvider>
    </div>
  );
};

/**
 * PlayerPageContent - Inner component that uses PlayerContext
 */
const PlayerPageContent: React.FC = () => {
  const { manifest, loading, error } = usePlayer();

  console.log('[PlayerPageContent] Render:', { hasManifest: !!manifest, loading, error });

  if (loading) {
    return (
      <Card className="p-8 text-center">
        <div className="flex flex-col items-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          <p className="text-muted-foreground">Загрузка презентации...</p>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-8 text-center">
        <h2 className="text-2xl font-bold text-destructive mb-4">
          Ошибка загрузки
        </h2>
        <p className="text-muted-foreground">{error}</p>
      </Card>
    );
  }

  if (!manifest) {
    return (
      <Card className="p-8 text-center">
        <p className="text-muted-foreground">Манифест не найден</p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Slide Display with Visual Effects */}
      <Card className="overflow-hidden">
        <SlideViewer />
      </Card>

      {/* Player Controls */}
      <PlayerControls />
    </div>
  );
};

export default PlayerPage;
