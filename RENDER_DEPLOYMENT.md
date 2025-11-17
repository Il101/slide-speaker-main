# Развертывание `slide-speaker-main` на Render

Этот репозиторий — Vite + React приложение, которое после `npm run build` собирается в папку `dist`. Чтобы задеплоить его на Render, создайте статический сайт и укажите в качестве публикации эту папку.

> ⚙️ Для backend и Celery worker используйте отдельный гайд `RENDER_BACKEND_DEPLOYMENT.md`, в нём описан blueprint `render.yaml` и список обязательных переменных окружения.

## 1. Настройка сервиса Render
1. Зайдите на https://render.com и создайте новый **Static Site**.
2. Подключите аккаунт GitHub/GitLab/Bitbucket и выберите репозиторий `slide-speaker-main` (ветку `production-deploy` или другую нужную). 
3. В поле команды сборки укажите:
   ```bash
   npm install && npm run build
   ```
4. В качестве директории публикации укажите `dist`. Render сам установит Node и выполнит сборку; по умолчанию платформа использует Node 20, который совместим с Vite.
5. Если проект находится в подпапке, укажите её в **Root Directory**. В этом репозитории Vite-приложение лежит в корне, так что поле можно оставить пустым.
6. Задайте имя сайта (например, `slide-speaker-frontend`) и завершите настройку.

## 2. Переменные окружения
Приложение зависит от нескольких переменных `VITE_*`, которые задаются во время сборки. Установите их в разделе **Environment** Render или в `render.yaml`, чтобы они указывали на ваш production-бэкенд:

| Переменная | Назначение | Пример значения |
| --- | --- | --- |
| `VITE_API_BASE` | Базовый URL для прямых запросов к API (например, для получения изображений/аудио). | `https://api.yourdomain.com` |
| `VITE_API_URL` | Базовый URL для клиентского API (используется по всему приложению). | `https://api.yourdomain.com/api` |
| `VITE_WS_URL` | URL для WebSocket-соединений (live-плеер, аналитика). | `wss://api.yourdomain.com/ws` |
| `NODE_ENV` | Установите в `production`, чтобы включить оптимизации. | `production` |

Если бэкенд также работает на Render, можно ссылаться на внутренние хостнеймы (например, `https://backend.onrender.com`).

## 3. Опциональный файл `render.yaml`
Если вы предпочитаете описывать инфраструктуру в коде и хранить настройки в репозитории, создайте рядом с `package.json` файл `render.yaml`:

```yaml
services:
  - type: static
    name: slide-speaker-frontend
    env: node
    region: oregon # или другой регион по выбору
    repo: https://github.com/Il101/slide-speaker-main
    branch: production-deploy
    buildCommand: npm install && npm run build
    publishPath: dist
    envVars:
      - key: VITE_API_BASE
        value: https://api.yourdomain.com
      - key: VITE_API_URL
        value: https://api.yourdomain.com/api
      - key: VITE_WS_URL
        value: wss://api.yourdomain.com/ws
      - key: NODE_ENV
        value: production
```

Render будет анализировать этот файл при каждом пуше и применять настройки автоматически.

## 4. Собственный домен и SSL
1. В настройках сервиса Render добавьте собственный домен, например `app.yourdomain.com`.
2. Настройте DNS (A/AAAA записи) в соответствии с инструкциями Render. Платформа автоматически выпустит SSL-сертификат.

## 5. Проверка
- После завершения сборки на вкладке **Live** появится ваш сайт из папки `dist`. Проверьте, что активы загружаются и `VITE_*` точки работают.
- Чтобы протестировать новую переменную, измените её через панель Render и запустите ручной деплой, затем проверьте лог сборки.
- Воспользуйтесь **Deploy Hooks** Render или интеграцией с GitHub/GitLab, чтобы автоматически собирать проект при пуше в ветку `production-deploy`.

## 6. Советы после деплоя
- Локально запускайте `npm run build:analyze`, если хотите оценить размеры бандлов перед деплоем.
- Держите `package.json` и lock-файл (`package-lock.json`/`bun.lockb`) в актуальном состоянии, чтобы Render ставил зафиксированные зависимости.
- Делитесь ссылкой на лог сборки Render с командой, если нужно разобраться с ошибкой.
