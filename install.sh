#!/bin/bash

#
# Установщик для CommitPilot
# 
# Проверяет зависимости, устанавливает необходимые компоненты и 
# настраивает удобные алиасы для использования
#

set -e

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Функция для проверки наличия команды
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}❌ $1 не установлен${NC}"
        return 1
    else
        echo -e "${GREEN}✓ $1 установлен${NC}"
        return 0
    fi
}

# Заголовок
echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}             Установка CommitPilot              ${NC}"
echo -e "${GREEN}==================================================${NC}"

# Проверка зависимостей
echo -e "\n${YELLOW}Проверка необходимых зависимостей...${NC}"

# Проверка Git
check_command "git" || { 
    echo -e "${RED}Git требуется для работы. Пожалуйста, установите Git: https://git-scm.com/downloads${NC}"
    exit 1
}

# Проверка Python
check_command "python3" || check_command "python" || { 
    echo -e "${RED}Python 3.6+ требуется для работы. Пожалуйста, установите Python: https://www.python.org/downloads/${NC}"
    exit 1
}

# Определяем команду Python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

# Проверка pip
check_command "pip" || check_command "pip3" || {
    echo -e "${RED}pip требуется для установки зависимостей. Он обычно устанавливается вместе с Python.${NC}"
    exit 1
}

# Определяем команду pip
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
else
    PIP_CMD="pip"
fi

# Установка зависимостей
echo -e "\n${YELLOW}Установка зависимостей Python...${NC}"
$PIP_CMD install requests python-dotenv

# Установка OpenAI SDK (нужен для AITUNNEL и OpenAI)
echo -e "\n${YELLOW}Установка библиотеки OpenAI SDK (требуется для AITUNNEL и OpenAI)...${NC}"
$PIP_CMD install openai
echo -e "${GREEN}✓ Библиотека OpenAI SDK установлена${NC}"

# Получение текущего пути
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Сделать скрипты исполняемыми
echo -e "\n${YELLOW}Настройка прав доступа...${NC}"
chmod +x "$SCRIPT_DIR/auto_commit.py"
chmod +x "$SCRIPT_DIR/prepare-commit-msg"

# Создание алиасов
SHELL_RC=""
if [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
elif [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
fi

echo -e "\n${YELLOW}Настройка алиасов...${NC}"

if [ -n "$SHELL_RC" ]; then
    # Базовый алиас
    if grep -q "alias acommit=" "$SHELL_RC"; then
        echo -e "${YELLOW}Обновляем существующий алиас acommit...${NC}"
        sed -i "s|alias acommit=.*|alias acommit=\"$PYTHON_CMD $SCRIPT_DIR/auto_commit.py\"|g" "$SHELL_RC"
    else
        echo -e "# CommitPilot" >> "$SHELL_RC"
        echo -e "alias acommit=\"$PYTHON_CMD $SCRIPT_DIR/auto_commit.py\"" >> "$SHELL_RC"
    fi
    
    # Дополнительные алиасы для удобства
    if ! grep -q "alias acommit-dev=" "$SHELL_RC"; then
        echo -e "alias acommit-dev=\"$PYTHON_CMD $SCRIPT_DIR/auto_commit.py -b dev\"" >> "$SHELL_RC"
        echo -e "alias acommit-main=\"$PYTHON_CMD $SCRIPT_DIR/auto_commit.py -b main\"" >> "$SHELL_RC"
        echo -e "alias acommit-master=\"$PYTHON_CMD $SCRIPT_DIR/auto_commit.py -b master\"" >> "$SHELL_RC"
        echo -e "alias acommit-here=\"$PYTHON_CMD $SCRIPT_DIR/auto_commit.py -c\"" >> "$SHELL_RC"
    fi
    
    echo -e "${GREEN}✓ Алиасы добавлены в $SHELL_RC${NC}"
    echo -e "${YELLOW}Для активации алиасов выполните: source $SHELL_RC${NC}"
else
    echo -e "${YELLOW}⚠️ Не удалось найти файл конфигурации оболочки.${NC}"
    echo -e "${YELLOW}Добавьте следующие алиасы вручную в ваш файл конфигурации:${NC}"
    echo -e "alias acommit=\"$PYTHON_CMD $SCRIPT_DIR/auto_commit.py\""
    echo -e "alias acommit-dev=\"$PYTHON_CMD $SCRIPT_DIR/auto_commit.py -b dev\""
    echo -e "alias acommit-main=\"$PYTHON_CMD $SCRIPT_DIR/auto_commit.py -b main\""
    echo -e "alias acommit-master=\"$PYTHON_CMD $SCRIPT_DIR/auto_commit.py -b master\""
    echo -e "alias acommit-here=\"$PYTHON_CMD $SCRIPT_DIR/auto_commit.py -c\""
fi

# Создание конфигурационного файла
echo -e "\n${YELLOW}Создание конфигурационного файла...${NC}"
CONFIG_PATH="$SCRIPT_DIR/config.ini"
if [ ! -f "$CONFIG_PATH" ]; then
    echo -e "# CommitPilot - Конфигурация\n# Для настройки отредактируйте этот файл вручную\n\n[DEFAULT]\n# Выберите провайдера AI: aitunnel (по умолчанию), huggingface или openai\napi_provider = aitunnel\n\n# AITUNNEL API настройки (рекомендуется)\n# Токен можно также указать в файле .env как AI_TUNNEL=sk-aitunnel-xxx\naitunnel_token = \naitunnel_base_url = https://api.aitunnel.ru/v1/\naitunnel_model = gpt-4.1\n\n# Hugging Face API настройки\nhuggingface_token = \n\n# OpenAI API настройки\nopenai_token = \n\n# Ветка по умолчанию для git push\nbranch = master\n\n# Максимальный размер diff для отправки в AI API\nmax_diff_size = 7000" > "$CONFIG_PATH"
    echo -e "${GREEN}✓ Создан файл конфигурации $CONFIG_PATH${NC}"
    echo -e "${YELLOW}⚠️ Пожалуйста, отредактируйте файл конфигурации и добавьте ваш API токен${NC}"
    echo -e "${YELLOW}   Или создайте файл .env в корне проекта со строкой: AI_TUNNEL=sk-aitunnel-ваш_токен${NC}"
else
    echo -e "${GREEN}✓ Файл конфигурации уже существует${NC}"
fi

# Создание примера .env файла
ENV_PATH="$SCRIPT_DIR/.env.example"
if [ ! -f "$ENV_PATH" ]; then
    echo -e "# CommitPilot - Пример файла переменных окружения\n# Скопируйте этот файл в .env и добавьте ваш токен\n\n# AITUNNEL API токен (рекомендуется)\nAI_TUNNEL=sk-aitunnel-ваш_токен_здесь\n\n# Кастомный URL для AITUNNEL (опционально)\n# AITUNNEL_BASE_URL=https://api.aitunnel.ru/v1/\n\n# Модель для AITUNNEL (опционально)\n# AITUNNEL_MODEL=gpt-4.1" > "$ENV_PATH"
    echo -e "${GREEN}✓ Создан пример файла .env.example${NC}"
fi

# Создание примера config.ini файла
CONFIG_EXAMPLE_PATH="$SCRIPT_DIR/config.ini.example"
if [ ! -f "$CONFIG_EXAMPLE_PATH" ]; then
    cp "$CONFIG_PATH" "$CONFIG_EXAMPLE_PATH"
    echo -e "${GREEN}✓ Создан пример файла config.ini.example${NC}"
fi

# Установка Git hooks
echo -e "\n${YELLOW}Установка Git hooks в текущем репозитории...${NC}"
# Проверяем наличие директории .git
if [ -d ".git" ]; then
    # Создаем директорию hooks, если ее нет
    mkdir -p .git/hooks
    # Копируем hook
    cp "$SCRIPT_DIR/prepare-commit-msg" .git/hooks/
    chmod +x .git/hooks/prepare-commit-msg
    echo -e "${GREEN}✓ Git hook установлен в .git/hooks/prepare-commit-msg${NC}"
else
    echo -e "${YELLOW}⚠️ Текущая директория не является git-репозиторием. Git hook не установлен.${NC}"
    echo -e "${YELLOW}⚠️ Чтобы установить hook в другом проекте, выполните:${NC}"
    echo -e "${YELLOW}   cp $SCRIPT_DIR/prepare-commit-msg /путь/к/вашему/проекту/.git/hooks/${NC}"
fi

# Проверяем возможность генерации сообщений
if [ -f "$CONFIG_PATH" ]; then
    echo -e "\n${YELLOW}Проверка возможности генерации сообщений...${NC}"
    TEST_MESSAGE=$($PYTHON_CMD "$SCRIPT_DIR/auto_commit.py" --get-message 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$TEST_MESSAGE" ]; then
        echo -e "${GREEN}✓ Пример сгенерированного сообщения:${NC} \"$TEST_MESSAGE\""
    else
        echo -e "${YELLOW}⚠️ Для генерации сообщений требуется настроить API токен в config.ini или .env${NC}"
    fi
fi

echo -e "\n${GREEN}==================================================${NC}"
echo -e "${GREEN}      Установка CommitPilot завершена!          ${NC}"
echo -e "${GREEN}==================================================${NC}"
echo -e "\n${YELLOW}Доступные команды:${NC}"
echo -e "  ${GREEN}acommit${NC} - Создать коммит и отправить в ветку по умолчанию"
echo -e "  ${GREEN}acommit-dev${NC} - Создать коммит и отправить в ветку dev"
echo -e "  ${GREEN}acommit-main${NC} - Создать коммит и отправить в ветку main"
echo -e "  ${GREEN}acommit-master${NC} - Создать коммит и отправить в ветку master"
echo -e "  ${GREEN}acommit-here${NC} - Создать коммит без push"
echo -e "\n${YELLOW}Для использования в других проектах:${NC}"
echo -e "  ${GREEN}1.${NC} Создайте alias для вызова CommitPilot из любой директории"
echo -e "  ${GREEN}2.${NC} Или скопируйте hook: cp $SCRIPT_DIR/prepare-commit-msg /путь/к/проекту/.git/hooks/"
echo -e "\n${YELLOW}Для получения дополнительной информации см. файл README.md${NC}" 