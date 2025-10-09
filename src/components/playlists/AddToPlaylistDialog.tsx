import React, { useState, useEffect } from 'react';
import { Loader2, Plus, Check, ListPlus } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { toast } from 'sonner';
import { playlistApi } from '@/lib/playlistApi';
import type { PlaylistListItem } from '@/types/playlist';

interface AddToPlaylistDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  lessonIds: string[];
  onSuccess?: () => void;
}

export const AddToPlaylistDialog: React.FC<AddToPlaylistDialogProps> = ({
  open,
  onOpenChange,
  lessonIds,
  onSuccess,
}) => {
  const [playlists, setPlaylists] = useState<PlaylistListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [adding, setAdding] = useState(false);
  const [creating, setCreating] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newPlaylistTitle, setNewPlaylistTitle] = useState('');

  useEffect(() => {
    if (open) {
      loadPlaylists();
    }
  }, [open]);

  const loadPlaylists = async () => {
    try {
      setLoading(true);
      const data = await playlistApi.getAll();
      setPlaylists(data);
    } catch (error) {
      console.error('Failed to load playlists:', error);
      toast.error('Не удалось загрузить плейлисты');
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePlaylist = async () => {
    if (!newPlaylistTitle.trim()) {
      toast.error('Введите название плейлиста');
      return;
    }

    try {
      setCreating(true);
      await playlistApi.create({
        title: newPlaylistTitle,
        lesson_ids: lessonIds,
      });
      toast.success('Плейлист создан');
      setNewPlaylistTitle('');
      setShowCreateForm(false);
      onSuccess?.();
      onOpenChange(false);
    } catch (error: any) {
      console.error('Failed to create playlist:', error);
      toast.error(error.message || 'Не удалось создать плейлист');
    } finally {
      setCreating(false);
    }
  };

  const handleAddToPlaylist = async (playlistId: string) => {
    try {
      setAdding(true);
      await playlistApi.addVideos(playlistId, lessonIds);
      toast.success('Добавлено в плейлист');
      onSuccess?.();
      onOpenChange(false);
    } catch (error: any) {
      console.error('Failed to add to playlist:', error);
      if (error.message?.includes('already in playlist')) {
        toast.warning('Некоторые видео уже в плейлисте');
      } else {
        toast.error(error.message || 'Не удалось добавить в плейлист');
      }
    } finally {
      setAdding(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <ListPlus className="h-5 w-5" />
            Добавить в плейлист
          </DialogTitle>
          <DialogDescription>
            {lessonIds.length === 1
              ? 'Выберите плейлист или создайте новый'
              : `Добавить ${lessonIds.length} видео в плейлист`}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Create New Playlist Button */}
          <Button
            variant="outline"
            className="w-full"
            onClick={() => setShowCreateForm(!showCreateForm)}
          >
            <Plus className="h-4 w-4 mr-2" />
            Создать новый плейлист
          </Button>

          {/* Create Form */}
          {showCreateForm && (
            <div className="flex gap-2">
              <Input
                placeholder="Название плейлиста"
                value={newPlaylistTitle}
                onChange={(e) => setNewPlaylistTitle(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleCreatePlaylist();
                  }
                }}
                disabled={creating}
              />
              <Button
                onClick={handleCreatePlaylist}
                disabled={creating || !newPlaylistTitle.trim()}
              >
                {creating ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Check className="h-4 w-4" />
                )}
              </Button>
            </div>
          )}

          {/* Playlists List */}
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : playlists.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <p>У вас пока нет плейлистов</p>
              <p className="text-sm mt-1">Создайте первый плейлист выше</p>
            </div>
          ) : (
            <ScrollArea className="h-[300px] pr-4">
              <div className="space-y-2">
                {playlists.map((playlist) => (
                  <Button
                    key={playlist.id}
                    variant="ghost"
                    className="w-full justify-start h-auto p-3"
                    onClick={() => handleAddToPlaylist(playlist.id)}
                    disabled={adding}
                  >
                    <div className="flex items-start gap-3 w-full">
                      {playlist.thumbnail_url ? (
                        <img
                          src={playlist.thumbnail_url}
                          alt={playlist.title}
                          className="w-16 h-12 object-cover rounded"
                        />
                      ) : (
                        <div className="w-16 h-12 bg-muted rounded flex items-center justify-center">
                          <ListPlus className="h-6 w-6 text-muted-foreground" />
                        </div>
                      )}
                      <div className="flex-1 text-left">
                        <p className="font-medium">{playlist.title}</p>
                        <p className="text-sm text-muted-foreground">
                          {playlist.video_count} видео
                          {playlist.total_duration && (
                            <> · {Math.round(playlist.total_duration / 60)} мин</>
                          )}
                        </p>
                      </div>
                    </div>
                  </Button>
                ))}
              </div>
            </ScrollArea>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};
