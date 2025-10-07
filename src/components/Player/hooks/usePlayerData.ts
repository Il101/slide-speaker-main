import { useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { usePlayer } from '../PlayerContext';

export const usePlayerData = (lessonId: string) => {
  const { setManifest, setLoading, setError } = usePlayer();

  useEffect(() => {
    const loadManifest = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await apiClient.getManifest(lessonId);
        setManifest(data);
      } catch (err) {
        console.error('Failed to load manifest:', err);
        setError('Не удалось загрузить данные лекции');
      } finally {
        setLoading(false);
      }
    };

    loadManifest();
  }, [lessonId, setManifest, setLoading, setError]);
};
