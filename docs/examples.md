# Примеры использования

> Практические примеры работы с CommitPilot

## Основные команды

### Стандартный рабочий процесс

```bash
# Внесите изменения в проект

# Создайте коммит с AI-генерацией сообщения и отправьте изменения
acommit

# Проверьте историю коммитов
git log --oneline
```

### Локальный коммит без push

```bash
# Создание коммита без отправки в удаленный репозиторий
acommit-here
# или
acommit -c
```

### Работа с разными ветками

```bash
# Отправка в ветку dev
acommit-dev
# или
acommit -b dev

# Отправка в ветку feature
acommit -b feature/new-feature
```

### Пользовательское сообщение

```bash
# Создание коммита с вашим сообщением
acommit -m "feat: добавлена функция авторизации"
```

## Сценарии использования

### Работа в проекте CommitPilot

```bash
# Клонирование репозитория
git clone https://github.com/yourusername/CommitPilot.git
cd CommitPilot

# Установка
bash install.sh
source ~/.bashrc

# Внесение изменений
echo "// Новая функция" >> auto_commit.py

# Создание коммита
acommit-here
```

### Использование в другом проекте

```bash
# Клонирование CommitPilot (если еще не установлен)
git clone https://github.com/yourusername/CommitPilot.git
cd CommitPilot
bash install.sh
source ~/.bashrc

# Переход в другой проект
cd /путь/к/другому/проекту

# Использование в другом проекте
acommit
```

### Установка Git hook в другом проекте

```bash
# Копирование Git hook в другой проект
COMMITPILOT_DIR=/путь/к/CommitPilot
TARGET_PROJECT=/путь/к/проекту

# Копируем hook
mkdir -p $TARGET_PROJECT/.git/hooks
cp $COMMITPILOT_DIR/prepare-commit-msg $TARGET_PROJECT/.git/hooks/
chmod +x $TARGET_PROJECT/.git/hooks/prepare-commit-msg

# Добавление переменной окружения для поиска скрипта
echo "export COMMITPILOT_PATH=$COMMITPILOT_DIR" >> ~/.bashrc
source ~/.bashrc

# Теперь можно использовать стандартную команду git commit
cd $TARGET_PROJECT
git add .
git commit  # Сообщение будет сгенерировано автоматически
```

### Работа с Git hooks

Если вы установили Git hooks, можно использовать обычные Git команды:

```bash
# Добавить изменения
git add .

# Создать коммит (сообщение будет сгенерировано автоматически)
git commit

# Отправить изменения
git push origin main
```

### Выбор провайдера AI

```bash
# Использование Hugging Face
acommit -p huggingface

# Использование OpenAI
acommit -p openai
```

## Примеры сгенерированных сообщений

| Тип изменений      | Пример сообщения                                          |
| ------------------ | --------------------------------------------------------- |
| Новая функция      | `feat(auth): добавлена система авторизации через OAuth`   |
| Исправление ошибки | `fix(api): исправлен неверный формат ответа в /users`     |
| Рефакторинг        | `refactor(core): оптимизирована обработка больших файлов` |
| Документация       | `docs: обновлена документация по установке`               |
| Стилевые изменения | `style: унифицирован формат кода согласно ESLint`         |

## Советы

-   **Делайте атомарные коммиты**: каждый коммит должен содержать логически завершенное изменение
-   **Используйте правильные ветки**: выбирайте подходящую ветку для ваших изменений
-   **Проверяйте сгенерированные сообщения**: AI может ошибаться, проверяйте сообщения перед отправкой
-   **Защитите API токены**: добавьте `config.ini` в `.gitignore`
-   **Настройте переменную окружения**: установите `COMMITPILOT_PATH` для использования в других проектах

## Шпаргалка

```
acommit           # Стандартный коммит с отправкой
acommit-here      # Только коммит без push
acommit-dev       # Коммит в ветку dev
acommit-main      # Коммит в ветку main
acommit -b NAME   # Коммит в указанную ветку
acommit -m "MSG"  # Коммит с указанным сообщением
acommit -p openai # Использовать OpenAI вместо Hugging Face
```
