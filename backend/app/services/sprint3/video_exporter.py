"""Sprint 3: Video export service"""
from __future__ import annotations

import asyncio
import logging
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, TYPE_CHECKING
import subprocess
import ffmpeg
import numpy as np
import cv2
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed

from ...core.exceptions import ExportError
from ...core.config import settings
from ...models.schemas import ExportRequest, ExportResponse, Manifest, Slide, Cue, ActionType
from .s3_storage import S3StorageManager
from .effects import VisualEffects

if TYPE_CHECKING:
    from PIL import ImageDraw

logger = logging.getLogger(__name__)

class VideoExporter:
    """Video export service using FFmpeg"""
    
    def __init__(self, use_optimized: bool = True):
        self.ffmpeg_path = settings.FFMPEG_PATH
        self.quality_settings = {
            "low": {"resolution": "1280x720", "bitrate": "1M", "fps": 24},
            "medium": {"resolution": "1920x1080", "bitrate": "2M", "fps": 30},
            "high": {"resolution": "1920x1080", "bitrate": "4M", "fps": 30}
        }
        self.temp_dir = Path(tempfile.gettempdir()) / "slide_speaker_exports"
        self.temp_dir.mkdir(exist_ok=True)
        self.s3_storage = S3StorageManager()
        
        # Настройки оптимизации
        self.use_optimized = use_optimized
        self.num_workers = max(1, mp.cpu_count() - 1) if use_optimized else 1
        self.effects = VisualEffects()
        
        logger.info(f"VideoExporter initialized: optimized={use_optimized}, workers={self.num_workers}")
    
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
                
                # Generate frames for this slide (используем оптимизированный метод если включено)
                if self.use_optimized:
                    slide_frames = await self._render_slide_frames_optimized(
                        slide_image_path, slide, audio_duration, fps, temp_dir, frame_count
                    )
                else:
                    slide_frames = await self._render_slide_frames(
                        slide_image_path, slide, audio_duration, fps, temp_dir, frame_count
                    )
                
                frame_count += slide_frames
                
                # Логируем прогресс
                progress_percent = int((manifest.slides.index(slide) + 1) / len(manifest.slides) * 100)
                logger.info(f"Progress: {progress_percent}% ({manifest.slides.index(slide) + 1}/{len(manifest.slides)} slides)")
                
            logger.info(f"Generated {frame_count} frames for lesson {lesson_id}")
            
        except Exception as e:
            logger.error(f"Error generating video frames: {e}")
            raise ExportError(f"Failed to generate video frames: {e}")
    
    async def _render_slide_frames(self, slide_image_path: Path, slide: Slide, duration: float, fps: int, temp_dir: Path, start_frame: int) -> int:
        """Render frames for a single slide with visual effects (legacy PIL-based method)"""
        try:
            from PIL import Image, ImageDraw
            
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
    
    async def _render_slide_frames_optimized(self, slide_image_path: Path, slide: Slide, duration: float, fps: int, temp_dir: Path, start_frame: int) -> int:
        """
        \u041e\u043f\u0442\u0438\u043c\u0438\u0437\u0438\u0440\u043e\u0432\u0430\u043d\u043d\u044b\u0439 \u0440\u0435\u043d\u0434\u0435\u0440\u0438\u043d\u0433 \u043a\u0430\u0434\u0440\u043e\u0432 \u0441 \u0438\u0441\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u043d\u0438\u0435\u043c OpenCV \u0438 \u043f\u0430\u0440\u0430\u043b\u043b\u0435\u043b\u0438\u0437\u0430\u0446\u0438\u0438
        \u0423\u0441\u043a\u043e\u0440\u044f\u0435\u0442 \u0433\u0435\u043d\u0435\u0440\u0430\u0446\u0438\u044e \u0432 ~20 \u0440\u0430\u0437 \u043f\u043e \u0441\u0440\u0430\u0432\u043d\u0435\u043d\u0438\u044e \u0441 PIL
        """
        try:
            logger.info(f"Starting optimized frame rendering: {slide_image_path.name}")            
            # 1. \u0417\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c \u0431\u0430\u0437\u043e\u0432\u043e\u0435 \u0438\u0437\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u0438\u0435 \u0447\u0435\u0440\u0435\u0437 OpenCV (\u0432 5 \u0440\u0430\u0437 \u0431\u044b\u0441\u0442\u0440\u0435\u0435 PIL)
            base_image = cv2.imread(str(slide_image_path))
            if base_image is None:
                raise ExportError(f"Failed to load image: {slide_image_path}")
            
            # \u041a\u043e\u043d\u0432\u0435\u0440\u0442\u0438\u0440\u0443\u0435\u043c BGR -> RGB
            base_image = cv2.cvtColor(base_image, cv2.COLOR_BGR2RGB)
            
            # 2. \u0412\u044b\u0447\u0438\u0441\u043b\u044f\u0435\u043c \u043a\u043e\u043b\u0438\u0447\u0435\u0441\u0442\u0432\u043e \u043a\u0430\u0434\u0440\u043e\u0432
            frame_count = int(duration * fps)
            logger.info(f"Rendering {frame_count} frames at {fps} FPS (duration: {duration:.2f}s)")
            
            # \u0421\u043e\u0440\u0442\u0438\u0440\u0443\u0435\u043c cues \u043f\u043e \u0432\u0440\u0435\u043c\u0435\u043d\u0438
            sorted_cues = sorted(slide.cues, key=lambda c: c.t0)
            
            # 3. Pre-compute \u0430\u043a\u0442\u0438\u0432\u043d\u044b\u0435 cues \u0434\u043b\u044f \u043a\u0430\u0436\u0434\u043e\u0433\u043e \u043a\u0430\u0434\u0440\u0430 (\u043e\u043f\u0442\u0438\u043c\u0438\u0437\u0430\u0446\u0438\u044f)
            frames_data = []
            for frame_idx in range(frame_count):
                current_time = frame_idx / fps
                # \u0424\u0438\u043b\u044c\u0442\u0440\u0443\u0435\u043c \u0442\u043e\u043b\u044c\u043a\u043e \u0430\u043a\u0442\u0438\u0432\u043d\u044b\u0435 cues \u0434\u043b\u044f \u044d\u0442\u043e\u0433\u043e \u043a\u0430\u0434\u0440\u0430
                active_cues = [cue for cue in sorted_cues if cue.t0 <= current_time <= cue.t1]
                frames_data.append((frame_idx, current_time, active_cues))
            
            # 4. \u0420\u0430\u0437\u0431\u0438\u0432\u0430\u0435\u043c \u043d\u0430 \u0431\u0430\u0442\u0447\u0438 \u0434\u043b\u044f \u043f\u0430\u0440\u0430\u043b\u043b\u0435\u043b\u044c\u043d\u043e\u0439 \u043e\u0431\u0440\u0430\u0431\u043e\u0442\u043a\u0438
            batch_size = max(1, frame_count // self.num_workers)
            batches = [frames_data[i:i + batch_size] for i in range(0, len(frames_data), batch_size)]
            
            logger.info(f"Processing {len(batches)} batches with {self.num_workers} workers")
            
            # 5. \u041f\u0430\u0440\u0430\u043b\u043b\u0435\u043b\u044c\u043d\u043e \u043e\u0431\u0440\u0430\u0431\u0430\u0442\u044b\u0432\u0430\u0435\u043c \u0431\u0430\u0442\u0447\u0438
            loop = asyncio.get_event_loop()
            
            with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
                # \u0417\u0430\u043f\u0443\u0441\u043a\u0430\u0435\u043c \u0437\u0430\u0434\u0430\u0447\u0438
                futures = []
                for batch_idx, batch in enumerate(batches):
                    future = loop.run_in_executor(
                        executor,
                        VideoExporter._render_batch,
                        base_image.copy(),  # \u041a\u043e\u043f\u0438\u0440\u0443\u0435\u043c \u0434\u043b\u044f \u043a\u0430\u0436\u0434\u043e\u0433\u043e worker
                        batch,
                        str(temp_dir),
                        start_frame
                    )
                    futures.append((batch_idx, future))
                
                # \u0416\u0434\u0435\u043c \u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u0438\u044f \u0432\u0441\u0435\u0445 \u0437\u0430\u0434\u0430\u0447
                for batch_idx, future in futures:
                    try:
                        await future
                        logger.info(f"Batch {batch_idx + 1}/{len(batches)} completed")
                    except Exception as e:
                        logger.error(f"Error processing batch {batch_idx}: {e}")
                        raise
            
            logger.info(f"Optimized rendering completed: {frame_count} frames")
            return frame_count
            
        except Exception as e:
            logger.error(f"Error in optimized frame rendering: {e}")
            raise ExportError(f"Failed to render frames (optimized): {e}")
    
    @staticmethod
    def _render_batch(base_image: np.ndarray, frames_data: List[Tuple], temp_dir_str: str, start_frame: int):
        """
        \u0421\u0442\u0430\u0442\u0438\u0447\u0435\u0441\u043a\u0438\u0439 \u043c\u0435\u0442\u043e\u0434 \u0434\u043b\u044f \u043e\u0431\u0440\u0430\u0431\u043e\u0442\u043a\u0438 \u0431\u0430\u0442\u0447\u0430 \u043a\u0430\u0434\u0440\u043e\u0432 \u0432 \u043e\u0442\u0434\u0435\u043b\u044c\u043d\u043e\u043c \u043f\u0440\u043e\u0446\u0435\u0441\u0441\u0435
        \u041c\u0443\u0441\u0442 \u0431\u044b\u0442\u044c static \u0434\u043b\u044f ProcessPoolExecutor
        """
        try:
            temp_dir = Path(temp_dir_str)
            effects = VisualEffects()
            laser_position = None
            
            for frame_idx, current_time, active_cues in frames_data:
                # \u041a\u043e\u043f\u0438\u0440\u0443\u0435\u043c \u0431\u0430\u0437\u043e\u0432\u044b\u0439 \u043a\u0430\u0434\u0440
                frame = base_image.copy()
                
                # \u041f\u0440\u0438\u043c\u0435\u043d\u044f\u0435\u043c \u044d\u0444\u0444\u0435\u043a\u0442\u044b
                for cue in active_cues:
                    try:
                        if cue.action == ActionType.HIGHLIGHT and cue.bbox:
                            frame = effects.apply_highlight(frame, cue.bbox, cue.t0, cue.t1, current_time)
                        
                        elif cue.action == ActionType.UNDERLINE and cue.bbox:
                            frame = effects.apply_underline(frame, cue.bbox, cue.t0, cue.t1, current_time)
                        
                        elif cue.action == ActionType.LASER_MOVE and cue.to:
                            from_pos = cue.from_pos if hasattr(cue, 'from_pos') else None
                            frame, laser_position = effects.apply_laser_pointer(
                                frame, from_pos, cue.to, cue.t0, cue.t1, current_time, laser_position
                            )
                        
                        elif cue.action == ActionType.FADE_IN and cue.bbox:
                            frame = effects.apply_fade_in(frame, cue.bbox, cue.t0, cue.t1, current_time)
                        
                        elif cue.action == ActionType.FADE_OUT and cue.bbox:
                            frame = effects.apply_fade_out(frame, cue.bbox, cue.t0, cue.t1, current_time)
                    
                    except Exception as e:
                        logger.error(f"Error applying effect {cue.action}: {e}")
                        continue
                
                # \u0421\u043e\u0445\u0440\u0430\u043d\u044f\u0435\u043c \u043a\u0430\u0434\u0440 \u043a\u0430\u043a PNG \u0441 \u043e\u043f\u0442\u0438\u043c\u0438\u0437\u0430\u0446\u0438\u0435\u0439
                # PNG \u043d\u0443\u0436\u0435\u043d \u0434\u043b\u044f \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u0438\u044f \u0447\u0435\u0442\u043a\u043e\u0441\u0442\u0438 \u0442\u0435\u043a\u0441\u0442\u0430 (lossless compression)
                frame_path = temp_dir / f"frame_{start_frame + frame_idx:06d}.png"
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Compression level 3 = \u0431\u0430\u043b\u0430\u043d\u0441 \u043c\u0435\u0436\u0434\u0443 \u0441\u043a\u043e\u0440\u043e\u0441\u0442\u044c\u044e \u0438 \u0440\u0430\u0437\u043c\u0435\u0440\u043e\u043c
                # (0 = \u043d\u0435\u0442 \u0441\u0436\u0430\u0442\u0438\u044f, 9 = \u043c\u0430\u043a\u0441\u0438\u043c\u0430\u043b\u044c\u043d\u043e\u0435 \u0441\u0436\u0430\u0442\u0438\u0435 \u043d\u043e \u043c\u0435\u0434\u043b\u0435\u043d\u043d\u043e)
                cv2.imwrite(str(frame_path), frame_bgr, [cv2.IMWRITE_PNG_COMPRESSION, 3])
            
        except Exception as e:
            logger.error(f"Error in _render_batch: {e}")
            raise
    
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
            
            # Use FFmpeg filter complex to concatenate audio
            inputs = [ffmpeg.input(audio_file) for audio_file in audio_files]

            # ✅ FIX: Don't resample audio - keep original sample rate to prevent metallic sound
            # Removing ar=22050 to preserve original 48kHz quality
            (
                ffmpeg
                .concat(*inputs, v=0, a=1)
                .output(str(output_path), acodec="pcm_s16le")
                .overwrite_output()
                .run(quiet=True)
            )
            
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
            video = ffmpeg.input(str(video_path))
            audio = ffmpeg.input(str(audio_path))
            
            (
                ffmpeg
                .output(video, audio, str(output_path), vcodec="libx264", acodec="aac", pix_fmt="yuv420p", **{"b:v": quality["bitrate"], "b:a": "128k"})
                .overwrite_output()
                .run(quiet=True)
            )
            
        except Exception as e:
            logger.error(f"Error combining video and audio: {e}")
            raise
    
    def _get_slide_image_path(self, lesson_id: str, slide: Slide) -> Path:
        """Get path to slide image"""
        image_path = slide.image
        
        # Convert /assets/ path to .data/ path
        if image_path.startswith("/assets/"):
            image_path = image_path.replace("/assets/", "")
            return settings.DATA_DIR / image_path
        elif image_path.startswith("assets/"):
            image_path = image_path.replace("assets/", "")
            return settings.DATA_DIR / image_path
        elif image_path.startswith("/"):
            return Path(image_path[1:])  # Remove leading slash
        
        return settings.DATA_DIR / image_path
    
    def _get_audio_path(self, lesson_id: str, slide: Slide) -> Path:
        """Get path to slide audio"""
        audio_path = slide.audio
        
        # Convert /assets/ path to .data/ path
        if audio_path.startswith("/assets/"):
            audio_path = audio_path.replace("/assets/", "")
            audio_file = settings.DATA_DIR / audio_path
        elif audio_path.startswith("assets/"):
            audio_path = audio_path.replace("assets/", "")
            audio_file = settings.DATA_DIR / audio_path
        elif audio_path.startswith("/"):
            audio_file = Path(audio_path[1:])  # Remove leading slash
        else:
            audio_file = settings.DATA_DIR / audio_path
        
        # Try to find the actual audio file (might be .wav instead of .mp3)
        if not audio_file.exists() and audio_file.suffix == '.mp3':
            # Try .wav instead
            wav_file = audio_file.with_suffix('.wav')
            if wav_file.exists():
                return wav_file
        
        return audio_file
    
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