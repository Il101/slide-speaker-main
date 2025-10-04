import React, { useCallback, useState, useEffect } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { apiClient } from '@/lib/api';
import { SimpleProcessingProgress } from '@/components/SimpleProcessingProgress';

interface FileUploaderProps {
  onUploadSuccess: (lessonId: string) => void;
}

export const FileUploader: React.FC<FileUploaderProps> = ({ onUploadSuccess }) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'processing' | 'success' | 'error'>('idle');
  const [lessonId, setLessonId] = useState<string | null>(null);
  const [processingStage, setProcessingStage] = useState<string>('initializing');
  const [processingProgress, setProcessingProgress] = useState<number>(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (status !== 'processing' || !lessonId) return;

    console.log('[FileUploader] Starting polling for lesson:', lessonId);

    const pollInterval = setInterval(async () => {
      try {
        const statusData = await apiClient.getLessonStatus(lessonId);
        
        console.log('[FileUploader] Status poll result:', {
          lesson_id: statusData.lesson_id,
          status: statusData.status,
          stage: statusData.stage,
          progress: statusData.progress,
          message: statusData.message
        });
        
        setProcessingStage(statusData.stage);
        setProcessingProgress(statusData.progress);
        
        console.log('[FileUploader] Updated state - stage:', statusData.stage, 'progress:', statusData.progress);

        if (statusData.status === 'completed') {
          console.log('[FileUploader] Processing completed! Keeping status as "processing" for SimpleProcessingProgress');
          // НЕ меняем status на 'success' здесь!
          // SimpleProcessingProgress сам вызовет onComplete через 1.5 секунды
          clearInterval(pollInterval);
        } else if (statusData.status === 'failed') {
          console.error('[FileUploader] Processing failed:', statusData.message);
          setStatus('error');
          setErrorMessage(statusData.message || 'Ошибка обработки');
          clearInterval(pollInterval);
        }
      } catch (error) {
        console.error('[FileUploader] Error polling status:', error);
      }
    }, 2000);

    return () => {
      console.log('[FileUploader] Stopping polling');
      clearInterval(pollInterval);
    };
  }, [status, lessonId]);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleFileSelection = useCallback(async (file: File) => {
    const validTypes = ['application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation', 'application/pdf'];
    
    if (!validTypes.includes(file.type)) {
      setStatus('error');
      setErrorMessage('Поддерживаются только файлы PPTX и PDF');
      return;
    }

    setSelectedFile(file);
    setStatus('uploading');
    setUploadProgress(0);
    setErrorMessage(null);

    try {
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          const newProgress = prev + Math.random() * 20;
          return Math.min(newProgress, 90);
        });
      }, 200);

      const response = await apiClient.uploadFile(file);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      setLessonId(response.lesson_id);
      setStatus('processing');
      setProcessingStage('parsing');
      setProcessingProgress(20);
      
    } catch (error) {
      setStatus('error');
      setErrorMessage(error instanceof Error ? error.message : 'Ошибка загрузки файла');
      console.error('Upload error:', error);
    }
  }, []);

  const handleProcessingComplete = useCallback(() => {
    console.log('[FileUploader] handleProcessingComplete called with lessonId:', lessonId);
    if (lessonId) {
      console.log('[FileUploader] Calling onUploadSuccess in 1500ms');
      setTimeout(() => {
        console.log('[FileUploader] Calling onUploadSuccess now with lessonId:', lessonId);
        onUploadSuccess(lessonId);
      }, 1500);
    }
  }, [lessonId, onUploadSuccess]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    const files = e.dataTransfer.files;
    if (files && files[0]) {
      handleFileSelection(files[0]);
    }
  }, [handleFileSelection]);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelection(e.target.files[0]);
    }
  };

  if (status === 'processing' && lessonId) {
    return (
      <SimpleProcessingProgress
        lessonId={lessonId}
        currentStage={processingStage}
        currentProgress={processingProgress}
        error={errorMessage}
        onComplete={handleProcessingComplete}
      />
    );
  }

  return (
    <Card className="p-8 card-gradient card-shadow">
      <div
        className={`border-2 border-dashed rounded-xl p-8 text-center smooth-transition ${
          dragActive 
            ? 'border-primary bg-primary/10' 
            : 'border-muted-foreground/30 hover:border-primary/50'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        {status === 'idle' && (
          <>
            <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-xl font-semibold mb-2">Загрузите презентацию</h3>
            <p className="text-muted-foreground mb-4">
              Поддерживаются форматы PPTX и PDF
            </p>
            <Button
              variant="outline"
              className="relative"
              onClick={() => document.getElementById('file-upload')?.click()}
            >
              Выбрать файл
            </Button>
            <input
              id="file-upload"
              type="file"
              className="hidden"
              accept=".pptx,.pdf"
              onChange={handleFileInput}
            />
          </>
        )}

        {status === 'uploading' && selectedFile && (
          <div className="animate-fade-in-up">
            <FileText className="mx-auto h-12 w-12 text-primary mb-4" />
            <h3 className="text-xl font-semibold mb-2">{selectedFile.name}</h3>
            <Progress value={uploadProgress} className="mb-4" />
            <p className="text-muted-foreground">Загрузка файла на сервер...</p>
          </div>
        )}

        {status === 'success' && selectedFile && (
          <div className="animate-fade-in-up">
            <CheckCircle className="mx-auto h-12 w-12 text-accent mb-4" />
            <h3 className="text-xl font-semibold mb-2">Готово!</h3>
            <p className="text-muted-foreground mb-4">Презентация готова к просмотру</p>
            <p className="text-sm text-muted-foreground">Переход к плееру...</p>
          </div>
        )}

        {status === 'error' && (
          <div className="animate-fade-in-up">
            <AlertCircle className="mx-auto h-12 w-12 text-destructive mb-4" />
            <h3 className="text-xl font-semibold mb-2">Ошибка</h3>
            <p className="text-muted-foreground mb-4">
              {errorMessage || 'Поддерживаются только файлы PPTX и PDF'}
            </p>
            <Button
              variant="outline"
              onClick={() => {
                setStatus('idle');
                setSelectedFile(null);
                setErrorMessage(null);
                setUploadProgress(0);
              }}
            >
              Попробовать снова
            </Button>
          </div>
        )}
      </div>
    </Card>
  );
};
