# CommitPilot 🤖

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

> Автоматизируйте создание коммитов с помощью AI, который понимает ваш код

## Что это такое?

Инструмент, который анализирует ваши изменения и генерирует осмысленные сообщения для коммитов в соответствии с [Conventional Commits](https://www.conventionalcommits.org/). Больше не нужно тратить время на придумывание хороших сообщений!

## Особенности

-   🚀 Автоматизация `git add`, `git commit` и `git push` одной командой
-   🧠 Поддержка нескольких AI провайдеров (Hugging Face и OpenAI)
-   🔄 Интеграция с Git hooks для автоматической генерации сообщений
-   🛠️ Простая настройка и использование

## Быстрый старт

### Установка

```bash
# Клонируйте репозиторий CommitPilot
git clone https://github.com/yourusername/CommitPilot.git
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
-   Установленная библиотека `requests`
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

## Конфиденциальность

Для защиты вашего API токена рекомендуется добавить `config.ini` в `.gitignore`:

```bash
echo "config.ini" >> .gitignore
```

## Лицензия

MIT © Andrej Spinej

## Вклад в проект

Вклады приветствуются! Пожалуйста, ознакомьтесь с [руководством по содействию](./docs/development.md).
