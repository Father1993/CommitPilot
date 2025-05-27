# Установка и настройка

> Простое руководство по установке CommitPilot

## Содержание

-   [Быстрая установка](#быстрая-установка)
-   [Установка вручную](#установка-вручную)
-   [Настройка API ключей](#настройка-api-ключей)
-   [Алиасы](#алиасы)
-   [Установка в других проектах](#установка-в-других-проектах)
-   [Устранение проблем](#устранение-проблем)

## Быстрая установка

Самый простой способ — использовать наш установочный скрипт:

```bash
# Клонируйте репозиторий CommitPilot
git clone https://github.com/yourusername/CommitPilot.git
cd CommitPilot

# Запустите установочный скрипт
bash install.sh

# Перезагрузите ваш shell для активации алиасов
source ~/.bashrc   # или ~/.zshrc
```

Скрипт автоматически:

-   Проверит необходимые зависимости
-   Установит библиотеку requests
-   Настроит Git hooks (если проект является git-репозиторием)
-   Создаст удобные алиасы
-   Создаст файл конфигурации `config.ini`

## Установка вручную

Если вы предпочитаете ручную установку:

1. Клонируйте репозиторий:

    ```bash
    git clone https://github.com/yourusername/CommitPilot.git
    cd CommitPilot
    ```

2. Установите зависимости:

    ```bash
    pip install requests
    ```

3. Сделайте скрипты исполняемыми:

    ```bash
    chmod +x auto_commit.py
    chmod +x prepare-commit-msg
    ```

4. Установите Git hooks (если нужно):

    ```bash
    mkdir -p .git/hooks
    cp prepare-commit-msg .git/hooks/
    chmod +x .git/hooks/prepare-commit-msg
    ```

5. Добавьте алиасы в ваш файл конфигурации оболочки (~/.bashrc или ~/.zshrc):

    ```bash
    INSTALL_DIR=$(pwd)
    echo "alias acommit=\"python $INSTALL_DIR/auto_commit.py\"" >> ~/.bashrc
    echo "alias acommit-dev=\"python $INSTALL_DIR/auto_commit.py -b dev\"" >> ~/.bashrc
    echo "alias acommit-main=\"python $INSTALL_DIR/auto_commit.py -b main\"" >> ~/.bashrc
    echo "alias acommit-master=\"python $INSTALL_DIR/auto_commit.py -b master\"" >> ~/.bashrc
    echo "alias acommit-here=\"python $INSTALL_DIR/auto_commit.py -c\"" >> ~/.bashrc
    ```

6. Создайте файл конфигурации `config.ini`:
    ```bash
    cat > config.ini << EOL
    ```

# CommitPilot - Конфигурация

# Для настройки отредактируйте этот файл вручную

[DEFAULT]

# Выберите провайдера AI: huggingface или openai

api_provider = huggingface

# Вставьте ваш Hugging Face API токен

huggingface_token = YOUR_TOKEN_HERE

# Вставьте ваш OpenAI API токен (если используете OpenAI)

openai_token =

# Ветка по умолчанию для git push

branch = dev

# Максимальный размер diff для отправки в AI API

max_diff_size = 5000
EOL
```

## Настройка API ключей

После установки вам нужно вручную отредактировать файл `config.ini`:

### Получение Hugging Face токена (рекомендуется)

1. Зарегистрируйтесь на [huggingface.co](https://huggingface.co/)
2. Перейдите в [настройки токенов](https://huggingface.co/settings/tokens)
3. Создайте новый токен с правами чтения (READ)
4. Вставьте токен в поле `huggingface_token` в файле `config.ini`

### Получение OpenAI токена (альтернативно)

1. Зарегистрируйтесь на [platform.openai.com](https://platform.openai.com/)
2. Создайте API ключ в разделе [API keys](https://platform.openai.com/api-keys)
3. Вставьте ключ в поле `openai_token` в файле `config.ini`
4. Измените значение `api_provider` на `openai`

## Алиасы

При установке создаются следующие алиасы для удобства:

| Алиас            | Действие                                        |
| ---------------- | ----------------------------------------------- |
| `acommit`        | Создать коммит и отправить в ветку по умолчанию |
| `acommit-dev`    | Создать коммит и отправить в ветку dev          |
| `acommit-main`   | Создать коммит и отправить в ветку main         |
| `acommit-master` | Создать коммит и отправить в ветку master       |
| `acommit-here`   | Создать коммит без push                         |

## Установка в других проектах

Вы можете использовать CommitPilot в других проектах двумя способами:

### 1. Глобальные алиасы

После установки CommitPilot алиасы будут работать из любой директории. Просто перейдите в другой проект и используйте команды:

```bash
cd /путь/к/другому/проекту
acommit
```

### 2. Установка Git hook в другом проекте

Для автоматической генерации сообщений при использовании `git commit` в другом проекте:

```bash
# Установка в конкретный проект
COMMITPILOT_DIR=/путь/к/CommitPilot
TARGET_PROJECT=/путь/к/проекту

# Копируем hook
mkdir -p $TARGET_PROJECT/.git/hooks
cp $COMMITPILOT_DIR/prepare-commit-msg $TARGET_PROJECT/.git/hooks/
chmod +x $TARGET_PROJECT/.git/hooks/prepare-commit-msg

# Опционально: установка переменной окружения для поиска основного скрипта
echo "export COMMITPILOT_PATH=$COMMITPILOT_DIR" >> ~/.bashrc
source ~/.bashrc
```

## Устранение проблем

### Ошибка: "ModuleNotFoundError: No module named 'requests'"

Установите библиотеку requests:

```bash
pip install requests
```

### Git hook не работает

Убедитесь, что hook правильно установлен и имеет права на выполнение:

```bash
ls -la .git/hooks/prepare-commit-msg
chmod +x .git/hooks/prepare-commit-msg
```

### Ошибка доступа к API

Проверьте ваш API ключ в файле `config.ini` и убедитесь, что он действительный.

### Команда acommit не найдена

Возможно, алиасы не были активированы. Выполните:

```bash
source ~/.bashrc   # или ~/.zshrc
```

Или перезапустите терминал.

### Скрипт не находит путь к основному файлу

Установите переменную окружения COMMITPILOT_PATH:

```bash
echo "export COMMITPILOT_PATH=/полный/путь/к/директории/CommitPilot" >> ~/.bashrc
source ~/.bashrc
```
