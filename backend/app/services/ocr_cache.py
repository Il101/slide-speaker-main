"""
OCR Results Caching Service
Кэширование результатов OCR в Redis для ускорения повторной обработки
"""
import json
import hashlib
import logging
from typing import Optional, Dict, Any
from pathlib import Path

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)


class OCRCache:
    """Кэш для OCR результатов"""
    
    def __init__(self, redis_url: str = "redis://redis:6379/0", ttl: int = 604800):
        """
        Args:
            redis_url: Redis connection URL
            ttl: Time to live в секундах (default: 7 дней)
        """
        self.ttl = ttl
        self.redis_client = None
        self.enabled = False
        
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                # Test connection
                self.redis_client.ping()
                self.enabled = True
                logger.info("OCR Cache: Redis connection established")
            except Exception as e:
                logger.warning(f"OCR Cache: Redis not available: {e}. Cache disabled.")
                self.enabled = False
        else:
            logger.warning("OCR Cache: redis package not installed. Cache disabled.")
    
    def _compute_image_hash(self, image_path: str) -> str:
        """Вычисляем хэш изображения для использования в качестве ключа"""
        try:
            with open(image_path, 'rb') as f:
                # Читаем первые 64KB для хэша (достаточно для уникальности)
                data = f.read(65536)
                return hashlib.sha256(data).hexdigest()
        except Exception as e:
            logger.error(f"Error computing image hash: {e}")
            return None
    
    def compute_perceptual_hash(self, image_path: str) -> Optional[str]:
        """
        ✅ FIX: Вычислить перцептивный хэш слайда для дедупликации
        
        Perceptual hash устойчив к небольшим изменениям изображения.
        Одинаковые слайды (например, "Questions?", "Thank you") будут 
        иметь одинаковый или очень похожий хэш.
        
        Args:
            image_path: Путь к изображению слайда
            
        Returns:
            SHA256 хэш перцептивного отпечатка или None при ошибке
        """
        try:
            from PIL import Image
            import numpy as np
            
            # Открыть изображение
            img = Image.open(image_path).convert('L')  # Grayscale
            
            # Уменьшить для быстрого хэширования (32x32 достаточно)
            img = img.resize((32, 32), Image.Resampling.LANCZOS)
            
            # Перцептивный хэш: binary pattern основанный на среднем
            pixels = np.array(img).flatten()
            avg = pixels.mean()
            
            # Создаём binary hash (1 если пиксель > среднего, 0 иначе)
            hash_bits = (pixels > avg).astype(int)
            hash_str = ''.join(str(b) for b in hash_bits)
            
            # SHA256 для компактного представления
            return hashlib.sha256(hash_str.encode()).hexdigest()
            
        except ImportError:
            logger.warning("PIL not available, falling back to file hash")
            return self._compute_image_hash(image_path)
        except Exception as e:
            logger.error(f"Error computing perceptual hash: {e}")
            return None
    
    def get_processed_slide(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        ✅ FIX: Получить результат обработки похожего слайда из кэша
        
        Использует perceptual hash для поиска одинаковых/похожих слайдов.
        Экономит AI вызовы на повторяющихся слайдах.
        
        Args:
            image_path: Путь к изображению слайда
            
        Returns:
            Результат обработки (semantic_map, script, etc.) или None
        """
        if not self.enabled:
            return None
        
        try:
            perceptual_hash = self.compute_perceptual_hash(image_path)
            if not perceptual_hash:
                return None
            
            cache_key = f"slide_processed:{perceptual_hash}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                logger.info(f"✅ Slide Dedup HIT: {Path(image_path).name} (perceptual)")
                return json.loads(cached_data)
            else:
                logger.debug(f"Slide Dedup MISS: {Path(image_path).name}")
                return None
                
        except Exception as e:
            logger.error(f"Error reading processed slide from cache: {e}")
            return None
    
    def save_processed_slide(
        self, 
        image_path: str, 
        processed_data: Dict[str, Any]
    ) -> bool:
        """
        ✅ FIX: Сохранить результат обработки слайда в кэш дедупликации
        
        Args:
            image_path: Путь к изображению слайда
            processed_data: Результат обработки (semantic_map, script, etc.)
            
        Returns:
            True если успешно сохранено
        """
        if not self.enabled:
            return False
        
        try:
            perceptual_hash = self.compute_perceptual_hash(image_path)
            if not perceptual_hash:
                return False
            
            cache_key = f"slide_processed:{perceptual_hash}"
            
            # Добавляем метаданные
            processed_data['_cached_at'] = Path(image_path).name
            processed_data['_perceptual_hash'] = perceptual_hash[:16]
            
            serialized = json.dumps(processed_data, ensure_ascii=False)
            
            # Сохраняем с длительным TTL (7 дней)
            ttl_processed = 604800  # 7 дней
            self.redis_client.setex(cache_key, ttl_processed, serialized)
            
            logger.debug(f"💾 Slide Dedup SAVE: {Path(image_path).name}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving processed slide: {e}")
            return False
    
    def get(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Получить кэшированный OCR результат
        
        Args:
            image_path: Путь к изображению
            
        Returns:
            OCR результат или None если не найден
        """
        if not self.enabled:
            return None
        
        try:
            image_hash = self._compute_image_hash(image_path)
            if not image_hash:
                return None
            
            cache_key = f"ocr:{image_hash}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                logger.info(f"✅ OCR Cache HIT: {Path(image_path).name}")
                return json.loads(cached_data)
            else:
                logger.debug(f"OCR Cache MISS: {Path(image_path).name}")
                return None
                
        except Exception as e:
            logger.error(f"Error reading from OCR cache: {e}")
            return None
    
    def set(self, image_path: str, ocr_result: Dict[str, Any]) -> bool:
        """
        Сохранить OCR результат в кэш
        
        Args:
            image_path: Путь к изображению
            ocr_result: OCR результат для кэширования
            
        Returns:
            True если успешно сохранено
        """
        if not self.enabled:
            return False
        
        try:
            image_hash = self._compute_image_hash(image_path)
            if not image_hash:
                return False
            
            cache_key = f"ocr:{image_hash}"
            serialized = json.dumps(ocr_result, ensure_ascii=False)
            
            # Сохраняем с TTL
            self.redis_client.setex(cache_key, self.ttl, serialized)
            
            logger.debug(f"💾 OCR Cache SAVE: {Path(image_path).name} (TTL: {self.ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Error writing to OCR cache: {e}")
            return False
    
    def invalidate(self, image_path: str) -> bool:
        """Инвалидировать кэш для конкретного изображения"""
        if not self.enabled:
            return False
        
        try:
            image_hash = self._compute_image_hash(image_path)
            if not image_hash:
                return False
            
            cache_key = f"ocr:{image_hash}"
            self.redis_client.delete(cache_key)
            
            logger.info(f"🗑️ OCR Cache INVALIDATED: {Path(image_path).name}")
            return True
            
        except Exception as e:
            logger.error(f"Error invalidating OCR cache: {e}")
            return False
    
    def clear_all(self) -> int:
        """Очистить весь OCR кэш"""
        if not self.enabled:
            return 0
        
        try:
            # Находим все ключи с префиксом ocr:
            keys = self.redis_client.keys("ocr:*")
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"🗑️ OCR Cache CLEARED: {deleted} entries")
                return deleted
            return 0
            
        except Exception as e:
            logger.error(f"Error clearing OCR cache: {e}")
            return 0
    
    def get_batch(self, image_paths: list[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        ✅ FIX: Получить несколько OCR результатов за один запрос
        
        Вместо N отдельных запросов к Redis делаем 1 batch запрос.
        Ускорение в 10-100 раз для больших презентаций.
        
        Args:
            image_paths: Список путей к изображениям
            
        Returns:
            Dict {image_path: ocr_result or None}
        """
        if not self.enabled or not image_paths:
            return {path: None for path in image_paths}
        
        try:
            # Вычисляем хэши для всех изображений
            path_to_hash = {}
            hash_to_path = {}
            
            for path in image_paths:
                img_hash = self._compute_image_hash(path)
                if img_hash:
                    path_to_hash[path] = img_hash
                    hash_to_path[img_hash] = path
            
            if not path_to_hash:
                return {path: None for path in image_paths}
            
            # Создаём pipeline для batch запроса
            cache_keys = [f"ocr:{h}" for h in path_to_hash.values()]
            
            pipe = self.redis_client.pipeline()
            for key in cache_keys:
                pipe.get(key)
            
            # Выполняем все запросы одновременно
            results = pipe.execute()
            
            # Собираем результаты
            cached_data = {}
            hits = 0
            
            for img_hash, result in zip(path_to_hash.values(), results):
                path = hash_to_path[img_hash]
                if result:
                    try:
                        cached_data[path] = json.loads(result)
                        hits += 1
                    except json.JSONDecodeError:
                        cached_data[path] = None
                else:
                    cached_data[path] = None
            
            # Добавляем None для путей без хэша
            for path in image_paths:
                if path not in cached_data:
                    cached_data[path] = None
            
            logger.info(f"✅ OCR Batch: {hits}/{len(image_paths)} cache hits")
            return cached_data
            
        except Exception as e:
            logger.error(f"Error in batch get: {e}")
            return {path: None for path in image_paths}
    
    def set_batch(self, image_data: Dict[str, Dict[str, Any]]) -> int:
        """
        ✅ FIX: Сохранить несколько OCR результатов за один запрос
        
        Args:
            image_data: Dict {image_path: ocr_result}
            
        Returns:
            Количество успешно сохранённых записей
        """
        if not self.enabled or not image_data:
            return 0
        
        try:
            pipe = self.redis_client.pipeline()
            saved_count = 0
            
            for image_path, ocr_result in image_data.items():
                img_hash = self._compute_image_hash(image_path)
                if not img_hash:
                    continue
                
                cache_key = f"ocr:{img_hash}"
                serialized = json.dumps(ocr_result, ensure_ascii=False)
                pipe.setex(cache_key, self.ttl, serialized)
                saved_count += 1
            
            # Выполняем все записи одновременно
            pipe.execute()
            
            logger.debug(f"💾 OCR Batch SAVE: {saved_count} entries")
            return saved_count
            
        except Exception as e:
            logger.error(f"Error in batch set: {e}")
            return 0
    
    def get_processed_slides_batch(
        self, 
        image_paths: list[str]
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        ✅ FIX: Batch получение обработанных слайдов (с дедупликацией)
        
        Args:
            image_paths: Список путей к изображениям слайдов
            
        Returns:
            Dict {image_path: processed_data or None}
        """
        if not self.enabled or not image_paths:
            return {path: None for path in image_paths}
        
        try:
            # Вычисляем perceptual хэши
            path_to_hash = {}
            hash_to_path = {}
            
            for path in image_paths:
                perceptual_hash = self.compute_perceptual_hash(path)
                if perceptual_hash:
                    path_to_hash[path] = perceptual_hash
                    hash_to_path[perceptual_hash] = path
            
            if not path_to_hash:
                return {path: None for path in image_paths}
            
            # Batch запрос
            cache_keys = [f"slide_processed:{h}" for h in path_to_hash.values()]
            
            pipe = self.redis_client.pipeline()
            for key in cache_keys:
                pipe.get(key)
            
            results = pipe.execute()
            
            # Собираем результаты
            cached_data = {}
            hits = 0
            
            for perceptual_hash, result in zip(path_to_hash.values(), results):
                path = hash_to_path[perceptual_hash]
                if result:
                    try:
                        cached_data[path] = json.loads(result)
                        hits += 1
                    except json.JSONDecodeError:
                        cached_data[path] = None
                else:
                    cached_data[path] = None
            
            # Добавляем None для остальных
            for path in image_paths:
                if path not in cached_data:
                    cached_data[path] = None
            
            if hits > 0:
                logger.info(f"✅ Slide Dedup Batch: {hits}/{len(image_paths)} hits")
            
            return cached_data
            
        except Exception as e:
            logger.error(f"Error in batch get processed slides: {e}")
            return {path: None for path in image_paths}
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику кэша"""
        if not self.enabled:
            return {"enabled": False}
        
        try:
            keys = self.redis_client.keys("ocr:*")
            total_size = 0
            
            for key in keys:
                value = self.redis_client.get(key)
                if value:
                    total_size += len(value.encode('utf-8'))
            
            return {
                "enabled": True,
                "total_entries": len(keys),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / 1024 / 1024, 2),
                "ttl_seconds": self.ttl
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"enabled": True, "error": str(e)}


# Global cache instance
_cache_instance: Optional[OCRCache] = None


def get_ocr_cache() -> OCRCache:
    """Получить глобальный экземпляр OCR кэша (singleton)"""
    global _cache_instance
    
    if _cache_instance is None:
        import os
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        cache_ttl = int(os.getenv("OCR_CACHE_TTL", "604800"))  # 7 дней
        _cache_instance = OCRCache(redis_url=redis_url, ttl=cache_ttl)
    
    return _cache_instance
