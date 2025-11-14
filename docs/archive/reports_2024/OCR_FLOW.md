# 🔍 OCR и Vision API - Где и Когда Происходит

## 📍 TL;DR - Ответ на вопрос

**OCR с Vision API происходит ДО pipeline** - в `main.py` при загрузке PPTX файла.

```
Upload PPTX → main.py (OCR) → manifest.json → Pipeline (использует OCR результаты)
```

---

## 🔄 Полный Flow

### **1. Загрузка файла (main.py)**

**Endpoint:** `POST /upload`  
**Файл:** `backend/app/main.py:240-389`

```python
@app.post("/upload")
async def upload_file(file: UploadFile):
    # 1. Сохранить PPTX файл
    lesson_id = uuid.uuid4()
    lesson_dir = settings.DATA_DIR / lesson_id
    file_path = lesson_dir / file.filename
    
    # 2. Парсить документ
    parser = ParserFactory.create_parser(file_path)  # ← Создаёт PPTXParser
    manifest = await parser.parse()                   # ← Здесь происходит OCR!
    
    # 3. Сохранить manifest.json
    manifest_path = lesson_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest.dict(), f)
    
    # 4. Запустить Celery task для pipeline
    task = process_lesson_full_pipeline.delay(lesson_id, ...)
    
    return {"lesson_id": lesson_id, "status": "processing"}
```

---

### **2. Parser (document_parser.py)**

**Класс:** `PPTXParser`  
**Файл:** `backend/app/services/sprint1/document_parser.py`

```python
class PPTXParser(DocumentParser):
    async def parse(self) -> Manifest:
        # 1. Конвертировать PPTX → PNG изображения
        slides_png = self._convert_pptx_to_images()  # → 001.png, 002.png, ...
        
        # 2. Для каждого слайда извлечь элементы
        slides = []
        for i, slide_png in enumerate(slides_png):
            # 🔍 Здесь вызывается OCR!
            elements = build_slide_elements(slide_png)
            
            slide = Slide(
                id=i+1,
                image=f"/assets/.../slides/{i+1:03d}.png",
                elements=elements,  # ← OCR результаты
                cues=[]
            )
            slides.append(slide)
        
        return Manifest(slides=slides)
```

---

### **3. OCR Extraction (build_slide_elements)**

**Функция:** `build_slide_elements()`  
**Файл:** `backend/app/services/sprint1/document_parser.py:71-88`

```python
def build_slide_elements(slide_png: Path) -> List[Dict]:
    """Build slide elements with fallback guarantees"""
    elements = []
    
    # 1. Try vector layer extraction first (TODO)
    elements += _extract_from_vector_layers(slide_png)
    
    # 2. If no elements and OCR is enabled, try OCR
    if not elements and _ocr_enabled():
        try:
            # 🔍 ЗДЕСЬ ВЫЗЫВАЕТСЯ OCR!
            elements += _extract_with_ocr(slide_png)
        except Exception as e:
            logger.warning("OCR failed")
    
    # 3. Guarantee at least one element (fallback)
    if not elements:
        elements = [_placeholder_element()]
    
    return elements
```

---

### **4. OCR Provider (Vision API)**

**Функция:** `_extract_with_ocr()`  
**Файл:** `backend/app/services/sprint1/document_parser.py:48-62`

```python
def _extract_with_ocr(slide_png: Path) -> List[Dict]:
    """Extract elements using configured OCR provider"""
    from ...services.provider_factory import extract_elements_from_pages
    
    # 🔍 Вызывает OCR provider через ProviderFactory
    elements_data = extract_elements_from_pages([str(slide_png)])
    
    if elements_data and elements_data[0]:
        logger.info(f"OCR extracted {len(elements_data[0])} elements")
        return elements_data[0]
    else:
        logger.warning("OCR returned no elements")
        return []
```

---

### **5. Provider Factory**

**Функция:** `extract_elements_from_pages()`  
**Файл:** `backend/app/services/provider_factory.py:368-371`

```python
def extract_elements_from_pages(png_paths: List[str]) -> List[List[Dict]]:
    """Extract elements from pages using configured OCR provider"""
    provider = ProviderFactory.get_ocr_provider()  # ← Определяет какой OCR использовать
    return provider.extract_elements_from_pages(png_paths)
```

**Метод:** `get_ocr_provider()`  
**Файл:** `backend/app/services/provider_factory.py:60-95`

```python
@staticmethod
def get_ocr_provider():
    """Get OCR provider based on OCR_PROVIDER setting"""
    provider = settings.OCR_PROVIDER.lower()
    
    if provider == "vision":
        # 🎯 Google Cloud Vision API
        from workers.ocr_vision import GoogleVisionOCRWorker
        return GoogleVisionOCRWorker()
    
    elif provider == "enhanced_vision":
        # 🎯 Enhanced Vision API (с object detection)
        from workers.ocr_vision_enhanced import EnhancedVisionOCRWorker
        return EnhancedVisionOCRWorker()
    
    elif provider == "google":
        # Document AI
        from workers.ocr_google import GoogleOCRWorker
        return GoogleOCRWorker()
    
    elif provider == "easyocr":
        # Local EasyOCR
        return ProviderFactory._get_easyocr_provider()
    
    else:
        # Fallback
        return ProviderFactory._get_fallback_ocr()
```

---

### **6. Vision API Worker**

**Класс:** `GoogleVisionOCRWorker`  
**Файл:** `backend/workers/ocr_vision.py:50-200`

```python
class GoogleVisionOCRWorker:
    def __init__(self):
        # Инициализация Google Cloud Vision API client
        self.client = vision.ImageAnnotatorClient()
        self.ocr_cache = get_ocr_cache()  # Redis cache
    
    def extract_elements_from_pages(self, image_paths: List[str]) -> List[List[Dict]]:
        """Извлекает элементы из изображений слайдов используя Vision API"""
        
        all_results = []
        
        for image_path in image_paths:
            # 1. Проверить кэш
            image_hash = self._get_image_hash(image_path)
            cached_result = self.ocr_cache.get(image_hash)
            
            if cached_result:
                logger.info(f"✅ OCR cache HIT for {image_path}")
                all_results.append(cached_result)
                continue
            
            logger.info(f"🔍 OCR cache MISS, calling Vision API for {image_path}")
            
            # 2. Загрузить изображение
            with open(image_path, 'rb') as f:
                image_content = f.read()
            
            image = vision.Image(content=image_content)
            
            # 3. 🎯 Вызвать Google Cloud Vision API для TEXT_DETECTION
            response = self.client.text_detection(image=image)
            
            # 4. Обработать результаты
            elements = self._process_vision_response(response)
            
            # 5. Сохранить в кэш
            self.ocr_cache.set(image_hash, elements, ttl=604800)  # 7 days
            
            all_results.append(elements)
        
        return all_results
    
    def _process_vision_response(self, response) -> List[Dict]:
        """Преобразует Vision API response в элементы"""
        elements = []
        
        if response.text_annotations:
            # Первая аннотация - весь текст (пропускаем)
            # Остальные - отдельные слова/блоки
            
            for i, annotation in enumerate(response.text_annotations[1:]):
                # Получить bbox
                vertices = annotation.bounding_poly.vertices
                x_coords = [v.x for v in vertices]
                y_coords = [v.y for v in vertices]
                
                x = min(x_coords)
                y = min(y_coords)
                width = max(x_coords) - x
                height = max(y_coords) - y
                
                element = {
                    "id": f"slide_1_block_{i}",
                    "type": "paragraph",  # или heading, определяется эвристикой
                    "text": annotation.description,
                    "bbox": [x, y, width, height],
                    "confidence": 0.9,  # Vision API не возвращает confidence
                    "source": "vision_api"
                }
                
                elements.append(element)
        
        return elements
```

---

## 🎯 Google Cloud Vision API - Детали

### **API Call:**

```python
# Request
client.text_detection(image=vision.Image(content=image_bytes))

# Response
TextAnnotation {
  text_annotations: [
    {
      description: "Das Blatt",
      bounding_poly: {
        vertices: [{x: 588, y: 97}, {x: 853, y: 97}, ...]
      }
    },
    {
      description: "Anatomische",
      bounding_poly: {
        vertices: [{x: 72, y: 346}, ...]
      }
    },
    ...
  ]
}
```

### **Что Vision API возвращает:**

1. **text_annotations[0]** - весь текст на изображении (игнорируется)
2. **text_annotations[1..N]** - отдельные слова/блоки с:
   - `description` - текст
   - `bounding_poly` - координаты прямоугольника
   - Нет `confidence` (всегда считается высоким)

### **Обработка:**

```python
# Преобразуем в формат элемента:
{
  "id": "slide_1_block_0",
  "type": "paragraph",  # Определяется по размеру шрифта
  "text": "Das Blatt",
  "bbox": [588, 97, 265, 47],  # [x, y, width, height]
  "confidence": 0.9,
  "source": "vision_api"
}
```

---

## 📊 OCR Providers - Сравнение

| Provider | API | Speed | Quality | Cost |
|----------|-----|-------|---------|------|
| **vision** | Google Cloud Vision API | ⚡ Fast (0.5-1s/slide) | ⭐⭐⭐⭐⭐ | 💰 $1.50/1000 images |
| **enhanced_vision** | Vision API + Object Detection | 🐌 Slower (1-2s/slide) | ⭐⭐⭐⭐⭐ | 💰💰 $3.00/1000 images |
| **google** | Document AI | ⚡ Fast (0.5-1s/slide) | ⭐⭐⭐⭐⭐ | 💰💰 $2.50/1000 pages |
| **easyocr** | Local (CPU/GPU) | 🐌 Slow (3-5s/slide) | ⭐⭐⭐ | 💵 Free |
| **fallback** | Placeholder | ⚡⚡ Instant | ⭐ | 💵 Free |

**Текущий:** `OCR_PROVIDER=vision` (из docker.env)

---

## 🔄 OCR Caching (Redis)

**Зачем:** Избежать повторных API calls для одних и тех же слайдов

**Как работает:**

```python
# 1. Вычислить хэш изображения
image_hash = hashlib.md5(image_bytes).hexdigest()
# → "a1b2c3d4e5f6..."

# 2. Проверить кэш
cached_result = redis.get(f"ocr:{image_hash}")

if cached_result:
    return cached_result  # ✅ Cache HIT - экономия $0.0015 и 0.5 сек
else:
    # ❌ Cache MISS - вызываем Vision API
    result = vision_api.text_detection(image)
    redis.set(f"ocr:{image_hash}", result, ex=604800)  # 7 days TTL
    return result
```

**Экономия:**
- Повторная обработка: 0.01s вместо 0.5s (50x быстрее)
- Стоимость: $0 вместо $0.0015 на слайд

---

## 🎯 Итоговый Timeline

```
t=0.0s   → Upload PPTX файл
t=0.1s   → Сохранить в lesson_dir/
t=0.2s   → Конвертировать PPTX → PNG (PyMuPDF)
           - 001.png
           - 002.png
           - 003.png

t=0.5s   → OCR для 001.png
           ├─ Проверить Redis cache (MISS)
           ├─ 🎯 Google Vision API call
           └─ Сохранить в cache
           → elements = [{id, type, text, bbox}, ...]

t=1.0s   → OCR для 002.png
           └─ Cache MISS → Vision API

t=1.5s   → OCR для 003.png
           └─ Cache MISS → Vision API

t=2.0s   → Построить manifest.json:
           {
             "slides": [
               {
                 "id": 1,
                 "image": "/assets/.../001.png",
                 "elements": [...],  ← OCR результаты
                 "cues": []
               }
             ]
           }

t=2.1s   → Сохранить manifest.json
t=2.2s   → Запустить Celery task (process_full_pipeline)

========== Pipeline начинается ПОСЛЕ OCR ===========

t=2.3s   → Pipeline.ingest() - валидация manifest
t=2.4s   → Pipeline.plan() - использует elements из OCR
           ├─ Stage 0: Presentation Context
           ├─ Stage 2: Semantic Analysis (использует OCR elements!)
           └─ Stage 3: Script Generation

t=15s    → Pipeline.tts() - генерация аудио
t=25s    → Pipeline.build_manifest() - visual effects
t=25.5s  → ✅ Готово!
```

---

## 📁 Где Хранятся Результаты OCR

```
.data/{lesson_id}/
├── slides/
│   ├── 001.png              ← Изображение слайда
│   ├── 002.png
│   └── ...
└── manifest.json            ← OCR результаты здесь!
    {
      "slides": [
        {
          "id": 1,
          "image": "/assets/.../001.png",
          "elements": [          ← 🎯 OCR элементы
            {
              "id": "slide_1_block_0",
              "type": "heading",
              "text": "Das Blatt",
              "bbox": [588, 97, 265, 47],
              "confidence": 0.9,
              "source": "vision_api"
            }
          ]
        }
      ]
    }
```

---

## 🔧 Environment Variables

```bash
# docker.env

# OCR Provider
OCR_PROVIDER=vision              # vision | enhanced_vision | google | easyocr

# Google Cloud Vision API
GOOGLE_APPLICATION_CREDENTIALS=/app/keys/inspiring-keel-473421-j2-22cc51dfb336.json

# OCR Cache (Redis)
OCR_CACHE_TTL=604800            # 7 days
REDIS_HOST=redis
REDIS_PORT=6379
```

---

## 🎓 Ключевые Моменты

1. **OCR происходит ДО pipeline** - в `main.py` при загрузке
2. **Vision API используется** - через `GoogleVisionOCRWorker`
3. **Результаты кэшируются** - в Redis на 7 дней
4. **Pipeline использует готовые элементы** - из manifest.json
5. **Нет повторного OCR в pipeline** - всё уже извлечено

---

## 🤔 Почему OCR ДО Pipeline?

**Преимущества:**
- ✅ Manifest.json сразу полный (можно показать превью)
- ✅ Кэширование работает независимо от pipeline
- ✅ Можно повторно запустить pipeline без повторного OCR
- ✅ Fail-fast: если OCR не сработал, узнаём сразу

**Альтернатива (OCR внутри pipeline):**
- ❌ Медленнее: каждый запуск pipeline = новый OCR
- ❌ Нет превью до завершения pipeline
- ❌ Сложнее кэшировать

---

**Автор:** Droid AI Assistant  
**Дата:** 2025-01-06 02:00
