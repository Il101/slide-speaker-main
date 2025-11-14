/**
 * Quiz Generator Component
 * UI for generating quizzes from lesson content
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuizGenerator } from '../hooks/useQuizGenerator';
import { QuestionType, Difficulty, ExportFormat } from '../types/quiz';
import type { QuizGenerationSettings } from '../types/quiz';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Label } from './ui/label';
import { Input } from './ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Checkbox } from './ui/checkbox';
import { Alert, AlertDescription } from './ui/alert';
import { Loader2, Download, Sparkles, CheckCircle2, XCircle } from 'lucide-react';

interface QuizGeneratorProps {
  lessonId?: string;
  standalone?: boolean;
}

export const QuizGenerator: React.FC<QuizGeneratorProps> = ({ 
  lessonId: propLessonId,
  standalone = false
}) => {
  const { lessonId: paramLessonId } = useParams<{ lessonId: string }>();
  const navigate = useNavigate();
  const lessonId = propLessonId || paramLessonId;
  const { quiz, loading, error, generateQuiz, downloadQuiz, clearError } = useQuizGenerator();

  const [settings, setSettings] = useState<QuizGenerationSettings>({
    num_questions: 10,
    question_types: [QuestionType.MULTIPLE_CHOICE],
    difficulty: Difficulty.MEDIUM,
    language: 'ru',
  });

  const [isGenerating, setIsGenerating] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  const handleGenerate = async () => {
    if (!lessonId) return;

    setIsGenerating(true);
    setShowSuccess(false);
    clearError();

    try {
      await generateQuiz(lessonId, settings);
      setShowSuccess(true);
    } catch (err) {
      console.error('Quiz generation failed:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleExport = async (format: ExportFormat) => {
    if (!quiz) return;

    try {
      const filename = `${quiz.title.replace(/\s+/g, '_')}_${quiz.id}.${format}`;
      await downloadQuiz(quiz.id, format, filename);
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  const toggleQuestionType = (type: QuestionType) => {
    setSettings((prev) => {
      const types = prev.question_types.includes(type)
        ? prev.question_types.filter((t) => t !== type)
        : [...prev.question_types, type];
      
      // Ensure at least one type is selected
      return {
        ...prev,
        question_types: types.length > 0 ? types : prev.question_types,
      };
    });
  };

  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      <div className="mb-6">
        {standalone && (
          <Button
            variant="outline"
            onClick={() => navigate(-1)}
            className="mb-4"
          >
            ← Назад к уроку
          </Button>
        )}
        <h1 className="text-3xl font-bold">Генератор тестов</h1>
        <p className="text-muted-foreground mt-2">
          Создайте тест на основе материалов лекции с помощью ИИ
        </p>
      </div>

      {/* Settings Card */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Настройки теста</CardTitle>
          <CardDescription>
            Настройте параметры генерации теста
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Number of Questions */}
          <div className="space-y-2">
            <Label htmlFor="num-questions">
              Количество вопросов: {settings.num_questions}
            </Label>
            <Input
              id="num-questions"
              type="range"
              min={5}
              max={50}
              step={5}
              value={settings.num_questions}
              onChange={(e) =>
                setSettings((prev) => ({
                  ...prev,
                  num_questions: parseInt(e.target.value),
                }))
              }
              className="w-full"
            />
            <p className="text-sm text-muted-foreground">
              От 5 до 50 вопросов
            </p>
          </div>

          {/* Question Types */}
          <div className="space-y-3">
            <Label>Типы вопросов</Label>
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="type-mc"
                  checked={settings.question_types.includes(QuestionType.MULTIPLE_CHOICE)}
                  onCheckedChange={() => toggleQuestionType(QuestionType.MULTIPLE_CHOICE)}
                />
                <label
                  htmlFor="type-mc"
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  Множественный выбор (один правильный)
                </label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="type-ms"
                  checked={settings.question_types.includes(QuestionType.MULTIPLE_SELECT)}
                  onCheckedChange={() => toggleQuestionType(QuestionType.MULTIPLE_SELECT)}
                />
                <label
                  htmlFor="type-ms"
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  Выбор нескольких ответов
                </label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="type-tf"
                  checked={settings.question_types.includes(QuestionType.TRUE_FALSE)}
                  onCheckedChange={() => toggleQuestionType(QuestionType.TRUE_FALSE)}
                />
                <label
                  htmlFor="type-tf"
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  Верно / Неверно
                </label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="type-sa"
                  checked={settings.question_types.includes(QuestionType.SHORT_ANSWER)}
                  onCheckedChange={() => toggleQuestionType(QuestionType.SHORT_ANSWER)}
                />
                <label
                  htmlFor="type-sa"
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  Краткий ответ
                </label>
              </div>
            </div>
          </div>

          {/* Difficulty */}
          <div className="space-y-2">
            <Label htmlFor="difficulty">Сложность</Label>
            <Select
              value={settings.difficulty}
              onValueChange={(value) =>
                setSettings((prev) => ({ ...prev, difficulty: value as Difficulty }))
              }
            >
              <SelectTrigger id="difficulty">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={Difficulty.EASY}>Легкий</SelectItem>
                <SelectItem value={Difficulty.MEDIUM}>Средний</SelectItem>
                <SelectItem value={Difficulty.HARD}>Сложный</SelectItem>
                <SelectItem value={Difficulty.MIXED}>Смешанный</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Language */}
          <div className="space-y-2">
            <Label htmlFor="language">Язык</Label>
            <Select
              value={settings.language}
              onValueChange={(value) =>
                setSettings((prev) => ({ ...prev, language: value }))
              }
            >
              <SelectTrigger id="language">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ru">Русский</SelectItem>
                <SelectItem value="en">English</SelectItem>
                <SelectItem value="de">Deutsch</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Generate Button */}
          <Button
            onClick={handleGenerate}
            disabled={isGenerating || loading}
            className="w-full"
            size="lg"
          >
            {isGenerating || loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Генерация теста...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                Сгенерировать тест
              </>
            )}
          </Button>

          <p className="text-xs text-muted-foreground text-center">
            Генерация займет 2-5 секунд. Используется Gemini 2.0 Flash (бесплатно).
          </p>
        </CardContent>
      </Card>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive" className="mb-6">
          <XCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Success Alert */}
      {showSuccess && quiz && (
        <Alert className="mb-6 border-green-500 bg-green-50">
          <CheckCircle2 className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">
            Тест успешно сгенерирован! {quiz.questions.length} вопросов создано.
          </AlertDescription>
        </Alert>
      )}

      {/* Generated Quiz Preview */}
      {quiz && (
        <Card>
          <CardHeader>
            <CardTitle>{quiz.title}</CardTitle>
            {quiz.description && (
              <CardDescription>{quiz.description}</CardDescription>
            )}
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Quiz Stats */}
            <div className="flex gap-4 text-sm text-muted-foreground">
              <span>Вопросов: {quiz.questions.length}</span>
              <span>•</span>
              <span>Создан: {new Date(quiz.created_at).toLocaleDateString('ru-RU')}</span>
            </div>

            {/* Questions Preview */}
            <div className="space-y-4 mt-6">
              <h3 className="font-semibold text-lg">Вопросы:</h3>
              {quiz.questions.slice(0, 3).map((question, index) => (
                <div
                  key={question.id}
                  className="p-4 border rounded-lg bg-muted/30"
                >
                  <p className="font-medium mb-2">
                    {index + 1}. {question.text}
                  </p>
                  <div className="space-y-1 ml-4">
                    {question.answers.map((answer, aIndex) => (
                      <div
                        key={answer.id}
                        className={`text-sm ${
                          answer.is_correct ? 'text-green-600 font-medium' : 'text-muted-foreground'
                        }`}
                      >
                        {String.fromCharCode(65 + aIndex)}. {answer.text}
                        {answer.is_correct && ' ✓'}
                      </div>
                    ))}
                  </div>
                  {question.explanation && (
                    <p className="text-xs text-muted-foreground mt-2 ml-4">
                      💡 {question.explanation}
                    </p>
                  )}
                </div>
              ))}
              {quiz.questions.length > 3 && (
                <p className="text-sm text-muted-foreground text-center">
                  ... и еще {quiz.questions.length - 3} вопросов
                </p>
              )}
            </div>

            {/* Export Buttons */}
            <div className="flex flex-wrap gap-2 mt-6 pt-6 border-t">
              <Button
                variant="outline"
                onClick={() => handleExport(ExportFormat.JSON)}
                disabled={loading}
              >
                <Download className="mr-2 h-4 w-4" />
                JSON
              </Button>
              <Button
                variant="outline"
                onClick={() => handleExport(ExportFormat.MOODLE_XML)}
                disabled={loading}
              >
                <Download className="mr-2 h-4 w-4" />
                Moodle XML
              </Button>
              <Button
                variant="outline"
                onClick={() => handleExport(ExportFormat.HTML)}
                disabled={loading}
              >
                <Download className="mr-2 h-4 w-4" />
                HTML
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Info Card */}
      {!quiz && !isGenerating && (
        <Card className="bg-muted/30">
          <CardContent className="pt-6">
            <h3 className="font-semibold mb-2">ℹ️ Как это работает</h3>
            <ul className="space-y-1 text-sm text-muted-foreground">
              <li>• ИИ анализирует содержание вашей лекции</li>
              <li>• Генерирует вопросы на основе ключевых концепций</li>
              <li>• Создает правдоподобные варианты ответов</li>
              <li>• Добавляет объяснения к правильным ответам</li>
              <li>• Экспортируйте в Moodle, JSON или HTML</li>
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default QuizGenerator;
