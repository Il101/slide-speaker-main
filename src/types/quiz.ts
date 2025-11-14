/**
 * Quiz TypeScript Types
 * Type definitions for quiz generation and management
 */

export enum QuestionType {
  MULTIPLE_CHOICE = 'multiple_choice',
  MULTIPLE_SELECT = 'multiple_select',
  TRUE_FALSE = 'true_false',
  SHORT_ANSWER = 'short_answer',
}

export enum Difficulty {
  EASY = 'easy',
  MEDIUM = 'medium',
  HARD = 'hard',
  MIXED = 'mixed',
}

export enum ExportFormat {
  JSON = 'json',
  PDF = 'pdf',
  GOOGLE_FORMS = 'google_forms',
  MOODLE_XML = 'moodle',
  HTML = 'html',
}

export interface Answer {
  id: string;
  text: string;
  is_correct: boolean;
  order_index: number;
}

export interface AnswerCreate {
  text: string;
  is_correct: boolean;
}

export interface Question {
  id: string;
  quiz_id: string;
  text: string;
  type: QuestionType;
  difficulty: Difficulty;
  explanation?: string;
  points: number;
  order_index: number;
  answers: Answer[];
  created_at: string;
}

export interface QuestionCreate {
  text: string;
  type: QuestionType;
  difficulty?: Difficulty;
  explanation?: string;
  points?: number;
  answers: AnswerCreate[];
}

export interface Quiz {
  id: string;
  lesson_id: string;
  user_id: string;
  title: string;
  description?: string;
  questions: Question[];
  created_at: string;
  updated_at: string;
}

export interface QuizListItem {
  id: string;
  lesson_id: string;
  title: string;
  description?: string;
  questions_count: number;
  created_at: string;
  updated_at: string;
}

export interface QuizGenerationSettings {
  num_questions: number;
  question_types: QuestionType[];
  difficulty: Difficulty;
  language: string;
  focus_slides?: number[];
}

export interface QuizGenerateRequest {
  lesson_id: string;
  settings: QuizGenerationSettings;
}

export interface QuizCreate {
  lesson_id: string;
  title: string;
  description?: string;
  questions: QuestionCreate[];
}

export interface QuizUpdate {
  title?: string;
  description?: string;
  questions?: QuestionCreate[];
}

export interface QuizExportRequest {
  format: ExportFormat;
}

export interface QuizExportResponse {
  format: string;
  content: string;
  content_type: string;
  filename: string;
}
