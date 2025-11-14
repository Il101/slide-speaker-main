"""
Shared State Management for Locust Load Tests

This module provides thread-safe shared state between all user instances,
allowing realistic cross-user interactions (e.g., one user creates a lesson,
another user adds it to a playlist).

Usage:
    from shared_state import SharedState
    
    # In ContentCreator:
    SharedState.add_lesson(lesson_id)
    
    # In PlaylistManager:
    lesson_id = SharedState.get_random_lesson()
"""

import threading
import random
import logging
from typing import Optional, List
from collections import defaultdict

logger = logging.getLogger(__name__)


class SharedState:
    """Thread-safe shared state for all Locust users"""
    
    # Thread lock for thread-safe operations
    _lock = threading.Lock()
    
    # Shared data pools
    _lesson_ids: List[str] = []
    _playlist_ids: List[str] = []
    _quiz_ids: List[str] = []
    
    # Counters for statistics
    _stats = defaultdict(int)
    
    # Max pool sizes to prevent memory issues
    MAX_LESSON_POOL = 100
    MAX_PLAYLIST_POOL = 50
    MAX_QUIZ_POOL = 50
    
    @classmethod
    def add_lesson(cls, lesson_id: str) -> None:
        """Add lesson ID to shared pool (thread-safe)"""
        with cls._lock:
            if lesson_id and lesson_id not in cls._lesson_ids:
                cls._lesson_ids.append(lesson_id)
                cls._stats['lessons_created'] += 1
                
                # Prevent pool from growing too large
                if len(cls._lesson_ids) > cls.MAX_LESSON_POOL:
                    removed = cls._lesson_ids.pop(0)  # FIFO
                    logger.debug(f"Removed old lesson {removed} from pool")
    
    @classmethod
    def get_random_lesson(cls) -> Optional[str]:
        """Get random lesson ID from pool (thread-safe)"""
        with cls._lock:
            if cls._lesson_ids:
                return random.choice(cls._lesson_ids)
        return None
    
    @classmethod
    def get_all_lessons(cls) -> List[str]:
        """Get all lesson IDs (thread-safe)"""
        with cls._lock:
            return cls._lesson_ids.copy()
    
    @classmethod
    def lesson_count(cls) -> int:
        """Get number of lessons in pool"""
        with cls._lock:
            return len(cls._lesson_ids)
    
    @classmethod
    def add_playlist(cls, playlist_id: str) -> None:
        """Add playlist ID to shared pool (thread-safe)"""
        with cls._lock:
            if playlist_id and playlist_id not in cls._playlist_ids:
                cls._playlist_ids.append(playlist_id)
                cls._stats['playlists_created'] += 1
                
                if len(cls._playlist_ids) > cls.MAX_PLAYLIST_POOL:
                    cls._playlist_ids.pop(0)
    
    @classmethod
    def get_random_playlist(cls) -> Optional[str]:
        """Get random playlist ID from pool (thread-safe)"""
        with cls._lock:
            if cls._playlist_ids:
                return random.choice(cls._playlist_ids)
        return None
    
    @classmethod
    def playlist_count(cls) -> int:
        """Get number of playlists in pool"""
        with cls._lock:
            return len(cls._playlist_ids)
    
    @classmethod
    def add_quiz(cls, quiz_id: str) -> None:
        """Add quiz ID to shared pool (thread-safe)"""
        with cls._lock:
            if quiz_id and quiz_id not in cls._quiz_ids:
                cls._quiz_ids.append(quiz_id)
                cls._stats['quizzes_created'] += 1
                
                if len(cls._quiz_ids) > cls.MAX_QUIZ_POOL:
                    cls._quiz_ids.pop(0)
    
    @classmethod
    def get_random_quiz(cls) -> Optional[str]:
        """Get random quiz ID from pool (thread-safe)"""
        with cls._lock:
            if cls._quiz_ids:
                return random.choice(cls._quiz_ids)
        return None
    
    @classmethod
    def quiz_count(cls) -> int:
        """Get number of quizzes in pool"""
        with cls._lock:
            return len(cls._quiz_ids)
    
    @classmethod
    def increment_stat(cls, key: str) -> None:
        """Increment a statistic counter (thread-safe)"""
        with cls._lock:
            cls._stats[key] += 1
    
    @classmethod
    def get_stats(cls) -> dict:
        """Get all statistics (thread-safe)"""
        with cls._lock:
            return dict(cls._stats)
    
    @classmethod
    def reset(cls) -> None:
        """Reset all shared state (useful between test runs)"""
        with cls._lock:
            cls._lesson_ids.clear()
            cls._playlist_ids.clear()
            cls._quiz_ids.clear()
            cls._stats.clear()
            logger.info("SharedState reset")
    
    @classmethod
    def get_summary(cls) -> str:
        """Get human-readable summary of shared state"""
        with cls._lock:
            return f"""
SharedState Summary:
  Lessons in pool: {len(cls._lesson_ids)}
  Playlists in pool: {len(cls._playlist_ids)}
  Quizzes in pool: {len(cls._quiz_ids)}
  
  Total created:
    - Lessons: {cls._stats.get('lessons_created', 0)}
    - Playlists: {cls._stats.get('playlists_created', 0)}
    - Quizzes: {cls._stats.get('quizzes_created', 0)}
"""


# Locust event hooks to log shared state
from locust import events


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Reset shared state at test start"""
    SharedState.reset()
    logger.info("SharedState initialized for new test run")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Log shared state summary at test end"""
    logger.info(SharedState.get_summary())
    print("\n" + "=" * 80)
    print(SharedState.get_summary())
    print("=" * 80)


# Example usage in locustfile.py:
"""
from shared_state import SharedState

class ContentCreatorUser(AuthenticatedUser, HttpUser):
    @task(5)
    def upload_presentation(self):
        # ... upload logic ...
        if response.status_code in [200, 201]:
            data = response.json()
            lesson_id = data.get("lesson_id") or data.get("id")
            self.lesson_id = lesson_id
            SharedState.add_lesson(lesson_id)  # ✅ Share with others
            response.success()


class PlaylistManagerUser(AuthenticatedUser, HttpUser):
    @task(5)
    def create_playlist(self):
        lesson_id = SharedState.get_random_lesson()  # ✅ Get real ID
        
        if not lesson_id:
            return  # No lessons available yet
        
        self.client.post("/api/playlists", json={
            "title": f"Playlist {random.randint(1, 10000)}",
            "lesson_ids": [lesson_id]  # ✅ Real lesson ID
        }, headers=self.headers)


class QuizUser(AuthenticatedUser, HttpUser):
    @task(3)
    def create_quiz(self):
        lesson_id = SharedState.get_random_lesson()
        
        if not lesson_id:
            return
        
        self.client.post(f"/api/quizzes/generate", json={
            "lesson_id": lesson_id,
            "question_count": 5
        }, headers=self.headers)
"""
