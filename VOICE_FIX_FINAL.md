# Исправление голоса TTS - Финальное обновление

## Дата: 2 октября 2025

## Проблема
После первоначального изменения кода на мужской голос `ru-RU-Chirp3-HD-Puck`, в аудио все еще звучал женский голос. 

## Причина
Переменные окружения в `.env` файлах **переопределяли** дефолтные значения в коде и содержали старые настройки женских голосов.

## Решение
Обновлены **ВСЕ** конфигурационные файлы на мужской голос `ru-RU-Chirp3-HD-Puck`.

### Обновленные файлы:

#### Файлы кода (уже были обновлены ранее):
1. ✅ `backend/workers/tts_google_ssml.py` - дефолт в конструкторе
2. ✅ `backend/app/core/config.py` - дефолт в классе Settings

#### Файлы конфигурации (обновлены сейчас):
3. ✅ `backend/.env` - **было**: `ru-RU-Wavenet-A` (женский)
4. ✅ `backend/gcp_config.env` - **было**: `ru-RU-Neural2-B` (мужской старый)
5. ✅ `docker.env` (2 места):
   - TTS_VOICE - **было**: `ru-RU-SvetlanaNeural` (женский)
   - GOOGLE_TTS_VOICE - **было**: `ru-RU-Wavenet-A` (женский)
6. ✅ `backend_env_local.env` - **было**: `ru-RU-Wavenet-A` (женский)
7. ✅ `backend_env_openrouter.env` - **было**: `ru-RU-Neural2-B` (мужской старый)
8. ✅ `backend_env_ready.env` - **было**: `ru-RU-Wavenet-A` (женский)
9. ✅ `backend_env_docker.env` - **было**: `ru-RU-Standard-A` (женский)
10. ✅ `backend_env_vision_api.env` - **было**: `ru-RU-Wavenet-A` (женский)
11. ✅ `backend_env_enhanced_hybrid.env` - **было**: `ru-RU-Wavenet-B` (мужской старый)
12. ✅ `backend_env_final.env` - **было**: `ru-RU-Wavenet-A` (женский)

**Всего обновлено: 12 конфигурационных файлов**

### Теперь везде установлено:
```env
GOOGLE_TTS_VOICE=ru-RU-Chirp3-HD-Puck
TTS_VOICE=ru-RU-Chirp3-HD-Puck
```

## Проверка

### 1. Переменные окружения в контейнерах:
```bash
# Backend
docker exec slide-speaker-main-backend-1 env | grep GOOGLE_TTS_VOICE
# Вывод: GOOGLE_TTS_VOICE=ru-RU-Chirp3-HD-Puck ✅

# Celery
docker exec slide-speaker-main-celery-1 env | grep GOOGLE_TTS_VOICE
# Вывод: GOOGLE_TTS_VOICE=ru-RU-Chirp3-HD-Puck ✅
```

### 2. Контейнеры перезапущены:
```bash
docker-compose down && docker-compose up -d
```

Все сервисы успешно запущены с новыми настройками.

## Приоритет загрузки переменных окружения

Docker Compose загружает переменные в следующем порядке (последнее имеет приоритет):

1. Dockerfile ENV
2. docker-compose.yml environment
3. docker-compose.yml env_file (docker.env)
4. Монтированный .env файл (backend/.env)

**Вывод**: Монтированный `backend/.env` имеет наивысший приоритет, поэтому было критически важно обновить именно его.

## Почему было несколько env файлов?

Разные env файлы использовались для разных конфигураций:
- `backend_env_local.env` - локальная разработка
- `backend_env_docker.env` - Docker окружение
- `backend_env_openrouter.env` - конфигурация с OpenRouter
- `backend_env_vision_api.env` - конфигурация с Vision API
- И т.д.

Все они теперь обновлены для консистентности.

## Итоговый результат

✅ Мужской голос **ru-RU-Chirp3-HD-Puck** установлен во **всех** конфигурациях  
✅ Контейнеры перезапущены с новыми настройками  
✅ Визуальные эффекты синхронизированы с речью через SSML marks  
✅ Проект готов к созданию презентаций с мужским голосом

## Тестирование

Для проверки:
1. Создайте новую презентацию через веб-интерфейс
2. Загрузите PowerPoint файл
3. Дождитесь обработки
4. Проверьте аудио - должен звучать мужской голос
5. Проверьте визуальные эффекты - должны появляться синхронно с речью

## Примечания для будущего

⚠️ **ВАЖНО**: При изменении настроек голоса, нужно обновить:
1. Код (backend/workers/tts_google_ssml.py, backend/app/core/config.py)
2. Все .env файлы (особенно backend/.env и docker.env)
3. Перезапустить контейнеры: `docker-compose restart backend celery`

💡 **Рекомендация**: Рассмотреть возможность использования единого источника конфигурации вместо множества env файлов.
