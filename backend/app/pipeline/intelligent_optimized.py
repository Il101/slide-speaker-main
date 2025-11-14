"""
Optimized Intelligent Pipeline - с параллельной обработкой
Phase 1: Quick Wins (без изменения AI моделей)
"""
import json
import logging
import asyncio
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor
import time

from .base import BasePipeline
from ..services.provider_factory import synthesize_slide_text_google_ssml, synthesize_slide_text_gemini
from ..services.ocr_cache import get_ocr_cache
from ..services.presentation_intelligence import PresentationIntelligence
from ..services.semantic_analyzer import SemanticAnalyzer
from ..services.smart_script_generator import SmartScriptGenerator
from ..services.validation_engine import ValidationEngine
from ..services.ssml_generator import generate_ssml_from_talk_track
# ❌ DISABLED: Old visual_cues system (replaced by Visual Effects V2)
# from ..services.bullet_point_sync import BulletPointSyncService
from ..services.visual_effects import VisualEffectsEngineV2

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
    
    def __init__(self, max_parallel_slides: int = 5, max_parallel_tts: int = 1):
        """
        Args:
            max_parallel_slides: Максимум параллельных слайдов для Stage 2-3
            max_parallel_tts: Максимум параллельных TTS запросов (CRITICAL: set to 1 due to Docker 3.8GB memory limit)
        """
        super().__init__()
        
        # Initialize services
        self.presentation_intelligence = PresentationIntelligence()
        self.semantic_analyzer = SemanticAnalyzer()
        self.script_generator = SmartScriptGenerator()
        self.validation_engine = ValidationEngine()
        
        # ❌ DISABLED: Old bullet point sync for visual_cues (replaced by Visual Effects V2)
        # self.bullet_sync = BulletPointSyncService(whisper_model="base")
        
        # ✅ NEW: Visual Effects V2 engine
        self.visual_effects_engine = VisualEffectsEngineV2()
        
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
        
        Uses actual TTS sentence timings when available, with fallback to character-based interpolation.
        Modifies talk_track in-place to add 'start' and 'end' times.
        """
        # ✅ FIX: Explicit None check instead of falsy check
        if talk_track is None or not talk_track or sentences is None or not sentences:
            return
        
        import re
        
        def normalize_text(text: str) -> str:
            """Normalize text for comparison by removing markers and extra whitespace"""
            # Remove SSML markers: [visual:XX]...[/visual], [lang:XX]...[/lang], [phoneme:...]...[/phoneme]
            text = re.sub(r'\[visual:[a-z]{2}\](.*?)\[/visual\]', r'\1', text)
            text = re.sub(r'\[phoneme:ipa:.*?\](.*?)\[/phoneme\]', r'\1', text)
            text = re.sub(r'\[lang:[a-z]{2}\](.*?)\[/lang\]', r'\1', text)
            # Remove extra whitespace and punctuation
            text = re.sub(r'[^\w\s]', '', text.lower())
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        
        # Try to match talk_track segments with sentences by group_marker or text similarity
        strategies_used = {'group_marker': 0, 'text_similarity': 0, 'interpolation': 0}
        
        for i, segment in enumerate(talk_track):
            group_id = segment.get('group_id')
            seg_text = segment.get("text", "")
            seg_text_norm = normalize_text(seg_text)
            
            matched = False
            
            # Strategy 1: Match by group_marker (most accurate)
            if group_id:
                for sentence in sentences:
                    if sentence.get('group_marker') == group_id:
                        segment["start"] = round(sentence['t0'], 2)
                        segment["end"] = round(sentence['t1'], 2)
                        matched = True
                        strategies_used['group_marker'] += 1
                        break
            
            # Strategy 2: Match by text similarity (fallback)
            if not matched and seg_text_norm:
                best_match = None
                best_similarity = 0.0
                
                for sentence in sentences:
                    sent_text_norm = normalize_text(sentence.get('text', ''))
                    if not sent_text_norm:
                        continue
                    
                    # Simple word overlap similarity
                    seg_words = set(seg_text_norm.split())
                    sent_words = set(sent_text_norm.split())
                    if not seg_words or not sent_words:
                        continue
                    
                    intersection = seg_words & sent_words
                    union = seg_words | sent_words
                    similarity = len(intersection) / len(union) if union else 0.0
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = sentence
                
                # Use match if similarity is reasonable (>30%)
                if best_match and best_similarity > 0.3:
                    segment["start"] = round(best_match['t0'], 2)
                    segment["end"] = round(best_match['t1'], 2)
                    matched = True
                    strategies_used['text_similarity'] += 1
            
            # Strategy 3: Character-based interpolation (last resort)
            if not matched:
                # Build full text from talk_track
                full_text = " ".join(seg.get("text", "") for seg in talk_track)
                
                # Calculate character positions
                char_pos = sum(len(talk_track[j].get("text", "")) + 1 for j in range(i))
                seg_start_char = char_pos
                seg_end_char = char_pos + len(seg_text)
                
                # Use relative position in full text to estimate timing
                relative_start = seg_start_char / max(len(full_text), 1)
                relative_end = seg_end_char / max(len(full_text), 1)
                
                # Get total audio duration
                total_duration = sentences[-1].get("t1", 0.0) if sentences else 0.0
                
                # Calculate timing
                start_time = relative_start * total_duration
                end_time = relative_end * total_duration
                
                segment["start"] = round(start_time, 2)
                segment["end"] = round(end_time, 2)
                strategies_used['interpolation'] += 1
        
        # Log which strategies were used
        self.logger.info(f"✅ Talk track timing calculated: {strategies_used['group_marker']} by marker, "
                        f"{strategies_used['text_similarity']} by similarity, "
                        f"{strategies_used['interpolation']} by interpolation")
    
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
            
        except (ImportError, RuntimeError, FileNotFoundError) as e:
            self.logger.error(f"Failed to convert PDF: {e}")
            raise
        except Exception as e:
            self.logger.exception(f"Unexpected error converting PDF: {e}")
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
        
        # 4.1. NEW: Diagram Detection & Classification
        self.logger.info(f"🖼️ Stage 2.1: Diagram detection for {len(slides)} slides...")
        
        from ..services.diagram_detector import DiagramDetector
        diagram_detector = DiagramDetector()
        
        total_diagrams = 0
        for i, slide in enumerate(slides):
            slide_id = slide['id']
            slide_number = i + 1
            png_path = lesson_path / "slides" / f"{slide_id:03d}.png"
            
            if not png_path.exists():
                continue
            
            # Detect diagrams on this slide
            text_elements = slide.get('elements', [])
            diagrams = diagram_detector.detect_diagrams(
                str(png_path),
                text_elements=text_elements,
                slide_number=slide_number
            )
            
            # Add diagrams to elements
            if diagrams:
                slide['elements'].extend(diagrams)
                slide['has_diagrams'] = True
                slide['diagram_count'] = len(diagrams)
                total_diagrams += len(diagrams)
                
                self.logger.info(
                    f"   Slide {slide_number}: found {len(diagrams)} diagrams "
                    f"({', '.join(d['diagram_type'] for d in diagrams)})"
                )
            else:
                slide['has_diagrams'] = False
                slide['diagram_count'] = 0
        
        self.logger.info(f"✅ Stage 2.1: Detected {total_diagrams} diagrams across all slides")
        
        # 4.5. Language Detection & Translation
        self.logger.info(f"🌍 Stage 2.5: Language detection and translation...")
        
        from ..services.language_detector import LanguageDetector
        from ..services.translation_service import TranslationService
        
        language_detector = LanguageDetector()
        translation_service = TranslationService()
        
        # Определяем язык презентации
        presentation_lang = language_detector.detect_presentation_language(slides)
        manifest['presentation_language'] = presentation_lang
        
        self.logger.info(f"📝 Detected presentation language: {presentation_lang}")
        
        # Получаем целевой язык для TTS из конфигурации
        target_tts_lang = os.getenv('SILERO_TTS_LANGUAGE', 'ru')
        
        self.logger.info(f"🎙️ Target TTS language: {target_tts_lang}")
        
        # Проверяем, нужен ли перевод
        translation_needed = translation_service.is_translation_needed(
            presentation_lang, 
            target_tts_lang
        )
        
        if translation_needed:
            self.logger.info(f"🔄 Translation enabled: {presentation_lang} → {target_tts_lang}")
            
            # Переводим элементы на каждом слайде
            for i, slide in enumerate(slides):
                elements = slide.get('elements', [])
                
                if not elements:
                    continue
                
                self.logger.info(f"   Translating slide {i+1}/{len(slides)}...")
                
                # Применяем перевод
                translated_elements = translation_service.translate_elements(
                    elements,
                    source_lang=presentation_lang,
                    target_lang=target_tts_lang
                )
                
                slide['elements'] = translated_elements
                slide['translation_applied'] = True
                slide['source_language'] = presentation_lang
                slide['target_language'] = target_tts_lang
            
            self.logger.info(f"✅ Translation completed for {len(slides)} slides")
        else:
            self.logger.info(f"⏭️  Translation skipped (languages match or disabled)")
            
            # Всё равно добавляем поля для совместимости
            for slide in slides:
                elements = slide.get('elements', [])
                for elem in elements:
                    text = elem.get('text', '')
                    elem['text_original'] = text
                    elem['text_translated'] = text
                    elem['language_original'] = presentation_lang
                    elem['language_target'] = target_tts_lang
                
                slide['translation_applied'] = False
                slide['source_language'] = presentation_lang
                slide['target_language'] = target_tts_lang
        
        # 5. Update metadata
        manifest['metadata']['stage'] = 'translation_complete'
        manifest['metadata']['translation_applied'] = translation_needed
        
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
        # ✅ CRITICAL: Use translated text for summaries to avoid language mixing
        self.logger.info("📝 Pre-computing slide summaries for context...")
        slides_summary_cache = {}
        for i, slide in enumerate(slides):
            elements = slide.get('elements', [])
            # Extract key text from elements (prefer translated)
            texts = [(e.get('text_translated') or e.get('text', ''))[:50] for e in elements[:3]]
            summary = " ".join(texts) if texts else "No text"
            slides_summary_cache[i] = summary
        
        # Stage 2-3: Параллельная обработка слайдов
        self.logger.info(f"⚡ Processing {len(slides)} slides in parallel (max {self.max_parallel_slides} concurrent)")
        
        async def process_single_slide(slide_data: Tuple[int, Dict[str, Any]]) -> Tuple[int, Dict[str, Any], Dict[str, Any]]:
            """
            Обработка одного слайда (Stage 2 + Stage 3) с дедупликацией
            
            ✅ IMPROVED: Проверяет кэш обработанных слайдов перед AI вызовами
            """
            i, slide = slide_data
            slide_id = slide["id"]
            elements = slide.get("elements", [])
            
            self.logger.info(f"📄 Processing slide {slide_id} ({i+1}/{len(slides)})")
            
            slide_image_path = lesson_path / "slides" / f"{slide_id:03d}.png"
            
            # ✅ NEW: Try to get processed slide from deduplication cache
            cached_processed = self.ocr_cache.get_processed_slide(str(slide_image_path))
            
            if cached_processed:
                semantic_map = cached_processed.get('semantic_map', {"groups": [], "mock": True})
                script = cached_processed.get('script', {"talk_track": [], "speaker_notes": "", "estimated_duration": 0})
                
                self.logger.info(f"✨ Slide {slide_id}: loaded from dedup cache (saved AI calls!)")
                return (i, semantic_map, script)
            
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
                
            except (ValueError, KeyError, json.JSONDecodeError) as e:
                self.logger.error(f"❌ Semantic analysis failed for slide {slide_id}: {e}")
            except Exception as e:
                self.logger.exception(f"❌ Unexpected error in semantic analysis for slide {slide_id}: {e}")
            
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
                
            except (ValueError, KeyError, json.JSONDecodeError, TimeoutError) as e:
                self.logger.error(f"❌ Script generation failed for slide {slide_id}: {e}")
            except Exception as e:
                self.logger.exception(f"❌ Unexpected error in script generation for slide {slide_id}: {e}")
            
            # ✅ NEW: Save processed slide to deduplication cache
            self.ocr_cache.save_processed_slide(str(slide_image_path), {
                'semantic_map': semantic_map,
                'script': script
            })
            
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
                
                # ✅ SOLUTION #1: Pre-calculate talk_track timing BEFORE TTS
                # This provides accurate VFX synchronization without additional costs
                estimated_duration = script.get('estimated_duration', 45)
                
                # Calculate total text length for proportional distribution
                total_chars = sum(len(seg.get('text', '')) for seg in talk_track_raw)
                current_time = 0.0
                
                if total_chars > 0:
                    for segment in talk_track_raw:
                        text_len = len(segment.get('text', ''))
                        segment_duration = (text_len / total_chars) * estimated_duration
                        
                        segment['start'] = round(current_time, 3)
                        segment['end'] = round(current_time + segment_duration, 3)
                        current_time += segment_duration
                    
                    # Also update cleaned version with timing
                    for i, segment in enumerate(talk_track_clean):
                        if i < len(talk_track_raw):
                            segment['start'] = talk_track_raw[i].get('start', 0.0)
                            segment['end'] = talk_track_raw[i].get('end', 0.0)
                    
                    self.logger.info(f"✅ Slide {slides[index]['id']}: Pre-calculated timing for {len(talk_track_raw)} segments")
                else:
                    self.logger.warning(f"⚠️ Slide {slides[index]['id']}: No text in talk_track, skipping timing calculation")
                
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
            
            # ✅ Log SSML for verification with detailed group marker context
            if ssml_texts:
                ssml_text = ssml_texts[0]
                ssml_preview = ssml_text[:500] if ssml_text else ""
                has_marks = '<mark' in ssml_text
                
                # Count group markers and extract context
                import re
                group_mark_matches = list(re.finditer(r'<mark name="(group_[^"]+)"/>(.*?)(?=<mark|</prosody>|</speak>)', ssml_text, re.DOTALL))
                group_marks = [m.group(1) for m in group_mark_matches]
                
                word_marks = re.findall(r'<mark name="(w\d+)"', ssml_text)
                
                self.logger.info(f"🎙️ Slide {slide_id}: SSML generated")
                self.logger.info(f"   SSML length: {len(ssml_text)} chars")
                self.logger.info(f"   Has <mark> tags: {has_marks}")
                self.logger.info(f"   Group markers: {len(group_marks)} found - {group_marks[:5]}")
                self.logger.info(f"   Word markers: {len(word_marks)} found")
                
                # Log context for each group marker (first 50 chars after marker)
                for match in group_mark_matches[:3]:  # Show first 3
                    marker = match.group(1)
                    context = match.group(2)[:50].strip()
                    self.logger.info(f"   Group '{marker}' context: '{context}...'")
                
                self.logger.info(f"   SSML preview: {ssml_preview}...")
            else:
                self.logger.warning(f"⚠️ Slide {slide_id}: no text generated!")
            
            # ✅ NEW: Use Gemini TTS Flash 2.5 (superior voice, sentence-level timing)
            # ⚠️ Note: Gemini TTS does NOT support SSML, so we extract plain text from talk_track
            import os
            tts_provider = os.getenv("TTS_PROVIDER", "gemini").lower()
            
            loop = asyncio.get_event_loop()
            
            if tts_provider == "gemini":
                # ✅ Gemini TTS: Extract plain text from talk_track (no SSML)
                if talk_track_raw and isinstance(talk_track_raw, list):
                    plain_texts = [segment.get('text', '') for segment in talk_track_raw if segment.get('text')]
                    self.logger.info(f"🎤 Slide {slide_id}: Using Gemini TTS Flash 2.5 with {len(plain_texts)} text segments")
                else:
                    # Fallback to OCR text
                    plain_texts = [speaker_notes]
                    self.logger.warning(f"⚠️ Slide {slide_id}: Using fallback text for Gemini TTS")
                
                # ✅ FIX: Add timeout to prevent hanging forever
                try:
                    audio_path, tts_words = await asyncio.wait_for(
                        loop.run_in_executor(
                            self.executor,
                            lambda: synthesize_slide_text_gemini(
                                plain_texts,
                                voice=os.getenv("GEMINI_TTS_VOICE", "Charon"),
                                prompt=os.getenv("GEMINI_TTS_PROMPT", "Speak naturally and clearly, with good pacing and intonation.")
                            )
                        ),
                        timeout=60.0  # 60 seconds timeout per slide
                    )
                    self.logger.info(f"✅ Slide {slide_id}: Gemini TTS complete (sentence-level timing)")
                except asyncio.TimeoutError:
                    self.logger.error(f"⏱️ Slide {slide_id}: Gemini TTS timeout after 60 seconds - will retry once")
                    # ✅ RETRY once on timeout
                    try:
                        self.logger.info(f"🔄 Retrying Gemini TTS for slide {slide_id}...")
                        audio_path, tts_words = await asyncio.wait_for(
                            loop.run_in_executor(
                                self.executor,
                                lambda: synthesize_slide_text_gemini(plain_texts)
                            ),
                            timeout=90.0  # Longer timeout for retry
                        )
                    except (asyncio.TimeoutError, ConnectionError, OSError) as retry_error:
                        self.logger.error(f"❌ Slide {slide_id}: Retry failed: {retry_error}")
                        return (index, None, {}, 0.0, None)
                except (ValueError, RuntimeError, OSError, IOError) as e:
                    self.logger.error(f"❌ Slide {slide_id}: Gemini TTS error: {e}")
                    return (index, None, {}, 0.0, None)
                except Exception as e:
                    self.logger.exception(f"❌ Slide {slide_id}: Unexpected Gemini TTS error: {e}")
                    return (index, None, {}, 0.0, None)
            else:
                # ✅ Fallback: Use SSML TTS (Chirp 3 HD) for word-level timings
                self.logger.info(f"🎤 Slide {slide_id}: Using Chirp 3 HD TTS with SSML (word-level timing)")
                
                # ✅ FIX: Add timeout to prevent hanging forever
                try:
                    # ✅ Use SSML TTS function for proper SSML support
                    audio_path, tts_words = await asyncio.wait_for(
                        loop.run_in_executor(
                            self.executor,
                            lambda: synthesize_slide_text_google_ssml(ssml_texts)
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
                                lambda: synthesize_slide_text_google_ssml(ssml_texts)
                            ),
                            timeout=90.0  # Longer timeout for retry
                        )
                    except (asyncio.TimeoutError, ConnectionError, OSError) as retry_error:
                        self.logger.error(f"❌ Slide {slide_id}: Retry failed: {retry_error}")
                        return (index, None, {}, 0.0, None)
                except (ValueError, RuntimeError, OSError, IOError) as e:
                    self.logger.error(f"❌ Slide {slide_id}: TTS error: {e}")
                    return (index, None, {}, 0.0, None)
                except Exception as e:
                    self.logger.exception(f"❌ Slide {slide_id}: Unexpected TTS error: {e}")
                    return (index, None, {}, 0.0, None)
            
            # Get duration
            duration = 0.0
            if tts_words and tts_words.get("sentences"):
                duration = tts_words["sentences"][-1].get("t1", 0.0)
            
            # Log word timings statistics with detailed info
            word_timings = tts_words.get("word_timings", []) if tts_words else []
            sentences = tts_words.get("sentences", []) if tts_words else []
            
            # Count group markers in timings
            import re
            group_timing_marks = [wt for wt in word_timings if wt.get('mark_name', '').startswith('group_')]
            
            self.logger.info(f"✅ Slide {slide_id}: audio generated ({duration:.1f}s)")
            self.logger.info(f"   TTS returned: {len(word_timings)} marks total, {len(sentences)} sentences")
            self.logger.info(f"   Group markers in TTS: {len(group_timing_marks)}")
            
            # ✅ FIX: Use debug for detailed timing logs to reduce noise in production
            if self.logger.isEnabledFor(logging.DEBUG):
                for gm in group_timing_marks[:5]:  # First 5
                    mark_name = gm.get('mark_name')
                    time_sec = gm.get('time_seconds', 0)
                    self.logger.debug(f"      • '{mark_name}' at {time_sec:.2f}s")
            
            # ✅ FIX: Detailed mark logging only in debug mode
            if self.logger.isEnabledFor(logging.DEBUG) and word_timings:
                if len(word_timings) <= 10:  # If few marks, show all
                    marks_info = [{'name': wt.get('mark_name'), 't': f"{wt.get('time_seconds', 0):.2f}s"} for wt in word_timings]
                    self.logger.debug(f"   All marks: {marks_info}")
                else:
                    marks_info = [{'name': wt.get('mark_name'), 't': f"{wt.get('time_seconds', 0):.2f}s"} for wt in word_timings[:5]]
                    self.logger.debug(f"   First 5 marks: {marks_info}")
            
            # ✅ CRITICAL: Force aggressive garbage collection after each slide to prevent OOM
            import gc
            gc.collect()

            return (index, audio_path, tts_words, duration, ssml_texts[0] if ssml_texts else None)

        # ✅ SEQUENTIAL generation to prevent OOM (Docker has only 3.8GB memory)
        # Even with semaphore=1, asyncio.gather creates all tasks upfront which loads memory
        async def generate_all_audio_sequential():
            """Generate audio one slide at a time with aggressive memory cleanup"""
            results = []
            for i, slide in enumerate(slides):
                self.logger.info(f"🎙️ Processing TTS for slide {i+1}/{len(slides)}")
                try:
                    result = await generate_audio_for_slide((i, slide))
                    results.append(result)

                    # ✅ CRITICAL: Aggressive memory cleanup after each slide
                    import gc
                    gc.collect()

                except Exception as e:
                    self.logger.error(f"❌ TTS failed for slide {i+1}: {e}")
                    results.append(e)

            return results

        results = loop.run_until_complete(generate_all_audio_sequential())
        
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
        
        # ✅ NEW: Generate Visual Effects V2 manifests for all slides
        self.logger.info("🎨 Generating Visual Effects V2 manifests...")
        vfx_start_time = time.time()
        vfx_success = 0
        
        for slide in slides:
            try:
                slide_id = slide.get("id")
                
                # Skip slides without audio
                if not slide.get("audio") or not slide.get("audio_duration"):
                    self.logger.warning(f"⚠️ Slide {slide_id}: skipping VFX (no audio)")
                    continue
                
                # Generate visual effects manifest
                vfx_manifest = self.visual_effects_engine.generate_slide_manifest(
                    semantic_map=slide.get("semantic_map", {"groups": []}),
                    elements=slide.get("elements", []),
                    audio_duration=slide.get("audio_duration", 0.0),
                    slide_id=f"slide_{slide_id}",
                    tts_words=slide.get("tts_words"),
                    talk_track=slide.get("talk_track_raw", [])
                )
                
                # Add to slide
                slide["visual_effects_manifest"] = vfx_manifest
                vfx_success += 1
                
                self.logger.info(f"✅ Slide {slide_id}: VFX manifest generated ({len(vfx_manifest.get('effects', []))} effects)")
                
            except Exception as e:
                self.logger.error(f"❌ Slide {slide_id}: VFX generation failed: {e}")
                # Continue even if VFX fails - it's not critical
                continue
        
        vfx_elapsed = time.time() - vfx_start_time
        self.logger.info(f"🎨 Visual Effects V2: completed in {vfx_elapsed:.1f}s ({vfx_success}/{len(slides)} slides)")
        
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
    
    def process_full_pipeline(self, lesson_dir: str, progress_callback=None) -> Dict[str, Any]:
        """
        Полный pipeline с замером времени и graceful degradation
        
        ✅ FIX: Теперь возвращает PipelineResult с поддержкой частичного успеха.
        Если некоторые слайды не удалось обработать, возвращаем частичный результат
        вместо полного провала.
        
        Args:
            lesson_dir: Path to lesson directory
            progress_callback: Optional callback(stage: str, progress: int, message: str)
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
                if progress_callback:
                    progress_callback('parsing', 10, 'Parsing presentation...')
                
                ingest_start = time.time()
                self.ingest(lesson_dir)  # PPTX/PDF → PNG
                ingest_time = time.time() - ingest_start
                
                if progress_callback:
                    progress_callback('parsing', 20, 'Extracting elements...')
                
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
            if progress_callback:
                progress_callback('generating_notes', 40, 'Generating lecture notes...')
            
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
            if progress_callback:
                progress_callback('generating_audio', 65, 'Synthesizing audio...')
            
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
            if progress_callback:
                progress_callback('generating_cues', 85, 'Creating visual effects...')
            
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
                duration = slide.get('duration')
                # ✅ FIX: Try audio_path first, then audio (different naming in old vs new pipeline)
                audio_path = slide.get('audio_path') or slide.get('audio')
                tts_words = slide.get('tts_words')
                # ✅ Use talk_track_raw (with markers) for visual effects sync
                talk_track_raw = slide.get('talk_track_raw', [])
                
                # ✅ FIX: Create simple semantic_map if missing (for old lessons)
                if not semantic_map or not semantic_map.get('groups'):
                    self.logger.warning(f"⚠️ No semantic_map for slide {slide_id}, creating simple one")
                    # Create simple groups from elements (one element = one group)
                    simple_groups = []
                    for i, elem in enumerate(elements):
                        elem_type = elem.get('type', 'text')
                        # Skip tiny elements (bullets, dots)
                        bbox = elem.get('bbox', [0, 0, 0, 0])
                        if len(bbox) >= 4 and (bbox[2] < 20 or bbox[3] < 10):
                            continue
                        
                        group = {
                            'id': f'simple_group_{i}',
                            'type': 'bullet_list' if elem_type == 'list_item' else elem_type,
                            'element_ids': [elem.get('id')],
                            'priority': 'normal',
                            'highlight_strategy': {
                                'when': 'during_explanation',
                                'effect_type': 'highlight',
                                'duration': 2.0,
                                'intensity': 'normal'
                            }
                        }
                        simple_groups.append(group)
                    
                    semantic_map = {'groups': simple_groups, 'fallback': True}
                    slide['semantic_map'] = semantic_map
                    self.logger.info(f"✅ Created {len(simple_groups)} simple groups from elements")
                
                # ✅ FIX: Calculate duration from audio file if missing
                if (not duration or duration == 0) and audio_path:
                    audio_filename = Path(audio_path).name
                    audio_full_path = lesson_path / "audio" / audio_filename
                    
                    if audio_full_path.exists():
                        try:
                            import wave
                            with wave.open(str(audio_full_path), 'rb') as audio_file:
                                frames = audio_file.getnframes()
                                rate = audio_file.getframerate()
                                duration = frames / float(rate)
                                slide['duration'] = duration
                                self.logger.info(f"✅ Calculated duration from audio file: {duration:.2f}s")
                        except Exception as e:
                            self.logger.warning(f"⚠️ Could not read audio file: {e}")
                            # Try fallback with pydub
                            try:
                                from pydub import AudioSegment
                                audio = AudioSegment.from_file(str(audio_full_path))
                                duration = len(audio) / 1000.0  # Convert ms to seconds
                                slide['duration'] = duration
                                self.logger.info(f"✅ Calculated duration with pydub: {duration:.2f}s")
                            except Exception as e2:
                                self.logger.error(f"❌ Failed to calculate duration: {e2}")
                
                if not duration or duration == 0 or not audio_path:
                    self.logger.warning(f"⚠️ Slide {slide_id} has no audio or duration, skipping cues")
                    slide['cues'] = []
                    slide['visual_cues'] = []  # Frontend expects this field
                    continue
                
                # ✅ Generate visual cues with smart timing strategy:
                # - Google TTS: Uses native word_timings from SSML <mark> tags (no Whisper needed)
                # - Silero TTS: Uses Whisper to extract word-level timing from generated audio
                # BulletPointSyncService automatically detects TTS provider and uses appropriate method

                # Convert relative audio path to absolute path
                audio_filename = Path(audio_path).name  # Extract "001.wav"
                audio_full_path = lesson_path / "audio" / audio_filename

                # ✅ NEW: Create synthetic talk_track_raw with group_id from semantic_map
                # This allows BulletPointSync to match visual effects even when LLM didn't provide group_id
                # ✅ FIX: Use talk_track WITH timing (if available)
                talk_track = slide.get('talk_track', [])

                # Check if talk_track has timing (start/end)
                has_timing = talk_track and len(talk_track) > 0 and 'start' in talk_track[0]
                if not has_timing:
                    self.logger.warning(f"⚠️ Slide {slide_id}: talk_track has NO timing, will use fallback distribution")
                else:
                    self.logger.info(f"✅ Slide {slide_id}: talk_track has timing from TTS")

                semantic_groups = semantic_map.get('groups', [])

                # Create element lookup for text matching
                elements_by_id = {elem.get('id'): elem for elem in elements}

                # Build group text index for better matching
                group_texts = {}
                for group in semantic_groups:
                    # Skip watermarks and decorative elements
                    if group.get('type') in ['watermark', 'decoration', 'noise']:
                        continue

                    # Collect text from all elements in this group
                    # ✅ FIX: Use text_translated for matching with Russian TTS
                    element_ids = group.get('element_ids', [])
                    texts = []
                    for elem_id in element_ids:
                        elem = elements_by_id.get(elem_id)
                        if elem:
                            # Prefer translated text (for matching with TTS)
                            text = elem.get('text_translated') or elem.get('text', '')
                            if text:
                                texts.append(text.lower())

                    if texts:
                        group_texts[group.get('id')] = ' '.join(texts)

                # Build talk_track_raw by matching talk_track text with semantic groups
                talk_track_raw = []
                used_groups = set()  # Track which groups were already used

                for i, segment in enumerate(talk_track):
                    segment_text = segment.get('text', '').lower()
                    segment_type = segment.get('segment', '')
                    group_id = None

                    # Strategy 1: Text similarity matching
                    best_match_score = 0
                    best_match_group = None

                    for gid, gtext in group_texts.items():
                        # Skip if group already used (prefer one-to-one mapping)
                        if gid in used_groups and best_match_score < 0.7:
                            continue

                        # Count matching words
                        segment_words = set(w for w in segment_text.split() if len(w) > 3)
                        group_words = set(w for w in gtext.split() if len(w) > 3)

                        if not segment_words:
                            continue

                        matches = segment_words & group_words
                        score = len(matches) / len(segment_words)

                        if score > best_match_score:
                            best_match_score = score
                            best_match_group = gid

                    # Use text match if score is good enough
                    if best_match_score > 0.2:  # At least 20% word overlap
                        group_id = best_match_group
                        used_groups.add(group_id)
                    else:
                        # Strategy 2: Fallback heuristics
                        # First segment -> title group
                        if i == 0 and semantic_groups:
                            title_groups = [g for g in semantic_groups if g.get('type') == 'title']
                            if title_groups:
                                group_id = title_groups[0].get('id')
                                used_groups.add(group_id)
                        # Other segments -> distribute among remaining groups
                        elif semantic_groups:
                            unused_groups = [g for g in semantic_groups
                                           if g.get('id') not in used_groups
                                           and g.get('type') not in ['watermark', 'decoration', 'noise']]
                            if unused_groups:
                                # Prefer content/key_point/bullet_list groups
                                priority_groups = [g for g in unused_groups
                                                 if g.get('type') in ['content', 'key_point', 'bullet_list']]
                                if priority_groups:
                                    group_id = priority_groups[0].get('id')
                                else:
                                    group_id = unused_groups[0].get('id')
                                if group_id:
                                    used_groups.add(group_id)

                    talk_track_raw.append({
                        **segment,
                        'group_id': group_id  # Add group_id for timing matching
                    })

                # ❌ DISABLED: Old visual_cues generation system (replaced by Visual Effects V2)
                # logger.info(f"🎯 Using BulletPointSync for visual effects on slide {slide_id}...")
                # logger.info(f"   Synthetic talk_track_raw: {len(talk_track_raw)} segments, {sum(1 for s in talk_track_raw if s.get('group_id'))} with group_id")
                # logger.info(f"   Semantic groups: {[g.get('id') for g in semantic_groups]}")
                # logger.info(f"   Mapped groups: {[s.get('group_id') for s in talk_track_raw if s.get('group_id')]}")
                # logger.info(f"   Elements: {len(elements)} total")

                # cues = self.bullet_sync.sync_bullet_points(
                #     audio_path=str(audio_full_path),
                #     talk_track_raw=talk_track_raw,
                #     semantic_map=semantic_map,
                #     elements=elements,
                #     slide_language="auto",
                #     audio_duration=duration,
                #     tts_words=tts_words
                # )
                
                # # Validate cues
                # cues, cue_errors = self.validation_engine.validate_cues(
                #     cues,
                #     duration,
                #     elements
                # )
                
                # if cue_errors:
                #     self.logger.warning(f"⚠️ Cue validation: {len(cue_errors)} issues")
                
                # # ✅ Save to BOTH 'cues' and 'visual_cues' for compatibility
                # slide['cues'] = cues
                # slide['visual_cues'] = cues  # Frontend expects this field

                # self.logger.info(f"✅ Generated {len(cues)} visual cues")
                # self.logger.info(f"   Slide {slide_id} now has {len(slide.get('cues', []))} cues in memory")
                
                # # Keep tts_words for debugging and potential runtime fallback
                # # Don't delete them - they contain sentences needed for text matching
                
            except Exception as e:
                self.logger.error(f"❌ Visual effects generation failed for slide {slide_id}: {e}")
                # slide['cues'] = []  # Not needed anymore - using visual_effects_manifest
        
        # Build timeline
        timeline = []
        current_time = 0.0
        
        for slide in manifest_data["slides"]:
            slide_id = slide["id"]
            duration = slide.get("duration") or 0.0
            
            if duration and duration > 0:
                timeline.append({
                    "t0": current_time,
                    "t1": current_time + duration,
                    "action": "slide_change",
                    "slide_id": slide_id
                })
                
                current_time += duration
        
        manifest_data["timeline"] = timeline
        
        # ✅ DEBUG: Log cues before saving
        for slide in manifest_data["slides"]:
            cues_count = len(slide.get('cues', []))
            self.logger.info(f"   Slide {slide['id']}: {cues_count} cues before save")

        # Save final manifest
        self.save_manifest(lesson_dir, manifest_data)

        self.logger.info(f"✅ OptimizedPipeline: Final manifest built for {lesson_dir}")
        self.logger.info(f"📊 Total slides: {len(manifest_data['slides'])}")
        self.logger.info(f"⏱️ Total duration: {current_time:.1f}s")
