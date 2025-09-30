"""Sprint 3: Video export service"""
import asyncio
import logging
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
import subprocess
import ffmpeg
from PIL import Image, ImageDraw, ImageFont
import numpy as np

from ...core.exceptions import ExportError
from ...core.config import settings
from ...models.schemas import ExportRequest, ExportResponse, Manifest, Slide, Cue, ActionType
from .s3_storage import S3StorageManager

logger = logging.getLogger(__name__)

class VideoExporter:
    """Video export service using FFmpeg"""
    
    def __init__(self):
        self.ffmpeg_path = settings.FFMPEG_PATH
        self.quality_settings = {
            "low": {"resolution": "1280x720", "bitrate": "1M", "fps": 24},
            "medium": {"resolution": "1920x1080", "bitrate": "2M", "fps": 30},
            "high": {"resolution": "1920x1080", "bitrate": "4M", "fps": 30}
        }
        self.temp_dir = Path(tempfile.gettempdir()) / "slide_speaker_exports"
        self.temp_dir.mkdir(exist_ok=True)
        self.s3_storage = S3StorageManager()
    
    async def export_lesson(self, lesson_id: str, request: ExportRequest) -> ExportResponse:
        """Export lesson to MP4 video"""
        try:
            logger.info(f"Starting video export for lesson {lesson_id}")
            
            # Load manifest
            manifest_path = settings.DATA_DIR / lesson_id / "manifest.json"
            if not manifest_path.exists():
                raise ExportError(f"Manifest not found for lesson {lesson_id}")
            
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
            
            # Validate manifest with detailed error reporting
            try:
                manifest = Manifest(**manifest_data)
            except Exception as e:
                logger.error(f"Manifest validation failed: {e}")
                logger.error(f"Manifest data: {json.dumps(manifest_data, indent=2)}")
                raise ExportError(f"Invalid manifest format: {e}")
            
            # Generate task ID
            task_id = f"export_{lesson_id}_{int(asyncio.get_event_loop().time())}"
            
            # Start background export task
            asyncio.create_task(self._export_video_background(lesson_id, request, manifest, task_id))
            
            return ExportResponse(
                status="processing",
                task_id=task_id,
                estimated_time="5-10 minutes"
            )
            
        except Exception as e:
            logger.error(f"Error starting video export: {e}")
            raise ExportError(f"Failed to start video export: {e}")
    
    async def _export_video_background(self, lesson_id: str, request: ExportRequest, manifest: Manifest, task_id: str):
        """Background video export task"""
        try:
            logger.info(f"Processing video export task {task_id}")
            
            # Create temporary directory for this export
            temp_export_dir = self.temp_dir / task_id
            temp_export_dir.mkdir(exist_ok=True)
            
            try:
                # Generate video frames with effects
                await self._generate_video_frames(lesson_id, manifest, temp_export_dir, request)
                
                # Combine frames with audio
                output_path = settings.EXPORTS_DIR / f"{lesson_id}_export.mp4"
                await self._render_final_video(lesson_id, manifest, temp_export_dir, output_path, request)
                
                # Upload to S3 if configured
                if self.s3_storage.s3_client:
                    s3_key = f"exports/{lesson_id}_export.mp4"
                    await self.s3_storage.upload_file(output_path, s3_key, "video/mp4")
                    logger.info(f"Video uploaded to S3: {s3_key}")
                
                logger.info(f"Video export completed: {output_path}")
                
            finally:
                # Clean up temporary files
                shutil.rmtree(temp_export_dir, ignore_errors=True)
            
        except Exception as e:
            logger.error(f"Error in background video export: {e}")
            raise
    
    async def _generate_video_frames(self, lesson_id: str, manifest: Manifest, temp_dir: Path, request: ExportRequest):
        """Generate video frames with visual effects"""
        try:
            logger.info(f"Generating video frames for lesson {lesson_id}")
            
            quality = self.quality_settings.get(request.quality, self.quality_settings["high"])
            fps = quality["fps"]
            
            frame_count = 0
            
            for slide in manifest.slides:
                # Load slide image
                slide_image_path = self._get_slide_image_path(lesson_id, slide)
                if not slide_image_path.exists():
                    logger.warning(f"Slide image not found: {slide_image_path}")
                    continue
                
                # Load audio to get duration
                audio_duration = await self._get_audio_duration(lesson_id, slide)
                if not audio_duration:
                    audio_duration = 5.0  # Default duration
                
                # Generate frames for this slide
                slide_frames = await self._render_slide_frames(
                    slide_image_path, slide, audio_duration, fps, temp_dir, frame_count
                )
                
                frame_count += slide_frames
                
            logger.info(f"Generated {frame_count} frames for lesson {lesson_id}")
            
        except Exception as e:
            logger.error(f"Error generating video frames: {e}")
            raise ExportError(f"Failed to generate video frames: {e}")
    
    async def _render_slide_frames(self, slide_image_path: Path, slide: Slide, duration: float, fps: int, temp_dir: Path, start_frame: int) -> int:
        """Render frames for a single slide with visual effects"""
        try:
            # Load base image
            base_image = Image.open(slide_image_path)
            base_image = base_image.convert("RGB")
            
            # Calculate frame count for this slide
            frame_count = int(duration * fps)
            
            # Sort cues by time
            sorted_cues = sorted(slide.cues, key=lambda c: c.t0)
            
            for frame_idx in range(frame_count):
                current_time = frame_idx / fps
                
                # Create frame image
                frame_image = base_image.copy()
                draw = ImageDraw.Draw(frame_image)
                
                # Apply visual effects for current time
                await self._apply_visual_effects(draw, sorted_cues, current_time, frame_image.size)
                
                # Save frame
                frame_path = temp_dir / f"frame_{start_frame + frame_idx:06d}.png"
                frame_image.save(frame_path, "PNG")
            
            return frame_count
            
        except Exception as e:
            logger.error(f"Error rendering slide frames: {e}")
            raise ExportError(f"Failed to render slide frames: {e}")
    
    async def _apply_visual_effects(self, draw: ImageDraw.Draw, cues: List[Cue], current_time: float, image_size: tuple):
        """Apply visual effects to current frame"""
        try:
            for cue in cues:
                if cue.t0 <= current_time <= cue.t1:
                    if cue.action == ActionType.HIGHLIGHT:
                        await self._draw_highlight(draw, cue, current_time)
                    elif cue.action == ActionType.UNDERLINE:
                        await self._draw_underline(draw, cue, current_time)
                    elif cue.action == ActionType.LASER_MOVE:
                        await self._draw_laser_pointer(draw, cue, current_time, image_size)
                    elif cue.action == ActionType.FADE_IN:
                        await self._draw_fade_in(draw, cue, current_time)
                    elif cue.action == ActionType.FADE_OUT:
                        await self._draw_fade_out(draw, cue, current_time)
                        
        except Exception as e:
            logger.error(f"Error applying visual effects: {e}")
    
    async def _draw_highlight(self, draw: ImageDraw.Draw, cue: Cue, current_time: float):
        """Draw highlight effect"""
        if cue.bbox:
            x, y, w, h = cue.bbox
            # Semi-transparent yellow highlight
            highlight_color = (255, 255, 0, 100)
            draw.rectangle([x, y, x + w, y + h], fill=highlight_color)
    
    async def _draw_underline(self, draw: ImageDraw.Draw, cue: Cue, current_time: float):
        """Draw underline effect"""
        if cue.bbox:
            x, y, w, h = cue.bbox
            # Red underline
            draw.line([x, y + h, x + w, y + h], fill="red", width=3)
    
    async def _draw_laser_pointer(self, draw: ImageDraw.Draw, cue: Cue, current_time: float, image_size: tuple):
        """Draw laser pointer effect"""
        if cue.to:
            x, y = cue.to
            # Red laser dot
            draw.ellipse([x - 5, y - 5, x + 5, y + 5], fill="red")
            # Laser beam effect
            draw.line([x, 0, x, y], fill="red", width=2)
    
    async def _draw_fade_in(self, draw: ImageDraw.Draw, cue: Cue, current_time: float):
        """Draw fade in effect"""
        if cue.bbox:
            x, y, w, h = cue.bbox
            progress = (current_time - cue.t0) / (cue.t1 - cue.t0)
            alpha = int(255 * progress)
            fade_color = (255, 255, 255, alpha)
            draw.rectangle([x, y, x + w, y + h], fill=fade_color)
    
    async def _draw_fade_out(self, draw: ImageDraw.Draw, cue: Cue, current_time: float):
        """Draw fade out effect"""
        if cue.bbox:
            x, y, w, h = cue.bbox
            progress = (current_time - cue.t0) / (cue.t1 - cue.t0)
            alpha = int(255 * (1 - progress))
            fade_color = (0, 0, 0, alpha)
            draw.rectangle([x, y, x + w, y + h], fill=fade_color)
    
    async def _render_final_video(self, lesson_id: str, manifest: Manifest, temp_dir: Path, output_path: Path, request: ExportRequest):
        """Render final video using FFmpeg"""
        try:
            logger.info(f"Rendering final video for lesson {lesson_id}")
            
            quality = self.quality_settings.get(request.quality, self.quality_settings["high"])
            
            # Create audio concat file
            audio_files = []
            for slide in manifest.slides:
                audio_path = self._get_audio_path(lesson_id, slide)
                if audio_path.exists():
                    audio_files.append(str(audio_path))
            
            if not audio_files:
                logger.warning("No audio files found, creating silent video")
                # Create silent video
                await self._create_silent_video(temp_dir, output_path, quality)
                return
            
            # Combine audio files
            combined_audio_path = temp_dir / "combined_audio.wav"
            await self._combine_audio_files(audio_files, combined_audio_path)
            
            # Create video from frames
            video_path = temp_dir / "video.mp4"
            await self._create_video_from_frames(temp_dir, video_path, quality)
            
            # Combine video and audio
            await self._combine_video_audio(video_path, combined_audio_path, output_path, quality)
            
            logger.info(f"Final video rendered: {output_path}")
            
        except Exception as e:
            logger.error(f"Error rendering final video: {e}")
            raise ExportError(f"Failed to render final video: {e}")
    
    async def _create_silent_video(self, temp_dir: Path, output_path: Path, quality: dict):
        """Create silent video from frames"""
        try:
            # Get frame pattern
            frame_pattern = str(temp_dir / "frame_%06d.png")
            
            # Create video using FFmpeg
            (
                ffmpeg
                .input(frame_pattern, framerate=quality["fps"])
                .output(str(output_path), vcodec="libx264", pix_fmt="yuv420p", **{"b:v": quality["bitrate"]})
                .overwrite_output()
                .run(quiet=True)
            )
            
        except Exception as e:
            logger.error(f"Error creating silent video: {e}")
            raise
    
    async def _combine_audio_files(self, audio_files: List[str], output_path: Path):
        """Combine multiple audio files into one"""
        try:
            if len(audio_files) == 1:
                # Single audio file, just copy
                shutil.copy2(audio_files[0], output_path)
                return
            
            # Create concat file for FFmpeg
            concat_file = output_path.parent / "concat.txt"
            with open(concat_file, "w") as f:
                for audio_file in audio_files:
                    f.write(f"file '{audio_file}'\n")
            
            # Combine audio files
            (
                ffmpeg
                .input(str(concat_file), format="concat", safe=0)
                .output(str(output_path), acodec="aac", **{"b:a": "128k"})
                .overwrite_output()
                .run(quiet=True)
            )
            
            # Clean up concat file
            concat_file.unlink()
            
        except Exception as e:
            logger.error(f"Error combining audio files: {e}")
            raise
    
    async def _create_video_from_frames(self, temp_dir: Path, output_path: Path, quality: dict):
        """Create video from frame sequence"""
        try:
            frame_pattern = str(temp_dir / "frame_%06d.png")
            
            (
                ffmpeg
                .input(frame_pattern, framerate=quality["fps"])
                .output(str(output_path), vcodec="libx264", pix_fmt="yuv420p", **{"b:v": quality["bitrate"]})
                .overwrite_output()
                .run(quiet=True)
            )
            
        except Exception as e:
            logger.error(f"Error creating video from frames: {e}")
            raise
    
    async def _combine_video_audio(self, video_path: Path, audio_path: Path, output_path: Path, quality: dict):
        """Combine video and audio into final MP4"""
        try:
            (
                ffmpeg
                .input(str(video_path))
                .input(str(audio_path))
                .output(str(output_path), vcodec="libx264", acodec="aac", pix_fmt="yuv420p", **{"b:v": quality["bitrate"], "b:a": "128k"})
                .overwrite_output()
                .run(quiet=True)
            )
            
        except Exception as e:
            logger.error(f"Error combining video and audio: {e}")
            raise
    
    def _get_slide_image_path(self, lesson_id: str, slide: Slide) -> Path:
        """Get path to slide image"""
        if slide.image.startswith("/"):
            return Path(slide.image[1:])  # Remove leading slash
        return settings.DATA_DIR / slide.image
    
    def _get_audio_path(self, lesson_id: str, slide: Slide) -> Path:
        """Get path to slide audio"""
        if slide.audio.startswith("/"):
            return Path(slide.audio[1:])  # Remove leading slash
        return settings.DATA_DIR / slide.audio
    
    async def _get_audio_duration(self, lesson_id: str, slide: Slide) -> Optional[float]:
        """Get audio duration in seconds"""
        try:
            audio_path = self._get_audio_path(lesson_id, slide)
            if not audio_path.exists():
                return None
            
            # Use FFprobe to get duration
            probe = ffmpeg.probe(str(audio_path))
            duration = float(probe['streams'][0]['duration'])
            return duration
            
        except Exception as e:
            logger.error(f"Error getting audio duration: {e}")
            return None
    
    async def get_export_status(self, task_id: str) -> Dict[str, Any]:
        """Get export task status"""
        try:
            # Extract lesson_id from task_id
            lesson_id = task_id.split("_")[1] if "_" in task_id else task_id
            
            # Check if export file exists
            output_path = settings.EXPORTS_DIR / f"{lesson_id}_export.mp4"
            
            if output_path.exists():
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "progress": 100,
                    "message": "Export completed successfully",
                    "download_url": f"/exports/{lesson_id}_export.mp4"
                }
            else:
                # Check if task is still running (simplified check)
                temp_dir = self.temp_dir / task_id
                if temp_dir.exists():
                    return {
                        "task_id": task_id,
                        "status": "processing",
                        "progress": 50,
                        "message": "Rendering video frames"
                    }
                else:
                    return {
                        "task_id": task_id,
                        "status": "failed",
                        "progress": 0,
                        "message": "Export task not found or failed"
                    }
            
        except Exception as e:
            logger.error(f"Error getting export status: {e}")
            raise ExportError(f"Failed to get export status: {e}")
    
    async def get_export_download_url(self, lesson_id: str) -> Optional[str]:
        """Get download URL for exported video"""
        try:
            # Check local file first
            output_path = settings.EXPORTS_DIR / f"{lesson_id}_export.mp4"
            
            if output_path.exists():
                return f"/exports/{lesson_id}_export.mp4"
            
            # Check S3 if configured
            if self.s3_storage.s3_client:
                s3_key = f"exports/{lesson_id}_export.mp4"
                file_info = await self.s3_storage.get_file_info(s3_key)
                
                if file_info:
                    # Generate presigned URL for S3 file
                    presigned_url = await self.s3_storage.generate_presigned_url(s3_key, expiration=3600)
                    return presigned_url
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting download URL: {e}")
            return None

class QueueManager:
    """Task queue management service"""
    
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self.celery_broker = settings.CELERY_BROKER_URL
        self.celery_backend = settings.CELERY_RESULT_BACKEND
    
    async def enqueue_export_task(self, lesson_id: str, request: ExportRequest) -> str:
        """Enqueue video export task"""
        try:
            logger.info(f"Enqueuing export task for lesson {lesson_id}")
            
            # Import Celery task
            from ...tasks import export_video_task
            
            # Enqueue task
            task = export_video_task.delay(lesson_id, request.dict())
            task_id = task.id
            
            logger.info(f"Export task enqueued with ID: {task_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"Error enqueuing export task: {e}")
            raise ExportError(f"Failed to enqueue export task: {e}")
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status from queue"""
        try:
            # Import Celery task
            from ...tasks import export_video_task
            
            # Get task result
            task_result = export_video_task.AsyncResult(task_id)
            
            if task_result.state == 'PENDING':
                return {
                    "task_id": task_id,
                    "status": "pending",
                    "progress": 0,
                    "message": "Task is waiting to be processed"
                }
            elif task_result.state == 'PROGRESS':
                return {
                    "task_id": task_id,
                    "status": "processing",
                    "progress": task_result.info.get('progress', 0),
                    "message": task_result.info.get('message', 'Processing...')
                }
            elif task_result.state == 'SUCCESS':
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "progress": 100,
                    "message": "Export completed successfully",
                    "result": task_result.result
                }
            elif task_result.state == 'FAILURE':
                return {
                    "task_id": task_id,
                    "status": "failed",
                    "progress": 0,
                    "message": "Export failed",
                    "error": str(task_result.info)
                }
            else:
                return {
                    "task_id": task_id,
                    "status": "unknown",
                    "progress": 0,
                    "message": f"Unknown task state: {task_result.state}"
                }
            
        except Exception as e:
            logger.error(f"Error getting task status: {e}")
            raise ExportError(f"Failed to get task status: {e}")

class StorageManager:
    """File storage and management service"""
    
    def __init__(self):
        self.data_dir = settings.DATA_DIR
        self.assets_dir = settings.ASSETS_DIR
        self.exports_dir = settings.EXPORTS_DIR
        self.s3_storage = S3StorageManager()
    
    async def cleanup_old_files(self, max_age_days: int = 7):
        """Clean up old files to save storage"""
        try:
            logger.info(f"Cleaning up files older than {max_age_days} days")
            
            # Clean up local files
            await self._cleanup_local_files(max_age_days)
            
            # Clean up S3 files if configured
            if self.s3_storage.s3_client:
                await self.s3_storage.cleanup_old_files("exports/", max_age_days)
                await self.s3_storage.cleanup_old_files("assets/", max_age_days)
            
            logger.info("File cleanup completed")
            
        except Exception as e:
            logger.error(f"Error cleaning up files: {e}")
    
    async def _cleanup_local_files(self, max_age_days: int):
        """Clean up local files"""
        try:
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            
            # Clean up exports
            for file_path in self.exports_dir.glob("*.mp4"):
                if datetime.fromtimestamp(file_path.stat().st_mtime) < cutoff_date:
                    file_path.unlink()
                    logger.info(f"Deleted old export file: {file_path}")
            
            # Clean up temporary files
            temp_dir = Path(tempfile.gettempdir()) / "slide_speaker_exports"
            if temp_dir.exists():
                for temp_file in temp_dir.glob("*"):
                    if datetime.fromtimestamp(temp_file.stat().st_mtime) < cutoff_date:
                        if temp_file.is_file():
                            temp_file.unlink()
                        elif temp_file.is_dir():
                            shutil.rmtree(temp_file, ignore_errors=True)
                        logger.info(f"Deleted old temp file: {temp_file}")
            
        except Exception as e:
            logger.error(f"Error cleaning up local files: {e}")
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage usage statistics"""
        try:
            # Get local storage stats
            local_stats = await self._get_local_storage_stats()
            
            # Get S3 storage stats
            s3_stats = await self.s3_storage.get_storage_stats()
            
            return {
                "local": local_stats,
                "s3": s3_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {}
    
    async def _get_local_storage_stats(self) -> Dict[str, Any]:
        """Get local storage statistics"""
        try:
            def get_dir_size(path: Path) -> int:
                total_size = 0
                if path.exists():
                    for file_path in path.rglob("*"):
                        if file_path.is_file():
                            total_size += file_path.stat().st_size
                return total_size
            
            def get_file_count(path: Path) -> int:
                count = 0
                if path.exists():
                    count = len(list(path.rglob("*")))
                return count
            
            total_size = get_dir_size(self.data_dir)
            exports_size = get_dir_size(self.exports_dir)
            assets_size = get_dir_size(self.assets_dir)
            
            total_files = get_file_count(self.data_dir)
            exports_files = get_file_count(self.exports_dir)
            assets_files = get_file_count(self.assets_dir)
            
            return {
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "exports_size_bytes": exports_size,
                "exports_size_mb": round(exports_size / (1024 * 1024), 2),
                "assets_size_bytes": assets_size,
                "assets_size_mb": round(assets_size / (1024 * 1024), 2),
                "total_files": total_files,
                "exports_files": exports_files,
                "assets_files": assets_files
            }
            
        except Exception as e:
            logger.error(f"Error getting local storage stats: {e}")
            return {}