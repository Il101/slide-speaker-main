import React from 'react';
import { FileVideo, Upload, Search, AlertCircle, Inbox } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export const EmptyState: React.FC<EmptyStateProps> = ({ 
  title, 
  description, 
  icon, 
  action 
}) => (
  <Card className="flex flex-col items-center justify-center py-12 px-4 text-center">
    {icon && (
      <div className="mb-4 text-muted-foreground">
        {icon}
      </div>
    )}
    <h3 className="text-lg font-semibold mb-2">{title}</h3>
    <p className="text-muted-foreground text-sm mb-6 max-w-md">
      {description}
    </p>
    {action && (
      <Button onClick={action.onClick}>
        {action.label}
      </Button>
    )}
  </Card>
);

export const EmptyVideos: React.FC<{ onAction?: () => void }> = ({ onAction }) => (
  <EmptyState
    icon={<FileVideo className="h-16 w-16" />}
    title="Нет загруженных лекций"
    description="Начните с загрузки вашей первой презентации. ИИ превратит её в интерактивную лекцию с озвучкой."
    action={onAction ? {
      label: 'Загрузить презентацию',
      onClick: onAction
    } : undefined}
  />
);

export const EmptySearch: React.FC<{ query: string; onClear?: () => void }> = ({ 
  query, 
  onClear 
}) => (
  <EmptyState
    icon={<Search className="h-16 w-16" />}
    title="Ничего не найдено"
    description={`По запросу "${query}" ничего не найдено. Попробуйте изменить поисковый запрос.`}
    action={onClear ? {
      label: 'Очистить поиск',
      onClick: onClear
    } : undefined}
  />
);

export const EmptyInbox: React.FC = () => (
  <EmptyState
    icon={<Inbox className="h-16 w-16" />}
    title="Все задачи выполнены"
    description="У вас нет новых уведомлений или задач."
  />
);

export const ErrorState: React.FC<{ 
  title?: string;
  message: string; 
  onRetry?: () => void;
}> = ({ 
  title = 'Произошла ошибка',
  message, 
  onRetry 
}) => (
  <EmptyState
    icon={<AlertCircle className="h-16 w-16 text-destructive" />}
    title={title}
    description={message}
    action={onRetry ? {
      label: 'Повторить попытку',
      onClick: onRetry
    } : undefined}
  />
);

export const EmptyUploadZone: React.FC<{ 
  isDragActive?: boolean;
  onUpload?: () => void;
}> = ({ isDragActive, onUpload }) => (
  <div className={`
    border-2 border-dashed rounded-lg p-12 text-center
    transition-colors
    ${isDragActive 
      ? 'border-primary bg-primary/5' 
      : 'border-muted-foreground/25 hover:border-primary/50'
    }
  `}>
    <Upload className={`
      h-16 w-16 mx-auto mb-4
      ${isDragActive ? 'text-primary' : 'text-muted-foreground'}
    `} />
    <h3 className="text-lg font-semibold mb-2">
      {isDragActive ? 'Отпустите файл здесь' : 'Загрузите презентацию'}
    </h3>
    <p className="text-muted-foreground text-sm mb-4">
      {isDragActive 
        ? 'Файл готов к загрузке'
        : 'Перетащите файл сюда или нажмите для выбора'
      }
    </p>
    <p className="text-xs text-muted-foreground">
      Поддерживаются форматы: PPTX, PDF
    </p>
    {onUpload && !isDragActive && (
      <Button onClick={onUpload} className="mt-4">
        Выбрать файл
      </Button>
    )}
  </div>
);
