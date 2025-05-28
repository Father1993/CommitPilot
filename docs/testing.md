# Тестирование CommitPilot

В этом документе описано, как настроить и протестировать функциональность проекта CommitPilot.

## Настройка для тестирования

### 1. Установка зависимостей

```bash
pip install requests pytest pytest-mock pytest-cov
```

### 2. Настройка API токенов

Для полного тестирования вам потребуется API токен от Hugging Face или OpenAI:

1. Откройте файл `config.ini` в корне проекта
2. Добавьте ваш токен в соответствующее поле:

```ini
[DEFAULT]
# Выберите провайдера AI: huggingface или openai
api_provider = huggingface

# Вставьте ваш Hugging Face API токен
huggingface_token = ваш_токен_здесь

# Или вставьте ваш OpenAI API токен
openai_token = ваш_токен_здесь
```

## Запуск автоматических тестов

### Базовые тесты

```bash
# Запуск всех тестов
pytest tests/

# Запуск с подробным выводом
pytest -v tests/

# Запуск конкретного теста
pytest tests/test_auto_commit.py::test_get_git_diff
```

### Проверка покрытия кода

```bash
# Запуск тестов с отчетом о покрытии
pytest --cov=. tests/

# Генерация HTML-отчета о покрытии
pytest --cov=. --cov-report=html tests/
```

## Ручное тестирование

### Тестирование CLI

```bash
# Проверка версии
python auto_commit.py -v

# Проверка работоспособности (тестовый режим)
python auto_commit.py --test

# Только генерация сообщения без коммита
python auto_commit.py --get-message
```

### Тестирование Git-интеграции

Для проверки работы с Git:

1. Создайте тестовый репозиторий:

    ```bash
    mkdir test_repo
    cd test_repo
    git init
    echo "# Test" > README.md
    git add README.md
    git commit -m "Initial commit"
    ```

2. Настройте Git пользователя, если это еще не сделано:

    ```bash
    git config user.email "test@example.com"
    git config user.name "Test User"
    ```

3. Скопируйте Git hook:

    ```bash
    cp /путь/к/CommitPilot/prepare-commit-msg .git/hooks/
    chmod +x .git/hooks/prepare-commit-msg
    ```

4. Сделайте изменения и выполните коммит:

    ```bash
    echo "New line" >> README.md
    git add README.md
    git commit
    ```

5. Должно появиться сгенерированное сообщение коммита.

## Устранение проблем

### API токены не работают

1. Проверьте, правильно ли указан токен в `config.ini`
2. Убедитесь, что токен активен и не имеет ограничений
3. Проверьте подключение к интернету

### Тесты не находятся

1. Убедитесь, что вы запускаете команду из корня проекта
2. Проверьте, что структура директорий корректна

### Ошибки в тестах

1. Убедитесь, что все зависимости установлены
2. Проверьте версию Python (требуется 3.6+)
3. Проверьте наличие доступа к Git-командам
