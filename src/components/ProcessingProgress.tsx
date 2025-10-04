import React, { useEffect, useState } from 'react';
import { CheckCircle, Clock, Loader2, AlertTriangle, FileText, Brain, Mic, Video, Sparkles } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

export interface ProcessingStage {
  id: string;
  name: string;
  description: string;
  progress: number;
  status: 'pending' | 'in-progress' | 'completed' | 'error';
  icon: React.ElementType;
}

interface ProcessingProgressProps {
  lessonId: string;
  currentStage: string;
  currentProgress: number;
  error?: string | null;
  onComplete?: () => void;
}

const STAGES_CONFIG: Record<string, { name: string; description: string; icon: React.ElementType }> = {
  'initializing': {
    name: 'Инициализация',
    description: 'Подготовка к обработке файла',
    icon: Clock
  },
  'parsing': {
    name: 'Парсинг презентации',
    description: 'Извлечение слайдов и текста',
    icon: FileText
  },
  'generating_notes': {
    name: 'Генерация лекции',
    description: 'AI создает текст лекции для каждого слайда',
    icon: Brain
  },
  'generating_audio': {
    name: 'Синтез речи',
    description: 'Преобразование текста в аудио',
    icon: Mic
  },
  'generating_cues': {
    name: 'Создание визуальных эффектов',
    description: 'Добавление подсветок и анимаций',
    icon: Sparkles
  },
  'completed': {
    name: 'Готово',
    description: 'Презентация готова к просмотру!',
    icon: CheckCircle
  }
};

const STAGE_ORDER = [
  'initializing',
  'parsing',
  'generating_notes',
  'generating_audio',
  'generating_cues',
  'completed'
];

export const ProcessingProgress: React.FC<ProcessingProgressProps> = ({
  lessonId,
  currentStage,
  currentProgress,
  error,
  onComplete
}) => {
  const [stages, setStages] = useState<ProcessingStage[]>([]);

  useEffect(() => {
    const currentStageIndex = STAGE_ORDER.indexOf(currentStage);
    
    const updatedStages: ProcessingStage[] = STAGE_ORDER.map((stageId, index) => {
      const config = STAGES_CONFIG[stageId] || {
        name: stageId,
        description: 'Обработка...',
        icon: Loader2
      };

      let status: ProcessingStage['status'] = 'pending';
      let progress = 0;

      if (index < currentStageIndex) {
        status = 'completed';
        progress = 100;
      } else if (index === currentStageIndex) {
        status = error ? 'error' : 'in-progress';
        progress = currentProgress;
      }

      return {
        id: stageId,
        name: config.name,
        description: config.description,
        progress,
        status,
        icon: config.icon
      };
    });

    setStages(updatedStages);

    // Если достигнута стадия completed, вызываем callback
    if (currentStage === 'completed' && onComplete) {
      setTimeout(() => onComplete(), 1500);
    }
  }, [currentStage, currentProgress, error, onComplete]);

  const getStatusColor = (status: ProcessingStage['status']) => {
    switch (status) {
      case 'completed':
        return 'text-green-500';
      case 'in-progress':
        return 'text-blue-500';
      case 'error':
        return 'text-red-500';
      default:
        return 'text-gray-400';
    }
  };

  const getStatusBg = (status: ProcessingStage['status']) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500/10 border-green-500/30';
      case 'in-progress':
        return 'bg-blue-500/10 border-blue-500/30';
      case 'error':
        return 'bg-red-500/10 border-red-500/30';
      default:
        return 'bg-gray-500/5 border-gray-500/20';
    }
  };

  const overallProgress = stages.reduce((sum, stage) => sum + stage.progress, 0) / stages.length;

  return (
    <Card className="p-8 card-gradient card-shadow max-w-2xl mx-auto">
      <div className="space-y-6">
        {/* Заголовок */}
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-2">
            {error ? '❌ Ошибка обработки' : '⚙️ Обработка презентации'}
          </h2>
          <p className="text-muted-foreground">
            {error ? error : 'Пожалуйста, подождите, пока мы готовим вашу презентацию'}
          </p>
        </div>

        {/* Общий прогресс */}
        <div className="space-y-2">
          <div className="flex justify-between items-center text-sm">
            <span className="font-medium">Общий прогресс</span>
            <span className="text-muted-foreground">{Math.round(overallProgress)}%</span>
          </div>
          <Progress value={overallProgress} className="h-3" />
        </div>

        {/* Список стадий */}
        <div className="space-y-3">
          {stages.map((stage, index) => {
            const Icon = stage.icon;
            const isActive = stage.status === 'in-progress';
            
            return (
              <div
                key={stage.id}
                className={`
                  p-4 rounded-lg border-2 transition-all duration-300
                  ${getStatusBg(stage.status)}
                  ${isActive ? 'scale-[1.02] shadow-md' : ''}
                `}
              >
                <div className="flex items-start gap-3">
                  {/* Иконка */}
                  <div className={`flex-shrink-0 ${getStatusColor(stage.status)}`}>
                    {stage.status === 'in-progress' ? (
                      <Loader2 className="h-6 w-6 animate-spin" />
                    ) : stage.status === 'error' ? (
                      <AlertTriangle className="h-6 w-6" />
                    ) : (
                      <Icon className={`h-6 w-6 ${stage.status === 'completed' ? '' : 'opacity-50'}`} />
                    )}
                  </div>

                  {/* Контент */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="font-semibold text-sm">
                        {index + 1}. {stage.name}
                      </h3>
                      {stage.status !== 'pending' && (
                        <span className={`text-xs font-medium ${getStatusColor(stage.status)}`}>
                          {stage.status === 'completed' && '✓ Завершено'}
                          {stage.status === 'in-progress' && `${Math.round(stage.progress)}%`}
                          {stage.status === 'error' && 'Ошибка'}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground mb-2">
                      {stage.description}
                    </p>
                    
                    {/* Прогресс бар для текущей стадии */}
                    {stage.status === 'in-progress' && (
                      <Progress value={stage.progress} className="h-1.5" />
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* ID лекции (для отладки) */}
        <div className="text-center">
          <p className="text-xs text-muted-foreground">
            ID: {lessonId.substring(0, 8)}...
          </p>
        </div>
      </div>
    </Card>
  );
};
