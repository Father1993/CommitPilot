# CommitPilot 🤖

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

> Автоматизируйте создание коммитов с помощью AI, который понимает ваш код

## Что это такое?

Инструмент, который анализирует ваши изменения и генерирует осмысленные сообщения для коммитов в соответствии с [Conventional Commits](https://www.conventionalcommits.org/). Больше не нужно тратить время на придумывание хороших сообщений!

## Особенности

-   🚀 Автоматизация `git add`, `git commit` и `git push` одной командой
-   🧠 Поддержка нескольких AI провайдеров:
    -   Hugging Face (модель Mixtral-8x7B-Instruct)
    -   OpenAI (модели gpt-4o-mini, gpt-3.5-turbo)
-   🔄 Интеграция с Git hooks для автоматической генерации сообщений
-   🛠️ Простая настройка и использование
-   💡 Генерация качественных сообщений в формате Conventional Commits

## Быстрый старт

### Установка

```bash
# Клонируйте репозиторий CommitPilot
git clone https://github.com/Father1993/CommitPilot.git
cd CommitPilot

# Запустите установочный скрипт
bash install.sh

# Перезагрузите ваш shell для активации алиасов
source ~/.bashrc   # или ~/.zshrc
```

### Настройка

После установки отредактируйте файл `config.ini` и добавьте ваш API токен:

```ini
[DEFAULT]
# Выберите провайдера AI: huggingface или openai
api_provider = huggingface

# Вставьте ваш Hugging Face API токен
huggingface_token = ваш_токен_здесь
```

### Использование

```bash
# Создание коммита с AI-генерацией сообщения и отправка в ветку по умолчанию
acommit

# Только создание коммита без push
acommit-here
# или
acommit -c

# С указанием ветки
acommit -b feature/branch

# Свое сообщение
acommit -m "feat: моя новая функция"
```

### Использование в других проектах

Есть два способа использовать CommitPilot в других проектах:

1. **Глобальные алиасы** - после установки алиасы работают из любой директории:

    ```bash
    cd /путь/к/другому/проекту
    acommit  # Будет использовать CommitPilot из установленной директории
    ```

2. **Установка Git hook** - для автоматической генерации сообщений при `git commit`:
    ```bash
    cp /путь/к/CommitPilot/prepare-commit-msg /путь/к/другому/проекту/.git/hooks/
    chmod +x /путь/к/другому/проекту/.git/hooks/prepare-commit-msg
    ```

## Требования

-   Python 3.6+
-   Git
-   Установленные библиотеки:
    -   `requests` (обязательно)
    -   `openai` (опционально, для использования OpenAI API)
-   Доступ к интернету для API запросов
-   API ключ Hugging Face или OpenAI (можно получить бесплатно)

## Как это работает?

1. CommitPilot анализирует изменения в вашем коде через `git diff`
2. Отправляет эти изменения в API искусственного интеллекта
3. Получает сгенерированное сообщение в формате Conventional Commits
4. Создает коммит с этим сообщением
5. При необходимости отправляет изменения в удаленный репозиторий

## Подробная документация

-   [Установка и настройка](./docs/installation.md)
-   [Принцип работы](./docs/how_it_works.md)
-   [Примеры использования](./docs/examples.md)
-   [Руководство для разработчиков](./docs/development.md)
-   [Тестирование проекта](./docs/testing.md)

## Конфиденциальность и API токены

Ваш API токен для Hugging Face или OpenAI хранится в файле `config.ini`. Для безопасности:

1. **Этот файл уже добавлен в `.gitignore`**, чтобы предотвратить случайную публикацию ваших ключей
2. **Не публикуйте `config.ini` с вашими реальными ключами** в публичных репозиториях
3. **Получите бесплатный API токен** на:
    - Hugging Face: https://huggingface.co/settings/tokens
    - OpenAI: https://platform.openai.com/api-keys

## Тестирование

Проект содержит набор автоматических тестов для проверки работоспособности:

```bash
# Установка зависимостей для тестирования
pip install pytest pytest-mock

# Запуск тестов
pytest tests/

# Запуск тестов с подробным выводом
pytest -v tests/
```

Дополнительную информацию о тестировании можно найти в [руководстве для разработчиков](./docs/development.md).

## Лицензия

MIT © Andrej Spinej

## Вклад в проект

Вклады приветствуются! Пожалуйста, ознакомьтесь с [руководством по содействию](./docs/development.md).
