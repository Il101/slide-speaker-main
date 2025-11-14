export interface SlideElement {
  id: string;
  type: string;
  bbox: [number, number, number, number];
  text?: string;
  confidence: number;
}

export interface SlideAction {
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
  cues: SlideAction[];
  duration?: number;
  visual_effects_manifest?: any; // Visual Effects V2 manifest
}

export interface Presentation {
  id: string;
  title: string;
  slides: Slide[];
  totalDuration: number;
}

export interface PlayerState {
  isPlaying: boolean;
  currentSlide: number;
  currentTime: number;
  playbackRate: number;
  volume: number;
}

export interface EditingState {
  isEditing: boolean;
  editingElement: SlideElement | null;
  showSubtitles: boolean;
  dimOthers: boolean;
}