/**
 * Real-Time Progress Component
 * 
 * Displays live progress updates for lesson processing using WebSocket
 */
import React, { useState, useEffect } from 'react';
import { Loader2, CheckCircle2, XCircle, Clock, Zap } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useWebSocket, ProgressMessage } from '@/hooks/useWebSocket';

interface RealTimeProgressProps {
  lessonId: string;
  token?: string;
  onComplete?: (success: boolean, result?: any) => void;
}

const stageLabels: Record<string, string> = {
  initializing: 'Инициализация',
  ocr: 'Извлечение текста',
  ai_generation: 'Генерация скриптов',
  tts: 'Синтез речи',
  visual_effects: 'Визуальные эффекты',
  finalization: 'Финализация',
  completed: 'Завершено',
};

const stageIcons: Record<string, React.ReactNode> = {
  initializing: <Loader2 className="h-4 w-4 animate-spin" />,
  ocr: <Zap className="h-4 w-4" />,
  ai_generation: <Zap className="h-4 w-4" />,
  tts: <Zap className="h-4 w-4" />,
  visual_effects: <Zap className="h-4 w-4" />,
  finalization: <Loader2 className="h-4 w-4 animate-spin" />,
  completed: <CheckCircle2 className="h-4 w-4 text-green-500" />,
};

export const RealTimeProgress: React.FC<RealTimeProgressProps> = ({
  lessonId,
  token,
  onComplete,
}) => {
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState<string>('initializing');
  const [message, setMessage] = useState<string>('Подключение...');
  const [eta, setEta] = useState<string | null>(null);
  const [currentSlide, setCurrentSlide] = useState<number | null>(null);
  const [totalSlides, setTotalSlides] = useState<number | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const [isError, setIsError] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [slideUpdates, setSlideUpdates] = useState<Map<number, string>>(new Map());

  const handleProgress = (data: ProgressMessage) => {
    setProgress(data.percent || 0);
    setStage(data.stage || 'processing');
    setMessage(data.message || 'Обработка...');
    setEta(data.eta_formatted || null);
    
    if (data.current_slide !== undefined) {
      setCurrentSlide(data.current_slide);
    }
    if (data.total_slides !== undefined) {
      setTotalSlides(data.total_slides);
    }
  };

  const handleCompletion = (data: ProgressMessage) => {
    setProgress(100);
    setStage('completed');
    setMessage(data.message || 'Обработка завершена');
    setIsComplete(true);
    setEta(null);
    
    onComplete?.(data.success !== false, data.result);
  };

  const handleError = (data: ProgressMessage) => {
    setIsError(true);
    setErrorMessage(data.error_message || 'Произошла ошибка');
    setMessage('Ошибка обработки');
    
    onComplete?.(false);
  };

  const handleSlideUpdate = (data: ProgressMessage) => {
    if (data.slide_number !== undefined && data.status) {
      setSlideUpdates(prev => {
        const newMap = new Map(prev);
        newMap.set(data.slide_number!, data.status!);
        return newMap;
      });
    }
  };

  const { isConnected, error: wsError } = useWebSocket({
    lessonId,
    token,
    onProgress: handleProgress,
    onCompletion: handleCompletion,
    onError: handleError,
    onSlideUpdate: handleSlideUpdate,
    autoConnect: true,
  });

  // Connection status indicator
  const connectionStatus = isConnected ? (
    <Badge variant="outline" className="gap-1">
      <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
      Live
    </Badge>
  ) : (
    <Badge variant="outline" className="gap-1">
      <div className="h-2 w-2 rounded-full bg-yellow-500" />
      Подключение...
    </Badge>
  );

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">Обработка презентации</CardTitle>
            <CardDescription>
              {isComplete
                ? 'Презентация готова'
                : isError
                ? 'Произошла ошибка'
                : 'Отслеживание прогресса в реальном времени'}
            </CardDescription>
          </div>
          {connectionStatus}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* WebSocket Error */}
        {wsError && (
          <Alert variant="destructive">
            <AlertDescription>{wsError}</AlertDescription>
          </Alert>
        )}

        {/* Processing Error */}
        {isError && errorMessage && (
          <Alert variant="destructive">
            <XCircle className="h-4 w-4" />
            <AlertDescription>{errorMessage}</AlertDescription>
          </Alert>
        )}

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              {stageIcons[stage] || <Loader2 className="h-4 w-4 animate-spin" />}
              <span className="font-medium">
                {stageLabels[stage] || stage}
              </span>
            </div>
            <span className="text-muted-foreground">{Math.round(progress)}%</span>
          </div>
          
          <Progress value={progress} className="h-2" />
          
          <p className="text-sm text-muted-foreground">{message}</p>
        </div>

        {/* Slide Progress */}
        {currentSlide !== null && totalSlides !== null && (
          <div className="flex items-center gap-2 text-sm">
            <span className="text-muted-foreground">Слайд:</span>
            <Badge variant="secondary">
              {currentSlide} / {totalSlides}
            </Badge>
          </div>
        )}

        {/* ETA */}
        {eta && !isComplete && !isError && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock className="h-4 w-4" />
            <span>Осталось: {eta}</span>
          </div>
        )}

        {/* Slide Status Grid */}
        {totalSlides && totalSlides > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium">Статус слайдов:</p>
            <div className="grid grid-cols-10 gap-1">
              {Array.from({ length: totalSlides }, (_, i) => i + 1).map((slideNum) => {
                const status = slideUpdates.get(slideNum);
                const isProcessing = slideNum === currentSlide;
                const isCompleted = status === 'completed';
                const isFailed = status === 'failed';
                
                return (
                  <div
                    key={slideNum}
                    className={`
                      h-8 rounded flex items-center justify-center text-xs font-medium
                      ${isCompleted ? 'bg-green-500 text-white' : ''}
                      ${isFailed ? 'bg-red-500 text-white' : ''}
                      ${isProcessing ? 'bg-blue-500 text-white animate-pulse' : ''}
                      ${!isCompleted && !isFailed && !isProcessing ? 'bg-gray-200 text-gray-600' : ''}
                    `}
                    title={`Слайд ${slideNum}${status ? `: ${status}` : ''}`}
                  >
                    {slideNum}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Success Message */}
        {isComplete && (
          <Alert className="border-green-500 bg-green-50">
            <CheckCircle2 className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">
              Презентация успешно обработана! Вы можете просмотреть результат.
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};
