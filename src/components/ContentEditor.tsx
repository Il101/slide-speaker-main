/**
 * Content Editor Component
 * 
 * Allows users to edit and regenerate slide scripts
 */
import React, { useState, useEffect } from 'react';
import { Edit3, RefreshCw, Save, X, Loader2, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { apiClient } from '@/lib/api';
import { useToast } from '@/components/ui/use-toast';

interface ContentEditorProps {
  lessonId: string;
  slideNumber: number;
  initialScript?: string;
  onSave?: (newScript: string) => void;
  onClose?: () => void;
}

type SegmentType = 'intro' | 'main' | 'conclusion' | 'full';
type StyleType = 'casual' | 'formal' | 'technical';

export const ContentEditor: React.FC<ContentEditorProps> = ({
  lessonId,
  slideNumber,
  initialScript = '',
  onSave,
  onClose,
}) => {
  const [script, setScript] = useState(initialScript);
  const [originalScript, setOriginalScript] = useState(initialScript);
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasChanges, setHasChanges] = useState(false);
  
  // Regeneration settings
  const [segmentType, setSegmentType] = useState<SegmentType>('intro');
  const [style, setStyle] = useState<StyleType>('casual');
  const [customPrompt, setCustomPrompt] = useState('');

  const { toast } = useToast();

  // Load current script if not provided
  useEffect(() => {
    if (!initialScript) {
      loadScript();
    }
  }, [lessonId, slideNumber]);

  // Track changes
  useEffect(() => {
    setHasChanges(script !== originalScript);
  }, [script, originalScript]);

  const loadScript = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch(
        `/api/content/slide-script/${lessonId}/${slideNumber}`,
        {
          headers: {
            ...apiClient.getAuthHeaders(),
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to load script');
      }

      const data = await response.json();
      setScript(data.script || '');
      setOriginalScript(data.script || '');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load script');
      toast({
        title: 'Ошибка',
        description: 'Не удалось загрузить скрипт',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegenerateSegment = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch('/api/content/regenerate-segment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...apiClient.getAuthHeaders(),
        },
        body: JSON.stringify({
          lesson_id: lessonId,
          slide_number: slideNumber,
          segment_type: segmentType,
          style,
          custom_prompt: customPrompt || undefined,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to regenerate segment');
      }

      const data = await response.json();
      setScript(data.script);
      setOriginalScript(data.script);
      
      toast({
        title: 'Успешно',
        description: `Сегмент "${segmentType}" регенерирован`,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to regenerate');
      toast({
        title: 'Ошибка',
        description: 'Не удалось регенерировать сегмент',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async (regenerateAudio = true) => {
    try {
      setIsSaving(true);
      setError(null);

      const response = await fetch('/api/content/edit-script', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...apiClient.getAuthHeaders(),
        },
        body: JSON.stringify({
          lesson_id: lessonId,
          slide_number: slideNumber,
          new_script: script,
          regenerate_audio: regenerateAudio,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save script');
      }

      const data = await response.json();
      setOriginalScript(script);
      setIsEditing(false);
      
      toast({
        title: 'Сохранено',
        description: regenerateAudio
          ? 'Скрипт сохранён, аудио генерируется...'
          : 'Скрипт сохранён',
      });

      onSave?.(script);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save');
      toast({
        title: 'Ошибка',
        description: 'Не удалось сохранить изменения',
        variant: 'destructive',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setScript(originalScript);
    setIsEditing(false);
    setHasChanges(false);
    onClose?.();
  };

  if (isLoading && !script) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Редактор контента</CardTitle>
            <CardDescription>
              Слайд {slideNumber} • {script.length} символов
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {hasChanges && (
              <Badge variant="secondary">Есть изменения</Badge>
            )}
            {!isEditing && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsEditing(true)}
              >
                <Edit3 className="h-4 w-4 mr-2" />
                Редактировать
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <Tabs defaultValue="edit" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="edit">Редактирование</TabsTrigger>
            <TabsTrigger value="regenerate">Регенерация</TabsTrigger>
          </TabsList>

          {/* Manual Editing Tab */}
          <TabsContent value="edit" className="space-y-4">
            <Textarea
              value={script}
              onChange={(e) => setScript(e.target.value)}
              disabled={!isEditing || isSaving}
              rows={12}
              className="font-mono text-sm"
              placeholder="Текст скрипта для слайда..."
            />

            {isEditing && (
              <div className="flex gap-2">
                <Button
                  onClick={() => handleSave(true)}
                  disabled={!hasChanges || isSaving}
                  className="flex-1"
                >
                  {isSaving ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Сохранение...
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4 mr-2" />
                      Сохранить и регенерировать аудио
                    </>
                  )}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleSave(false)}
                  disabled={!hasChanges || isSaving}
                >
                  Сохранить без аудио
                </Button>
                <Button
                  variant="ghost"
                  onClick={handleCancel}
                  disabled={isSaving}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            )}
          </TabsContent>

          {/* AI Regeneration Tab */}
          <TabsContent value="regenerate" className="space-y-4">
            <div className="grid gap-4">
              <div className="grid gap-2">
                <Label htmlFor="segment">Сегмент для регенерации</Label>
                <Select
                  value={segmentType}
                  onValueChange={(value) => setSegmentType(value as SegmentType)}
                >
                  <SelectTrigger id="segment">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="intro">Вступление</SelectItem>
                    <SelectItem value="main">Основной контент</SelectItem>
                    <SelectItem value="conclusion">Заключение</SelectItem>
                    <SelectItem value="full">Весь скрипт</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="style">Стиль</Label>
                <Select
                  value={style}
                  onValueChange={(value) => setStyle(value as StyleType)}
                >
                  <SelectTrigger id="style">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="casual">Неформальный</SelectItem>
                    <SelectItem value="formal">Формальный</SelectItem>
                    <SelectItem value="technical">Технический</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="prompt">Дополнительные инструкции (опционально)</Label>
                <Textarea
                  id="prompt"
                  value={customPrompt}
                  onChange={(e) => setCustomPrompt(e.target.value)}
                  rows={3}
                  placeholder="Например: Добавить больше примеров, упростить язык..."
                />
              </div>

              <Button
                onClick={handleRegenerateSegment}
                disabled={isLoading}
                className="w-full"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Генерация...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-2" />
                    Регенерировать с помощью AI
                  </>
                )}
              </Button>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>

      {onClose && (
        <CardFooter>
          <Button variant="ghost" onClick={onClose} className="w-full">
            Закрыть
          </Button>
        </CardFooter>
      )}
    </Card>
  );
};
