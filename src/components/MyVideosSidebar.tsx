import React, { useState, useEffect } from 'react';
import { Play, Clock, FileVideo, Loader2, AlertCircle, Download, Trash2, CheckSquare, Square } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { toast } from 'sonner';
import { apiClient, getImageUrl } from '@/lib/api';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

export interface VideoItem {
  lesson_id: string;
  title: string;
  thumbnail_url: string | null;
  duration: number | null;
  slides_count: number | null;
  status: string;
  created_at: string;
  updated_at: string;
  video_url: string | null;
  video_size: number | null;
  can_play: boolean;
}

interface MyVideosSidebarProps {
  currentLessonId?: string;
  onVideoSelect: (lessonId: string) => void;
  onVideoDownload?: (videoUrl: string, title: string) => void;
}

const formatDuration = (seconds: number | null): string => {
  if (!seconds) return '—';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
};

const formatFileSize = (bytes: number | null): string => {
  if (!bytes) return '—';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'только что';
  if (diffMins < 60) return `${diffMins} мин назад`;
  if (diffHours < 24) return `${diffHours} ч назад`;
  if (diffDays < 7) return `${diffDays} дн назад`;
  
  return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
};

const getStatusBadge = (status: string) => {
  const statusMap: Record<string, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }> = {
    completed: { label: 'Готово', variant: 'default' },
    processing: { label: 'Обработка', variant: 'secondary' },
    failed: { label: 'Ошибка', variant: 'destructive' },
    queued: { label: 'В очереди', variant: 'outline' },
  };

  const statusInfo = statusMap[status] || { label: status, variant: 'outline' };
  return <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>;
};

export const MyVideosSidebar: React.FC<MyVideosSidebarProps> = ({
  currentLessonId,
  onVideoSelect,
  onVideoDownload,
}) => {
  const [videos, setVideos] = useState<VideoItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [videoToDelete, setVideoToDelete] = useState<VideoItem | null>(null);
  const [deleting, setDeleting] = useState(false);
  
  // Состояние для режима выбора
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedVideos, setSelectedVideos] = useState<Set<string>>(new Set());

  const loadVideos = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.getUserVideos();
      setVideos(response.videos);
    } catch (err) {
      console.error('Failed to load videos:', err);
      setError('Не удалось загрузить список видео');
      toast.error('Ошибка загрузки видео');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadVideos();
  }, []);

  const handleVideoClick = (video: VideoItem) => {
    if (selectionMode) {
      // В режиме выбора переключаем выделение
      toggleVideoSelection(video.lesson_id);
    } else {
      // В обычном режиме открываем видео
      if (video.can_play) {
        onVideoSelect(video.lesson_id);
      } else {
        toast.warning('Видео еще обрабатывается');
      }
    }
  };

  const toggleVideoSelection = (lessonId: string) => {
    setSelectedVideos(prev => {
      const newSet = new Set(prev);
      if (newSet.has(lessonId)) {
        newSet.delete(lessonId);
      } else {
        newSet.add(lessonId);
      }
      return newSet;
    });
  };

  const toggleSelectionMode = () => {
    setSelectionMode(!selectionMode);
    if (selectionMode) {
      // Выходим из режима выбора - очищаем выделение
      setSelectedVideos(new Set());
    }
  };

  const selectAll = () => {
    if (selectedVideos.size === videos.length) {
      setSelectedVideos(new Set());
    } else {
      setSelectedVideos(new Set(videos.map(v => v.lesson_id)));
    }
  };

  const handleDeleteSelected = () => {
    if (selectedVideos.size === 0) {
      toast.warning('Выберите видео для удаления');
      return;
    }
    setDeleteDialogOpen(true);
  };

  const handleDownloadClick = (e: React.MouseEvent, video: VideoItem) => {
    e.stopPropagation();
    if (video.video_url && onVideoDownload) {
      onVideoDownload(video.video_url, video.title);
    } else {
      toast.info('Видео еще не экспортировано в MP4');
    }
  };

  const handleDeleteClick = (e: React.MouseEvent, video: VideoItem) => {
    e.stopPropagation();
    setVideoToDelete(video);
    setSelectedVideos(new Set([video.lesson_id]));
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (selectedVideos.size === 0 && !videoToDelete) return;

    try {
      setDeleting(true);
      
      // Удаляем все выбранные видео
      const idsToDelete = selectedVideos.size > 0 
        ? Array.from(selectedVideos) 
        : videoToDelete 
        ? [videoToDelete.lesson_id] 
        : [];

      // Удаляем каждое видео
      await Promise.all(
        idsToDelete.map(id => apiClient.deleteVideo(id))
      );

      // Обновляем список видео
      setVideos(videos.filter(v => !idsToDelete.includes(v.lesson_id)));
      
      toast.success(
        idsToDelete.length === 1 
          ? 'Видео удалено' 
          : `Удалено видео: ${idsToDelete.length}`
      );
      
      setDeleteDialogOpen(false);
      setVideoToDelete(null);
      setSelectedVideos(new Set());
      setSelectionMode(false);
    } catch (err) {
      console.error('Failed to delete video:', err);
      toast.error('Не удалось удалить видео');
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <Card className="h-screen w-full flex flex-col p-6 rounded-lg border-2 border-border/50 shadow-xl bg-gradient-to-br from-background to-muted/20">
        <h2 className="text-2xl font-bold mb-4 bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
          Мои видео
        </h2>
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="h-10 w-10 animate-spin text-muted-foreground" />
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="h-screen w-full flex flex-col p-6 rounded-lg border-2 border-border/50 shadow-xl bg-gradient-to-br from-background to-muted/20">
        <h2 className="text-2xl font-bold mb-4 bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
          Мои видео
        </h2>
        <div className="flex-1 flex flex-col items-center justify-center text-center p-4">
          <AlertCircle className="h-14 w-14 text-destructive mb-3" />
          <p className="text-sm text-muted-foreground mb-4">{error}</p>
          <Button onClick={loadVideos} variant="outline" size="sm">
            Повторить
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <>
      <Card className="h-screen w-full flex flex-col rounded-lg border-2 border-border/50 shadow-xl bg-gradient-to-br from-background to-muted/20">
        {/* Заголовок с кнопками управления */}
        <div className="p-6 border-b-2 border-border/50 flex-shrink-0 bg-gradient-to-r from-primary/5 to-primary/10">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
              Мои видео
            </h2>
            <Badge variant="secondary" className="text-base font-semibold px-3 py-1">
              {videos.length}
            </Badge>
          </div>
          
          {/* Панель управления */}
          {videos.length > 0 && (
            <div className="flex gap-2">
              <Button
                variant={selectionMode ? "default" : "outline"}
                size="sm"
                onClick={toggleSelectionMode}
                className="flex-1 h-10"
              >
                {selectionMode ? (
                  <>
                    <CheckSquare className="h-4 w-4 mr-2" />
                    Отмена
                  </>
                ) : (
                  <>
                    <Square className="h-4 w-4 mr-2" />
                    Выделить
                  </>
                )}
              </Button>
              
              {selectionMode && (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={selectAll}
                    className="flex-1 h-10"
                  >
                    {selectedVideos.size === videos.length ? 'Снять все' : 'Все'}
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={handleDeleteSelected}
                    disabled={selectedVideos.size === 0}
                    className="h-10 px-4"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </>
              )}
            </div>
          )}
          
          {selectionMode && selectedVideos.size > 0 && (
            <p className="text-sm text-muted-foreground mt-3 font-medium">
              Выбрано: {selectedVideos.size}
            </p>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-4 min-h-0">
          {videos.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center p-6">
              <FileVideo className="h-20 w-20 text-muted-foreground/50 mb-4" />
              <p className="text-base text-muted-foreground font-medium">
                У вас пока нет видео
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {videos.map((video) => {
                const isActive = video.lesson_id === currentLessonId;
                const isSelected = selectedVideos.has(video.lesson_id);
                
                return (
                  <Card
                    key={video.lesson_id}
                    className={`
                      cursor-pointer transition-all duration-200
                      ${isActive && !selectionMode ? 'ring-2 ring-primary shadow-lg scale-[1.02]' : ''}
                      ${isSelected ? 'ring-2 ring-blue-500 shadow-lg' : 'hover:shadow-md hover:scale-[1.01]'}
                      ${!video.can_play && !selectionMode ? 'opacity-60' : ''}
                      relative
                    `}
                    onClick={() => handleVideoClick(video)}
                  >
                    {/* Чекбокс в режиме выбора */}
                    {selectionMode && (
                      <div className="absolute top-3 left-3 z-10">
                        <Checkbox
                          checked={isSelected}
                          onCheckedChange={() => toggleVideoSelection(video.lesson_id)}
                          className="h-5 w-5 bg-background border-2"
                          onClick={(e) => e.stopPropagation()}
                        />
                      </div>
                    )}
                    {/* Превью */}
                    <div className="relative aspect-video bg-muted rounded-t-lg overflow-hidden">
                      {video.thumbnail_url ? (
                        <img
                          src={getImageUrl(video.thumbnail_url) || ''}
                          alt={video.title}
                          className="w-full h-full object-contain bg-white"
                          onError={(e) => {
                            // Если изображение не загрузилось, показать placeholder
                            e.currentTarget.style.display = 'none';
                            const placeholder = e.currentTarget.parentElement?.querySelector('.thumbnail-placeholder');
                            if (placeholder) {
                              placeholder.classList.remove('hidden');
                            }
                          }}
                        />
                      ) : null}
                      
                      {/* Placeholder если нет thumbnail или ошибка загрузки */}
                      <div className={`thumbnail-placeholder w-full h-full flex flex-col items-center justify-center gap-2 ${video.thumbnail_url ? 'hidden' : ''}`}>
                        <FileVideo className="h-14 w-14 text-muted-foreground/50" />
                        <span className="text-xs text-muted-foreground font-medium">Нет превью</span>
                      </div>
                      
                      {/* Иконка Play - только когда не в режиме выбора */}
                      {video.can_play && !selectionMode && (
                        <div className="absolute inset-0 flex items-center justify-center bg-black/20 rounded-t-lg opacity-0 hover:opacity-100 transition-opacity">
                          <Play className="h-14 w-14 text-white drop-shadow-lg" fill="white" />
                        </div>
                      )}

                      {/* Статус */}
                      <div className="absolute top-3 right-3">
                        {getStatusBadge(video.status)}
                      </div>

                      {/* Длительность */}
                      {video.duration && (
                        <div className="absolute bottom-3 right-3 bg-black/80 text-white text-xs px-2.5 py-1 rounded-md font-semibold">
                          {formatDuration(video.duration)}
                        </div>
                      )}
                    </div>

                    {/* Информация */}
                    <div className="p-4">
                      <h3 className="font-semibold text-sm line-clamp-2 mb-2.5">
                        {video.title}
                      </h3>

                      <div className="flex items-center gap-2 text-xs text-muted-foreground mb-3">
                        <Clock className="h-3.5 w-3.5" />
                        <span>{formatDate(video.created_at)}</span>
                        {video.slides_count && (
                          <>
                            <span>•</span>
                            <span>{video.slides_count} слайдов</span>
                          </>
                        )}
                      </div>

                      {/* Действия - только когда не в режиме выбора */}
                      {!selectionMode && (
                        <div className="flex gap-2">
                          {video.video_url && (
                            <Button
                              variant="outline"
                              size="sm"
                              className="flex-1 h-8"
                              onClick={(e) => handleDownloadClick(e, video)}
                            >
                              <Download className="h-3.5 w-3.5 mr-1.5" />
                              MP4
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8"
                            onClick={(e) => handleDeleteClick(e, video)}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      )}

                      {video.video_size && !selectionMode && (
                        <div className="text-xs text-muted-foreground mt-2">
                          Размер: {formatFileSize(video.video_size)}
                        </div>
                      )}
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      </Card>

      {/* Диалог удаления */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {selectedVideos.size > 1 
                ? `Удалить ${selectedVideos.size} видео?` 
                : 'Удалить видео?'}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {selectedVideos.size > 1 
                ? `Выбранные видео (${selectedVideos.size} шт.) будут удалены безвозвратно.` 
                : `Видео "${videoToDelete?.title}" будет удалено безвозвратно.`}
              {' '}Это действие нельзя отменить.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>Отмена</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              disabled={deleting}
              className="bg-destructive hover:bg-destructive/90"
            >
              {deleting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Удаление...
                </>
              ) : (
                'Удалить'
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};
