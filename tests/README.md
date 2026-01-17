# Тестирование CommitPilot

## Быстрый старт

```bash
pip install pytest pytest-mock python-dotenv openai
pytest tests/ -v
```

## Структура тестов

- `test_auto_commit.py` - тесты основного модуля
- `__init__.py` - инициализация пакета тестов

## Запуск тестов

```bash
# Все тесты
pytest tests/

# С подробным выводом
pytest tests/ -v

# Конкретный тест
pytest tests/test_auto_commit.py::test_get_git_diff
```

## Покрытие кода

```bash
pip install pytest-cov
pytest --cov=. --cov-report=term tests/
```

## Рекомендации

- Используйте моки для внешних зависимостей
- Тестируйте успешные сценарии и обработку ошибок
- Документируйте тестовые функции
