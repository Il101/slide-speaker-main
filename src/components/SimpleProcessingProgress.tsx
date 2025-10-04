import React, { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

interface SimpleProcessingProgressProps {
  lessonId: string;
  currentStage: string;
  currentProgress: number;
  error?: string | null;
  onComplete?: () => void;
}

const STAGE_NAMES: Record<string, string> = {
  'initializing': 'Инициализация',
  'parsing': 'Извлечение слайдов',
  'generating_notes': 'Генерация текста лекции',
  'generating_audio': 'Синтез речи',
  'generating_cues': 'Создание визуальных эффектов',
  'completed': 'Готово'
};

const STAGE_ORDER = [
  'initializing',
  'parsing',
  'generating_notes',
  'generating_audio',
  'generating_cues',
  'completed'
];

export const SimpleProcessingProgress: React.FC<SimpleProcessingProgressProps> = ({
  lessonId,
  currentStage,
  currentProgress,
  error,
  onComplete
}) => {
  const [displayProgress, setDisplayProgress] = useState(0);

  useEffect(() => {
    // Плавная анимация прогресса
    const interval = setInterval(() => {
      setDisplayProgress(prev => {
        if (prev < currentProgress) {
          return Math.min(prev + 2, currentProgress);
        }
        return prev;
      });
    }, 50);

    return () => clearInterval(interval);
  }, [currentProgress]);

  useEffect(() => {
    console.log('[SimpleProcessingProgress] Stage changed:', currentStage);
    if (currentStage === 'completed' && onComplete) {
      console.log('[SimpleProcessingProgress] Triggering onComplete in 1500ms');
      setTimeout(() => {
        console.log('[SimpleProcessingProgress] Calling onComplete now');
        onComplete();
      }, 1500);
    }
  }, [currentStage, onComplete]);

  const currentStepIndex = STAGE_ORDER.indexOf(currentStage);
  const totalSteps = STAGE_ORDER.length - 1; // -1 потому что 'completed' не считается как шаг
  const currentStep = Math.max(1, currentStepIndex);
  const stageName = STAGE_NAMES[currentStage] || currentStage;

  return (
    <Card className="p-8 card-gradient card-shadow max-w-2xl mx-auto">
      <div className="space-y-6">
        {/* Заголовок */}
        <div className="text-center">
          <div className="inline-flex items-center justify-center mb-4">
            <Loader2 className="h-8 w-8 animate-spin text-primary mr-3" />
            <h2 className="text-2xl font-bold">
              {error ? '❌ Ошибка обработки' : '⚙️ Обработка презентации'}
            </h2>
          </div>
          {error && (
            <p className="text-destructive text-sm">{error}</p>
          )}
        </div>

        {/* Прогресс-бар */}
        <div className="space-y-3">
          <Progress 
            value={displayProgress} 
            className="h-4"
          />
          
          {/* Информация о прогрессе */}
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <span className="font-medium text-foreground">
                {stageName}
              </span>
              {currentStage !== 'completed' && (
                <span className="text-muted-foreground">
                  • Шаг {currentStep} из {totalSteps}
                </span>
              )}
            </div>
            <span className="font-semibold text-primary">
              {Math.round(displayProgress)}%
            </span>
          </div>
        </div>

        {/* ID лекции (для отладки) */}
        {process.env.NODE_ENV === 'development' && (
          <div className="text-center">
            <p className="text-xs text-muted-foreground">
              ID: {lessonId.substring(0, 8)}...
            </p>
          </div>
        )}
      </div>
    </Card>
  );
};
