import React, { useCallback, useState } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { apiClient } from '@/lib/api';

interface FileUploaderProps {
  onUploadSuccess: (lessonId: string) => void;
}

export const FileUploader: React.FC<FileUploaderProps> = ({ onUploadSuccess }) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');

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
      return;
    }

    setSelectedFile(file);
    setStatus('uploading');
    setUploadProgress(0);

    try {
      // Симулируем прогресс загрузки
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          const newProgress = prev + Math.random() * 20;
          return Math.min(newProgress, 90); // Останавливаемся на 90% до получения ответа
        });
      }, 200);

      const response = await apiClient.uploadFile(file);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      setStatus('success');
      
      // Небольшая задержка для показа успешного состояния
      setTimeout(() => {
        onUploadSuccess(response.lesson_id);
      }, 1000);
      
    } catch (error) {
      setStatus('error');
      console.error('Upload error:', error);
    }
  }, [onUploadSuccess]);

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
            <p className="text-muted-foreground">Загрузка файла...</p>
          </div>
        )}

        {status === 'success' && selectedFile && (
          <div className="animate-fade-in-up">
            <CheckCircle className="mx-auto h-12 w-12 text-accent mb-4" />
            <h3 className="text-xl font-semibold mb-2">Файл загружен!</h3>
            <p className="text-muted-foreground mb-4">{selectedFile.name}</p>
            <p className="text-sm text-muted-foreground">Перенаправление...</p>
          </div>
        )}

        {status === 'error' && (
          <div className="animate-fade-in-up">
            <AlertCircle className="mx-auto h-12 w-12 text-destructive mb-4" />
            <h3 className="text-xl font-semibold mb-2">Ошибка загрузки</h3>
            <p className="text-muted-foreground mb-4">
              Поддерживаются только файлы PPTX и PDF
            </p>
            <Button
              variant="outline"
              onClick={() => {
                setStatus('idle');
                setSelectedFile(null);
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