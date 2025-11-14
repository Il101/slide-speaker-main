# 🚀 Slide Speaker - Quick Deploy Guide

## ⚡ **Быстрый старт (5 минут)**

### 1. **Подготовка:**
```bash
# Установите Railway CLI
npm install -g @railway/cli

# Войдите в Railway
railway login

# Запустите автоматический деплой
./deploy.sh
```

### 2. **Выберите опцию 1** (Полный деплой)

### 3. **Загрузите фронтенд на Netlify:**
- Откройте [netlify.com](https://netlify.com)
- Перетащите файл `netlify-deploy.tar.gz`
- Настройте переменные окружения

---

## 📋 **Что включено в ветку production-deploy:**

### **Backend (Railway):**
- ✅ `Dockerfile.railway` - оптимизированный Dockerfile
- ✅ `railway.json` - конфигурация Railway
- ✅ `.railwayignore` - исключение ненужных файлов
- ✅ `railway.env.template` - шаблон переменных окружения

### **Frontend (Netlify):**
- ✅ `Dockerfile.netlify` - Dockerfile для фронтенда
- ✅ `nginx.conf` - конфигурация Nginx
- ✅ `netlify.toml` - конфигурация Netlify
- ✅ `netlify.env.template` - шаблон переменных окружения

### **Автоматизация:**
- ✅ `deploy.sh` - скрипт автоматического деплоя
- ✅ `PRODUCTION_DEPLOYMENT_GUIDE.md` - подробная инструкция

### **Оптимизации:**
- ✅ CORS настроен для Railway и Netlify
- ✅ Переменные окружения оптимизированы
- ✅ Кэширование и параллельная обработка включены

---

## 🎯 **Результат:**

После деплоя у вас будет:
- **Backend**: https://your-app.up.railway.app
- **Frontend**: https://your-app.netlify.app
- **API Docs**: https://your-app.up.railway.app/docs
- **Health Check**: https://your-app.up.railway.app/health

---

## 💰 **Стоимость:**
- **Railway**: $0 (бесплатный план)
- **Netlify**: $0 (бесплатный план)
- **Google Cloud**: $0 (бесплатные кредиты)

---

## 🚨 **Если что-то пошло не так:**

### Проблема: Railway не деплоится
```bash
# Проверьте логи
railway logs --tail 50

# Проверьте переменные
railway variables
```

### Проблема: CORS ошибки
```bash
# Обновите CORS с вашим Netlify URL
railway variables set CORS_ORIGINS="https://your-app.netlify.app"
```

### Проблема: Frontend не подключается к API
```bash
# Проверьте переменные в Netlify
VITE_API_BASE=https://your-app.up.railway.app
VITE_WS_URL=wss://your-app.up.railway.app
```

---

## 🎉 **Готово!**

**Ваш Slide Speaker развернут в продакшене!** 🚀

Теперь можете:
- Загружать презентации
- Обрабатывать их через AI
- Экспортировать в видео
- Приглашать пользователей

**Удачи с вашим проектом!** 🎯
