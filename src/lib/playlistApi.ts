/**
 * Playlist API Service
 * HTTP client for playlist management endpoints
 */
import axios, { AxiosError } from 'axios';
import type {
  Playlist,
  PlaylistListItem,
  PlaylistCreateRequest,
  PlaylistUpdateRequest,
  PlaylistAddVideosRequest,
  PlaylistReorderRequest,
  PlaylistShareInfo,
  PlaylistAnalytics,
  PlaylistViewTrack,
} from '../types/playlist';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Get auth token from localStorage
 */
function getAuthToken(): string | null {
  return localStorage.getItem('token');
}

/**
 * Create axios config with auth headers
 */
function getConfig() {
  const token = getAuthToken();
  return {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
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

export const playlistApi = {
  /**
   * Create a new playlist
   */
  async create(data: PlaylistCreateRequest): Promise<Playlist> {
    try {
      const response = await axios.post<Playlist>(
        `${API_BASE}/api/playlists`,
        data,
        getConfig()
      );
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Get all playlists for current user
   */
  async getAll(): Promise<PlaylistListItem[]> {
    try {
      const response = await axios.get<PlaylistListItem[]>(
        `${API_BASE}/api/playlists`,
        getConfig()
      );
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Get a single playlist by ID
   */
  async get(playlistId: string, password?: string): Promise<Playlist> {
    try {
      const params = password ? { password } : {};
      const response = await axios.get<Playlist>(
        `${API_BASE}/api/playlists/${playlistId}`,
        { ...getConfig(), params }
      );
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Update playlist metadata
   */
  async update(playlistId: string, data: PlaylistUpdateRequest): Promise<Playlist> {
    try {
      const response = await axios.put<Playlist>(
        `${API_BASE}/api/playlists/${playlistId}`,
        data,
        getConfig()
      );
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Delete a playlist
   */
  async delete(playlistId: string): Promise<void> {
    try {
      await axios.delete(
        `${API_BASE}/api/playlists/${playlistId}`,
        getConfig()
      );
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Add videos to existing playlist
   */
  async addVideos(playlistId: string, lessonIds: string[]): Promise<Playlist> {
    try {
      const data: PlaylistAddVideosRequest = { lesson_ids: lessonIds };
      const response = await axios.post<Playlist>(
        `${API_BASE}/api/playlists/${playlistId}/videos`,
        data,
        getConfig()
      );
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Remove video from playlist
   */
  async removeVideo(playlistId: string, itemId: string): Promise<Playlist> {
    try {
      const response = await axios.delete<Playlist>(
        `${API_BASE}/api/playlists/${playlistId}/videos/${itemId}`,
        getConfig()
      );
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Reorder items in playlist
   */
  async reorder(playlistId: string, itemId: string, newOrderIndex: number): Promise<Playlist> {
    try {
      const data: PlaylistReorderRequest = {
        item_id: itemId,
        new_order_index: newOrderIndex,
      };
      const response = await axios.post<Playlist>(
        `${API_BASE}/api/playlists/${playlistId}/reorder`,
        data,
        getConfig()
      );
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Get share info for playlist (generates token if needed)
   */
  async getShareInfo(playlistId: string): Promise<PlaylistShareInfo> {
    try {
      const response = await axios.get<PlaylistShareInfo>(
        `${API_BASE}/api/playlists/${playlistId}/share`,
        getConfig()
      );
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Track playlist view for analytics
   */
  async trackView(playlistId: string, data: PlaylistViewTrack): Promise<void> {
    try {
      await axios.post(
        `${API_BASE}/api/playlists/${playlistId}/view`,
        data,
        getConfig()
      );
    } catch (error) {
      // Don't throw error for analytics - fail silently
      console.error('Failed to track playlist view:', error);
    }
  },

  /**
   * Get analytics for playlist (owner only)
   */
  async getAnalytics(playlistId: string): Promise<PlaylistAnalytics> {
    try {
      const response = await axios.get<PlaylistAnalytics>(
        `${API_BASE}/api/playlists/${playlistId}/analytics`,
        getConfig()
      );
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Get playlist by share token (public access)
   */
  async getByToken(shareToken: string, password?: string): Promise<Playlist> {
    try {
      const params = password ? { password } : {};
      const response = await axios.get<Playlist>(
        `${API_BASE}/api/playlists/shared/${shareToken}`,
        { params }
      );
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * Access password-protected playlist
   */
  async accessProtected(shareToken: string, password: string): Promise<Playlist> {
    try {
      const response = await axios.post<Playlist>(
        `${API_BASE}/api/playlists/shared/${shareToken}/access`,
        { password }
      );
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },
};
