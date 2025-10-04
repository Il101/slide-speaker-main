# Классификация файлов проекта Slide Speaker

## 📊 Легенда категорий:
- **🟢 PROD** - Используется в продакшене
- **🟡 DEV** - Используется в разработке (тесты, документация)
- **🟠 ALT** - Альтернативные файлы (бэкапы, разные версии)
- **🔴 OBSOLETE** - Устаревшие/неиспользуемые файлы
- **🗑️ TRASH** - Мусор (можно удалять)

---

## 🎯 CORE PRODUCTION FILES (🟢 PROD)

### Backend Core
| Файл | Категория | Описание |
|------|-----------|----------|
| `backend/app/main.py` | 🟢 PROD | Главное приложение FastAPI, точка входа API |
| `backend/app/tasks.py` | 🟢 PROD | Celery задачи для асинхронной обработки |
| `backend/app/celery_app.py` | 🟢 PROD | Конфигурация Celery |
| `backend/requirements.txt` | 🟢 PROD | Python зависимости |
| `backend/Dockerfile` | 🟢 PROD | Docker образ для backend |
| `backend/alembic.ini` | 🟢 PROD | Конфигурация миграций БД |
| `backend/alembic/` | 🟢 PROD | Миграции базы данных |

### Backend Core Modules
| Файл | Категория | Описание |
|------|-----------|----------|
| `backend/app/core/config.py` | 🟢 PROD | Конфигурация приложения |
| `backend/app/core/auth.py` | 🟢 PROD | Аутентификация и авторизация |
| `backend/app/core/database.py` | 🟢 PROD | Работа с БД (SQLAlchemy) |
| `backend/app/core/logging.py` | 🟢 PROD | Система логирования |
| `backend/app/core/exceptions.py` | 🟢 PROD | Обработка исключений |
| `backend/app/core/locks.py` | 🟢 PROD | Redis locks для синхронизации |
| `backend/app/core/prometheus_metrics.py` | 🟢 PROD | Метрики мониторинга |
| `backend/app/core/secrets.py` | 🟢 PROD | Управление секретами |
| `backend/app/core/csrf.py` | 🟢 PROD | CSRF защита |

### Backend Services
| Файл | Категория | Описание |
|------|-----------|----------|
| `backend/app/services/provider_factory.py` | 🟢 PROD | Фабрика провайдеров (GCP, OpenRouter) |
| `backend/app/services/sprint1/` | 🟢 PROD | Сервисы Sprint 1 (базовый функционал) |
| `backend/app/services/sprint2/` | 🟢 PROD | Сервисы Sprint 2 (расширенный функционал) |
| `backend/app/services/sprint3/` | 🟢 PROD | Сервисы Sprint 3 (экспорт и видео) |

### Backend Models
| Файл | Категория | Описание |
|------|-----------|----------|
| `backend/app/models/` | 🟢 PROD | SQLAlchemy модели данных |

### Frontend Core
| Файл | Категория | Описание |
|------|-----------|----------|
| `src/main.tsx` | 🟢 PROD | Точка входа React приложения |
| `src/App.tsx` | 🟢 PROD | Главный компонент приложения |
| `src/index.css` | 🟢 PROD | Глобальные стили |
| `package.json` | 🟢 PROD | Node.js зависимости |
| `vite.config.ts` | 🟢 PROD | Конфигурация Vite |
| `tsconfig.json` | 🟢 PROD | Конфигурация TypeScript |
| `tailwind.config.ts` | 🟢 PROD | Конфигурация Tailwind CSS |
| `postcss.config.js` | 🟢 PROD | Конфигурация PostCSS |
| `Dockerfile` | 🟢 PROD | Docker образ для frontend |

### Frontend Pages
| Файл | Категория | Описание |
|------|-----------|----------|
| `src/pages/Index.tsx` | 🟢 PROD | Главная страница |
| `src/pages/Login.tsx` | 🟢 PROD | Страница входа |
| `src/pages/NotFound.tsx` | 🟢 PROD | Страница 404 |

### Frontend Components
| Файл | Категория | Описание |
|------|-----------|----------|
| `src/components/Navigation.tsx` | 🟢 PROD | Навигация |
| `src/components/FileUploader.tsx` | 🟢 PROD | Загрузка файлов |
| `src/components/Player.tsx` | 🟢 PROD | Аудио/видео плеер |
| `src/components/CueEditor.tsx` | 🟢 PROD | Редактор визуальных подсказок |
| `src/components/ElementEditor.tsx` | 🟢 PROD | Редактор элементов |
| `src/components/ProtectedRoute.tsx` | 🟢 PROD | Защищенные маршруты |
| `src/components/VirtualizedList.tsx` | 🟢 PROD | Виртуализированный список |
| `src/components/VirtualizedSlideList.tsx` | 🟢 PROD | Список слайдов |
| `src/components/ui/` | 🟢 PROD | UI компоненты (shadcn/ui) |

### Frontend Utils
| Файл | Категория | Описание |
|------|-----------|----------|
| `src/lib/` | 🟢 PROD | Утилиты и хелперы |
| `src/hooks/` | 🟢 PROD | React хуки |
| `src/contexts/` | 🟢 PROD | React контексты |
| `src/types/` | 🟢 PROD | TypeScript типы |

### Infrastructure
| Файл | Категория | Описание |
|------|-----------|----------|
| `docker-compose.yml` | 🟢 PROD | Оркестрация Docker контейнеров |
| `.env.example` | 🟢 PROD | Пример переменных окружения |
| `.gitignore` | 🟢 PROD | Игнорирование файлов в Git |
| `README.md` | 🟢 PROD | Основная документация проекта |
| `start.sh` | 🟢 PROD | Скрипт запуска |
| `stop.sh` | 🟢 PROD | Скрипт остановки |

### Configuration
| Файл | Категория | Описание |
|------|-----------|----------|
| `components.json` | 🟢 PROD | Конфигурация shadcn/ui |
| `eslint.config.js` | 🟢 PROD | Конфигурация ESLint |
| `tsconfig.app.json` | 🟢 PROD | TypeScript для приложения |
| `tsconfig.node.json` | 🟢 PROD | TypeScript для Node.js |

### Google Cloud Integration
| Файл | Категория | Описание |
|------|-----------|----------|
| `inspiring-keel-473421-j2-22cc51dfb336.json` | 🟢 PROD | GCP Service Account ключ |
| `keys/` | 🟢 PROD | Директория с ключами |
| `backend/app/storage_gcs.py` | 🟢 PROD | Google Cloud Storage интеграция |

---

## 🛠️ DEVELOPMENT FILES (🟡 DEV)

### Testing
| Файл | Категория | Описание |
|------|-----------|----------|
| `tests/` | 🟡 DEV | Frontend тесты |
| `src/test/` | 🟡 DEV | Frontend unit тесты |
| `backend/app/tests/` | 🟡 DEV | Backend тесты |
| `backend/requirements-test.txt` | 🟡 DEV | Зависимости для тестирования |
| `playwright.config.ts` | 🟡 DEV | Конфигурация Playwright |
| `.playwright-mcp/` | 🟡 DEV | Playwright данные |

### Test Scripts - Smoke Tests
| Файл | Категория | Описание |
|------|-----------|----------|
| `simple_smoke_test.py` | 🟡 DEV | Простой smoke test |
| `smoke_test.py` | 🟡 DEV | Smoke test основного функционала |
| `simple_test.py` | 🟡 DEV | Базовый тест |
| `simple_google_test.py` | 🟡 DEV | Тест Google интеграции |

### Test Scripts - API Tests
| Файл | Категория | Описание |
|------|-----------|----------|
| `test_api.py` | 🟡 DEV | Тест API endpoints |
| `final_test.py` | 🟡 DEV | Финальный тест |
| `final_integration_test.py` | 🟡 DEV | Интеграционный тест |
| `upload_and_test.py` | 🟡 DEV | Тест загрузки файлов |

### Test Scripts - Pipeline Tests
| Файл | Категория | Описание |
|------|-----------|----------|
| `test_pipeline.py` | 🟡 DEV | Тест pipeline обработки |
| `test_full_pipeline.py` | 🟡 DEV | Полный pipeline тест |
| `test_hybrid_pipeline.py` | 🟡 DEV | Тест гибридного pipeline |
| `test_hybrid_fix.py` | 🟡 DEV | Тест исправлений hybrid pipeline |

### Test Scripts - Google Cloud Tests
| Файл | Категория | Описание |
|------|-----------|----------|
| `test_google_cloud_integration.py` | 🟡 DEV | Тест интеграции с GCP |
| `test_google_cloud_simple.py` | 🟡 DEV | Простой тест GCP |
| `test_gcp_integration.py` | 🟡 DEV | Тест GCP сервисов |
| `test_google_detailed.py` | 🟡 DEV | Детальный тест Google |
| `diagnose_gcp.py` | 🟡 DEV | Диагностика GCP |
| `enable_gcp_apis.py` | 🟡 DEV | Включение GCP API |

### Test Scripts - Gemini Tests
| Файл | Категория | Описание |
|------|-----------|----------|
| `test_gemini_models.py` | 🟡 DEV | Тест Gemini моделей |
| `test_gemini_google_ai.py` | 🟡 DEV | Тест Gemini через Google AI |
| `check_gemini_models.py` | 🟡 DEV | Проверка доступных Gemini моделей |
| `check_gemini_ai_studio.py` | 🟡 DEV | Проверка Gemini AI Studio |
| `check_gemini_europe.py` | 🟡 DEV | Проверка Gemini в Европе |
| `get_gemini_key.py` | 🟡 DEV | Получение Gemini API ключа |

### Test Scripts - TTS/Voice Tests
| Файл | Категория | Описание |
|------|-----------|----------|
| `test_tts_generation.py` | 🟡 DEV | Тест генерации TTS |
| `test_tts_detailed.py` | 🟡 DEV | Детальный тест TTS |
| `test_google_voices.py` | 🟡 DEV | Тест Google голосов |
| `test_russian_voices.py` | 🟡 DEV | Тест русских голосов |
| `test_current_voice.py` | 🟡 DEV | Тест текущего голоса |
| `test_voice_variations.py` | 🟡 DEV | Тест вариаций голоса |
| `test_different_voices.py` | 🟡 DEV | Тест разных голосов |
| `test_single_voice.py` | 🟡 DEV | Тест одного голоса |
| `test_wavenet_settings.py` | 🟡 DEV | Тест настроек WaveNet |
| `test_improved_voice.py` | 🟡 DEV | Тест улучшенного голоса |
| `test_improved_accent.py` | 🟡 DEV | Тест улучшенного акцента |
| `test_pitch_values.py` | 🟡 DEV | Тест значений pitch |
| `check_chirp_voices.py` | 🟡 DEV | Проверка Chirp голосов |
| `generate_audio_direct.py` | 🟡 DEV | Прямая генерация аудио |

### Test Scripts - SSML Tests
| Файл | Категория | Описание |
|------|-----------|----------|
| `test_ssml_integration.py` | 🟡 DEV | Тест SSML интеграции |
| `test_ssml_voice.py` | 🟡 DEV | Тест SSML голосов |
| `test_ssml_tts_debug.py` | 🟡 DEV | Отладка SSML TTS |

### Test Scripts - Vision/OCR Tests
| Файл | Категория | Описание |
|------|-----------|----------|
| `test_vision_api.py` | 🟡 DEV | Тест Vision API |
| `test_vision_coordinates.py` | 🟡 DEV | Тест координат Vision |
| `test_enhanced_vision.py` | 🟡 DEV | Тест улучшенного Vision |
| `test_kurs10_vision.py` | 🟡 DEV | Тест Vision на курсе 10 |
| `test_extract_elements.py` | 🟡 DEV | Тест извлечения элементов |

### Test Scripts - Visual Cues/Effects Tests
| Файл | Категория | Описание |
|------|-----------|----------|
| `test_visual_cues.py` | 🟡 DEV | Тест визуальных подсказок |
| `test_visual_cues_fix.py` | 🟡 DEV | Тест исправлений визуальных подсказок |
| `regenerate_visual_cues.py` | 🟡 DEV | Регенерация визуальных подсказок |

### Test Scripts - Lesson Tests
| Файл | Категория | Описание |
|------|-----------|----------|
| `test_existing_lesson.py` | 🟡 DEV | Тест существующего урока |
| `test_llm_generation.py` | 🟡 DEV | Тест LLM генерации |
| `test_language_support.py` | 🟡 DEV | Тест поддержки языков |
| `test_sprint2.py` | 🟡 DEV | Тест Sprint 2 функционала |

### Test Scripts - Export Tests
| Файл | Категория | Описание |
|------|-----------|----------|
| `test_export.py` | 🟡 DEV | Тест экспорта |

### Test Scripts - OpenRouter Tests
| Файл | Категория | Описание |
|------|-----------|----------|
| `test_openrouter.py` | 🟡 DEV | Тест OpenRouter API |
| `check_openrouter_models.py` | 🟡 DEV | Проверка OpenRouter моделей |

### Test Scripts - Other Tests
| Файл | Категория | Описание |
|------|-----------|----------|
| `check_regions.py` | 🟡 DEV | Проверка регионов GCP |
| `check_doc_ai_europe.py` | 🟡 DEV | Проверка Document AI в Европе |

### Utility Scripts
| Файл | Категория | Описание |
|------|-----------|----------|
| `backend/create_initial_users.py` | 🟡 DEV | Создание начальных пользователей |
| `backend/init_db.sh` | 🟡 DEV | Инициализация БД |
| `backend/init_alembic.sh` | 🟡 DEV | Инициализация Alembic |
| `init_minio.py` | 🟡 DEV | Инициализация MinIO |
| `clear_lesson_lock.py` | 🟡 DEV | Очистка блокировок уроков |
| `diagnose_redis_locks.py` | 🟡 DEV | Диагностика Redis locks |
| `fix_permissions.py` | 🟡 DEV | Исправление прав доступа |

### Processor Management Scripts
| Файл | Категория | Описание |
|------|-----------|----------|
| `create_processor.py` | 🟡 DEV | Создание процессора Document AI |
| `create_processor_europe.py` | 🟡 DEV | Создание процессора в Европе |
| `create_processor_fixed.py` | 🟡 DEV | Создание исправленного процессора |
| `find_processor.py` | 🟡 DEV | Поиск процессора |
| `find_all_processors.py` | 🟡 DEV | Поиск всех процессоров |
| `find_existing_processor.py` | 🟡 DEV | Поиск существующего процессора |
| `find_slide_speaker_processor.py` | 🟡 DEV | Поиск процессора Slide Speaker |

### Audio Regeneration Scripts
| Файл | Категория | Описание |
|------|-----------|----------|
| `regenerate_audio.py` | 🟡 DEV | Регенерация аудио |
| `regenerate_slide2_audio.py` | 🟡 DEV | Регенерация аудио слайда 2 |

### GitHub Integration
| Файл | Категория | Описание |
|------|-----------|----------|
| `create_github_issues.py` | 🟡 DEV | Создание GitHub issues |
| `github_issues.json` | 🟡 DEV | Данные GitHub issues |
| `issues.md` | 🟡 DEV | Список issues |

### Documentation - Project Docs
| Файл | Категория | Описание |
|------|-----------|----------|
| `DEPLOYMENT_GUIDE.md` | 🟡 DEV | Руководство по деплою |
| `DOCKER_README.md` | 🟡 DEV | Docker документация |
| `AUTH_INSTRUCTIONS.md` | 🟡 DEV | Инструкции по аутентификации |
| `SPRINT1_README.md` | 🟡 DEV | Документация Sprint 1 |
| `SPRINT2_README.md` | 🟡 DEV | Документация Sprint 2 |
| `SPRINT3_README.md` | 🟡 DEV | Документация Sprint 3 |
| `SPRINT3_SUMMARY.md` | 🟡 DEV | Итоги Sprint 3 |

### Documentation - Testing Guides
| Файл | Категория | Описание |
|------|-----------|----------|
| `FRONTEND_TESTING_GUIDE.md` | 🟡 DEV | Руководство по тестированию frontend |

### Monitoring
| Файл | Категория | Описание |
|------|-----------|----------|
| `monitoring/` | 🟡 DEV | Мониторинг и метрики |

### GitHub Actions
| Файл | Категория | Описание |
|------|-----------|----------|
| `.github/` | 🟡 DEV | GitHub Actions CI/CD |

### IDE Configuration
| Файл | Категория | Описание |
|------|-----------|----------|
| `.vscode/` | 🟡 DEV | VS Code настройки |
| `backend/.vscode/` | 🟡 DEV | VS Code настройки для backend |

### Templates
| Файл | Категория | Описание |
|------|-----------|----------|
| `gcp_env_template.txt` | 🟡 DEV | Шаблон GCP переменных |

---

## 📋 DOCUMENTATION & REPORTS (🟡 DEV)

### Status Reports
| Файл | Категория | Описание |
|------|-----------|----------|
| `REPORT.md` | 🟡 DEV | Общий отчет |
| `CURRENT_CONFIGURATION_REPORT.md` | 🟡 DEV | Текущая конфигурация |
| `INTEGRATION_SUMMARY.md` | 🟡 DEV | Итоги интеграции |
| `SECURITY_STATUS.md` | 🟡 DEV | Статус безопасности |
| `GOOGLE_CLOUD_INTEGRATION_STATUS.md` | 🟡 DEV | Статус GCP интеграции |

### Feature Reports
| Файл | Категория | Описание |
|------|-----------|----------|
| `GOOGLE_CLOUD_INTEGRATION_REPORT.md` | 🟡 DEV | Отчет по GCP интеграции |
| `GOOGLE_TTS_VOICES_REPORT.md` | 🟡 DEV | Отчет по Google TTS голосам |
| `CHIRP_V3_HD_REPORT.md` | 🟡 DEV | Отчет по Chirp v3 HD |
| `VISION_API_REPORT.md` | 🟡 DEV | Отчет по Vision API |
| `OCR_COMPARISON_REPORT.md` | 🟡 DEV | Сравнение OCR |
| `LANGUAGE_SUPPORT_REPORT.md` | 🟡 DEV | Отчет по поддержке языков |
| `OPENROUTER_INTEGRATION_COMPLETE.md` | 🟡 DEV | Завершение интеграции OpenRouter |

### Pipeline Reports
| Файл | Категория | Описание |
|------|-----------|----------|
| `ENHANCED_HYBRID_PIPELINE_REPORT.md` | 🟡 DEV | Улучшенный гибридный pipeline |
| `FINAL_ENHANCED_HYBRID_PIPELINE_REPORT.md` | 🟡 DEV | Финальный отчет по hybrid pipeline |
| `HYBRID_PIPELINE_AUDIT_REPORT.md` | 🟡 DEV | Аудит hybrid pipeline |
| `HYBRID_PIPELINE_DEFAULT_SETUP.md` | 🟡 DEV | Настройка hybrid pipeline по умолчанию |
| `HYBRID_PIPELINE_FINAL_REPORT.md` | 🟡 DEV | Финальный отчет pipeline |
| `PIPELINE_TESTING_REPORT.md` | 🟡 DEV | Отчет по тестированию pipeline |
| `PIPELINE_TESTING_REPORT_RETEST.md` | 🟡 DEV | Повторное тестирование pipeline |
| `PIPELINE_TEST_REPORT.md` | 🟡 DEV | Тестовый отчет pipeline |
| `PIPELINE_FIXES_REPORT.md` | 🟡 DEV | Исправления pipeline |
| `PIPELINE_PROBLEMS_SOLVED_REPORT.md` | 🟡 DEV | Решенные проблемы pipeline |
| `FULL_PIPELINE_VERIFICATION_REPORT.md` | 🟡 DEV | Полная верификация pipeline |
| `PIPELINE_FRONTEND_TEST_REPORT.md` | 🟡 DEV | Тестирование frontend pipeline |

### Frontend Reports
| Файл | Категория | Описание |
|------|-----------|----------|
| `FRONTEND_TESTING_REPORT.md` | 🟡 DEV | Отчет по тестированию frontend |
| `FRONTEND_TESTING_FIXES.md` | 🟡 DEV | Исправления тестов frontend |
| `FRONTEND_TESTS_FINAL_REPORT.md` | 🟡 DEV | Финальный отчет тестов frontend |

### Bug Fix Reports
| Файл | Категория | Описание |
|------|-----------|----------|
| `FIXED_ERRORS_REPORT.md` | 🟡 DEV | Исправленные ошибки |
| `ACCENT_FIX_REPORT.md` | 🟡 DEV | Исправление акцента |
| `CELERY_WORKER_FIX_REPORT.md` | 🟡 DEV | Исправление Celery worker |
| `EXPORT_FIX_REPORT.md` | 🟡 DEV | Исправление экспорта |
| `IMPORT_FIX_REPORT.md` | 🟡 DEV | Исправление импортов |
| `FALLBACK_PROBLEM_SOLVED_REPORT.md` | 🟡 DEV | Решение проблемы fallback |
| `VOICE_PROBLEM_SOLVED_REPORT.md` | 🟡 DEV | Решение проблемы с голосом |
| `SLIDES_PROBLEM_SOLVED_REPORT.md` | 🟡 DEV | Решение проблемы со слайдами |
| `SPEAKER_NOTES_FIX_SUCCESS.md` | 🟡 DEV | Успешное исправление заметок |
| `TWO_VOICES_FIX_REPORT.md` | 🟡 DEV | Исправление двух голосов |
| `VISUAL_CUES_FIX_REPORT.md` | 🟡 DEV | Исправление визуальных подсказок |
| `VISUAL_EFFECTS_FIX_REPORT.md` | 🟡 DEV | Исправление визуальных эффектов |
| `VOICE_SETTINGS_FIX_REPORT.md` | 🟡 DEV | Исправление настроек голоса |
| `VOICE_SETTINGS_UPDATE_REPORT.md` | 🟡 DEV | Обновление настроек голоса |
| `WAVENET_B_VOICE_SETUP_REPORT.md` | 🟡 DEV | Настройка голоса WaveNet B |

### Feature Integration Reports
| Файл | Категория | Описание |
|------|-----------|----------|
| `SSML_INTEGRATION_REPORT.md` | 🟡 DEV | Интеграция SSML |
| `SSML_INTEGRATION_FINAL_REPORT.md` | 🟡 DEV | Финальный отчет SSML |

### CI/CD Reports
| Файл | Категория | Описание |
|------|-----------|----------|
| `GITHUB_ACTIONS_FINAL_REPORT.md` | 🟡 DEV | Финальный отчет GitHub Actions |
| `GITHUB_ACTIONS_FIXES.md` | 🟡 DEV | Исправления GitHub Actions |

### Security Reports
| Файл | Категория | Описание |
|------|-----------|----------|
| `SECURITY_AUDIT_REPORT.md` | 🟡 DEV | Аудит безопасности |

### Product Reports
| Файл | Категория | Описание |
|------|-----------|----------|
| `PRODUCT_RESTART_REPORT.md` | 🟡 DEV | Перезапуск продукта |

---

## 🔄 ALTERNATIVE/BACKUP FILES (🟠 ALT)

### Backup Files
| Файл | Категория | Описание |
|------|-----------|----------|
| `backend/app/tasks_backup.py` | 🟠 ALT | Бэкап задач Celery |
| `src/components/Player.tsx.backup` | 🟠 ALT | Бэкап компонента Player |

### Alternative Environment Files
| Файл | Категория | Описание |
|------|-----------|----------|
| `backend_env_docker.env` | 🟠 ALT | Docker окружение (альтернатива) |
| `backend_env_enhanced_hybrid.env` | 🟠 ALT | Enhanced hybrid окружение |
| `backend_env_final.env` | 🟠 ALT | Финальное окружение |
| `backend_env_openrouter.env` | 🟠 ALT | OpenRouter окружение |
| `backend_env_ready.env` | 🟠 ALT | Ready окружение |
| `backend_env_vision_api.env` | 🟠 ALT | Vision API окружение |
| `docker.env` | 🟠 ALT | Docker окружение (используется docker-compose) |
| `backend/gcp_config.env` | 🟠 ALT | GCP конфигурация |

### Alternative Scripts
| Файл | Категория | Описание |
|------|-----------|----------|
| `backend/align.py` | 🟠 ALT | Альтернативный скрипт выравнивания |
| `backend/storage_gcs.py` | 🟠 ALT | Дубликат GCS storage (есть в app/) |

---

## ❌ OBSOLETE/TEST DATA (🔴 OBSOLETE)

### Test Audio Files (Generated)
| Файл | Категория | Описание |
|------|-----------|----------|
| `chirp_test_*.mp3` | 🔴 OBSOLETE | Тестовые Chirp аудио (8 файлов) |
| `voice_test_*.mp3` | 🔴 OBSOLETE | Тестовые голоса (10 файлов) |
| `voice_test_*.wav` | 🔴 OBSOLETE | Тестовые голоса WAV (8 файлов) |
| `voice_comparison_*.wav` | 🔴 OBSOLETE | Сравнение голосов (6 файлов) |
| `wavenet_test_*.wav` | 🔴 OBSOLETE | Тестовые WaveNet (25 файлов) |
| `current_voice_test.wav` | 🔴 OBSOLETE | Тест текущего голоса |

### Test HTML Files
| Файл | Категория | Описание |
|------|-----------|----------|
| `demo_visual_effects.html` | 🔴 OBSOLETE | Демо визуальных эффектов |
| `test_audio.html` | 🔴 OBSOLETE | Тест аудио |
| `test_kurs10.html` | 🔴 OBSOLETE | Тест курса 10 |
| `test_lesson.html` | 🔴 OBSOLETE | Тест урока |
| `test_processed_lesson.html` | 🔴 OBSOLETE | Тест обработанного урока |
| `test_visual_effects.html` | 🔴 OBSOLETE | Тест визуальных эффектов |
| `index.html` | 🔴 OBSOLETE | Старый HTML файл (не используется Vite) |

### Test Documents
| Файл | Категория | Описание |
|------|-----------|----------|
| `test.pdf` | 🔴 OBSOLETE | Тестовый PDF |
| `test.pptx` | 🔴 OBSOLETE | Тестовая презентация |
| `test_presentation.pptx` | 🔴 OBSOLETE | Тестовая презентация |
| `backend/test_presentation.pptx` | 🔴 OBSOLETE | Тестовая презентация (дубликат) |
| `Kurs_10.pdf` | 🔴 OBSOLETE | Тестовый курс 10 |
| `Kurs_10_short.pdf` | 🔴 OBSOLETE | Короткий курс 10 |

### Test Images
| Файл | Категория | Описание |
|------|-----------|----------|
| `test_leaf_anatomy.png` | 🔴 OBSOLETE | Тестовое изображение |
| `create_test_image.py` | 🔴 OBSOLETE | Создание тестового изображения |

### Test Data Directories
| Файл | Категория | Описание |
|------|-----------|----------|
| `kurs10_images_test/` | 🔴 OBSOLETE | Тестовые изображения курса 10 |
| `kurs10_slides/` | 🔴 OBSOLETE | Слайды курса 10 |

---

## 🗑️ TRASH (Можно удалять)

### System Files
| Файл | Категория | Описание |
|------|-----------|----------|
| `.DS_Store` | 🗑️ TRASH | macOS системный файл |
| `backend/.DS_Store` | 🗑️ TRASH | macOS системный файл |

### Temporary/Cache Files
| Файл | Категория | Описание |
|------|-----------|----------|
| `__pycache__/` | 🗑️ TRASH | Python кэш (всюду) |
| `node_modules/` | 🗑️ TRASH | Node.js модули (генерируется) |
| `.data/` | 🗑️ TRASH | Временные данные (генерируется) |
| `backend/.data/` | 🗑️ TRASH | Временные данные backend |

### Lock Files (Generated)
| Файл | Категория | Описание |
|------|-----------|----------|
| `bun.lockb` | 🗑️ TRASH | Bun lock (если не используется Bun) |
| `package-lock.json` | 🗑️ TRASH | NPM lock (генерируется) |

### Cookies/Credentials (Should be in .gitignore)
| Файл | Категория | Описание |
|------|-----------|----------|
| `cookies.txt` | 🗑️ TRASH | Куки (не должно быть в репо) |

### Environment Files (Should be in .gitignore)
| Файл | Категория | Описание |
|------|-----------|----------|
| `.env` | 🗑️ TRASH | Локальные переменные окружения |
| `.env.local` | 🗑️ TRASH | Локальные переменные окружения |
| `backend/.env` | 🗑️ TRASH | Backend переменные окружения |

---

## 📊 SUMMARY

### Статистика по категориям:

| Категория | Количество файлов | Описание |
|-----------|-------------------|----------|
| 🟢 **PROD** | ~80 файлов | Основной код приложения |
| 🟡 **DEV** | ~120 файлов | Тесты, документация, утилиты |
| 🟠 **ALT** | ~15 файлов | Альтернативные версии, бэкапы |
| 🔴 **OBSOLETE** | ~70 файлов | Старые тестовые данные |
| 🗑️ **TRASH** | ~10 файлов | Мусор, можно удалять |

### Рекомендации по очистке:

#### Немедленно удалить:
1. Все тестовые аудио файлы (`.mp3`, `.wav`) - **~57 файлов**
2. Тестовые HTML файлы - **7 файлов**
3. Тестовые документы (`test.pdf`, `test.pptx`, `Kurs_10*.pdf`) - **5 файлов**
4. Директории `kurs10_images_test/`, `kurs10_slides/`
5. Системные файлы `.DS_Store`
6. `cookies.txt`, `.env`, `.env.local` (добавить в `.gitignore`)

#### Можно архивировать:
1. Все отчеты `*_REPORT.md` - переместить в папку `docs/reports/`
2. Тестовые скрипты `test_*.py` - переместить в папку `tests/integration/`
3. Скрипты проверки `check_*.py` - переместить в папку `tests/integration/`

#### Оставить как есть:
1. Всё в категории **🟢 PROD**
2. GitHub Actions и CI/CD конфигурации
3. Основные тестовые фреймворки

---

## 📁 Предлагаемая структура после очистки:

```
slide-speaker-main/
├── backend/              # 🟢 Backend код
├── src/                  # 🟢 Frontend код
├── tests/                # 🟡 Тесты
│   ├── integration/      # Интеграционные тесты
│   ├── e2e/              # E2E тесты
│   └── unit/             # Unit тесты
├── docs/                 # 🟡 Документация
│   ├── reports/          # Отчеты
│   ├── guides/           # Руководства
│   └── api/              # API документация
├── scripts/              # 🟡 Утилиты
│   ├── setup/            # Настройка
│   ├── migration/        # Миграции
│   └── maintenance/      # Обслуживание
├── .github/              # 🟡 CI/CD
├── docker-compose.yml    # 🟢 Инфраструктура
├── package.json          # 🟢 Frontend deps
└── README.md             # 🟢 Документация
```

---

*Последнее обновление: 1 октября 2025*
