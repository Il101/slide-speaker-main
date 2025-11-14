import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Play, Plus, Edit, Share2, Trash2, Loader2, ListVideo, Clock, Globe, Lock } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { toast } from 'sonner';
import { playlistApi } from '@/lib/playlistApi';
import type { PlaylistListItem } from '@/types/playlist';
import { SharePlaylistDialog } from '@/components/playlists/SharePlaylistDialog';
import { PlaylistEditor } from '@/components/playlists/PlaylistEditor';

export const PlaylistsPage: React.FC = () => {
  const navigate = useNavigate();
  const [playlists, setPlaylists] = useState<PlaylistListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [playlistToDelete, setPlaylistToDelete] = useState<PlaylistListItem | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [playlistToShare, setPlaylistToShare] = useState<PlaylistListItem | null>(null);
  const [editorOpen, setEditorOpen] = useState(false);
  const [playlistToEdit, setPlaylistToEdit] = useState<string | null>(null);

  useEffect(() => {
    loadPlaylists();
  }, []);

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

  const handlePlay = (playlistId: string) => {
    navigate(`/playlists/${playlistId}/play`);
  };

  const handleEdit = (playlistId: string) => {
    setPlaylistToEdit(playlistId);
    setEditorOpen(true);
  };

  const handleShare = (playlist: PlaylistListItem) => {
    setPlaylistToShare(playlist);
    setShareDialogOpen(true);
  };

  const handleDeleteClick = (playlist: PlaylistListItem) => {
    setPlaylistToDelete(playlist);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!playlistToDelete) return;

    try {
      setDeleting(true);
      await playlistApi.delete(playlistToDelete.id);
      setPlaylists(playlists.filter((p) => p.id !== playlistToDelete.id));
      toast.success('Плейлист удален');
      setDeleteDialogOpen(false);
      setPlaylistToDelete(null);
    } catch (error: any) {
      console.error('Failed to delete playlist:', error);
      toast.error(error.message || 'Не удалось удалить плейлист');
    } finally {
      setDeleting(false);
    }
  };

  const formatDuration = (seconds?: number): string => {
    if (!seconds) return '—';
    const mins = Math.floor(seconds / 60);
    const hours = Math.floor(mins / 60);
    if (hours > 0) {
      return `${hours}ч ${mins % 60}м`;
    }
    return `${mins}м`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <ListVideo className="h-8 w-8" />
            Мои плейлисты
          </h1>
          <p className="text-muted-foreground mt-1">
            Управляйте коллекциями видео-лекций
          </p>
        </div>
        <Button
          size="lg"
          onClick={() => toast.info('Создание плейлиста пока доступно только из "Мои видео"')}
        >
          <Plus className="h-5 w-5 mr-2" />
          Создать плейлист
        </Button>
      </div>

      {/* Playlists Grid */}
      {playlists.length === 0 ? (
        <Card className="p-12">
          <div className="text-center">
            <ListVideo className="h-16 w-16 mx-auto text-muted-foreground/50 mb-4" />
            <h3 className="text-xl font-semibold mb-2">У вас пока нет плейлистов</h3>
            <p className="text-muted-foreground mb-6">
              Создайте первый плейлист из раздела "Мои видео"
            </p>
            <Button onClick={() => navigate('/')}>
              Перейти к видео
            </Button>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {playlists.map((playlist) => (
            <Card
              key={playlist.id}
              className="overflow-hidden hover:shadow-lg transition-shadow"
            >
              {/* Thumbnail */}
              <div
                className="relative aspect-video bg-muted cursor-pointer group"
                onClick={() => handlePlay(playlist.id)}
              >
                {playlist.thumbnail_url ? (
                  <img
                    src={playlist.thumbnail_url}
                    alt={playlist.title}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <ListVideo className="h-16 w-16 text-muted-foreground/30" />
                  </div>
                )}
                
                {/* Play Overlay */}
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <div className="w-16 h-16 rounded-full bg-primary flex items-center justify-center">
                    <Play className="h-8 w-8 text-primary-foreground ml-1" />
                  </div>
                </div>

                {/* Badges */}
                <div className="absolute top-2 right-2 flex gap-2">
                  {playlist.is_public ? (
                    <Badge variant="secondary" className="bg-green-500 text-white">
                      <Globe className="h-3 w-3 mr-1" />
                      Публичный
                    </Badge>
                  ) : (
                    <Badge variant="secondary">
                      <Lock className="h-3 w-3 mr-1" />
                      Приватный
                    </Badge>
                  )}
                </div>

                {/* Video Count Badge */}
                <div className="absolute bottom-2 right-2">
                  <Badge variant="default" className="bg-black/70 text-white">
                    {playlist.video_count} видео
                  </Badge>
                </div>
              </div>

              {/* Content */}
              <CardContent className="p-4">
                <h3 className="font-semibold text-lg line-clamp-2 mb-2">
                  {playlist.title}
                </h3>
                
                {playlist.description && (
                  <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                    {playlist.description}
                  </p>
                )}

                {/* Stats */}
                <div className="flex items-center gap-4 text-sm text-muted-foreground mb-4">
                  <span className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    {formatDuration(playlist.total_duration)}
                  </span>
                </div>

                {/* Actions */}
                <div className="grid grid-cols-4 gap-2">
                  <Button
                    variant="default"
                    size="sm"
                    className="col-span-2"
                    onClick={() => handlePlay(playlist.id)}
                  >
                    <Play className="h-4 w-4 mr-1" />
                    Играть
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleEdit(playlist.id)}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleShare(playlist)}
                  >
                    <Share2 className="h-4 w-4" />
                  </Button>
                </div>
                
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full mt-2 text-destructive hover:text-destructive"
                  onClick={() => handleDeleteClick(playlist)}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Удалить
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Delete Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Удалить плейлист?</AlertDialogTitle>
            <AlertDialogDescription>
              Плейлист "{playlistToDelete?.title}" будет удален безвозвратно.
              Сами видео останутся, удалится только плейлист.
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

      {/* Share Dialog */}
      {playlistToShare && (
        <SharePlaylistDialog
          open={shareDialogOpen}
          onOpenChange={setShareDialogOpen}
          playlistId={playlistToShare.id}
          playlistTitle={playlistToShare.title}
        />
      )}

      {/* Editor Dialog */}
      {playlistToEdit && (
        <PlaylistEditor
          open={editorOpen}
          onOpenChange={setEditorOpen}
          playlistId={playlistToEdit}
          onSuccess={() => {
            loadPlaylists();
            setEditorOpen(false);
          }}
        />
      )}
    </div>
  );
};

export default PlaylistsPage;
