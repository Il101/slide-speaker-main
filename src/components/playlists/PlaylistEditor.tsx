import React, { useState, useEffect } from 'react';
import { GripVertical, X, Plus, Loader2, Save, ListVideo } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';
import { playlistApi } from '@/lib/playlistApi';
import { apiClient } from '@/lib/api';
import type { Playlist, PlaylistItem, PlaylistUpdateRequest } from '@/types/playlist';

interface VideoItemForSelection {
  lesson_id: string;
  title: string;
  thumbnail_url: string | null;
  duration: number | null;
}

interface PlaylistEditorProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  playlistId: string | null;
  onSuccess?: () => void;
}

export const PlaylistEditor: React.FC<PlaylistEditorProps> = ({
  open,
  onOpenChange,
  playlistId,
  onSuccess,
}) => {
  const [playlist, setPlaylist] = useState<Playlist | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [isPublic, setIsPublic] = useState(false);
  const [password, setPassword] = useState('');
  const [items, setItems] = useState<PlaylistItem[]>([]);
  const [availableVideos, setAvailableVideos] = useState<VideoItemForSelection[]>([]);
  const [draggedItem, setDraggedItem] = useState<PlaylistItem | null>(null);

  useEffect(() => {
    if (open && playlistId) {
      loadPlaylist();
      loadAvailableVideos();
    }
  }, [open, playlistId]);

  const loadPlaylist = async () => {
    if (!playlistId) return;

    try {
      setLoading(true);
      const data = await playlistApi.get(playlistId);
      setPlaylist(data);
      setTitle(data.title);
      setDescription(data.description || '');
      setIsPublic(data.is_public);
      setItems(data.items);
    } catch (error: any) {
      console.error('Failed to load playlist:', error);
      toast.error(error.message || 'Не удалось загрузить плейлист');
    } finally {
      setLoading(false);
    }
  };

  const loadAvailableVideos = async () => {
    try {
      const response = await apiClient.getUserVideos();
      const videos = response.videos
        .filter((v: any) => v.status === 'completed')
        .map((v: any) => ({
          lesson_id: v.lesson_id,
          title: v.title,
          thumbnail_url: v.thumbnail_url,
          duration: v.duration,
        }));
      setAvailableVideos(videos);
    } catch (error) {
      console.error('Failed to load videos:', error);
    }
  };

  const handleSave = async () => {
    if (!playlistId) return;

    if (!title.trim()) {
      toast.error('Введите название плейлиста');
      return;
    }

    try {
      setSaving(true);

      // Update metadata
      const updateData: PlaylistUpdateRequest = {
        title,
        description: description || undefined,
        is_public: isPublic,
        password: password || undefined,
      };

      await playlistApi.update(playlistId, updateData);

      // Reorder items if changed
      const originalItems = playlist?.items || [];
      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        const originalItem = originalItems.find((oi) => oi.id === item.id);
        if (!originalItem || originalItem.order_index !== i) {
          await playlistApi.reorder(playlistId, item.id, i);
        }
      }

      toast.success('Плейлист обновлен');
      onSuccess?.();
      onOpenChange(false);
    } catch (error: any) {
      console.error('Failed to save playlist:', error);
      toast.error(error.message || 'Не удалось сохранить плейлист');
    } finally {
      setSaving(false);
    }
  };

  const handleRemoveItem = async (itemId: string) => {
    if (!playlistId) return;

    try {
      await playlistApi.removeVideo(playlistId, itemId);
      setItems(items.filter((item) => item.id !== itemId));
      toast.success('Видео удалено из плейлиста');
    } catch (error: any) {
      console.error('Failed to remove video:', error);
      toast.error(error.message || 'Не удалось удалить видео');
    }
  };

  const handleAddVideo = async (video: VideoItemForSelection) => {
    if (!playlistId) return;

    try {
      const updated = await playlistApi.addVideos(playlistId, [video.lesson_id]);
      setItems(updated.items);
      toast.success('Видео добавлено в плейлист');
    } catch (error: any) {
      console.error('Failed to add video:', error);
      if (error.message?.includes('already in playlist')) {
        toast.warning('Это видео уже в плейлисте');
      } else {
        toast.error(error.message || 'Не удалось добавить видео');
      }
    }
  };

  // Drag and Drop handlers
  const handleDragStart = (e: React.DragEvent, item: PlaylistItem) => {
    setDraggedItem(item);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent, targetItem: PlaylistItem) => {
    e.preventDefault();
    if (!draggedItem || draggedItem.id === targetItem.id) return;

    const draggedIdx = items.findIndex((item) => item.id === draggedItem.id);
    const targetIdx = items.findIndex((item) => item.id === targetItem.id);

    if (draggedIdx === targetIdx) return;

    const newItems = [...items];
    newItems.splice(draggedIdx, 1);
    newItems.splice(targetIdx, 0, draggedItem);

    setItems(newItems);
  };

  const handleDragEnd = () => {
    setDraggedItem(null);
  };

  const formatDuration = (seconds?: number): string => {
    if (!seconds) return '—';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Filter available videos (exclude already added)
  const addedLessonIds = new Set(items.map((item) => item.lesson_id));
  const videosToAdd = availableVideos.filter(
    (video) => !addedLessonIds.has(video.lesson_id)
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[800px] max-h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <ListVideo className="h-5 w-5" />
            Редактировать плейлист
          </DialogTitle>
          <DialogDescription>
            Измените название, порядок видео и настройки плейлиста
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : (
          <>
            <ScrollArea className="flex-1 pr-4">
              <div className="space-y-6 py-4">
                {/* Metadata */}
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="title">Название *</Label>
                    <Input
                      id="title"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      placeholder="Введите название плейлиста"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="description">Описание</Label>
                    <Textarea
                      id="description"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="Добавьте описание (необязательно)"
                      rows={3}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label htmlFor="is-public">Публичный плейлист</Label>
                      <p className="text-xs text-muted-foreground">
                        Разрешить доступ по ссылке
                      </p>
                    </div>
                    <Switch
                      id="is-public"
                      checked={isPublic}
                      onCheckedChange={setIsPublic}
                    />
                  </div>

                  {isPublic && (
                    <div className="space-y-2">
                      <Label htmlFor="password">Пароль (необязательно)</Label>
                      <Input
                        id="password"
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Оставьте пустым для открытого доступа"
                      />
                      <p className="text-xs text-muted-foreground">
                        Защитите плейлист паролем для ограничения доступа
                      </p>
                    </div>
                  )}
                </div>

                <Separator />

                {/* Playlist Items */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label>Видео в плейлисте ({items.length})</Label>
                    <p className="text-xs text-muted-foreground">
                      Перетащите для изменения порядка
                    </p>
                  </div>

                  {items.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <p>Нет видео в плейлисте</p>
                      <p className="text-xs mt-1">
                        Добавьте видео из списка ниже
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {items.map((item, index) => (
                        <div
                          key={item.id}
                          draggable
                          onDragStart={(e) => handleDragStart(e, item)}
                          onDragOver={(e) => handleDragOver(e, item)}
                          onDragEnd={handleDragEnd}
                          className={`flex items-center gap-3 p-3 rounded-lg border bg-card cursor-move transition-colors ${
                            draggedItem?.id === item.id ? 'opacity-50' : ''
                          } hover:bg-muted/50`}
                        >
                          <GripVertical className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                          <div className="w-8 h-8 rounded bg-muted flex items-center justify-center flex-shrink-0 text-sm font-medium">
                            {index + 1}
                          </div>
                          {item.lesson_thumbnail ? (
                            <img
                              src={item.lesson_thumbnail}
                              alt={item.lesson_title}
                              className="w-16 h-12 object-cover rounded flex-shrink-0"
                            />
                          ) : (
                            <div className="w-16 h-12 bg-muted rounded flex items-center justify-center flex-shrink-0">
                              <ListVideo className="h-6 w-6 text-muted-foreground" />
                            </div>
                          )}
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-sm line-clamp-1">
                              {item.lesson_title}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {formatDuration(item.lesson_duration)}
                            </p>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRemoveItem(item.id)}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <Separator />

                {/* Available Videos */}
                {videosToAdd.length > 0 && (
                  <div className="space-y-3">
                    <Label>Доступные видео ({videosToAdd.length})</Label>
                    <div className="space-y-2">
                      {videosToAdd.map((video) => (
                        <div
                          key={video.lesson_id}
                          className="flex items-center gap-3 p-3 rounded-lg border bg-card"
                        >
                          {video.thumbnail_url ? (
                            <img
                              src={video.thumbnail_url}
                              alt={video.title}
                              className="w-16 h-12 object-cover rounded flex-shrink-0"
                            />
                          ) : (
                            <div className="w-16 h-12 bg-muted rounded flex items-center justify-center flex-shrink-0">
                              <ListVideo className="h-6 w-6 text-muted-foreground" />
                            </div>
                          )}
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-sm line-clamp-1">
                              {video.title}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {formatDuration(video.duration)}
                            </p>
                          </div>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleAddVideo(video)}
                          >
                            <Plus className="h-4 w-4 mr-1" />
                            Добавить
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>

            <DialogFooter>
              <Button variant="outline" onClick={() => onOpenChange(false)}>
                Отмена
              </Button>
              <Button onClick={handleSave} disabled={saving || !title.trim()}>
                {saving ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Сохранение...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Сохранить
                  </>
                )}
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
};
