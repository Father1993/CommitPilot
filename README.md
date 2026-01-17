# CommitPilot 🤖

Автоматизация git-коммитов с AI-генерацией сообщений в формате Conventional Commits.

## Быстрый старт

### Установка

```bash
git clone https://github.com/Father1993/CommitPilot.git
cd CommitPilot
bash install.sh
source ~/.bashrc  # или ~/.zshrc
```

### Настройка

Создайте файл `.env` в корне проекта:

```env
AI_TUNNEL=sk-aitunnel-ваш_токен_здесь
```

Или используйте `config.ini`:

```ini
[DEFAULT]
api_provider = aitunnel
aitunnel_token = sk-aitunnel-ваш_токен_здесь
```

### Использование

```bash
acommit              # Коммит с AI-сообщением и push
acommit-here         # Только коммит без push
acommit -b dev       # Коммит в ветку dev
acommit -m "msg"     # Свое сообщение
acommit -p openai    # Выбор провайдера (aitunnel/openai/huggingface)
```

## Особенности

- 🚀 **Автоматизация**: `git add`, `git commit`, `git push` одной командой
- 🧠 **AI провайдеры**: AITUNNEL (по умолчанию), OpenAI, Hugging Face
- 🔄 **Git hooks**: Автоматическая генерация при `git commit`
- 💡 **Conventional Commits**: Сообщения в стандартном формате
- 🔒 **Безопасность**: Поддержка `.env` для токенов

## Требования

- Python 3.7+
- Git
- Зависимости: `requests`, `python-dotenv`, `openai`
- API токен: [AITUNNEL](https://aitunnel.ru/) (рекомендуется), [OpenAI](https://platform.openai.com/api-keys) или [Hugging Face](https://huggingface.co/settings/tokens)

## Как это работает

1. Анализ изменений через `git diff`
2. Отправка в AI API для генерации сообщения
3. Создание коммита с сгенерированным сообщением
4. Отправка в удаленный репозиторий (опционально)

## Использование в других проектах

**Глобальные алиасы** (работают из любой директории):
```bash
cd /путь/к/проекту
acommit
```

**Git hook** (автогенерация при `git commit`):
```bash
cp /путь/к/CommitPilot/prepare-commit-msg /путь/к/проекту/.git/hooks/
chmod +x /путь/к/проекту/.git/hooks/prepare-commit-msg
```

## Тестирование

```bash
pip install pytest pytest-mock python-dotenv openai
pytest tests/ -v
```

## Безопасность

- Файлы `.env` и `config.ini` в `.gitignore`
- Не публикуйте токены в публичных репозиториях
- Используйте `.env` для локальной разработки

## Лицензия

MIT © Andrej Spinej

## Архитектура

```
CommitPilot/
├── auto_commit.py          # Основной модуль
├── aitunnel_support.py     # AITUNNEL API
├── openai_support.py       # OpenAI API
├── prepare-commit-msg       # Git hook
└── install.sh              # Установщик
```

## API Провайдеры

| Провайдер | Модель | Токен |
|-----------|--------|-------|
| **AITUNNEL** (по умолчанию) | deepseek-r1 | `AI_TUNNEL` в `.env` |
| OpenAI | gpt-4o-mini | `openai_token` в config.ini |
| Hugging Face | Mixtral-8x7B | `huggingface_token` в config.ini |

## Примеры сообщений

- `feat(auth): add OAuth authentication`
- `fix(api): resolve timeout issue`
- `docs: update installation guide`
- `refactor(core): optimize diff processing`
