import React, { useState } from 'react';
import { Brain, Mic, Video, Zap, ArrowRight, PlayCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { FileUploader } from '@/components/FileUploader';
import { Player } from '@/components/Player';
import { MyVideosSidebar } from '@/components/MyVideosSidebar';
import Navigation from '@/components/Navigation';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import { apiClient } from '@/lib/api';

type AppState = 'landing' | 'upload' | 'player';

const Index = () => {
  const { isAuthenticated, user } = useAuth();
  const [appState, setAppState] = useState<AppState>(() => {
    // Восстанавливаем состояние из localStorage при загрузке
    const savedState = localStorage.getItem('slide-speaker-app-state');
    if (savedState) {
      try {
        const parsed = JSON.parse(savedState);
        // Проверяем, не устарели ли данные (старше 24 часов)
        const isExpired = Date.now() - parsed.timestamp > 24 * 60 * 60 * 1000;
        if (!isExpired) {
          return parsed.appState;
        }
      } catch (e) {
        console.warn('Failed to parse saved app state:', e);
      }
    }
    return 'landing';
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [lessonId, setLessonId] = useState<string | null>(() => {
    // Восстанавливаем lessonId из localStorage при загрузке
    const savedState = localStorage.getItem('slide-speaker-app-state');
    if (savedState) {
      try {
        const parsed = JSON.parse(savedState);
        // Проверяем, не устарели ли данные (старше 24 часов)
        const isExpired = Date.now() - parsed.timestamp > 24 * 60 * 60 * 1000;
        if (!isExpired) {
          return parsed.lessonId;
        }
      } catch (e) {
        console.warn('Failed to parse saved app state:', e);
      }
    }
    return null;
  });

  // Функция для сохранения состояния в localStorage
  const saveAppState = (newAppState: AppState, newLessonId: string | null) => {
    const stateToSave = {
      appState: newAppState,
      lessonId: newLessonId,
      timestamp: Date.now()
    };
    localStorage.setItem('slide-speaker-app-state', JSON.stringify(stateToSave));
  };

  const handleUploadSuccess = (id: string) => {
    setLessonId(id);
    setAppState('player');
    saveAppState('player', id);
    toast.success('Лекция готова! Запустите воспроизведение.');
  };

  const handleExportMP4 = () => {
    toast.success('Экспорт начат! Ссылка на готовое видео будет отправлена на email.');
  };

  const handleStartDemo = () => {
    // Для демо используем фиксированный lesson_id
    setLessonId('demo-lesson');
    setAppState('player');
    saveAppState('player', 'demo-lesson');
    toast.success('Демо загружено! Попробуйте плеер.');
  };

  const handleCreateNewLesson = () => {
    setAppState('landing');
    setLessonId(null);
    saveAppState('landing', null);
  };

  const handleVideoSelect = (videoLessonId: string) => {
    setLessonId(videoLessonId);
    setAppState('player');
    saveAppState('player', videoLessonId);
  };

  const handleVideoDownload = (videoUrl: string, title: string) => {
    // Создаем временную ссылку для загрузки
    const link = document.createElement('a');
    link.href = videoUrl;
    link.download = `${title}.mp4`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success('Загрузка видео начата');
  };

  if (appState === 'player') {
    return (
      <div className="min-h-screen hero-gradient">
        <Navigation />
        <div className="flex">
          {/* Основной контент - плеер */}
          <div className="flex-1 p-6">
            <div className="max-w-6xl mx-auto">
              <div className="mb-6 flex items-center justify-between">
                <div>
                  <h1 className="text-2xl font-bold text-foreground">
                    {selectedFile?.name || 'Демо лекция'}
                  </h1>
                  <p className="text-muted-foreground">
                    Интерактивная лекция с озвучкой и визуальными эффектами
                  </p>
                </div>
                <Button
                  variant="outline"
                  onClick={handleCreateNewLesson}
                >
                  Создать новую лекцию
                </Button>
              </div>
              
              {lessonId && (
                <Player 
                  lessonId={lessonId}
                  onExportMP4={handleExportMP4}
                />
              )}
            </div>
          </div>

          {/* Сайдбар справа с видео для авторизованных пользователей */}
          {isAuthenticated && (
            <div className="w-[560px]">
              <MyVideosSidebar
                currentLessonId={lessonId || undefined}
                onVideoSelect={handleVideoSelect}
                onVideoDownload={handleVideoDownload}
              />
            </div>
          )}
        </div>
      </div>
    );
  }


  if (appState === 'upload') {
    return (
      <div className="min-h-screen hero-gradient">
        <Navigation />
        <div className="flex">
          {/* Основной контент - форма загрузки */}
          <div className="flex-1 p-6">
            <div className="max-w-4xl mx-auto">
              <div className="text-center mb-8">
                <Button
                  variant="ghost"
                  onClick={() => setAppState('landing')}
                  className="mb-4"
                >
                  ← Назад
                </Button>
                <h1 className="text-3xl font-bold text-foreground mb-2">
                  Загрузите презентацию
                </h1>
                <p className="text-muted-foreground">
                  Поддерживаются форматы PPTX и PDF
                </p>
              </div>
              
              <FileUploader
                onUploadSuccess={handleUploadSuccess}
              />
            </div>
          </div>

          {/* Сайдбар справа с видео для авторизованных пользователей */}
          {isAuthenticated && (
            <div className="w-[560px]">
              <MyVideosSidebar
                currentLessonId={lessonId || undefined}
                onVideoSelect={handleVideoSelect}
                onVideoDownload={handleVideoDownload}
              />
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen hero-gradient">
      <Navigation />
      <div className="flex">
        {/* Основной контент */}
        <div className="flex-1">
          {/* Hero Section */}
          <div className="container mx-auto px-6 py-20">
        <div className="text-center mb-16 animate-fade-in-up">
          <div className="flex items-center justify-center mb-6">
            <Brain className="h-16 w-16 text-primary mr-4" />
            <h1 className="text-5xl font-bold text-foreground">
              ИИ-Лектор
            </h1>
          </div>
          <p className="text-xl text-muted-foreground mb-8 max-w-3xl mx-auto">
            Превращаем ваши презентации в интерактивные лекции с озвучкой, 
            визуальными акцентами и синхронизированными эффектами
          </p>
          <div className="flex items-center justify-center space-x-4">
            <Button
              size="lg"
              onClick={() => setAppState('upload')}
              variant="gradient-glow"
              className="text-lg px-8 py-3"
            >
              Создать лекцию
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              onClick={handleStartDemo}
              className="text-lg px-8 py-3"
            >
              <PlayCircle className="mr-2 h-5 w-5" />
              Посмотреть демо
            </Button>
          </div>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          <Card className="p-6 text-center card-gradient card-shadow smooth-transition hover:scale-105">
            <Mic className="h-12 w-12 text-primary mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-3">Естественная озвучка</h3>
            <p className="text-muted-foreground">
              ИИ генерирует естественную речь на основе содержимого слайдов
            </p>
          </Card>

          <Card className="p-6 text-center card-gradient card-shadow smooth-transition hover:scale-105">
            <Zap className="h-12 w-12 text-accent mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-3">Визуальные акценты</h3>
            <p className="text-muted-foreground">
              Подсветки, подчёркивания и лазерная указка синхронизированы с речью
            </p>
          </Card>

          <Card className="p-6 text-center card-gradient card-shadow smooth-transition hover:scale-105">
            <Video className="h-12 w-12 text-primary mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-3">Экспорт в MP4</h3>
            <p className="text-muted-foreground">
              Получите готовое видео одним кликом для любых целей
            </p>
          </Card>
        </div>

        {/* How it Works */}
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-foreground mb-12">
            Как это работает
          </h2>
          <div className="grid md:grid-cols-4 gap-6">
            {[
              { step: '1', title: 'Загрузите', desc: 'PPTX или PDF файл' },
              { step: '2', title: 'Обработка', desc: 'ИИ анализирует содержимое' },
              { step: '3', title: 'Воспроизведение', desc: 'Интерактивный плеер' },
              { step: '4', title: 'Экспорт', desc: 'Готовое MP4 видео' }
            ].map((item, index) => (
              <div key={index} className="text-center">
                <div className="w-12 h-12 rounded-full primary-gradient text-primary-foreground font-bold text-xl flex items-center justify-center mx-auto mb-4 glow-effect">
                  {item.step}
                </div>
                <h4 className="font-semibold mb-2">{item.title}</h4>
                <p className="text-sm text-muted-foreground">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div className="text-center">
          <Card className="p-8 card-gradient card-shadow max-w-2xl mx-auto">
            <h3 className="text-2xl font-bold text-foreground mb-4">
              Готовы создать первую лекцию?
            </h3>
            <p className="text-muted-foreground mb-6">
              Загрузите презентацию и получите профессиональную лекцию с озвучкой за несколько минут
            </p>
            <Button
              size="lg"
              onClick={() => setAppState('upload')}
              variant="gradient-glow"
            >
              Начать сейчас
            </Button>
          </Card>
        </div>
      </div>
    </div>

    {/* Сайдбар справа с видео для авторизованных пользователей */}
    {isAuthenticated && (
      <div className="w-[560px]">
        <MyVideosSidebar
          currentLessonId={lessonId || undefined}
          onVideoSelect={handleVideoSelect}
          onVideoDownload={handleVideoDownload}
        />
      </div>
    )}
  </div>
    </div>
  );
};

export default Index;