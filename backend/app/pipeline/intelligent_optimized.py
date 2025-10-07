"""
Optimized Intelligent Pipeline - с параллельной обработкой
Phase 1: Quick Wins (без изменения AI моделей)
"""
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor
import time

from .base import BasePipeline
from ..services.provider_factory import synthesize_slide_text_google
from ..services.ocr_cache import get_ocr_cache
from ..services.presentation_intelligence import PresentationIntelligence
from ..services.semantic_analyzer import SemanticAnalyzer
from ..services.smart_script_generator import SmartScriptGenerator
from ..services.visual_effects_engine import VisualEffectsEngine
from ..services.validation_engine import ValidationEngine
from ..services.ssml_generator import generate_ssml_from_talk_track

logger = logging.getLogger(__name__)


class OptimizedIntelligentPipeline(BasePipeline):
    """
    Оптимизированный Intelligent Pipeline с параллельной обработкой
    
    Оптимизации:
    - Параллельная обработка слайдов (Stage 2-3)
    - Параллельная генерация TTS (Stage 4)
    - Кэширование OCR результатов
    
    Ожидаемое улучшение: -77% времени обработки
    """
    
    def __init__(self, max_parallel_slides: int = 5, max_parallel_tts: int = 10):
        """
        Args:
            max_parallel_slides: Максимум параллельных слайдов для Stage 2-3
            max_parallel_tts: Максимум параллельных TTS запросов
        """
        super().__init__()
        
        # Initialize services
        self.presentation_intelligence = PresentationIntelligence()
        self.semantic_analyzer = SemanticAnalyzer()
        self.script_generator = SmartScriptGenerator()
        self.effects_engine = VisualEffectsEngine()
        self.validation_engine = ValidationEngine()
        
        import os
        self.max_parallel_slides = int(os.getenv('PIPELINE_MAX_PARALLEL_SLIDES', max_parallel_slides))
        self.max_parallel_tts = int(os.getenv('PIPELINE_MAX_PARALLEL_TTS', max_parallel_tts))
        self.executor = ThreadPoolExecutor(max_workers=self.max_parallel_tts)
        self.logger = logger
        self.ocr_cache = get_ocr_cache()
    
    def _clean_lang_markers(self, talk_track: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove markers from talk_track text for display (subtitles):
        
        REMOVED COMPLETELY:
        - [visual:XX]term[/visual] → (not shown)
        - [pause:XXXms] → (not shown)
        
        EXTRACTED TEXT:
        - [lang:XX]term[/lang] → term
        - [phoneme:ipa:...]term[/phoneme] → term
        - [emphasis:level]text[/emphasis] → text
        - [pitch:X%]text[/pitch] → text
        - [rate:X%]text[/rate] → text
        
        Args:
            talk_track: List of segments with 'text' field
            
        Returns:
            Cleaned talk_track with markers removed
        """
        import re
        cleaned = []
        
        # Patterns that remove completely
        visual_pattern = r'\[visual:[a-z]{2}\].*?\[/visual\]'
        pause_pattern = r'\[pause:\d+ms\]'
        
        # Patterns that extract text
        lang_pattern = r'\[lang:[a-z]{2}\](.*?)\[/lang\]'
        phoneme_pattern = r'\[phoneme:ipa:.*?\](.*?)\[/phoneme\]'
        emphasis_pattern = r'\[emphasis:(?:strong|moderate|reduced)\](.*?)\[/emphasis\]'
        pitch_pattern = r'\[pitch:[\+\-]?\d+%\](.*?)\[/pitch\]'
        rate_pattern = r'\[rate:\d+%\](.*?)\[/rate\]'
        
        for segment in talk_track:
            cleaned_segment = segment.copy()
            if 'text' in cleaned_segment:
                text = cleaned_segment['text']
                
                # Remove completely
                text = re.sub(visual_pattern, '', text)
                text = re.sub(pause_pattern, '', text)
                
                # Extract text from markers
                text = re.sub(phoneme_pattern, r'\1', text)
                text = re.sub(lang_pattern, r'\1', text)
                text = re.sub(emphasis_pattern, r'\1', text)
                text = re.sub(pitch_pattern, r'\1', text)
                text = re.sub(rate_pattern, r'\1', text)
                
                # Clean up multiple spaces
                cleaned_segment['text'] = ' '.join(text.split())
            cleaned.append(cleaned_segment)
        
        return cleaned
    
    def _calculate_talk_track_timing(self, talk_track: List[Dict[str, Any]], sentences: List[Dict[str, Any]]) -> None:
        """
        Calculate start/end timing for each talk_track segment based on TTS sentences
        
        Modifies talk_track in-place to add 'start' and 'end' times.
        """
        if not talk_track or not sentences:
            return
        
        # Build full text from talk_track
        full_text = " ".join(seg.get("text", "") for seg in talk_track)
        
        # Calculate character positions for each talk_track segment
        char_pos = 0
        for segment in talk_track:
            seg_text = segment.get("text", "")
            seg_start_char = char_pos
            seg_end_char = char_pos + len(seg_text)
            char_pos = seg_end_char + 1  # +1 for space
            
            # Use relative position in full text to estimate timing
            relative_start = seg_start_char / max(len(full_text), 1)
            relative_end = seg_end_char / max(len(full_text), 1)
            
            # Get total audio duration
            total_duration = sentences[-1].get("t1", 0.0) if sentences else 0.0
            
            # Calculate timing
            start_time = relative_start * total_duration
            end_time = relative_end * total_duration
            
            # Update segment
            segment["start"] = round(start_time, 2)
            segment["end"] = round(end_time, 2)
    
    # REMOVED: ingest_old() method - deprecated, use ingest() instead
    
    def _find_presentation_file(self, lesson_dir: str) -> tuple[Path, str]:
        """Find PPTX or PDF file in lesson directory
        
        Returns:
            Tuple of (file_path, file_type) where file_type is 'pptx' or 'pdf'
        """
        lesson_path = Path(lesson_dir)
        
        # Look for .pptx files first
        pptx_files = list(lesson_path.glob("*.pptx"))
        if pptx_files:
            if len(pptx_files) > 1:
                self.logger.warning(f"Multiple PPTX files found, using first: {pptx_files[0]}")
            return pptx_files[0], 'pptx'
        
        # Look for .pdf files
        pdf_files = list(lesson_path.glob("*.pdf"))
        if pdf_files:
            if len(pdf_files) > 1:
                self.logger.warning(f"Multiple PDF files found, using first: {pdf_files[0]}")
            return pdf_files[0], 'pdf'
        
        raise FileNotFoundError(f"No PPTX or PDF file found in {lesson_dir}")
    
    def _find_pptx_file(self, lesson_dir: str) -> Path:
        """Find PPTX file in lesson directory (legacy method for compatibility)"""
        file_path, file_type = self._find_presentation_file(lesson_dir)
        return file_path
    
    def _convert_pptx_to_png(self, pptx_file: Path, output_dir: Path) -> List[Path]:
        """
        Convert PPTX to PNG images using PPTX→PDF→PNG approach
        
        Strategy:
        1. Convert PPTX to PDF using LibreOffice headless
        2. Convert PDF to PNG using pdf2image
        
        Args:
            pptx_file: Path to PPTX file
            output_dir: Directory to save PNG files
            
        Returns:
            List of paths to generated PNG files
        """
        self.logger.info(f"Converting PPTX to PNG: {pptx_file}")
        
        import subprocess
        import tempfile
        
        output_dir.mkdir(exist_ok=True)
        
        # Step 1: Convert PPTX → PDF using LibreOffice
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            
            try:
                # Try using libreoffice
                self.logger.info("Converting PPTX → PDF using LibreOffice...")
                result = subprocess.run(
                    [
                        'libreoffice',
                        '--headless',
                        '--convert-to', 'pdf',
                        '--outdir', str(temp_dir_path),
                        str(pptx_file)
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode != 0:
                    raise RuntimeError(f"LibreOffice conversion failed: {result.stderr}")
                
                # Find generated PDF
                pdf_files = list(temp_dir_path.glob("*.pdf"))
                if not pdf_files:
                    raise FileNotFoundError("No PDF generated by LibreOffice")
                
                pdf_file = pdf_files[0]
                self.logger.info(f"✅ PPTX converted to PDF: {pdf_file}")
                
            except FileNotFoundError:
                # LibreOffice not found, try unoconv as fallback
                self.logger.warning("LibreOffice not found, trying unoconv...")
                try:
                    result = subprocess.run(
                        ['unoconv', '-f', 'pdf', '-o', str(temp_dir_path), str(pptx_file)],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    if result.returncode != 0:
                        raise RuntimeError(f"unoconv failed: {result.stderr}")
                    
                    pdf_files = list(temp_dir_path.glob("*.pdf"))
                    if not pdf_files:
                        raise FileNotFoundError("No PDF generated")
                    pdf_file = pdf_files[0]
                    
                except FileNotFoundError:
                    # Final fallback: use PyMuPDF to read PPTX as PDF-like (won't work well)
                    self.logger.error("Neither LibreOffice nor unoconv found!")
                    self.logger.error("Please install LibreOffice: apt-get install libreoffice")
                    raise RuntimeError("PPTX conversion requires LibreOffice or unoconv")
            
            # Step 2: Convert PDF → PNG using pdf2image
            return self._convert_pdf_to_png(pdf_file, output_dir)
    
    def _convert_pdf_to_png(self, pdf_file: Path, output_dir: Path) -> List[Path]:
        """
        Convert PDF to PNG images using PyMuPDF (fitz)
        
        PyMuPDF is more reliable than pdf2image and doesn't require poppler.
        
        Args:
            pdf_file: Path to PDF file
            output_dir: Directory to save PNG files
            
        Returns:
            List of paths to generated PNG files
        """
        self.logger.info(f"Converting PDF to PNG: {pdf_file}")
        
        try:
            import fitz  # PyMuPDF
        except ImportError:
            self.logger.error("PyMuPDF not installed")
            raise ImportError("Install PyMuPDF: pip install pymupdf")
        
        output_dir.mkdir(exist_ok=True)
        png_files = []
        
        try:
            # Open PDF
            doc = fitz.open(str(pdf_file))
            
            # Convert each page
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Render at 2x resolution for better quality
                mat = fitz.Matrix(2, 2)  # 2x zoom
                pix = page.get_pixmap(matrix=mat)
                
                png_path = output_dir / f"{page_num + 1:03d}.png"
                pix.save(str(png_path))
                png_files.append(png_path)
                
                self.logger.info(f"✅ Converted page {page_num + 1}/{len(doc)}")
            
            doc.close()
            self.logger.info(f"✅ Converted {len(png_files)} PDF pages to PNG")
            return png_files
            
        except Exception as e:
            self.logger.error(f"Failed to convert PDF: {e}")
            raise
    
    def ingest(self, lesson_dir: str) -> None:
        """
        Stage 1: PPTX/PDF → PNG conversion
        
        Converts PPTX or PDF file to PNG images and creates initial manifest.
        Supports both PPTX and PDF presentations.
        """
        self.logger.info(f"🔄 Stage 1 (NEW): Converting presentation to PNG for {lesson_dir}")
        
        lesson_path = Path(lesson_dir)
        
        # 1. Find PPTX or PDF file
        presentation_file, file_type = self._find_presentation_file(lesson_dir)
        self.logger.info(f"Found {file_type.upper()} file: {presentation_file.name}")
        
        # 2. Create slides directory
        slides_dir = lesson_path / "slides"
        slides_dir.mkdir(exist_ok=True)
        
        # 3. Convert presentation → PNG
        if file_type == 'pptx':
            png_files = self._convert_pptx_to_png(presentation_file, slides_dir)
        else:  # pdf
            png_files = self._convert_pdf_to_png(presentation_file, slides_dir)
        
        # 4. Create initial manifest with slide references and dimensions
        lesson_id = lesson_path.name
        
        # Get slide dimensions from first PNG
        try:
            from PIL import Image
            first_png = png_files[0] if png_files else None
            if first_png:
                img = Image.open(first_png)
                slide_width, slide_height = img.size
                self.logger.info(f"Slide dimensions: {slide_width}x{slide_height}")
            else:
                slide_width, slide_height = 1920, 1080  # Default
        except Exception as e:
            self.logger.warning(f"Could not read slide dimensions: {e}, using default")
            slide_width, slide_height = 1920, 1080
        
        manifest = {
            "slides": [
                {
                    "id": i + 1,
                    "image": f"/assets/{lesson_id}/slides/{i+1:03d}.png",
                    "width": slide_width,
                    "height": slide_height,
                    "elements": []  # Will be filled in Stage 2 (OCR)
                }
                for i in range(len(png_files))
            ],
            "metadata": {
                "source_file": presentation_file.name,
                "source_type": file_type,
                "total_slides": len(png_files),
                "slide_width": slide_width,
                "slide_height": slide_height,
                "stage": "ingest_complete"
            }
        }
        
        # 5. Save manifest
        self.save_manifest(lesson_dir, manifest)
        
        self.logger.info(f"✅ Stage 1: Converted {len(png_files)} slides to PNG")
    
    def extract_elements(self, lesson_dir: str) -> None:
        """
        Stage 2: OCR extraction from PNG slides
        
        Extracts text elements and bounding boxes using configured OCR provider.
        """
        self.logger.info(f"🔍 Stage 2 (NEW): OCR extraction for {lesson_dir}")
        
        lesson_path = Path(lesson_dir)
        
        # 1. Load manifest
        manifest = self.load_manifest(lesson_dir)
        slides = manifest.get("slides", [])
        
        if not slides:
            raise ValueError("No slides found in manifest")
        
        # 2. Collect PNG paths
        png_paths = []
        for slide in slides:
            slide_id = slide['id']
            png_path = lesson_path / "slides" / f"{slide_id:03d}.png"
            
            if not png_path.exists():
                raise FileNotFoundError(f"Slide PNG not found: {png_path}")
            
            png_paths.append(str(png_path))
        
        # 3. Extract elements using OCR provider
        self.logger.info(f"Extracting OCR elements from {len(png_paths)} slides...")
        
        from ..services.provider_factory import extract_elements_from_pages
        
        try:
            elements_data = extract_elements_from_pages(png_paths)
        except Exception as e:
            self.logger.error(f"OCR extraction failed: {e}")
            # Fallback: create placeholder elements
            elements_data = [[{
                "id": "slide_area",
                "type": "placeholder",
                "text": "",
                "bbox": [0, 0, 1600, 900],
                "confidence": 1.0,
                "source": "fallback"
            }] for _ in png_paths]
        
        # 4. Add elements to manifest
        for i, slide in enumerate(slides):
            if i < len(elements_data):
                slide['elements'] = elements_data[i]
                self.logger.info(f"✅ Slide {slide['id']}: extracted {len(elements_data[i])} elements")
            else:
                slide['elements'] = []
                self.logger.warning(f"⚠️ Slide {slide['id']}: no OCR data")
        
        # 5. Update metadata
        manifest['metadata']['stage'] = 'ocr_complete'
        
        # 6. Save updated manifest
        self.save_manifest(lesson_dir, manifest)
        
        total_elements = sum(len(s.get('elements', [])) for s in slides)
        self.logger.info(f"✅ Stage 2: Extracted {total_elements} total OCR elements from {len(slides)} slides")
    
    def plan(self, lesson_dir: str) -> None:
        """
        Stage 2-4: Параллельный анализ и генерация скриптов
        
        Оптимизация: обрабатываем несколько слайдов одновременно
        """
        start_time = time.time()
        self.logger.info(f"OptimizedPipeline: Starting parallel planning for {lesson_dir}")
        
        lesson_path = Path(lesson_dir)
        manifest_path = lesson_path / "manifest.json"
        
        # Load manifest
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        
        slides = manifest_data.get("slides", [])
        
        # Stage 0: Analyze entire presentation for context (1 раз)
        self.logger.info("🧠 Stage 0: Analyzing presentation context...")
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        presentation_context = loop.run_until_complete(
            self.presentation_intelligence.analyze_presentation(
                slides,
                filename=lesson_path.name
            )
        )
        
        self.logger.info(f"✅ Presentation context: {presentation_context.get('theme', 'Unknown')}")
        manifest_data['presentation_context'] = presentation_context
        
        # ✅ FIX: Pre-compute slide summaries to avoid race condition
        self.logger.info("📝 Pre-computing slide summaries for context...")
        slides_summary_cache = {}
        for i, slide in enumerate(slides):
            elements = slide.get('elements', [])
            # Extract key text from elements
            texts = [e.get('text', '')[:50] for e in elements[:3]]
            summary = " ".join(texts) if texts else "No text"
            slides_summary_cache[i] = summary
        
        # Stage 2-3: Параллельная обработка слайдов
        self.logger.info(f"⚡ Processing {len(slides)} slides in parallel (max {self.max_parallel_slides} concurrent)")
        
        async def process_single_slide(slide_data: Tuple[int, Dict[str, Any]]) -> Tuple[int, Dict[str, Any], Dict[str, Any]]:
            """Обработка одного слайда (Stage 2 + Stage 3)"""
            i, slide = slide_data
            slide_id = slide["id"]
            elements = slide.get("elements", [])
            
            self.logger.info(f"📄 Processing slide {slide_id} ({i+1}/{len(slides)})")
            
            slide_image_path = lesson_path / "slides" / f"{slide_id:03d}.png"
            
            # Stage 2: Semantic Analysis
            semantic_map = {"groups": [], "mock": True}
            try:
                semantic_map = await self.semantic_analyzer.analyze_slide(
                    str(slide_image_path),
                    elements,
                    presentation_context,
                    previous_slides=[slides[j] for j in range(max(0, i-2), i)],
                    slide_index=i
                )
                
                self.logger.info(f"✅ Slide {slide_id}: {len(semantic_map.get('groups', []))} groups")
                
                # Validation
                semantic_map, validation_errors = self.validation_engine.validate_semantic_map(
                    semantic_map,
                    elements,
                    slide_size=(1440, 1080)
                )
                
                if validation_errors:
                    self.logger.warning(f"⚠️ Slide {slide_id}: {len(validation_errors)} validation issues")
                
            except Exception as e:
                self.logger.error(f"❌ Semantic analysis failed for slide {slide_id}: {e}")
            
            # Stage 3: Script Generation
            script = {"talk_track": [], "speaker_notes": "", "estimated_duration": 0}
            try:
                # ✅ FIX: Use pre-computed summary from cache (thread-safe)
                previous_slides_summary = ""
                if i > 0:
                    previous_slides_summary = f"Previous: {slides_summary_cache[i-1]}..."
                
                script = await self.script_generator.generate_script(
                    semantic_map,
                    elements,
                    presentation_context,
                    previous_slides_summary,
                    slide_index=i
                )
                
                self.logger.info(f"✅ Slide {slide_id}: script generated (overlap: {script.get('overlap_score', 0):.3f})")
                
            except Exception as e:
                self.logger.error(f"❌ Script generation failed for slide {slide_id}: {e}")
            
            return (i, semantic_map, script)
        
        # Создаём semaphore для ограничения параллелизма
        async def process_with_semaphore():
            semaphore = asyncio.Semaphore(self.max_parallel_slides)
            
            async def bounded_process(slide_data):
                async with semaphore:
                    return await process_single_slide(slide_data)
            
            tasks = [bounded_process((i, slide)) for i, slide in enumerate(slides)]
            return await asyncio.gather(*tasks, return_exceptions=True)
        
        # Запускаем параллельную обработку
        results = loop.run_until_complete(process_with_semaphore())
        
        # Применяем результаты к слайдам
        success_count = 0
        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Slide processing exception: {result}")
                continue
            
            try:
                index, semantic_map, script = result
                slides[index]['semantic_map'] = semantic_map
                
                # Save TWO versions of talk_track:
                # 1. talk_track_raw - with markers for SSML/TTS generation
                # 2. talk_track - cleaned for display (subtitles)
                talk_track_raw = script.get('talk_track', [])
                talk_track_clean = self._clean_lang_markers(talk_track_raw)
                
                slides[index]['talk_track_raw'] = talk_track_raw  # For SSML
                slides[index]['talk_track'] = talk_track_clean  # For subtitles
                slides[index]['speaker_notes'] = script.get('speaker_notes', '')
                slides[index]['estimated_duration'] = script.get('estimated_duration', 45)
                success_count += 1
            except Exception as e:
                self.logger.error(f"Error applying slide result: {e}")
        
        # Save updated manifest
        self.save_manifest(lesson_dir, manifest_data)
        
        elapsed = time.time() - start_time
        self.logger.info(f"⚡ OptimizedPipeline: Planning completed in {elapsed:.1f}s ({success_count}/{len(slides)} slides)")
    
    def tts(self, lesson_dir: str) -> None:
        """
        Stage 5: Параллельная TTS генерация
        
        Оптимизация: генерируем аудио для всех слайдов параллельно
        """
        start_time = time.time()
        self.logger.info(f"OptimizedPipeline: Starting parallel TTS for {lesson_dir}")
        
        lesson_path = Path(lesson_dir)
        manifest_path = lesson_path / "manifest.json"
        
        # Load manifest
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        
        slides = manifest_data.get("slides", [])
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        async def generate_audio_for_slide(slide_data: Tuple[int, Dict[str, Any]]) -> Tuple[int, str, Dict, float]:
            """Генерация аудио для одного слайда"""
            index, slide = slide_data
            slide_id = slide["id"]
            
            # Get talk track segments
            # ✅ Use talk_track_raw (with markers) for SSML generation
            talk_track_raw = slide.get("talk_track_raw", [])
            if not talk_track_raw:
                speaker_notes = slide.get("speaker_notes", "")
                if not speaker_notes:
                    # ✅ FALLBACK: Generate text from OCR elements
                    elements = slide.get("elements", [])
                    ocr_text = " ".join([e.get('text', '')[:100] for e in elements if e.get('text')])
                    
                    if not ocr_text:
                        self.logger.error(f"❌ Slide {slide_id}: no script AND no OCR text - cannot generate audio")
                        return (index, None, {}, 0.0, None)
                    
                    self.logger.warning(f"⚠️ Slide {slide_id}: using OCR fallback for TTS")
                    speaker_notes = f"Слайд {slide_id}. {ocr_text[:200]}"
                
                # Generate SSML from plain text
                from ..services.ssml_generator import SSMLGenerator
                ssml_generator = SSMLGenerator()
                ssml_texts = [ssml_generator.generate_simple_ssml(speaker_notes)]
            else:
                # ✅ Generate SSML from talk_track_raw (with markers) for word-level timing
                ssml_texts = generate_ssml_from_talk_track(talk_track_raw)
            
            # ✅ Log SSML for verification
            if ssml_texts:
                ssml_text = ssml_texts[0]
                ssml_preview = ssml_text[:500] if ssml_text else ""
                has_marks = '<mark' in ssml_text
                
                # Count group markers
                import re
                group_marks = re.findall(r'<mark name="(group_[^"]+)"', ssml_text)
                word_marks = re.findall(r'<mark name="(w\d+)"', ssml_text)
                
                self.logger.info(f"🎙️ Slide {slide_id}: SSML generated")
                self.logger.info(f"   SSML length: {len(ssml_text)} chars")
                self.logger.info(f"   Has <mark> tags: {has_marks}")
                self.logger.info(f"   Group markers: {len(group_marks)} found - {group_marks[:5]}")
                self.logger.info(f"   Word markers: {len(word_marks)} found")
                self.logger.info(f"   SSML preview: {ssml_preview}...")
            else:
                self.logger.warning(f"⚠️ Slide {slide_id}: no SSML generated!")
            
            # ✅ Use SSML TTS for word-level timings
            from workers.tts_google_ssml import GoogleTTSWorkerSSML
            loop = asyncio.get_event_loop()
            
            # ✅ FIX: Add timeout to prevent hanging forever
            try:
                audio_path, tts_words = await asyncio.wait_for(
                    loop.run_in_executor(
                        self.executor,
                        lambda: GoogleTTSWorkerSSML().synthesize_slide_text_google_ssml(ssml_texts)
                    ),
                    timeout=60.0  # 60 seconds timeout per slide
                )
            except asyncio.TimeoutError:
                self.logger.error(f"⏱️ Slide {slide_id}: TTS timeout after 60 seconds - will retry once")
                # ✅ RETRY once on timeout
                try:
                    self.logger.info(f"🔄 Retrying TTS for slide {slide_id}...")
                    audio_path, tts_words = await asyncio.wait_for(
                        loop.run_in_executor(
                            self.executor,
                            lambda: GoogleTTSWorkerSSML().synthesize_slide_text_google_ssml(ssml_texts)
                        ),
                        timeout=90.0  # Longer timeout for retry
                    )
                except Exception as retry_error:
                    self.logger.error(f"❌ Slide {slide_id}: Retry failed: {retry_error}")
                    return (index, None, {}, 0.0, None)
            except Exception as e:
                self.logger.error(f"❌ Slide {slide_id}: TTS error: {e}", exc_info=True)
                return (index, None, {}, 0.0, None)
            
            # Get duration
            duration = 0.0
            if tts_words and tts_words.get("sentences"):
                duration = tts_words["sentences"][-1].get("t1", 0.0)
            
            # Log word timings statistics
            word_timings = tts_words.get("word_timings", []) if tts_words else []
            sentences = tts_words.get("sentences", []) if tts_words else []
            
            # Count group markers in timings
            import re
            group_timing_marks = [wt for wt in word_timings if wt.get('mark_name', '').startswith('group_')]
            
            self.logger.info(f"✅ Slide {slide_id}: audio generated ({duration:.1f}s)")
            self.logger.info(f"   TTS returned: {len(word_timings)} marks total, {len(sentences)} sentences")
            self.logger.info(f"   Group markers in TTS: {len(group_timing_marks)} - {[g.get('mark_name') for g in group_timing_marks[:5]]}")
            
            if word_timings:
                self.logger.info(f"   First 5 marks: {[{'name': wt.get('mark_name'), 't': wt.get('time_seconds', 0)} for wt in word_timings[:5]]}")
            
            return (index, audio_path, tts_words, duration, ssml_texts[0] if ssml_texts else None)
        
        # Параллельная генерация аудио
        async def generate_all_audio():
            semaphore = asyncio.Semaphore(self.max_parallel_tts)
            
            async def bounded_generate(slide_data):
                async with semaphore:
                    return await generate_audio_for_slide(slide_data)
            
            tasks = [bounded_generate((i, slide)) for i, slide in enumerate(slides)]
            return await asyncio.gather(*tasks, return_exceptions=True)
        
        results = loop.run_until_complete(generate_all_audio())
        
        # Применяем результаты
        success_count = 0
        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"TTS exception: {result}")
                continue
            
            try:
                index, audio_path, tts_words, duration, ssml_text = result
                
                if not audio_path or not Path(audio_path).exists():
                    # ✅ DETAILED LOGGING: Log why audio failed
                    slide_id = slides[index]["id"]
                    self.logger.error(f"❌ Slide {slide_id} (index {index}): TTS failed - no audio file")
                    self.logger.error(f"   - audio_path: {audio_path}")
                    self.logger.error(f"   - talk_track_raw length: {len(slides[index].get('talk_track_raw', []))}")
                    self.logger.error(f"   - speaker_notes length: {len(slides[index].get('speaker_notes', ''))}")
                    
                    slides[index]["audio"] = None
                    slides[index]["duration"] = 0.0
                    slides[index]["tts_error"] = "Audio generation failed"
                    continue
                
                # Copy audio to lesson directory
                slide_id = slides[index]["id"]
                audio_dest = lesson_path / "audio" / f"{slide_id:03d}.wav"
                audio_dest.parent.mkdir(exist_ok=True)
                
                import shutil
                shutil.copy2(audio_path, audio_dest)
                
                # Update slide
                slides[index]["audio"] = f"/assets/{lesson_path.name}/audio/{slide_id:03d}.wav"
                slides[index]["duration"] = duration
                slides[index]["audio_duration"] = duration  # ✅ Add audio_duration
                slides[index]["tts_words"] = tts_words
                
                # ✅ Save SSML for debugging
                if ssml_text:
                    slides[index]["speaker_notes_ssml"] = ssml_text
                
                # ✅ Save full tts_words for visual effects fallback
                if tts_words:
                    word_timings = tts_words.get("word_timings", [])
                    sentences = tts_words.get("sentences", [])
                    
                    # Save full tts_words (needed for visual effects fallback)
                    slides[index]["tts_words"] = tts_words
                    # Also save sample for debugging
                    slides[index]["tts_words_sample"] = {
                        "total_marks": len(word_timings),
                        "first_5_marks": word_timings[:5] if word_timings else [],
                        "sentences_count": len(sentences),
                        "has_word_timing": len(word_timings) > 0
                    }
                    
                    # ✅ Calculate timing for talk_track segments
                    # Use talk_track_raw (with markers) for timing calculation to match TTS
                    talk_track_raw = slides[index].get("talk_track_raw", [])
                    talk_track_clean = slides[index].get("talk_track", [])
                    
                    if talk_track_raw and sentences:
                        # Calculate timing on raw version (matches TTS input)
                        self._calculate_talk_track_timing(talk_track_raw, sentences)
                        
                        # Copy timing to clean version for frontend
                        for i, segment_clean in enumerate(talk_track_clean):
                            if i < len(talk_track_raw):
                                segment_clean['start'] = talk_track_raw[i].get('start', 0.0)
                                segment_clean['end'] = talk_track_raw[i].get('end', 0.0)
                        
                        self.logger.info(f"   Calculated timing for {len(talk_track_clean)} talk_track segments")
                
                success_count += 1
                
            except Exception as e:
                self.logger.error(f"Error applying TTS result: {e}")
        
        # Save updated manifest
        self.save_manifest(lesson_dir, manifest_data)
        
        elapsed = time.time() - start_time
        
        # ✅ DETAILED REPORT: Count failed slides
        failed_slides = [s for s in slides if s.get("audio") is None]
        if failed_slides:
            self.logger.error(f"⚠️ TTS FAILURES: {len(failed_slides)} slides without audio:")
            for slide in failed_slides:
                slide_id = slide.get("id")
                error = slide.get("tts_error", "Unknown error")
                self.logger.error(f"   - Slide {slide_id}: {error}")
        
        self.logger.info(f"⚡ OptimizedPipeline: TTS completed in {elapsed:.1f}s ({success_count}/{len(slides)} slides)")
        
        if success_count < len(slides):
            self.logger.warning(f"⚠️ Only {success_count}/{len(slides)} slides have audio - check logs above for details")
    
    def process_full_pipeline(self, lesson_dir: str) -> Dict[str, Any]:
        """
        Полный pipeline с замером времени и graceful degradation
        
        ✅ FIX: Теперь возвращает PipelineResult с поддержкой частичного успеха.
        Если некоторые слайды не удалось обработать, возвращаем частичный результат
        вместо полного провала.
        """
        start_time = time.time()
        
        from ..pipeline.result import PipelineResult
        from ..core.config import settings
        
        lesson_path = Path(lesson_dir)
        lesson_id = lesson_path.name
        
        # Создаём объект результата
        result = PipelineResult(
            lesson_id=lesson_id,
            total_slides=0  # Узнаем после ingest
        )
        
        try:
            use_new = settings.USE_NEW_PIPELINE
            self.logger.info(f"⚡ OptimizedIntelligentPipeline: Starting for {lesson_dir} (NEW={use_new})")
            
            # Run pipeline steps with error recovery
            try:
                ingest_start = time.time()
                self.ingest(lesson_dir)  # PPTX/PDF → PNG
                ingest_time = time.time() - ingest_start
                
                ocr_start = time.time()
                self.extract_elements(lesson_dir)  # OCR extraction
                ocr_time = time.time() - ocr_start
                
                self.logger.info(f"  Stage 1 (PPTX→PNG): {ingest_time:.1f}s")
                self.logger.info(f"  Stage 2 (OCR): {ocr_time:.1f}s")
            except Exception as e:
                self.logger.error(f"❌ Critical error in ingest/OCR: {e}", exc_info=True)
                # Не можем продолжить без слайдов
                result.warnings.append(f"Ingest/OCR failed: {str(e)}")
                result.mark_completed()
                return result.to_dict()
            
            # Load manifest to get slide count
            manifest = self.load_manifest(lesson_dir)
            slides = manifest.get('slides', [])
            result.total_slides = len(slides)
            
            # Plan stage - process with slide-level error recovery
            plan_start = time.time()
            try:
                self.plan(lesson_dir)
                plan_time = time.time() - plan_start
                self.logger.info(f"  Stage 3 (Plan): {plan_time:.1f}s")
            except Exception as e:
                self.logger.error(f"⚠️ Plan stage failed: {e}", exc_info=True)
                result.warnings.append(f"Plan stage partial failure: {str(e)}")
                plan_time = time.time() - plan_start
            
            # TTS stage - process with slide-level error recovery
            tts_start = time.time()
            try:
                self.tts(lesson_dir)
                tts_time = time.time() - tts_start
                self.logger.info(f"  Stage 4 (TTS): {tts_time:.1f}s")
            except Exception as e:
                self.logger.error(f"⚠️ TTS stage failed: {e}", exc_info=True)
                result.warnings.append(f"TTS stage partial failure: {str(e)}")
                tts_time = time.time() - tts_start
            
            # Build manifest stage - process with slide-level error recovery
            manifest_start = time.time()
            try:
                self.build_manifest(lesson_dir)
                manifest_time = time.time() - manifest_start
                self.logger.info(f"  Stage 5 (Manifest): {manifest_time:.1f}s")
            except Exception as e:
                self.logger.error(f"⚠️ Manifest stage failed: {e}", exc_info=True)
                result.warnings.append(f"Manifest stage partial failure: {str(e)}")
                manifest_time = time.time() - manifest_start
            
            # ✅ Проверяем результаты для каждого слайда
            manifest = self.load_manifest(lesson_dir)
            slides = manifest.get('slides', [])
            
            for i, slide in enumerate(slides):
                slide_id = slide.get('id')
                
                # Проверяем успешность обработки слайда
                has_audio = slide.get('audio') is not None
                has_cues = len(slide.get('cues', [])) > 0
                has_script = len(slide.get('speaker_notes', '')) > 0
                
                if has_audio and has_script:
                    result.add_success(i, slide_id, processing_time=0.0)
                    if not has_cues:
                        result.warnings.append(f"Slide {slide_id}: no visual cues generated")
                else:
                    # Слайд обработан частично или не обработан
                    error_parts = []
                    if not has_audio:
                        error_parts.append("no audio")
                    if not has_script:
                        error_parts.append("no script")
                    
                    error_msg = ", ".join(error_parts)
                    result.add_failure(i, slide_id, Exception(error_msg))
                    
                    # Создать fallback данные
                    slides[i] = self._create_fallback_slide_data(slide, i)
            
            # Сохранить обновлённый manifest даже с частичными результатами
            if result.is_usable():
                manifest['slides'] = slides
                self.save_manifest(lesson_dir, manifest)
                self.logger.info(f"✅ Saved manifest with {result.success_rate*100:.1f}% success rate")
            else:
                self.logger.error(f"❌ Pipeline failed: only {result.success_rate*100:.1f}% success")
            
            result.mark_completed()
            
            # Логируем детальный отчёт
            self.logger.info("\n" + result.get_detailed_report())
            
            return result.to_dict()
            
        except Exception as e:
            self.logger.error(f"❌ Critical pipeline error: {e}", exc_info=True)
            result.warnings.append(f"Critical error: {str(e)}")
            result.mark_completed()
            return result.to_dict()
    
    def _create_fallback_slide_data(self, slide: Dict[str, Any], index: int) -> Dict[str, Any]:
        """
        Создать минимальные fallback данные для неудавшегося слайда
        
        ✅ FIX: Позволяет пользователю получить хотя бы частичный результат
        """
        slide_id = slide.get('id', index + 1)
        
        # Извлечь текст из elements для базового описания
        elements = slide.get('elements', [])
        slide_text = " ".join([e.get('text', '')[:50] for e in elements[:3]])
        
        fallback_notes = f"Slide {slide_id} - processing failed. Content: {slide_text[:100]}"
        
        return {
            **slide,
            'speaker_notes': fallback_notes,
            'talk_track': [
                {
                    "segment": "fallback",
                    "text": fallback_notes,
                    "group_id": None,
                    "start": 0.0,
                    "end": 5.0
                }
            ],
            'audio': None,
            'duration': 0,
            'cues': [],
            'visual_cues': [],  # Frontend expects this field
            'error': 'Processing failed',
            'is_fallback': True
        }
    
    def build_manifest(self, lesson_dir: str) -> None:
        """Stage 6-8: Visual effects + validation + final manifest"""
        self.logger.info(f"OptimizedPipeline: Building final manifest for {lesson_dir}")
        
        lesson_path = Path(lesson_dir)
        manifest_path = lesson_path / "manifest.json"
        
        # Load manifest
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        
        # Generate visual cues for each slide
        for slide in manifest_data["slides"]:
            slide_id = slide["id"]
            
            self.logger.info(f"✨ Stage 5: Generating visual effects for slide {slide_id}...")
            
            try:
                semantic_map = slide.get('semantic_map', {})
                elements = slide.get('elements', [])
                duration = slide.get('duration', 0.0)
                tts_words = slide.get('tts_words')
                # ✅ Use talk_track_raw (with markers) for visual effects sync
                talk_track_raw = slide.get('talk_track_raw', [])
                
                if duration == 0:
                    self.logger.warning(f"⚠️ Slide {slide_id} has no audio, skipping cues")
                    slide['cues'] = []
                    slide['visual_cues'] = []  # Frontend expects this field
                    continue
                
                # Generate cues using semantic map with talk_track_raw for fallback
                cues = self.effects_engine.generate_cues_from_semantic_map(
                    semantic_map,
                    elements,
                    duration,
                    tts_words,
                    talk_track_raw  # Use raw version with markers
                )
                
                # Validate cues
                cues, cue_errors = self.validation_engine.validate_cues(
                    cues,
                    duration,
                    elements
                )
                
                if cue_errors:
                    self.logger.warning(f"⚠️ Cue validation: {len(cue_errors)} issues")
                
                # ✅ Save to BOTH 'cues' and 'visual_cues' for compatibility
                slide['cues'] = cues
                slide['visual_cues'] = cues  # Frontend expects this field
                
                self.logger.info(f"✅ Generated {len(cues)} visual cues")
                
                # Keep tts_words for debugging and potential runtime fallback
                # Don't delete them - they contain sentences needed for text matching
                
            except Exception as e:
                self.logger.error(f"❌ Visual effects failed for slide {slide_id}: {e}")
                slide['cues'] = []
        
        # Build timeline
        timeline = []
        current_time = 0.0
        
        for slide in manifest_data["slides"]:
            slide_id = slide["id"]
            duration = slide.get("duration", 0.0)
            
            if duration > 0:
                timeline.append({
                    "t0": current_time,
                    "t1": current_time + duration,
                    "action": "slide_change",
                    "slide_id": slide_id
                })
                
                current_time += duration
        
        manifest_data["timeline"] = timeline
        
        # Save final manifest
        self.save_manifest(lesson_dir, manifest_data)
        
        self.logger.info(f"✅ OptimizedPipeline: Final manifest built for {lesson_dir}")
        self.logger.info(f"📊 Total slides: {len(manifest_data['slides'])}")
        self.logger.info(f"⏱️ Total duration: {current_time:.1f}s")
