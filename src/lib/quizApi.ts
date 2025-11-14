/**
 * Quiz API Service
 * HTTP client for quiz generation and management endpoints
 */
import axios, { AxiosError } from 'axios';
import { apiClient } from './api';
import type {
  Quiz,
  QuizListItem,
  QuizGenerateRequest,
  QuizCreate,
  QuizUpdate,
  QuizExportRequest,
  QuizExportResponse,
} from '../types/quiz';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Create axios config with auth headers and credentials
 */
function getConfig() {
  const headers = apiClient.getAuthHeaders();
  return {
    headers,
    withCredentials: true, // Include cookies for same-origin requests
  };
}

/**
 * Handle API errors
 */
function handleError(error: unknown): never {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail: string }>;
    const message =
      axiosError.response?.data?.detail ||
      axiosError.message ||
      'An error occurred';
    throw new Error(message);
  }
  throw error;
}

export const quizApi = {
  /**
   * Generate a quiz from lesson content using AI
   */
  async generate(request: QuizGenerateRequest): Promise<Quiz> {
    try {
      const response = await axios.post<Quiz>(
        `${API_BASE}/api/quizzes/generate`,
        request,
        getConfig()
      );
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Get a quiz by ID
   */
  async get(quizId: string): Promise<Quiz> {
    try {
      const response = await axios.get<Quiz>(
        `${API_BASE}/api/quizzes/${quizId}`,
        getConfig()
      );
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Update a quiz (title, description, questions)
   */
  async update(quizId: string, data: QuizUpdate): Promise<Quiz> {
    try {
      const response = await axios.put<Quiz>(
        `${API_BASE}/api/quizzes/${quizId}`,
        data,
        getConfig()
      );
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Delete a quiz
   */
  async delete(quizId: string): Promise<void> {
    try {
      await axios.delete(`${API_BASE}/api/quizzes/${quizId}`, getConfig());
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Get all quizzes for a lesson
   */
  async getByLesson(lessonId: string): Promise<QuizListItem[]> {
    try {
      const response = await axios.get<QuizListItem[]>(
        `${API_BASE}/api/quizzes/lesson/${lessonId}`,
        getConfig()
      );
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Export quiz to various formats (JSON, Moodle XML, HTML)
   */
  async export(
    quizId: string,
    format: QuizExportRequest
  ): Promise<QuizExportResponse> {
    try {
      const response = await axios.post<QuizExportResponse>(
        `${API_BASE}/api/quizzes/${quizId}/export`,
        format,
        getConfig()
      );
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Download quiz export as file
   */
  async downloadExport(quizId: string, format: string, filename: string): Promise<void> {
    try {
      const exportData = await this.export(quizId, { format: format as any });
      
      // Create blob based on content type
      const blob = new Blob([exportData.content], {
        type: exportData.content_type || 'text/plain',
      });
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = exportData.filename || filename;
      document.body.appendChild(a);
      a.click();
      
      // Cleanup
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      handleError(error);
    }
  },
};
