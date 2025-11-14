#!/bin/bash

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Открытие Player с визуальными эффектами          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

LESSON_ID="c3bf4454-5711-4020-a767-6e4e6da29ca1"
URL="http://localhost:3000/player/${LESSON_ID}"

echo -e "${GREEN}✓${NC} Lesson ID: ${YELLOW}${LESSON_ID}${NC}"
echo -e "${GREEN}✓${NC} URL: ${YELLOW}${URL}${NC}"
echo ""

echo -e "${BLUE}Открываю браузер...${NC}"

# Определяем ОС и открываем браузер
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open "${URL}"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    xdg-open "${URL}" 2>/dev/null || firefox "${URL}" 2>/dev/null || google-chrome "${URL}"
else
    # Windows (Git Bash)
    start "${URL}"
fi

echo ""
echo -e "${GREEN}✓${NC} Браузер открыт!"
echo ""
echo -e "${YELLOW}Ожидаемые логи в консоли браузера:${NC}"
echo -e "  • ${GREEN}[SlideViewer]${NC} Current slide: {hasVisualEffects: true}"
echo -e "  • ${GREEN}[VisualEffectsEngine]${NC} Component render"
echo -e "  • ${GREEN}[VisualEffectsEngine]${NC} ✅ Valid manifest"
echo ""
echo -e "${YELLOW}Если этих логов НЕТ:${NC}"
echo -e "  1. Откройте DevTools (F12 или Cmd+Option+I)"
echo -e "  2. Перейдите во вкладку Console"
echo -e "  3. Скопируйте и отправьте мне все логи"
echo ""
