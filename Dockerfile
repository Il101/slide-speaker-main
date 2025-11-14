FROM node:20-alpine

WORKDIR /app

# Копируем package files
COPY package*.json ./

# Устанавливаем зависимости
RUN npm install

# Копируем исходный код
COPY . .

# Открываем порт
EXPOSE 5173

# Запускаем dev сервер (переменные окружения доступны во время выполнения)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]