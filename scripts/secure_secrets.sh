#!/bin/bash
# Скрипт для защиты секретов в приватном репозитории
# Не меняет ключи, только защищает от случайной утечки

set -e

echo "🔒 Защита секретов без изменения ключей..."
echo ""

# 1. Создаем backup текущих секретов
echo "📦 Шаг 1: Создание backup..."
mkdir -p .secrets-backup
cp docker.env .secrets-backup/docker.env.backup
cp railway.env .secrets-backup/railway.env.backup
cp .env .secrets-backup/.env.backup
cp inspiring-keel-473421-j2-22cc51dfb336.json .secrets-backup/gcp-sa.json.backup 2>/dev/null || true
echo "✅ Backup создан в .secrets-backup/"

# 2. Удаляем секреты из git tracking (но файлы остаются на диске!)
echo ""
echo "🗑️  Шаг 2: Удаление из git (файлы остаются на диске)..."
git rm --cached docker.env 2>/dev/null || true
git rm --cached railway.env 2>/dev/null || true
git rm --cached .env 2>/dev/null || true
git rm --cached inspiring-keel-473421-j2-22cc51dfb336.json 2>/dev/null || true
echo "✅ Файлы удалены из git tracking"

# 3. Создаем templates с плейсхолдерами
echo ""
echo "📝 Шаг 3: Создание template файлов..."

# Template для docker.env
cat > docker.env.template << 'EOF'
# Database Configuration
POSTGRES_DB=slide_speaker
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<SECURE_PASSWORD>
DATABASE_URL=postgresql+asyncpg://postgres:<PASSWORD>@postgres:5432/slide_speaker

# Redis Configuration
REDIS_URL=redis://redis:6379

# JWT Configuration
JWT_SECRET_KEY=<GENERATE_WITH: python3 -c 'import secrets; print(secrets.token_urlsafe(64))'>

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# MinIO Configuration
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=<SECURE_PASSWORD>

# Grafana Configuration
GRAFANA_PASSWORD=<SECURE_PASSWORD>

# Application Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Google Cloud Services Configuration
GOOGLE_APPLICATION_CREDENTIALS=/app/keys/gcp-sa.json
GCP_PROJECT_ID=<YOUR_PROJECT_ID>
GCP_LOCATION=us
GOOGLE_API_KEY=<YOUR_GOOGLE_API_KEY>

# Document AI (OCR) настройки
GCP_DOC_AI_PROCESSOR_ID=<YOUR_PROCESSOR_ID>
OCR_BATCH_SIZE=10

# Gemini (LLM) настройки
GEMINI_MODEL=gemini-2.0-flash
GEMINI_LOCATION=europe-west1
LLM_TEMPERATURE=0.2

# Google Cloud Text-to-Speech настройки
GOOGLE_TTS_VOICE=ru-RU-Wavenet-D
GOOGLE_TTS_SPEAKING_RATE=1.0
GOOGLE_TTS_PITCH=0.0

# Выбор провайдеров
OCR_PROVIDER=vision
LLM_PROVIDER=gemini
TTS_PROVIDER=google
STORAGE=gcs

# Pipeline Configuration
PIPELINE=intelligent_optimized
PIPELINE_MAX_PARALLEL_SLIDES=5
PIPELINE_MAX_PARALLEL_TTS=10

# OCR Cache Configuration (7 days TTL)
OCR_CACHE_TTL=604800

# OpenRouter (LLM) настройки - FREE MODEL
OPENROUTER_API_KEY=<YOUR_OPENROUTER_KEY>
OPENROUTER_MODEL=google/gemma-3-12b-it:free
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
LLM_TEMPERATURE=0.2
LLM_LANGUAGE=ru

# New Pipeline (default: true)
USE_NEW_PIPELINE=true

# Google Cloud Storage Configuration for Railway
GCS_BUCKET=slide-speaker-railway-storage
GCS_BASE_URL=https://storage.googleapis.com/slide-speaker-railway-storage
EOF

echo "✅ docker.env.template создан"

# Template для keys
mkdir -p keys
cat > keys/README.md << 'EOF'
# GCP Service Account Key

Положите сюда файл `gcp-sa.json` с вашим GCP service account ключом.

**НЕ КОММИТЬТЕ этот файл в git!**

Файл должен содержать:
- type: "service_account"
- project_id: "your-project-id"
- private_key_id: "..."
- private_key: "REPLACE_WITH_PRIVATE_KEY"
- client_email: "..."

Получить ключ:
```bash
gcloud iam service-accounts keys create gcp-sa.json \
  --iam-account=YOUR_SERVICE_ACCOUNT@PROJECT_ID.iam.gserviceaccount.com
```
EOF

echo "✅ keys/README.md создан"

# 4. Обновляем .gitignore
echo ""
echo "🚫 Шаг 4: Обновление .gitignore..."

cat >> .gitignore << 'EOF'

# ===== SECURITY: Secrets и credentials =====
# Добавлено для защиты секретов
docker.env
railway.env
.env
.env.local
.env.*.local
.secrets-backup/

# GCP credentials
keys/*.json
!keys/README.md
inspiring-keel-473421-j2-*.json
gcp-sa.json

# Backup files
*.backup
EOF

echo "✅ .gitignore обновлен"

# 5. Создаем pre-commit hook для проверки
echo ""
echo "🔍 Шаг 5: Установка pre-commit hook..."

mkdir -p .git/hooks

cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook для проверки секретов

RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Проверка на утечку секретов..."

# Файлы которые не должны быть в коммите
FORBIDDEN_FILES=(
    "docker.env"
    "railway.env"
    ".env"
    "inspiring-keel-473421-j2-22cc51dfb336.json"
    "keys/gcp-sa.json"
    ".secrets-backup/*"
)

# Проверяем staged файлы
FOUND_SECRETS=0
for file in "${FORBIDDEN_FILES[@]}"; do
    if git diff --cached --name-only | grep -q "$file"; then
        echo -e "${RED}❌ ОШИБКА: Попытка закоммитить секретный файл: $file${NC}"
        FOUND_SECRETS=1
    fi
done

# Проверяем содержимое на паттерны секретов
PATTERNS=(
    "AIzaSy[0-9A-Za-z_-]{33}"  # Google API Key
    "sk-or-v1-[0-9a-f]{64}"     # OpenRouter API Key
    "private_key.*BEGIN.*PRIVATE.*KEY"  # Private keys
)

for pattern in "${PATTERNS[@]}"; do
    if git diff --cached | grep -E "$pattern" > /dev/null; then
        echo -e "${RED}❌ ОШИБКА: Обнаружен паттерн секрета: $pattern${NC}"
        FOUND_SECRETS=1
    fi
done

if [ $FOUND_SECRETS -eq 1 ]; then
    echo ""
    echo -e "${RED}🚨 КОММИТ ЗАБЛОКИРОВАН!${NC}"
    echo -e "${YELLOW}Причина: Обнаружены секреты в staged файлах${NC}"
    echo ""
    echo "Что делать:"
    echo "1. Удалите файлы с секретами из staged: git reset HEAD <file>"
    echo "2. Убедитесь что файлы в .gitignore"
    echo "3. Используйте template файлы (*.template) вместо оригиналов"
    echo ""
    exit 1
fi

echo "✅ Секреты не обнаружены"
exit 0
EOF

chmod +x .git/hooks/pre-commit
echo "✅ Pre-commit hook установлен"

# 6. Создаем README с инструкциями
echo ""
echo "📖 Шаг 6: Создание документации..."

cat > SECRETS_SETUP.md << 'EOF'
# 🔒 Управление секретами

## Для новых разработчиков

### Первичная настройка

1. **Скопируйте template файлы:**
   ```bash
   cp docker.env.template docker.env
   cp railway.env.template railway.env
   ```

2. **Получите реальные секреты:**
   - Попросите у тимлида файл `.secrets-backup/docker.env.backup`
   - ИЛИ запросите доступ к secrets manager (Railway/AWS)

3. **Заполните значения:**
   ```bash
   # Откройте docker.env и замените плейсхолдеры на реальные значения
   nano docker.env
   ```

4. **Проверьте что файлы в .gitignore:**
   ```bash
   git status
   # docker.env НЕ ДОЛЖЕН быть в "Changes to be committed"
   ```

## Безопасность

### ✅ Что в git:
- `docker.env.template` - template с плейсхолдерами
- `railway.env.template` - template
- `.gitignore` - защита от случайных коммитов
- Pre-commit hook - автоматическая проверка

### ❌ Что НЕ в git:
- `docker.env` - реальные секреты
- `railway.env` - реальные секреты
- `*.backup` - backup файлы
- `keys/*.json` - GCP credentials

### 🔍 Pre-commit защита

При попытке закоммитить секреты вы получите ошибку:
```
🚨 КОММИТ ЗАБЛОКИРОВАН!
Причина: Обнаружены секреты в staged файлах
```

## Backup секретов

Ваши реальные секреты сохранены в:
```
.secrets-backup/docker.env.backup
.secrets-backup/railway.env.backup
.secrets-backup/gcp-sa.json.backup
```

⚠️ **ВАЖНО:** Эта папка в .gitignore и НЕ попадет в git!

## Восстановление секретов

Если случайно удалили docker.env:
```bash
cp .secrets-backup/docker.env.backup docker.env
```

## Ротация ключей (в будущем)

Когда захотите поменять ключи:
```bash
# 1. Сгенерируйте новый секрет
python3 -c 'import secrets; print(secrets.token_urlsafe(64))'

# 2. Обновите в docker.env
nano docker.env

# 3. Обновите backup
cp docker.env .secrets-backup/docker.env.backup

# 4. Перезапустите сервисы
docker-compose restart
```
EOF

echo "✅ SECRETS_SETUP.md создан"

# 7. Финальный отчет
echo ""
echo "════════════════════════════════════════════"
echo "✅ Защита секретов завершена!"
echo "════════════════════════════════════════════"
echo ""
echo "Что сделано:"
echo "  ✅ Backup создан в .secrets-backup/"
echo "  ✅ Секреты удалены из git tracking"
echo "  ✅ Template файлы созданы"
echo "  ✅ .gitignore обновлен"
echo "  ✅ Pre-commit hook установлен"
echo "  ✅ Документация создана"
echo ""
echo "Ваши ключи:"
echo "  ✅ Остались на диске без изменений"
echo "  ✅ Работают как раньше"
echo "  ✅ Защищены от случайного коммита"
echo "  ✅ Backed up в .secrets-backup/"
echo ""
echo "Следующие шаги:"
echo "  1. Закоммитьте изменения:"
echo "     git add .gitignore docker.env.template SECRETS_SETUP.md keys/README.md"
echo "     git commit -m 'security: Add secrets protection without changing keys'"
echo ""
echo "  2. Проверьте что секреты не в git:"
echo "     git status  # docker.env должен быть в 'Untracked files'"
echo ""
echo "  3. (Опционально) Очистите git историю от старых секретов:"
echo "     ./scripts/clean_git_history.sh"
echo ""
echo "⚠️  ВАЖНО: .secrets-backup/ только локально!"
echo "    Не забудьте сделать дополнительный backup в безопасное место"
echo ""
