import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Play, Pause, SkipBack, SkipForward, Repeat, Loader2, ListVideo, Check } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { playlistApi } from '@/lib/playlistApi';
import type { Playlist, PlaylistItem } from '@/types/playlist';
import { Player } from '@/components/Player';

export const PlaylistPlayerPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const [playlist, setPlaylist] = useState<Playlist | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loopEnabled, setLoopEnabled] = useState(false);
  const [viewTracked, setViewTracked] = useState(false);

  useEffect(() => {
    if (id) {
      loadPlaylist();
    }
  }, [id]);

  // Track view on mount
  useEffect(() => {
    if (playlist && !viewTracked) {
      trackView(0);
      setViewTracked(true);
    }
  }, [playlist]);

  // Track progress when moving to next video
  useEffect(() => {
    if (playlist && viewTracked) {
      trackView(currentIndex + 1);
    }
  }, [currentIndex]);

  const loadPlaylist = async () => {
    if (!id) return;

    try {
      setLoading(true);
      const data = await playlistApi.get(id);
      setPlaylist(data);
    } catch (error: any) {
      console.error('Failed to load playlist:', error);
      toast.error(error.message || 'Не удалось загрузить плейлист');
      navigate('/playlists');
    } finally {
      setLoading(false);
    }
  };

  const trackView = async (videosWatched: number) => {
    if (!id || !playlist) return;

    try {
      const completed = videosWatched >= playlist.items.length;
      await playlistApi.trackView(id, {
        videos_watched: videosWatched,
        completed,
      });
    } catch (error) {
      console.error('Failed to track view:', error);
    }
  };

  const handleNext = () => {
    if (!playlist) return;

    if (currentIndex < playlist.items.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else if (loopEnabled) {
      setCurrentIndex(0);
      toast.success('Плейлист начат с начала');
    } else {
      toast.info('Конец плейлиста');
    }
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  const handleJumpTo = (index: number) => {
    setCurrentIndex(index);
  };

  const formatDuration = (seconds?: number): string => {
    if (!seconds) return '—';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!playlist || playlist.items.length === 0) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Card className="p-8 text-center">
          <ListVideo className="h-16 w-16 mx-auto text-muted-foreground/50 mb-4" />
          <h2 className="text-xl font-semibold mb-2">Плейлист пуст</h2>
          <p className="text-muted-foreground mb-4">
            В этом плейлисте нет видео
          </p>
          <Button onClick={() => navigate('/playlists')}>
            Вернуться к плейлистам
          </Button>
        </Card>
      </div>
    );
  }

  const currentItem = playlist.items[currentIndex];

  return (
    <div className="flex h-screen bg-background">
      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="border-b p-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">{playlist.title}</h1>
              <p className="text-sm text-muted-foreground">
                Видео {currentIndex + 1} из {playlist.items.length}
              </p>
            </div>
            <Button variant="ghost" onClick={() => navigate('/playlists')}>
              <ChevronLeft className="h-4 w-4 mr-2" />
              К плейлистам
            </Button>
          </div>
        </div>

        {/* Player */}
        <div className="flex-1 flex items-center justify-center bg-black">
          <Player
            lessonId={currentItem.lesson_id}
            onExportMP4={() => {}}
          />
        </div>

        {/* Controls */}
        <div className="border-t p-4 bg-card">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handlePrevious}
                disabled={currentIndex === 0}
              >
                <SkipBack className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleNext}
                disabled={!loopEnabled && currentIndex === playlist.items.length - 1}
              >
                <SkipForward className="h-4 w-4" />
              </Button>
            </div>

            <div>
              <Button
                variant={loopEnabled ? 'default' : 'outline'}
                size="sm"
                onClick={() => setLoopEnabled(!loopEnabled)}
              >
                <Repeat className="h-4 w-4 mr-2" />
                Повтор
              </Button>
            </div>
          </div>

          <div className="text-sm">
            <h3 className="font-semibold">{currentItem.lesson_title}</h3>
            <p className="text-muted-foreground">
              {formatDuration(currentItem.lesson_duration)}
            </p>
          </div>
        </div>
      </div>

      {/* Sidebar - Playlist Items */}
      <div className="w-80 border-l flex flex-col">
        <div className="p-4 border-b">
          <h2 className="font-semibold flex items-center gap-2">
            <ListVideo className="h-5 w-5" />
            Плейлист
          </h2>
        </div>

        <ScrollArea className="flex-1">
          <div className="p-2">
            {playlist.items.map((item, index) => (
              <Card
                key={item.id}
                className={`mb-2 cursor-pointer transition-colors ${
                  index === currentIndex
                    ? 'border-primary bg-primary/5'
                    : 'hover:bg-muted/50'
                }`}
                onClick={() => handleJumpTo(index)}
              >
                <CardContent className="p-3">
                  <div className="flex gap-3">
                    {/* Thumbnail or Index */}
                    <div className="flex-shrink-0">
                      {item.lesson_thumbnail ? (
                        <img
                          src={item.lesson_thumbnail}
                          alt={item.lesson_title}
                          className="w-20 h-14 object-cover rounded"
                        />
                      ) : (
                        <div className="w-20 h-14 bg-muted rounded flex items-center justify-center">
                          <span className="text-lg font-bold text-muted-foreground">
                            {index + 1}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <h4 className="font-medium text-sm line-clamp-2 flex-1">
                          {item.lesson_title}
                        </h4>
                        {index === currentIndex && (
                          <Badge variant="default" className="flex-shrink-0">
                            <Play className="h-3 w-3" />
                          </Badge>
                        )}
                        {index < currentIndex && (
                          <Check className="h-4 w-4 text-green-500 flex-shrink-0" />
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        {formatDuration(item.lesson_duration)}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </ScrollArea>
      </div>
    </div>
  );
};

export default PlaylistPlayerPage;
