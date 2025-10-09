/**
 * Playlist TypeScript Types
 * Type definitions for playlist management and playback
 */

export interface PlaylistItem {
  id: string;
  playlist_id: string;
  lesson_id: string;
  order_index: number;
  lesson_title: string;
  lesson_thumbnail?: string;
  lesson_duration?: number;
  lesson_status: string;
  created_at: string;
}

export interface Playlist {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  thumbnail_url?: string;
  is_public: boolean;
  has_password: boolean;
  share_token?: string;
  video_count: number;
  total_duration?: number;
  items: PlaylistItem[];
  created_at: string;
  updated_at: string;
}

export interface PlaylistListItem {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  thumbnail_url?: string;
  is_public: boolean;
  has_password: boolean;
  video_count: number;
  total_duration?: number;
  created_at: string;
  updated_at: string;
}

export interface PlaylistCreateRequest {
  title: string;
  description?: string;
  is_public?: boolean;
  password?: string;
  lesson_ids: string[];
}

export interface PlaylistUpdateRequest {
  title?: string;
  description?: string;
  is_public?: boolean;
  password?: string;
  thumbnail_url?: string;
}

export interface PlaylistAddVideosRequest {
  lesson_ids: string[];
}

export interface PlaylistReorderRequest {
  item_id: string;
  new_order_index: number;
}

export interface PlaylistShareInfo {
  share_url: string;
  embed_code: string;
  share_token: string;
  is_public: boolean;
  has_password: boolean;
}

export interface PlaylistAnalytics {
  playlist_id: string;
  total_views: number;
  unique_viewers: number;
  completion_rate: number;
  average_watch_time?: number;
  total_watch_time?: number;
  videos_watched_distribution: Record<string, number>;
}

export interface PlaylistViewTrack {
  videos_watched: number;
  completed: boolean;
  total_watch_time?: number;
}
