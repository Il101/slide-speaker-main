import React, { useState, useEffect } from 'react';
import { Share2, Copy, Check, ExternalLink, Loader2, Globe, Lock } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { playlistApi } from '@/lib/playlistApi';
import type { PlaylistShareInfo } from '@/types/playlist';

interface SharePlaylistDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  playlistId: string;
  playlistTitle: string;
}

export const SharePlaylistDialog: React.FC<SharePlaylistDialogProps> = ({
  open,
  onOpenChange,
  playlistId,
  playlistTitle,
}) => {
  const [shareInfo, setShareInfo] = useState<PlaylistShareInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [copiedUrl, setCopiedUrl] = useState(false);
  const [copiedEmbed, setCopiedEmbed] = useState(false);

  useEffect(() => {
    if (open) {
      loadShareInfo();
    }
  }, [open, playlistId]);

  const loadShareInfo = async () => {
    try {
      setLoading(true);
      const info = await playlistApi.getShareInfo(playlistId);
      setShareInfo(info);
    } catch (error: any) {
      console.error('Failed to load share info:', error);
      toast.error(error.message || 'Не удалось загрузить информацию для шаринга');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyUrl = async () => {
    if (!shareInfo) return;

    try {
      await navigator.clipboard.writeText(shareInfo.share_url);
      setCopiedUrl(true);
      toast.success('Ссылка скопирована');
      setTimeout(() => setCopiedUrl(false), 2000);
    } catch (error) {
      toast.error('Не удалось скопировать ссылку');
    }
  };

  const handleCopyEmbed = async () => {
    if (!shareInfo) return;

    try {
      await navigator.clipboard.writeText(shareInfo.embed_code);
      setCopiedEmbed(true);
      toast.success('Код для встраивания скопирован');
      setTimeout(() => setCopiedEmbed(false), 2000);
    } catch (error) {
      toast.error('Не удалось скопировать код');
    }
  };

  const handlePreview = () => {
    if (!shareInfo) return;
    window.open(shareInfo.share_url, '_blank');
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Share2 className="h-5 w-5" />
            Поделиться плейлистом
          </DialogTitle>
          <DialogDescription>
            Поделитесь плейлистом "{playlistTitle}" с другими
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
          </div>
        ) : shareInfo ? (
          <div className="space-y-6">
            {/* Status Badges */}
            <div className="flex gap-2">
              {shareInfo.is_public ? (
                <Badge variant="default" className="bg-green-500">
                  <Globe className="h-3 w-3 mr-1" />
                  Публичный плейлист
                </Badge>
              ) : (
                <Badge variant="secondary">
                  <Lock className="h-3 w-3 mr-1" />
                  Приватный плейлист
                </Badge>
              )}
              {shareInfo.has_password && (
                <Badge variant="secondary">
                  <Lock className="h-3 w-3 mr-1" />
                  Защищен паролем
                </Badge>
              )}
            </div>

            {/* Share URL */}
            <div className="space-y-2">
              <Label htmlFor="share-url">Ссылка для доступа</Label>
              <div className="flex gap-2">
                <Input
                  id="share-url"
                  value={shareInfo.share_url}
                  readOnly
                  className="font-mono text-sm"
                />
                <Button
                  variant="outline"
                  size="icon"
                  onClick={handleCopyUrl}
                  className="flex-shrink-0"
                >
                  {copiedUrl ? (
                    <Check className="h-4 w-4 text-green-500" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                {shareInfo.is_public
                  ? 'Любой, у кого есть эта ссылка, может просмотреть плейлист'
                  : 'Плейлист приватный - нужно изменить настройки чтобы поделиться'}
              </p>
            </div>

            {/* Embed Code */}
            <div className="space-y-2">
              <Label htmlFor="embed-code">Код для встраивания</Label>
              <div className="space-y-2">
                <Textarea
                  id="embed-code"
                  value={shareInfo.embed_code}
                  readOnly
                  rows={3}
                  className="font-mono text-xs"
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCopyEmbed}
                  className="w-full"
                >
                  {copiedEmbed ? (
                    <>
                      <Check className="h-4 w-4 mr-2 text-green-500" />
                      Скопировано
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4 mr-2" />
                      Копировать код
                    </>
                  )}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Вставьте этот код на свой сайт для встраивания плейлиста
              </p>
            </div>

            {/* Preview Button */}
            <div className="flex gap-2 pt-4 border-t">
              <Button
                variant="outline"
                onClick={handlePreview}
                disabled={!shareInfo.is_public}
                className="flex-1"
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                Предпросмотр
              </Button>
              <Button onClick={() => onOpenChange(false)} className="flex-1">
                Готово
              </Button>
            </div>

            {/* Warning for private playlists */}
            {!shareInfo.is_public && (
              <div className="rounded-lg bg-amber-50 dark:bg-amber-950 p-4 text-sm">
                <p className="text-amber-900 dark:text-amber-100">
                  <strong>Внимание:</strong> Плейлист приватный. Чтобы
                  поделиться им, измените настройки приватности в редакторе
                  плейлиста.
                </p>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            Не удалось загрузить информацию
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};
