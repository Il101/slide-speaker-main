# 🔄 Pipeline Refactoring Plan - Всё в Pipeline

## 🎯 Цель

Перенести ВСЮ логику обработки в pipeline - от PPTX до готового видео.

---

## ❌ Текущая Проблема

### Размазанная логика:

```
main.py:
├─ Upload file ✓
├─ Convert PPTX → PNG ❌ (должно быть в pipeline)
├─ OCR extraction ❌ (должно быть в pipeline)
├─ Create manifest ❌ (должно быть в pipeline)
└─ Start Celery task → Pipeline

Pipeline:
├─ Stage 1: Ingest (только валидация!) ❌
├─ Stage 2-3: Plan
├─ Stage 4: TTS
└─ Stage 5-8: Build Manifest

❌ Build Video - вообще отсутствует!
```

**Проблемы:**
- 🔴 Дублирование: PPTX→PNG логика и в main.py и потенциально в pipeline
- 🔴 Несогласованность: OCR до pipeline, но pipeline его не контролирует
- 🔴 Нет видео: финальная сборка вообще не реализована
- 🔴 Сложно тестировать: нельзя запустить pipeline отдельно
- 🔴 Сложно дебажить: не понятно где что упало

---

## ✅ Новая Архитектура

### Простая и логичная:

```
main.py (ТОЛЬКО загрузка):
├─ Upload file
├─ Save to disk
└─ Start Celery task → Pipeline

Pipeline (ВСЁ остальное):
├─ Stage 1: Ingest - PPTX → PNG
├─ Stage 2: OCR - PNG → Elements
├─ Stage 3: Presentation Context
├─ Stage 4: Semantic Analysis (parallel)
├─ Stage 5: Script Generation (parallel)
├─ Stage 6: TTS (parallel)
├─ Stage 7: Visual Effects
├─ Stage 8: Timeline
└─ Stage 9: Build Video ← НОВОЕ!
```

---

## 📋 Новые Stages

### **Stage 1: Ingest (ОБНОВЛЕНО)**

**Было:**
```python
def ingest(self, lesson_dir: str):
    # Только валидация manifest
    if not manifest_path.exists():
        raise FileNotFoundError
```

**Станет:**
```python
def ingest(self, lesson_dir: str):
    """Stage 1: PPTX → PNG conversion"""
    
    # 1. Найти PPTX файл
    pptx_file = self._find_pptx_file(lesson_dir)
    
    # 2. Конвертировать в PNG
    slides_dir = Path(lesson_dir) / "slides"
    slides_dir.mkdir(exist_ok=True)
    
    png_files = self._convert_pptx_to_png(pptx_file, slides_dir)
    
    # 3. Создать начальный manifest
    manifest = {
        "slides": [
            {
                "id": i + 1,
                "image": f"/assets/{lesson_id}/slides/{i+1:03d}.png"
            }
            for i in range(len(png_files))
        ]
    }
    
    self.save_manifest(lesson_dir, manifest)
    
    logger.info(f"✅ Stage 1: Converted {len(png_files)} slides to PNG")
```

**Методы:**
- `_find_pptx_file()` - находит PPTX в директории
- `_convert_pptx_to_png()` - PyMuPDF конвертация

---

### **Stage 2: OCR (НОВОЕ)**

```python
def extract_elements(self, lesson_dir: str):
    """Stage 2: OCR - Extract elements from PNG slides"""
    
    # 1. Загрузить manifest
    manifest = self.load_manifest(lesson_dir)
    slides = manifest["slides"]
    
    # 2. Собрать пути к PNG
    lesson_path = Path(lesson_dir)
    png_paths = [
        lesson_path / "slides" / f"{slide['id']:03d}.png"
        for slide in slides
    ]
    
    # 3. Извлечь элементы через OCR provider
    from ..services.provider_factory import extract_elements_from_pages
    
    elements_data = extract_elements_from_pages([str(p) for p in png_paths])
    
    # 4. Добавить elements в manifest
    for i, slide in enumerate(slides):
        slide['elements'] = elements_data[i] if i < len(elements_data) else []
    
    self.save_manifest(lesson_dir, manifest)
    
    logger.info(f"✅ Stage 2: Extracted OCR elements from {len(slides)} slides")
```

---

### **Stage 3-8: Без изменений**

Просто переименуем:
- Stage 0 → Stage 3: Presentation Context
- Stage 2 → Stage 4: Semantic Analysis
- Stage 3 → Stage 5: Script Generation
- Stage 4 → Stage 6: TTS
- Stage 5 → Stage 7: Visual Effects
- Stage 8 → Stage 8: Timeline

---

### **Stage 9: Build Video (НОВОЕ)**

```python
def build_video(self, lesson_dir: str):
    """Stage 9: Build final video with slides, audio, and visual effects"""
    
    # 1. Загрузить manifest
    manifest = self.load_manifest(lesson_dir)
    
    # 2. Построить видео
    from ..services.video_builder import VideoBuilder
    
    builder = VideoBuilder()
    video_path = builder.build_video(
        manifest=manifest,
        lesson_dir=lesson_dir,
        output_path=Path(lesson_dir) / "lecture.mp4"
    )
    
    # 3. Обновить manifest
    manifest['video'] = f"/assets/{lesson_id}/lecture.mp4"
    manifest['video_duration'] = manifest['timeline'][-1]['t1']
    
    self.save_manifest(lesson_dir, manifest)
    
    logger.info(f"✅ Stage 9: Built video: {video_path}")
```

---

## 🔧 Упрощённый main.py

### Было (~150 строк логики):

```python
@app.post("/upload")
async def upload_file(file: UploadFile):
    # Сохранить файл
    lesson_dir = DATA_DIR / lesson_id
    file_path = lesson_dir / file.filename
    
    # ❌ Парсить документ (OCR, PNG conversion)
    parser = ParserFactory.create_parser(file_path)
    manifest = await parser.parse()
    
    # ❌ Сохранить manifest
    with open(manifest_path, "w") as f:
        json.dump(manifest.dict(), f)
    
    # ❌ Запустить pipeline.ingest()
    pipeline.ingest(str(lesson_dir))
    
    # Создать DB запись
    lesson = Lesson(...)
    db.add(lesson)
    
    # Запустить Celery task
    task = process_lesson_full_pipeline.delay(lesson_id, ...)
    
    return {"lesson_id": lesson_id}
```

### Станет (~30 строк):

```python
@app.post("/upload")
async def upload_file(file: UploadFile, db: AsyncSession = Depends(get_db)):
    """Upload PPTX file and start processing"""
    
    # 1. Validate file
    if not file.filename or not file.filename.endswith('.pptx'):
        raise HTTPException(400, "Only PPTX files allowed")
    
    # 2. Save file
    lesson_id = str(uuid.uuid4())
    lesson_dir = settings.DATA_DIR / lesson_id
    lesson_dir.mkdir(exist_ok=True)
    
    file_path = lesson_dir / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    logger.info(f"✅ Saved PPTX: {file_path}")
    
    # 3. Create DB record
    lesson = Lesson(
        id=lesson_id,
        user_id=get_current_user_id(request),
        title=file.filename,
        file_path=str(file_path),
        status="processing"
    )
    db.add(lesson)
    await db.commit()
    
    # 4. Start pipeline (everything happens here!)
    from .tasks import process_lesson_full_pipeline
    task = process_lesson_full_pipeline.delay(lesson_id)
    
    logger.info(f"✅ Started pipeline task {task.id} for {lesson_id}")
    
    return UploadResponse(lesson_id=lesson_id, status="processing")
```

**✅ Всего 30 строк вместо 150!**

---

## 📁 Файловая Структура

### Удалить:

```bash
# Больше не нужны - логика в pipeline
backend/app/services/sprint1/document_parser.py  ❌
backend/app/services/sprint1/__init__.py         ❌
```

### Создать:

```bash
# Новый сервис для сборки видео
backend/app/services/video_builder.py            ✅
```

### Обновить:

```bash
backend/app/pipeline/intelligent_optimized.py    🔄 (новые stages)
backend/app/main.py                              🔄 (упрощение)
```

---

## 🔄 Обновлённый Pipeline

```python
class OptimizedIntelligentPipeline(BasePipeline):
    
    def process_full_pipeline(self, lesson_dir: str):
        """Полный pipeline от PPTX до видео"""
        
        try:
            # Stage 1: PPTX → PNG
            self.ingest(lesson_dir)
            
            # Stage 2: OCR
            self.extract_elements(lesson_dir)
            
            # Stage 3-8: Интеллектуальная обработка
            self.plan(lesson_dir)        # Stage 3-5
            self.tts(lesson_dir)          # Stage 6
            self.build_manifest(lesson_dir)  # Stage 7-8
            
            # Stage 9: Сборка видео
            self.build_video(lesson_dir)
            
            return {
                "status": "success",
                "video": f"/assets/{lesson_id}/lecture.mp4"
            }
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            raise
    
    def ingest(self, lesson_dir: str):
        """Stage 1: Convert PPTX → PNG"""
        # Конвертация PPTX → PNG
        # Создание начального manifest
        pass
    
    def extract_elements(self, lesson_dir: str):
        """Stage 2: OCR extraction"""
        # OCR через Vision API
        # Добавление elements в manifest
        pass
    
    def plan(self, lesson_dir: str):
        """Stage 3-5: Context + Semantic + Script"""
        # Stage 3: Presentation Context
        # Stage 4: Semantic Analysis (parallel)
        # Stage 5: Script Generation (parallel)
        pass
    
    def tts(self, lesson_dir: str):
        """Stage 6: TTS Generation"""
        # SSML генерация
        # Параллельный TTS синтез
        pass
    
    def build_manifest(self, lesson_dir: str):
        """Stage 7-8: Visual Effects + Timeline"""
        # Stage 7: Visual Effects
        # Stage 8: Timeline
        pass
    
    def build_video(self, lesson_dir: str):
        """Stage 9: Build final video"""
        # Сборка MP4 с ffmpeg
        pass
```

---

## 🎬 VideoBuilder Service

```python
class VideoBuilder:
    """Builds MP4 video from slides, audio, and visual effects"""
    
    def build_video(self, manifest: Dict, lesson_dir: str, output_path: Path) -> Path:
        """
        Build video using ffmpeg
        
        Input:
        - Slides (PNG images)
        - Audio files (WAV)
        - Visual effects (cues from manifest)
        - Timeline
        
        Output:
        - lecture.mp4
        """
        
        # 1. Подготовить input файлы
        slides = self._prepare_slides(manifest, lesson_dir)
        audio = self._concatenate_audio(manifest, lesson_dir)
        
        # 2. Сгенерировать ffmpeg команду
        ffmpeg_cmd = self._build_ffmpeg_command(
            slides=slides,
            audio=audio,
            timeline=manifest['timeline'],
            output=output_path
        )
        
        # 3. Запустить ffmpeg
        subprocess.run(ffmpeg_cmd, check=True)
        
        logger.info(f"✅ Built video: {output_path}")
        
        return output_path
    
    def _build_ffmpeg_command(self, slides, audio, timeline, output):
        """
        Build ffmpeg command for video creation
        
        Example:
        ffmpeg -loop 1 -t 29.376 -i slide_001.png \
               -loop 1 -t 25.123 -i slide_002.png \
               -i audio.wav \
               -filter_complex "[0:v][1:v]concat=n=2:v=1:a=0[v]" \
               -map "[v]" -map 2:a \
               -c:v libx264 -c:a aac \
               -pix_fmt yuv420p \
               output.mp4
        """
        
        cmd = ["ffmpeg"]
        
        # Input slides with durations
        for entry in timeline:
            if entry['action'] == 'slide_change':
                slide_id = entry['slide_id']
                duration = entry['t1'] - entry['t0']
                slide_path = slides[slide_id - 1]
                
                cmd.extend([
                    "-loop", "1",
                    "-t", str(duration),
                    "-i", str(slide_path)
                ])
        
        # Input audio
        cmd.extend(["-i", str(audio)])
        
        # Filter complex (concatenate slides)
        n_slides = len(timeline)
        filter_inputs = "".join(f"[{i}:v]" for i in range(n_slides))
        cmd.extend([
            "-filter_complex",
            f"{filter_inputs}concat=n={n_slides}:v=1:a=0[v]"
        ])
        
        # Map video and audio
        cmd.extend([
            "-map", "[v]",
            "-map", f"{n_slides}:a",  # Last input is audio
            "-c:v", "libx264",
            "-c:a", "aac",
            "-pix_fmt", "yuv420p",
            "-shortest",
            str(output)
        ])
        
        return cmd
```

---

## 📊 Сравнение: До vs После

### До:

```
main.py (150 строк):
├─ Upload file
├─ PPTX → PNG conversion  ← дублирование
├─ OCR extraction         ← дублирование
├─ Create manifest        ← дублирование
├─ Pipeline.ingest()      ← только валидация
└─ Start Celery task

Pipeline (465 строк):
├─ Stage 1: Ingest (только валидация - бесполезно)
├─ Stage 2-3: Plan
├─ Stage 4: TTS
└─ Stage 5-8: Build Manifest

❌ Нет сборки видео!
```

**Проблемы:**
- 🔴 Дублирование логики
- 🔴 Непонятно где что происходит
- 🔴 Нельзя запустить pipeline отдельно
- 🔴 Нет финального видео

### После:

```
main.py (30 строк):
├─ Upload file
├─ Save to disk
└─ Start Celery task → Pipeline делает ВСЁ!

Pipeline (550 строк):
├─ Stage 1: PPTX → PNG     ✅
├─ Stage 2: OCR            ✅
├─ Stage 3: Context        ✅
├─ Stage 4-5: Plan         ✅
├─ Stage 6: TTS            ✅
├─ Stage 7-8: Effects      ✅
└─ Stage 9: Build Video    ✅ НОВОЕ!
```

**Преимущества:**
- ✅ Вся логика в одном месте
- ✅ Легко тестировать (запустить pipeline на локальном PPTX)
- ✅ Легко дебажить (все этапы видны)
- ✅ Нет дублирования
- ✅ Полностью самодостаточный pipeline
- ✅ Готовое видео на выходе

---

## 🚀 План Реализации

### Шаг 1: Создать VideoBuilder
```bash
✅ backend/app/services/video_builder.py
```

### Шаг 2: Обновить Pipeline
```bash
✅ Добавить ingest() - PPTX → PNG
✅ Добавить extract_elements() - OCR
✅ Добавить build_video() - ffmpeg
✅ Обновить process_full_pipeline()
```

### Шаг 3: Упростить main.py
```bash
✅ Удалить ParserFactory
✅ Удалить parser.parse()
✅ Удалить pipeline.ingest() call
✅ Оставить только upload + celery task
```

### Шаг 4: Удалить дублирование
```bash
✅ Удалить backend/app/services/sprint1/
✅ Обновить импорты
```

### Шаг 5: Тестирование
```bash
✅ Тест: загрузка PPTX
✅ Тест: полный pipeline
✅ Тест: проверка видео
```

---

## 📝 Checklist

- [ ] Создать VideoBuilder service
- [ ] Переместить PPTX→PNG в pipeline.ingest()
- [ ] Переместить OCR в pipeline.extract_elements()
- [ ] Добавить pipeline.build_video()
- [ ] Упростить main.py (только upload)
- [ ] Удалить document_parser.py
- [ ] Обновить process_full_pipeline()
- [ ] Добавить логирование всех stages
- [ ] Тестирование на реальной презентации
- [ ] Обновить документацию

---

## 🎯 Итог

**Новая архитектура:**
- 🎯 **Простая** - вся логика в pipeline
- 🎯 **Логичная** - от PPTX до MP4 в одном месте
- 🎯 **Без дублирования** - каждая функция в одном месте
- 🎯 **Полная** - включает сборку видео
- 🎯 **Тестируемая** - можно запустить pipeline отдельно

**Хотите чтобы я начал реализацию?** 🚀
