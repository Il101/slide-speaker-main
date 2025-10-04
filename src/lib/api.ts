const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

// Утилита для валидации URL
export const validateAssetUrl = (url: string): boolean => {
  if (!url) return false;
  try {
    const parsed = new URL(url, window.location.origin);
    // Разрешаем относительные URL или URL с тем же origin
    if (parsed.origin !== window.location.origin && parsed.protocol !== 'data:') {
      console.warn('SSRF protection: Only relative URLs allowed', url);
      return false;
    }
    return true;
  } catch {
    return false;
  }
};

// Утилита для получения полного URL изображения
export const getImageUrl = (relativePath: string | null): string | null => {
  if (!relativePath) return null;
  if (!validateAssetUrl(relativePath)) return null;
  
  // Если это уже полный URL или data URL, вернуть как есть
  if (relativePath.startsWith('http') || relativePath.startsWith('data:')) {
    return relativePath;
  }
  
  // Добавить API_BASE к относительному пути
  return `${API_BASE}${relativePath}`;
};

// Типы для авторизации
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface UserResponse {
  user_id: string;
  email: string;
  role: string;
}

// Типы для библиотеки видео
export interface VideoPreview {
  lesson_id: string;
  title: string;
  thumbnail_url: string | null;
  duration: number | null;
  slides_count: number | null;
  status: string;
  created_at: string;
  updated_at: string;
  video_url: string | null;
  video_size: number | null;
  can_play: boolean;
}

export interface UserVideosResponse {
  videos: VideoPreview[];
  total: number;
}

export interface UploadResponse {
  lesson_id: string;
}

export interface SlideElement {
  id: string;
  type: string;
  bbox: [number, number, number, number];
  text?: string;
  confidence: number;
}

export interface Cue {
  cue_id?: string;
  t0: number;
  t1: number;
  action: 'highlight' | 'underline' | 'laser_move';
  bbox?: [number, number, number, number];
  to?: [number, number];
  element_id?: string;
}

export interface Slide {
  id: number;
  image: string;
  audio: string;
  audio_path?: string;
  elements: SlideElement[];
  cues: Cue[];
  speaker_notes?: string | Array<{
    text: string;
    targetId?: string;
    target?: {
      type: string;
      tableId?: string;
      cells?: string[];
    };
  }>;
  speaker_notes_ssml?: string;
  lecture_text?: string;
  talk_track?: Array<{
    kind: string;
    text: string;
  }>;
  visual_cues?: Array<{
    at: string;
    targetId: string;
  }>;
  concepts?: {
    title?: string;
    key_theses?: string[];
    visual_insight?: string;
  };
  terms_to_define?: string[];
  duration?: number;
}

export interface TimelineRule {
  action_type: string;
  min_duration: number;
  max_duration: number;
  priority: number;
  gap_before: number;
  gap_after: number;
}

export interface Timeline {
  rules: TimelineRule[];
  default_duration: number;
  transition_duration: number;
  min_highlight_duration: number;
  min_gap: number;
  max_total_duration: number;
  smoothness_enabled: boolean;
}

export interface Manifest {
  slides: Slide[];
  timeline?: Timeline;
  lecture_outline?: {
    outline: Array<{
      idx: number;
      goal: string;
    }>;
    narrative_rules: string[];
  };
  course_title?: string;
  lecture_title?: string;
  audience_level?: string;
  style_preset?: string;
}

export interface ExportResponse {
  status: string;
  download_url: string;
  estimated_time: string;
}

export interface CuePatch {
  cue_id?: string;
  t0?: number;
  t1?: number;
  action?: string;
  bbox?: [number, number, number, number];
  to?: [number, number];
  element_id?: string;
}

export interface ElementPatch {
  element_id: string;
  bbox?: [number, number, number, number];
  text?: string;
  confidence?: number;
}

export interface SlidePatch {
  slide_id: number;
  speaker_notes?: string;
  duration?: number;
  cues?: CuePatch[];
  elements?: ElementPatch[];
}

export interface LessonPatchRequest {
  lesson_id: string;
  slides: SlidePatch[];
  timeline?: Partial<Timeline>;
}

export interface PatchResponse {
  success: boolean;
  message: string;
  updated_slides: number[];
  validation_issues: string[];
}

export interface ProcessingStatus {
  lesson_id: string;
  status: 'processing' | 'completed' | 'failed' | 'exporting';
  progress: number;
  stage: string;
  message: string;
}

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  // Получение CSRF токена из cookie
  private getCsrfToken(): string | null {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      const [name, value] = cookie.trim().split('=');
      if (name === 'csrf_token') {
        return value;
      }
    }
    return null;
  }

  // Получение JWT токена из localStorage
  private getAuthToken(): string | null {
    return localStorage.getItem('slide-speaker-auth-token');
  }

  // Создание заголовков для запросов
  private getHeaders(includeAuth: boolean = true, includeCsrf: boolean = false): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (includeAuth) {
      const token = this.getAuthToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
        console.log('[API] Auth token found and added to headers');
      } else {
        console.warn('[API] No auth token found in localStorage!');
      }
    }

    if (includeCsrf) {
      const csrfToken = this.getCsrfToken();
      if (csrfToken) {
        headers['X-CSRF-Token'] = csrfToken;
      }
    }

    return headers;
  }

  // Обработка ответов с проверкой авторизации
  private async handleResponse<T>(response: Response): Promise<T> {
    if (response.status === 401) {
      // Токен недействителен, очищаем данные
      localStorage.removeItem('slide-speaker-auth-token');
      localStorage.removeItem('slide-speaker-user');
      // Можно добавить редирект на страницу входа
      throw new Error('Unauthorized');
    }

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Request failed: ${response.status} ${response.statusText} - ${errorText}`);
    }

    return response.json();
  }

  // Методы авторизации
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: 'POST',
      headers: this.getHeaders(false, false), // Не включаем авторизацию и CSRF
      body: JSON.stringify(credentials),
    });

    return this.handleResponse<LoginResponse>(response);
  }

  async getCurrentUser(): Promise<UserResponse> {
    const response = await fetch(`${this.baseUrl}/auth/me`, {
      method: 'GET',
      headers: this.getHeaders(true, false), // Включаем авторизацию
    });

    return this.handleResponse<UserResponse>(response);
  }

  async testAuth(): Promise<{ message: string; features: string[] }> {
    const response = await fetch(`${this.baseUrl}/test-auth`, {
      method: 'GET',
      headers: this.getHeaders(true, false),
    });

    return this.handleResponse<{ message: string; features: string[] }>(response);
  }

  async uploadFile(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.getAuthToken()}`,
        'X-CSRF-Token': this.getCsrfToken() || '',
      },
      body: formData,
    });

    return this.handleResponse<UploadResponse>(response);
  }

  async getManifest(lessonId: string): Promise<Manifest> {
    const response = await fetch(`${this.baseUrl}/lessons/${lessonId}/manifest`, {
      method: 'GET',
      headers: this.getHeaders(true, false),
    });

    return this.handleResponse<Manifest>(response);
  }

  async getLessonStatus(lessonId: string): Promise<ProcessingStatus> {
    console.log('[API] Fetching lesson status for:', lessonId);
    
    const token = this.getAuthToken();
    console.log('[API] Token for status request:', token ? `${token.substring(0, 20)}...` : 'NO TOKEN');
    
    const headers = this.getHeaders(true, false);
    console.log('[API] Headers:', headers);
    
    const response = await fetch(`${this.baseUrl}/lessons/${lessonId}/status`, {
      method: 'GET',
      headers: headers,
    });

    const result = await this.handleResponse<ProcessingStatus>(response);
    console.log('[API] Lesson status response:', result);
    return result;
  }

  async exportLesson(lessonId: string): Promise<ExportResponse> {
    const response = await fetch(`${this.baseUrl}/lessons/${lessonId}/export`, {
      method: 'POST',
      headers: this.getHeaders(true, true),
    });

    return this.handleResponse<ExportResponse>(response);
  }

  async healthCheck(): Promise<{ status: string; message: string }> {
    const response = await fetch(`${this.baseUrl}/health`, {
      method: 'GET',
      headers: this.getHeaders(false, false),
    });

    return this.handleResponse<{ status: string; message: string }>(response);
  }

  async patchLesson(lessonId: string, patchRequest: LessonPatchRequest): Promise<PatchResponse> {
    const response = await fetch(`${this.baseUrl}/lessons/${lessonId}/patch`, {
      method: 'POST',
      headers: this.getHeaders(true, true),
      body: JSON.stringify(patchRequest),
    });

    return this.handleResponse<PatchResponse>(response);
  }

  // User videos library methods
  async getUserVideos(limit: number = 50, offset: number = 0): Promise<UserVideosResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/lessons/my-videos?limit=${limit}&offset=${offset}`,
      {
        method: 'GET',
        headers: this.getHeaders(true, false),
      }
    );

    return this.handleResponse<UserVideosResponse>(response);
  }

  async getVideoDetails(lessonId: string): Promise<VideoPreview> {
    const response = await fetch(`${this.baseUrl}/api/lessons/${lessonId}`, {
      method: 'GET',
      headers: this.getHeaders(true, false),
    });

    return this.handleResponse<VideoPreview>(response);
  }

  async deleteVideo(lessonId: string): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${this.baseUrl}/api/lessons/${lessonId}`, {
      method: 'DELETE',
      headers: this.getHeaders(true, true),
    });

    return this.handleResponse<{ success: boolean; message: string }>(response);
  }

  // New V2 API methods
  async generateLectureOutline(lectureTitle: string, courseTitle?: string, audienceLevel?: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/v2/lecture-outline`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        lecture_title: lectureTitle,
        course_title: courseTitle,
        audience_level: audienceLevel || 'undergrad'
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to generate lecture outline: ${response.statusText}`);
    }

    return response.json();
  }

  async generateSpeakerNotesV2(
    lessonId: string,
    slideId: number,
    courseTitle?: string,
    lectureTitle?: string,
    audienceLevel?: string,
    stylePreset?: string
  ): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/v2/speaker-notes`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        lesson_id: lessonId,
        slide_id: slideId,
        course_title: courseTitle,
        lecture_title: lectureTitle,
        audience_level: audienceLevel || 'undergrad',
        style_preset: stylePreset || 'explanatory'
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to generate speaker notes: ${response.statusText}`);
    }

    return response.json();
  }

  async regenerateSpeakerNotes(lessonId: string, slideId: number): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/v2/regenerate-speaker-notes`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        lesson_id: lessonId,
        slide_id: slideId
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to regenerate speaker notes: ${response.statusText}`);
    }

    return response.json();
  }

  async getManifestV2(lessonId: string): Promise<Manifest> {
    const response = await fetch(`${this.baseUrl}/api/v2/manifest/${lessonId}`);

    if (!response.ok) {
      throw new Error(`Failed to fetch manifest: ${response.statusText}`);
    }

    return response.json();
  }
}

export const apiClient = new ApiClient();