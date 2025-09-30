const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

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
  elements: SlideElement[];
  cues: Cue[];
  speaker_notes?: Array<{
    text: string;
    targetId?: string;
    target?: {
      type: string;
      tableId?: string;
      cells?: string[];
    };
  }>;
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

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  async uploadFile(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    return response.json();
  }

  async getManifest(lessonId: string): Promise<Manifest> {
    const response = await fetch(`${this.baseUrl}/lessons/${lessonId}/manifest`);

    if (!response.ok) {
      throw new Error(`Failed to fetch manifest: ${response.statusText}`);
    }

    return response.json();
  }

  async exportLesson(lessonId: string): Promise<ExportResponse> {
    const response = await fetch(`${this.baseUrl}/lessons/${lessonId}/export`, {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`);
    }

    return response.json();
  }

  async healthCheck(): Promise<{ status: string; message: string }> {
    const response = await fetch(`${this.baseUrl}/health`);
    return response.json();
  }

  async patchLesson(lessonId: string, patchRequest: LessonPatchRequest): Promise<PatchResponse> {
    const response = await fetch(`${this.baseUrl}/lessons/${lessonId}/patch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(patchRequest),
    });

    if (!response.ok) {
      throw new Error(`Patch failed: ${response.statusText}`);
    }

    return response.json();
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