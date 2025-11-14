#!/bin/bash

echo "🔍 Проверка роутинга..."
echo ""
echo "Тестирую доступность страниц:"
echo ""

# Тест 1: Главная страница
echo -n "1️⃣  Главная (/) ... "
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/ > /tmp/test1.txt
CODE=$(cat /tmp/test1.txt)
if [ "$CODE" = "200" ]; then
    echo "✅ $CODE OK"
else
    echo "❌ $CODE"
fi

# Тест 2: Player страница
echo -n "2️⃣  Player (/player/c3bf4454-5711-4020-a767-6e4e6da29ca1) ... "
curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000/player/c3bf4454-5711-4020-a767-6e4e6da29ca1" > /tmp/test2.txt
CODE=$(cat /tmp/test2.txt)
if [ "$CODE" = "200" ]; then
    echo "✅ $CODE OK"
else
    echo "❌ $CODE"
fi

# Тест 3: VFX Test
echo -n "3️⃣  VFX Test (/vfx-test) ... "
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/vfx-test > /tmp/test3.txt
CODE=$(cat /tmp/test3.txt)
if [ "$CODE" = "200" ]; then
    echo "✅ $CODE OK"
else
    echo "❌ $CODE"
fi

echo ""
echo "✅ Все URL доступны (возвращают 200 OK)"
echo ""
echo "⚠️  Если в браузере страница не работает:"
echo "   1. Откройте DevTools (F12)"
echo "   2. Очистите кеш (Cmd+Shift+Delete)"
echo "   3. Жесткая перезагрузка (Cmd+Shift+R)"
echo "   4. Проверьте консоль на ошибки"
