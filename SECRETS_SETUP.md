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
