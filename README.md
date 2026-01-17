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
# Опционально: кастомный API эндпоинт и модель
AITUNNEL_BASE_URL=https://api.aitunnel.ru/v1/
AITUNNEL_MODEL=gpt-4.1
```

Или используйте `config.ini`:

```ini
[DEFAULT]
api_provider = aitunnel
aitunnel_token = sk-aitunnel-ваш_токен_здесь
```

### Использование

**Основные команды:**
```bash
acommit              # Коммит с AI-сообщением и push в ветку по умолчанию
acommit-here         # Только коммит без push
acommit-dev          # Коммит и push в ветку dev
acommit-main         # Коммит и push в ветку main
acommit-master       # Коммит и push в ветку master
```

**Дополнительные опции:**
```bash
acommit -b branch    # Коммит в указанную ветку
acommit -m "msg"     # Свое сообщение (отключает AI)
acommit -p openai    # Выбор провайдера (aitunnel/openai/huggingface)
acommit --test       # Проверка настроек
acommit --get-message # Только генерация сообщения
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

1. **Анализ изменений**: Получение `git diff` и `git status`
2. **Генерация сообщения**: Отправка в AITUNNEL API (совместим с OpenAI)
3. **Создание коммита**: `git add .` и `git commit` с AI-сообщением
4. **Отправка**: `git push` в указанную ветку (опционально)

**Формат сообщений**: Conventional Commits (`тип(область): описание`)

## Примеры использования

**Локальный коммит:**
```bash
acommit-here  # Коммит без push
```

**Работа с ветками:**
```bash
acommit-dev   # Коммит в dev
acommit -b feature/new-feature  # В любую ветку
```

**Git hooks** (автогенерация при `git commit`):
```bash
cp prepare-commit-msg /путь/к/проекту/.git/hooks/
chmod +x /путь/к/проекту/.git/hooks/prepare-commit-msg
```

**Примеры сообщений:**
- `feat(auth): add OAuth authentication`
- `fix(api): resolve timeout issue`
- `docs: update installation guide`
- `refactor(core): optimize diff processing`

## Устранение проблем

**Проверка настроек:**
```bash
acommit --test
```

**Ошибка "API токен не настроен":**
- Проверьте `.env` файл с `AI_TUNNEL=sk-aitunnel-...`
- Или настройте `aitunnel_token` в `config.ini`

**Алиасы не работают:**
```bash
source ~/.bashrc  # или ~/.zshrc
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
| **AITUNNEL** (по умолчанию) | gpt-4.1 | `AI_TUNNEL` в `.env` |
| OpenAI | gpt-4o-mini | `openai_token` в config.ini |
| Hugging Face | Mixtral-8x7B | `huggingface_token` в config.ini |

