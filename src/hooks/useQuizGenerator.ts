/**
 * Quiz Generator Hook
 * React hook for quiz generation and management
 */
import { useState, useCallback } from 'react';
import { quizApi } from '../lib/quizApi';
import type {
  Quiz,
  QuizListItem,
  QuizGenerationSettings,
  QuizUpdate,
  ExportFormat,
} from '../types/quiz';

interface UseQuizGeneratorReturn {
  quiz: Quiz | null;
  quizzes: QuizListItem[];
  loading: boolean;
  error: string | null;
  generateQuiz: (
    lessonId: string,
    settings: QuizGenerationSettings
  ) => Promise<Quiz>;
  loadQuiz: (quizId: string) => Promise<Quiz>;
  updateQuiz: (quizId: string, updates: QuizUpdate) => Promise<Quiz>;
  deleteQuiz: (quizId: string) => Promise<void>;
  loadLessonQuizzes: (lessonId: string) => Promise<QuizListItem[]>;
  exportQuiz: (quizId: string, format: ExportFormat) => Promise<string>;
  downloadQuiz: (quizId: string, format: ExportFormat, filename: string) => Promise<void>;
  clearError: () => void;
}

export const useQuizGenerator = (): UseQuizGeneratorReturn => {
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [quizzes, setQuizzes] = useState<QuizListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const generateQuiz = useCallback(
    async (
      lessonId: string,
      settings: QuizGenerationSettings
    ): Promise<Quiz> => {
      setLoading(true);
      setError(null);

      try {
        const result = await quizApi.generate({
          lesson_id: lessonId,
          settings,
        });
        setQuiz(result);
        return result;
      } catch (err: any) {
        const message = err.message || 'Failed to generate quiz';
        setError(message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const loadQuiz = useCallback(async (quizId: string): Promise<Quiz> => {
    setLoading(true);
    setError(null);

    try {
      const result = await quizApi.get(quizId);
      setQuiz(result);
      return result;
    } catch (err: any) {
      const message = err.message || 'Failed to load quiz';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const updateQuiz = useCallback(
    async (quizId: string, updates: QuizUpdate): Promise<Quiz> => {
      setLoading(true);
      setError(null);

      try {
        const result = await quizApi.update(quizId, updates);
        setQuiz(result);
        return result;
      } catch (err: any) {
        const message = err.message || 'Failed to update quiz';
        setError(message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const deleteQuiz = useCallback(async (quizId: string): Promise<void> => {
    setLoading(true);
    setError(null);

    try {
      await quizApi.delete(quizId);
      setQuiz(null);
      // Remove from list if present
      setQuizzes((prev) => prev.filter((q) => q.id !== quizId));
    } catch (err: any) {
      const message = err.message || 'Failed to delete quiz';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const loadLessonQuizzes = useCallback(
    async (lessonId: string): Promise<QuizListItem[]> => {
      setLoading(true);
      setError(null);

      try {
        const result = await quizApi.getByLesson(lessonId);
        setQuizzes(result);
        return result;
      } catch (err: any) {
        const message = err.message || 'Failed to load quizzes';
        setError(message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const exportQuiz = useCallback(
    async (quizId: string, format: ExportFormat): Promise<string> => {
      setLoading(true);
      setError(null);

      try {
        const result = await quizApi.export(quizId, { format });
        return result.content;
      } catch (err: any) {
        const message = err.message || 'Failed to export quiz';
        setError(message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const downloadQuiz = useCallback(
    async (quizId: string, format: ExportFormat, filename: string): Promise<void> => {
      setLoading(true);
      setError(null);

      try {
        await quizApi.downloadExport(quizId, format, filename);
      } catch (err: any) {
        const message = err.message || 'Failed to download quiz';
        setError(message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return {
    quiz,
    quizzes,
    loading,
    error,
    generateQuiz,
    loadQuiz,
    updateQuiz,
    deleteQuiz,
    loadLessonQuizzes,
    exportQuiz,
    downloadQuiz,
    clearError,
  };
};
