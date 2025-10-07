# 🧪 Тестирование новой синхронизации

## Проблема
Старые манифесты (созданы ДО изменений) не содержат group_id в talk_track.

**Проверка старого манифеста:**
```bash
# Все манифесты созданы 7 октября
ls -lt .data/*/manifest.json
-rw-r--r--  1 iliazarikov  staff   46489 Oct  7 10:31  # ← СТАРЫЙ!
```

## Решение: Загрузить НОВУЮ презентацию

### Вариант 1: Через веб-интерфейс (РЕКОМЕНДУЕТСЯ)

1. Откройте http://localhost:3000
2. Нажмите "Upload Presentation"
3. Выберите любую презентацию
4. Дождитесь обработки
5. Запустите проверку:

```bash
# Найти свежий манифест
LATEST=$(find .data -name "manifest.json" -type f -mmin -5 | head -1)
echo "Latest manifest: $LATEST"

# Проверить group_id в talk_track
python3 << 'EOF'
import json, sys
from pathlib import Path

latest = Path("$LATEST")
if not latest.exists():
    print("❌ No fresh manifest found! Upload new presentation first.")
    sys.exit(1)

with open(latest) as f:
    m = json.load(f)

print("\n=== ✅ CHECKING NEW MANIFEST ===\n")

# Check talk_track
if 'slides' in m and len(m['slides']) > 0:
    talk_track = m['slides'][0].get('talk_track', [])
    
    print("📝 Talk Track:")
    has_group_id = False
    for seg in talk_track[:3]:
        gid = seg.get('group_id')
        print(f"  - {seg.get('segment')}: group_id={gid}")
        if gid:
            has_group_id = True
    
    if has_group_id:
        print("\n✅ talk_track contains group_id!")
    else:
        print("\n❌ talk_track does NOT contain group_id")
        print("   This might be mock mode or LLM error")
    
    # Check SSML
    ssml = m['slides'][0].get('speaker_notes_ssml', '')
    if 'group_' in ssml:
        print("✅ SSML contains group markers")
    else:
        print("❌ SSML does NOT contain group markers")
    
    # Check TTS
    tts = m['slides'][0].get('tts_words', {})
    if tts.get('word_timings'):
        markers = [w for w in tts['word_timings'] if w.get('mark_name', '').startswith('group_')]
        print(f"✅ TTS has {len(markers)} group markers")
    else:
        print("⚠️  TTS word_timings not found")
EOF
```

### Вариант 2: Регенерация существующей презентации

**⚠️ Внимание:** Это перезапишет существующий манифест!

```bash
# Найти презентацию
UUID="4e809954-deb6-46ad-8a7a-9d969ddabdaf"  # Ваш UUID

# Удалить старые стадии (оставить только PNG)
cd .data/$UUID
rm -f manifest.json
rm -rf audio/

# Запустить регенерацию через API
curl -X POST "http://localhost:8000/api/v2/lecture/$UUID/regenerate" \
  -H "Content-Type: application/json"

# Подождать 30-60 секунд
sleep 60

# Проверить новый манифест
python3 << EOF
import json
with open('.data/$UUID/manifest.json') as f:
    m = json.load(f)

talk_track = m['slides'][0].get('talk_track', [])
print("Talk track segments:")
for seg in talk_track[:3]:
    print(f"  {seg.get('segment')}: group_id={seg.get('group_id', 'MISSING')}")
EOF
```

## Что проверять

После загрузки НОВОЙ презентации:

### 1. Talk Track содержит group_id
```json
{
  "segment": "hook",
  "text": "Давайте рассмотрим...",
  "group_id": "group_title"  ← ДОЛЖЕН БЫТЬ!
}
```

### 2. SSML содержит метки группы
```xml
<speak>
  <mark name="group_title"/>  ← ДОЛЖНА БЫТЬ!
  <prosody rate="1.0">
    <mark name="w0"/>Рассмотрим...
  </prosody>
</speak>
```

### 3. TTS timings содержат group метки
```json
{
  "mark_name": "group_title",  ← ДОЛЖНА БЫТЬ!
  "time_seconds": 0.5
}
```

### 4. Визуальная синхронизация
- Откройте презентацию в Player
- Нажмите Play
- **Проверьте:** Когда диктор говорит о заголовке → заголовок подсвечивается СРАЗУ
- **Разница должна быть < 0.5 секунды**

## Логи для отладки

```bash
# Проверить что group метки создаются
docker-compose logs -f backend | grep -E "(group_|Added group|Found group)"

# Должны быть строки:
# Added group marker: group_title
# ✅ Found group marker 'group_title' at 0.50s
# ✅ Group 'group_title' synced to TTS: 0.50s - 3.00s
```

## Если group_id все равно MISSING

Это означает что используется **mock mode**. Проверьте:

```bash
# Проверить LLM provider
docker-compose logs backend | grep "SmartScriptGenerator"

# Должно быть:
# ✅ SmartScriptGenerator: Using gemini provider

# Если видите:
# ⚠️  using mock mode
# Значит LLM provider не настроен
```

### Как исправить mock mode:

1. Проверьте что API key настроен:
```bash
docker-compose exec backend env | grep GOOGLE_API_KEY
# Должен быть ваш ключ
```

2. Если ключа нет - добавьте в docker.env:
```bash
echo "GOOGLE_API_KEY=your-key-here" >> docker.env
docker-compose up -d backend
```

3. Mock mode ТОЖЕ должен работать! Проверьте логи:
```bash
docker-compose logs backend | grep "Using mock"
```

---

## Итог

✅ **Загрузите НОВУЮ презентацию**  
✅ **Проверьте что talk_track содержит group_id**  
✅ **Протестируйте синхронизацию визуально**

Старые манифесты НЕ БУДУТ работать с новой синхронизацией!
