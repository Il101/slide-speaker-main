/**
 * Enhanced File Uploader with Real-Time WebSocket Progress
 * 
 * Replaces polling with WebSocket for instant progress updates
 */
import React, { useCallback, useState } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { apiClient } from '@/lib/api';
import { RealTimeProgress } from '@/components/RealTimeProgress';

interface EnhancedFileUploaderProps {
  onUploadSuccess: (lessonId: string) => void;
}

export const EnhancedFileUploader: React.FC<EnhancedFileUploaderProps> = ({ 
  onUploadSuccess 
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'processing' | 'success' | 'error'>('idle');
  const [lessonId, setLessonId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  }, []);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFileSelection(e.target.files[0]);
    }
  }, []);

  const handleFileSelection = useCallback(async (file: File) => {
    const validTypes = [
      'application/vnd.ms-powerpoint',
      'application/vnd.openxmlformats-officedocument.presentationml.presentation',
      'application/pdf'
    ];
    
    if (!validTypes.includes(file.type)) {
      setStatus('error');
      setErrorMessage('Поддерживаются только файлы PPTX и PDF');
      return;
    }

    // Check file size (basic validation)
    const maxSize = 100 * 1024 * 1024; // 100MB
    if (file.size > maxSize) {
      setStatus('error');
      setErrorMessage('Размер файла превышает 100MB');
      return;
    }

    setSelectedFile(file);
    setStatus('uploading');
    setUploadProgress(0);
    setErrorMessage(null);

    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          const newProgress = prev + Math.random() * 20;
          return Math.min(newProgress, 90);
        });
      }, 200);

      // Upload file
      const response = await apiClient.uploadFile(file);
      
      clearInterval(progressInterval);
      setUploadProgress(100);

      // Switch to processing with WebSocket
      setLessonId(response.lesson_id);
      setStatus('processing');

      console.log('[EnhancedFileUploader] Upload complete, lesson_id:', response.lesson_id);
      console.log('[EnhancedFileUploader] Switching to WebSocket progress tracking');

    } catch (error) {
      setStatus('error');
      setErrorMessage(
        error instanceof Error ? error.message : 'Ошибка загрузки файла'
      );
      console.error('[EnhancedFileUploader] Upload error:', error);
    }
  }, []);

  const handleProcessingComplete = useCallback((success: boolean, result?: any) => {
    console.log('[EnhancedFileUploader] Processing complete:', { success, result });
    
    if (success && lessonId) {
      setStatus('success');
      
      // Redirect after 2 seconds
      setTimeout(() => {
        onUploadSuccess(lessonId);
      }, 2000);
    } else {
      setStatus('error');
      setErrorMessage('Обработка завершилась с ошибкой');
    }
  }, [lessonId, onUploadSuccess]);

  const resetUploader = () => {
    setSelectedFile(null);
    setStatus('idle');
    setUploadProgress(0);
    setLessonId(null);
    setErrorMessage(null);
  };

  // Idle state - drag & drop zone
  if (status === 'idle') {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Загрузить презентацию</CardTitle>
          <CardDescription>
            Поддерживаются файлы PPTX и PDF (до 100MB)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            className={`
              relative border-2 border-dashed rounded-lg p-12 text-center
              transition-colors cursor-pointer
              ${dragActive 
                ? 'border-primary bg-primary/5' 
                : 'border-muted-foreground/25 hover:border-primary/50'
              }
            `}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              type="file"
              id="file-upload"
              accept=".pptx,.ppt,.pdf"
              onChange={handleChange}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            
            <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            
            <p className="text-lg font-medium mb-2">
              Перетащите файл сюда
            </p>
            <p className="text-sm text-muted-foreground mb-4">
              или нажмите для выбора
            </p>
            
            <Button variant="outline" asChild>
              <label htmlFor="file-upload" className="cursor-pointer">
                <FileText className="h-4 w-4 mr-2" />
                Выбрать файл
              </label>
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Uploading state
  if (status === 'uploading') {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Загрузка файла</CardTitle>
          <CardDescription>
            {selectedFile?.name}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
            <span className="text-sm">Загрузка на сервер...</span>
          </div>
          
          <Progress value={uploadProgress} className="h-2" />
          
          <p className="text-sm text-muted-foreground text-right">
            {Math.round(uploadProgress)}%
          </p>
        </CardContent>
      </Card>
    );
  }

  // Processing state - WebSocket real-time progress
  if (status === 'processing' && lessonId) {
    return (
      <div className="space-y-4">
        <RealTimeProgress
          lessonId={lessonId}
          token={apiClient.getAuthToken() || undefined}
          onComplete={handleProcessingComplete}
        />
        
        <div className="text-center">
          <Button variant="outline" onClick={resetUploader}>
            Загрузить другую презентацию
          </Button>
        </div>
      </div>
    );
  }

  // Success state
  if (status === 'success') {
    return (
      <Card className="border-green-500">
        <CardContent className="pt-6">
          <div className="text-center">
            <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-2">
              Готово!
            </h3>
            <p className="text-muted-foreground mb-4">
              Презентация успешно обработана
            </p>
            <p className="text-sm text-muted-foreground">
              Перенаправление...
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (status === 'error') {
    return (
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive">Ошибка</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {errorMessage || 'Произошла неизвестная ошибка'}
            </AlertDescription>
          </Alert>
          
          <div className="flex gap-2">
            <Button onClick={resetUploader} className="flex-1">
              Попробовать снова
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return null;
};
