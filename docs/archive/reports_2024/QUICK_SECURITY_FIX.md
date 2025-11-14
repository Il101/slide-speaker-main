# ⚡ Быстрая защита секретов (5 минут)

## 🎯 Что это делает

✅ Защищает ваши текущие ключи от случайной утечки  
✅ **НЕ меняет** существующие ключи (они продолжают работать)  
✅ Блокирует коммиты с секретами (pre-commit hook)  
✅ Создает backup на случай ЧП  

## 🚀 Быстрый старт

### 1. Запустите скрипт защиты

```bash
# Сделайте скрипт исполняемым
chmod +x scripts/secure_secrets.sh

# Запустите
./scripts/secure_secrets.sh
```

Скрипт выполнит:
- 📦 Backup текущих секретов в `.secrets-backup/`
- 🗑️ Удалит секреты из git tracking (файлы останутся на диске!)
- 📝 Создаст template файлы для новых разработчиков
- 🚫 Обновит `.gitignore`
- 🔍 Установит pre-commit hook (защита от случайных коммитов)
- 📖 Создаст документацию

### 2. Закоммитьте изменения

```bash
# Проверьте что секреты не попадут в коммит
git status
# docker.env должен быть в "Untracked files" или вообще отсутствовать

# Добавьте только безопасные файлы
git add .gitignore docker.env.template railway.env.template SECRETS_SETUP.md keys/README.md

# Закоммитьте
git commit -m "security: Add secrets protection without changing keys"

# Запушьте (репозиторий приватный - безопасно)
git push
```

### 3. Проверьте что работает

```bash
# Попробуйте случайно закоммитить секрет (должна быть ошибка)
git add docker.env
git commit -m "test"

# Должны увидеть:
# 🚨 КОММИТ ЗАБЛОКИРОВАН!
# Причина: Обнаружены секреты в staged файлах

# Отмените staged файл
git reset HEAD docker.env
```

## ✅ Что получили

### Ваши ключи:
- ✅ Остались на диске без изменений  
- ✅ Продолжают работать как раньше  
- ✅ Backed up в `.secrets-backup/`  
- ✅ Защищены от случайного коммита  

### Защита:
- 🚫 docker.env в .gitignore (не попадет в git)
- 🔍 Pre-commit hook (блокирует коммиты с секретами)
- 📝 Template файлы (для новых разработчиков)
- 📖 Документация (SECRETS_SETUP.md)

## 📂 Структура после защиты

```
slide-speaker-main/
├── .secrets-backup/           # ⬅️ Ваши реальные секреты (backup)
│   ├── docker.env.backup      #    НЕ в git!
│   ├── railway.env.backup     #    НЕ в git!
│   └── gcp-sa.json.backup     #    НЕ в git!
│
├── docker.env                 # ⬅️ Рабочие секреты (НЕ в git!)
├── railway.env                #    НЕ в git!
├── .env                       #    НЕ в git!
│
├── docker.env.template        # ⬅️ Template для новых devs (В git ✅)
├── railway.env.template       #    С плейсхолдерами
│
├── keys/
│   ├── gcp-sa.json           # ⬅️ Реальный ключ (НЕ в git!)
│   └── README.md             # ⬅️ Инструкции (В git ✅)
│
├── .gitignore                 # ⬅️ Обновлен (В git ✅)
├── .git/hooks/pre-commit      # ⬅️ Защита (локально)
│
└── SECRETS_SETUP.md           # ⬅️ Документация (В git ✅)
```

## 🔄 Для новых разработчиков

Когда кто-то клонирует репозиторий:

```bash
# 1. Клонируют репозиторий
git clone <repo-url>
cd slide-speaker-main

# 2. Видят template файлы
ls -la *.template
# docker.env.template
# railway.env.template

# 3. Копируют templates
cp docker.env.template docker.env
cp railway.env.template railway.env

# 4. Вы отправляете им реальные секреты (через Slack/1Password/etc)
# Они заполняют docker.env

# 5. Готово! Pre-commit hook защищает от случайных коммитов
```

## 🛡️ Дополнительная защита (опционально)

### Очистка git истории

Если хотите удалить секреты из git истории (опционально):

```bash
chmod +x scripts/clean_git_history.sh
./scripts/clean_git_history.sh
```

⚠️ **ВНИМАНИЕ:** Это изменит git историю! Подходит только если:
- Репозиторий приватный
- Вы единственный разработчик ИЛИ
- Все готовы сделать fresh clone после очистки

### Шифрование секретов (advanced)

Если нужно хранить секреты в git зашифрованными:

```bash
# Установите git-crypt
brew install git-crypt  # macOS
# или
sudo apt install git-crypt  # Ubuntu

# Инициализируйте
git-crypt init

# Добавьте правила шифрования
echo "docker.env filter=git-crypt diff=git-crypt" >> .gitattributes
echo "railway.env filter=git-crypt diff=git-crypt" >> .gitattributes
echo "keys/*.json filter=git-crypt diff=git-crypt" >> .gitattributes

# Теперь эти файлы будут зашифрованы в git
git add .gitattributes docker.env railway.env keys/*.json
git commit -m "security: Encrypt secrets with git-crypt"
```

## ❓ FAQ

**Q: Мои ключи перестанут работать?**  
A: Нет! Они остаются на диске без изменений и работают как раньше.

**Q: Что если я случайно удалю docker.env?**  
A: Восстановите из backup: `cp .secrets-backup/docker.env.backup docker.env`

**Q: Нужно ли менять ключи?**  
A: Нет! Этот скрипт только защищает существующие ключи. Менять нужно только если они уже утекли.

**Q: Что делать если pre-commit hook блокирует нужный коммит?**  
A: Если уверены что секретов нет: `git commit --no-verify`

**Q: Безопасно ли для приватного репо?**  
A: Да! Для приватного репо основной риск - случайная публикация. Pre-commit hook защищает от этого.

## 🆘 Помощь

Если что-то пошло не так:

```bash
# Откатить изменения в git
git reset --hard HEAD~1

# Восстановить секреты
cp .secrets-backup/docker.env.backup docker.env
cp .secrets-backup/railway.env.backup railway.env
cp .secrets-backup/gcp-sa.json.backup inspiring-keel-473421-j2-22cc51dfb336.json

# Удалить pre-commit hook
rm .git/hooks/pre-commit
```

## 📞 Дополнительная информация

- Полный отчет по безопасности: `SECURITY_AUDIT_REPORT.md`
- Инструкции для новых devs: `SECRETS_SETUP.md`
- Backup ваших секретов: `.secrets-backup/`

---

**Время выполнения:** 5 минут  
**Изменение ключей:** НЕ требуется  
**Безопасность:** ⬆️ значительно повышена  
