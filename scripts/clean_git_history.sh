#!/bin/bash
# Опциональный скрипт для очистки git истории от секретов
# ВНИМАНИЕ: Это изменит git историю! Используйте с осторожностью

set -e

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${YELLOW}⚠️  ВНИМАНИЕ: Очистка git истории${NC}"
echo ""
echo "Этот скрипт удалит секреты из git истории."
echo "Это безопасно для приватного репозитория, НО:"
echo "  - Изменит все commit хэши"
echo "  - Потребует force push (если уже пушили)"
echo "  - Другие разработчики должны будут сделать fresh clone"
echo ""
echo -e "${RED}Убедитесь что у вас есть backup!${NC}"
echo ""
read -p "Продолжить? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Отменено."
    exit 0
fi

echo ""
echo "🧹 Очистка git истории..."

# Проверяем что есть git
if [ ! -d .git ]; then
    echo -e "${RED}Ошибка: Не найдена .git директория${NC}"
    exit 1
fi

# Используем git filter-repo (более современный и быстрый чем filter-branch)
if ! command -v git-filter-repo &> /dev/null; then
    echo ""
    echo -e "${YELLOW}git-filter-repo не установлен${NC}"
    echo "Установка:"
    echo "  macOS: brew install git-filter-repo"
    echo "  Ubuntu: sudo apt install git-filter-repo"
    echo "  Python: pip3 install git-filter-repo"
    echo ""
    echo "Используем fallback: git filter-branch (медленнее)..."
    echo ""
    
    # Fallback на git filter-branch
    FILES_TO_REMOVE=(
        "docker.env"
        "railway.env"
        ".env"
        "inspiring-keel-473421-j2-22cc51dfb336.json"
    )
    
    for file in "${FILES_TO_REMOVE[@]}"; do
        echo "Удаление $file из истории..."
        git filter-branch --force --index-filter \
            "git rm --cached --ignore-unmatch $file" \
            --prune-empty --tag-name-filter cat -- --all
    done
    
    # Очистка refs
    rm -rf .git/refs/original/
    git reflog expire --expire=now --all
    git gc --prune=now --aggressive
    
else
    # Используем git-filter-repo (рекомендуется)
    echo "Используем git-filter-repo..."
    
    # Создаем список файлов для удаления
    cat > /tmp/paths-to-remove.txt << EOF
docker.env
railway.env
.env
inspiring-keel-473421-j2-22cc51dfb336.json
keys/inspiring-keel-473421-j2-22cc51dfb336.json
EOF
    
    git filter-repo --invert-paths --paths-from-file /tmp/paths-to-remove.txt --force
    rm /tmp/paths-to-remove.txt
fi

echo ""
echo -e "${GREEN}✅ Git история очищена!${NC}"
echo ""
echo "Следующие шаги:"
echo ""
echo "1. Проверьте что всё работает:"
echo "   git log --all --oneline | head -20"
echo ""
echo "2. Если работает с удаленным репозиторием (GitHub/GitLab):"
echo "   git push origin --force --all"
echo "   git push origin --force --tags"
echo ""
echo "3. Другие разработчики должны:"
echo "   cd ../slide-speaker-backup  # Переименовать старую копию"
echo "   git clone <repo-url> slide-speaker"
echo ""
echo -e "${YELLOW}⚠️  После force push старые клоны будут несовместимы!${NC}"
echo ""
