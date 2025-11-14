/**
 * Quiz Editor Component
 * Advanced editor for modifying quiz questions and answers
 */
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useQuizGenerator } from '../hooks/useQuizGenerator';
import type { Quiz, QuestionCreate, AnswerCreate, QuestionType, Difficulty } from '../types/quiz';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Alert, AlertDescription } from './ui/alert';
import { Loader2, Save, Plus, Trash2, GripVertical, X, CheckCircle2 } from 'lucide-react';
import { Checkbox } from './ui/checkbox';

interface QuizEditorProps {
  quizId?: string;
  onSaved?: (quiz: Quiz) => void;
  onClose?: () => void;
}

export const QuizEditor: React.FC<QuizEditorProps> = ({ quizId: propQuizId, onSaved, onClose }) => {
  const { quizId: paramQuizId } = useParams<{ quizId: string }>();
  const quizId = propQuizId || paramQuizId;
  const { quiz, loading, error, loadQuiz, updateQuiz } = useQuizGenerator();
  
  const [editedTitle, setEditedTitle] = useState('');
  const [editedDescription, setEditedDescription] = useState('');
  const [editedQuestions, setEditedQuestions] = useState<QuestionCreate[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  // Load quiz on mount
  useEffect(() => {
    loadQuiz(quizId);
  }, [quizId]);

  // Initialize edited state when quiz loads
  useEffect(() => {
    if (quiz) {
      setEditedTitle(quiz.title);
      setEditedDescription(quiz.description || '');
      setEditedQuestions(
        quiz.questions.map((q) => ({
          text: q.text,
          type: q.type,
          difficulty: q.difficulty,
          explanation: q.explanation,
          points: q.points,
          answers: q.answers.map((a) => ({
            text: a.text,
            is_correct: a.is_correct,
          })),
        }))
      );
    }
  }, [quiz]);

  const handleSave = async () => {
    setIsSaving(true);
    setShowSuccess(false);

    try {
      const updated = await updateQuiz(quizId, {
        title: editedTitle,
        description: editedDescription,
        questions: editedQuestions,
      });
      
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
      
      if (onSaved) {
        onSaved(updated);
      }
    } catch (err) {
      console.error('Failed to save quiz:', err);
    } finally {
      setIsSaving(false);
    }
  };

  const updateQuestion = (index: number, updates: Partial<QuestionCreate>) => {
    setEditedQuestions((prev) => {
      const newQuestions = [...prev];
      newQuestions[index] = { ...newQuestions[index], ...updates };
      return newQuestions;
    });
  };

  const updateAnswer = (questionIndex: number, answerIndex: number, updates: Partial<AnswerCreate>) => {
    setEditedQuestions((prev) => {
      const newQuestions = [...prev];
      newQuestions[questionIndex].answers[answerIndex] = {
        ...newQuestions[questionIndex].answers[answerIndex],
        ...updates,
      };
      return newQuestions;
    });
  };

  const addAnswer = (questionIndex: number) => {
    setEditedQuestions((prev) => {
      const newQuestions = [...prev];
      newQuestions[questionIndex].answers.push({
        text: 'Новый вариант',
        is_correct: false,
      });
      return newQuestions;
    });
  };

  const removeAnswer = (questionIndex: number, answerIndex: number) => {
    setEditedQuestions((prev) => {
      const newQuestions = [...prev];
      if (newQuestions[questionIndex].answers.length > 2) {
        newQuestions[questionIndex].answers.splice(answerIndex, 1);
      }
      return newQuestions;
    });
  };

  const addQuestion = () => {
    setEditedQuestions((prev) => [
      ...prev,
      {
        text: 'Новый вопрос',
        type: 'multiple_choice' as QuestionType,
        difficulty: 'medium' as Difficulty,
        explanation: '',
        points: 1,
        answers: [
          { text: 'Вариант A', is_correct: true },
          { text: 'Вариант B', is_correct: false },
          { text: 'Вариант C', is_correct: false },
          { text: 'Вариант D', is_correct: false },
        ],
      },
    ]);
  };

  const removeQuestion = (index: number) => {
    if (editedQuestions.length > 1) {
      setEditedQuestions((prev) => prev.filter((_, i) => i !== index));
    }
  };

  const moveQuestion = (index: number, direction: 'up' | 'down') => {
    const newIndex = direction === 'up' ? index - 1 : index + 1;
    if (newIndex >= 0 && newIndex < editedQuestions.length) {
      setEditedQuestions((prev) => {
        const newQuestions = [...prev];
        [newQuestions[index], newQuestions[newIndex]] = [newQuestions[newIndex], newQuestions[index]];
        return newQuestions;
      });
    }
  };

  if (loading && !quiz) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error && !quiz) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Редактор теста</h2>
          <p className="text-muted-foreground text-sm">
            {editedQuestions.length} вопросов
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={handleSave}
            disabled={isSaving}
            size="lg"
          >
            {isSaving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Сохранение...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Сохранить
              </>
            )}
          </Button>
          {onClose && (
            <Button variant="outline" onClick={onClose} size="lg">
              <X className="mr-2 h-4 w-4" />
              Закрыть
            </Button>
          )}
        </div>
      </div>

      {/* Success Alert */}
      {showSuccess && (
        <Alert className="border-green-500 bg-green-50">
          <CheckCircle2 className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">
            Изменения успешно сохранены!
          </AlertDescription>
        </Alert>
      )}

      {/* Quiz Metadata */}
      <Card>
        <CardHeader>
          <CardTitle>Основная информация</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="quiz-title">Название теста</Label>
            <Input
              id="quiz-title"
              value={editedTitle}
              onChange={(e) => setEditedTitle(e.target.value)}
              placeholder="Введите название теста"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="quiz-description">Описание (опционально)</Label>
            <Textarea
              id="quiz-description"
              value={editedDescription}
              onChange={(e) => setEditedDescription(e.target.value)}
              placeholder="Краткое описание теста"
              rows={2}
            />
          </div>
        </CardContent>
      </Card>

      {/* Questions */}
      <div className="space-y-4">
        {editedQuestions.map((question, qIndex) => (
          <Card key={qIndex} className="relative">
            <CardHeader className="pb-3">
              <div className="flex items-start gap-3">
                <div className="flex flex-col gap-1 mt-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => moveQuestion(qIndex, 'up')}
                    disabled={qIndex === 0}
                    className="h-6 w-6 p-0"
                  >
                    <GripVertical className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => moveQuestion(qIndex, 'down')}
                    disabled={qIndex === editedQuestions.length - 1}
                    className="h-6 w-6 p-0"
                  >
                    <GripVertical className="h-4 w-4" />
                  </Button>
                </div>
                <div className="flex-1 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold text-muted-foreground">
                      Вопрос {qIndex + 1}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeQuestion(qIndex)}
                      disabled={editedQuestions.length === 1}
                      className="text-destructive hover:text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>

                  <Textarea
                    value={question.text}
                    onChange={(e) => updateQuestion(qIndex, { text: e.target.value })}
                    placeholder="Текст вопроса"
                    rows={2}
                  />

                  <div className="flex gap-4">
                    <div className="flex-1">
                      <Label className="text-xs">Тип</Label>
                      <Select
                        value={question.type}
                        onValueChange={(value) =>
                          updateQuestion(qIndex, { type: value as QuestionType })
                        }
                      >
                        <SelectTrigger className="h-9">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="multiple_choice">Один ответ</SelectItem>
                          <SelectItem value="multiple_select">Несколько</SelectItem>
                          <SelectItem value="true_false">Верно/Неверно</SelectItem>
                          <SelectItem value="short_answer">Краткий</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="flex-1">
                      <Label className="text-xs">Сложность</Label>
                      <Select
                        value={question.difficulty}
                        onValueChange={(value) =>
                          updateQuestion(qIndex, { difficulty: value as Difficulty })
                        }
                      >
                        <SelectTrigger className="h-9">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="easy">Легкий</SelectItem>
                          <SelectItem value="medium">Средний</SelectItem>
                          <SelectItem value="hard">Сложный</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="w-20">
                      <Label className="text-xs">Баллы</Label>
                      <Input
                        type="number"
                        min={1}
                        max={10}
                        value={question.points}
                        onChange={(e) =>
                          updateQuestion(qIndex, { points: parseInt(e.target.value) || 1 })
                        }
                        className="h-9"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {/* Answers */}
              <div className="space-y-2">
                <Label className="text-sm font-medium">Варианты ответов</Label>
                {question.answers.map((answer, aIndex) => (
                  <div key={aIndex} className="flex items-center gap-2">
                    <Checkbox
                      checked={answer.is_correct}
                      onCheckedChange={(checked) =>
                        updateAnswer(qIndex, aIndex, { is_correct: !!checked })
                      }
                    />
                    <Input
                      value={answer.text}
                      onChange={(e) =>
                        updateAnswer(qIndex, aIndex, { text: e.target.value })
                      }
                      placeholder={`Вариант ${String.fromCharCode(65 + aIndex)}`}
                      className="flex-1"
                    />
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeAnswer(qIndex, aIndex)}
                      disabled={question.answers.length <= 2}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => addAnswer(qIndex)}
                  className="w-full"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Добавить вариант
                </Button>
              </div>

              {/* Explanation */}
              <div className="space-y-2">
                <Label htmlFor={`explanation-${qIndex}`} className="text-sm">
                  Объяснение (опционально)
                </Label>
                <Textarea
                  id={`explanation-${qIndex}`}
                  value={question.explanation || ''}
                  onChange={(e) =>
                    updateQuestion(qIndex, { explanation: e.target.value })
                  }
                  placeholder="Почему этот ответ правильный?"
                  rows={2}
                />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Add Question Button */}
      <Button
        variant="outline"
        onClick={addQuestion}
        className="w-full"
        size="lg"
      >
        <Plus className="h-5 w-5 mr-2" />
        Добавить вопрос
      </Button>

      {/* Bottom Save Button */}
      <div className="flex justify-end gap-2 pt-4 border-t">
        {onClose && (
          <Button variant="outline" onClick={onClose} size="lg">
            Закрыть
          </Button>
        )}
        <Button onClick={handleSave} disabled={isSaving} size="lg">
          {isSaving ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Сохранение...
            </>
          ) : (
            <>
              <Save className="mr-2 h-4 w-4" />
              Сохранить изменения
            </>
          )}
        </Button>
      </div>
    </div>
  );
};

export default QuizEditor;
