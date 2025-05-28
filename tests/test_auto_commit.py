import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

# Добавляем родительскую директорию в sys.path для импорта тестируемых модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import auto_commit

@pytest.fixture
def mock_config_file(tmp_path):
    """Создает временный конфигурационный файл для тестирования."""
    config_path = tmp_path / "config.ini"
    config_content = """
[DEFAULT]
api_provider = huggingface
huggingface_token = test_token
openai_token = 
branch = dev
max_diff_size = 5000
"""
    config_path.write_text(config_content)
    return config_path

def test_setup_config_existing_file(mock_config_file):
    """Тестирует функцию setup_config когда файл конфигурации существует."""
    with patch('auto_commit.CONFIG_FILE', mock_config_file):
        config = auto_commit.setup_config()
        assert config['DEFAULT']['api_provider'] == 'huggingface'
        assert config['DEFAULT']['huggingface_token'] == 'test_token'
        assert config['DEFAULT']['branch'] == 'dev'

def test_setup_config_new_file():
    """Тестирует функцию setup_config когда файл конфигурации не существует."""
    mock_config = Path('nonexistent_config.ini')
    
    with patch('auto_commit.CONFIG_FILE', mock_config), \
         patch('os.makedirs') as mock_makedirs, \
         patch('builtins.open', mock_open()) as m:
        
        config = auto_commit.setup_config()
        
        # Проверяем, что были попытки создать директорию и файл
        mock_makedirs.assert_called_once()
        m.assert_called_once()
        
        # Проверяем значения по умолчанию
        assert config['DEFAULT']['api_provider'] == 'huggingface'
        assert config['DEFAULT']['branch'] == 'main'
        assert config['DEFAULT']['max_diff_size'] == '5000'

def test_get_git_diff():
    """Тестирует получение git diff с помощью моков."""
    expected_diff = "diff --git a/file.txt b/file.txt\nindex 123..456 789\n--- a/file.txt\n+++ b/file.txt\n@@ -1,1 +1,2 @@\n-old line\n+new line"

    # Мокам subprocess.run для возврата ожидаемого diff
    with patch('subprocess.run') as mock_run:
       mock_process = mock_run.return_value
       mock_process.stdout = expected_diff
       mock_process.returncode = 0

       result = auto_commit.get_git_diff()

       # проверим, что функция вызвалась с правильными параметрами
       mock_run.assert_called_with(['git', 'diff', '--cached'], capture_output=True, encoding='utf-8')
      
       assert result == expected_diff

def test_get_git_status():
    """Тестирует получение git status с помощью моков."""
    expected_status = "M file.txt\n?? new_file.txt"

    # Мокаем run для возврата ожидаемого статуса
    with patch('subprocess.run') as mock_run:
       mock_process = mock_run.return_value
       mock_process.stdout = expected_status
       mock_process.returncode = 0

       result = auto_commit.get_git_status()

       # Проверяем, что функция вызывалась с правильными параметрами
       mock_run.assert_called_with(['git', 'status', '--porcelain'], capture_output=True, encoding='utf-8')
      
       assert result == expected_status

def test_generate_commit_message_with_huggingface():
    """Тестирует генерацию сообщения коммита с использованием Hugging Face API."""
    mock_diff = "diff --git a/file.txt b/file.txt\n+new feature"
    mock_status = "M file.txt"
    mock_config = {
        'DEFAULT': {
            'huggingface_token': 'test_token',
            'max_diff_size': '5000'
        }
    }
    
    # Мокаем configparser.ConfigParser
    mock_parser = patch.object(auto_commit.configparser, 'ConfigParser')
    mock_parser.start()
    
    # Мокаем requests.post для возврата ожидаемого ответа от API
    expected_response = {'generated_text': 'feat(core): add new feature'}
    with patch('requests.post') as mock_post:
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = [expected_response]
        
        result = auto_commit.generate_commit_message_with_huggingface(mock_diff, mock_status, mock_config)
        
        # Проверяем, что запрос был отправлен с правильными параметрами
        mock_post.assert_called_once()
        
        assert result == 'feat(core): add new feature'
    
    mock_parser.stop()

def test_git_add_all_success():
    """Тестирует успешное добавление файлов в индекс."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        
        auto_commit.git_add_all()
        
        # Проверяем, что была вызвана правильная команда
        mock_run.assert_called_with(['git', 'add', '.'], check=True)

def test_git_add_all_failure():
    """Тестирует обработку ошибки при добавлении файлов в индекс."""
    with patch('subprocess.run') as mock_run, \
         patch('sys.exit') as mock_exit:
        mock_run.side_effect = Exception("Test error")
        
        auto_commit.git_add_all()
        
        # Проверяем, что программа завершилась с ошибкой
        mock_exit.assert_called_once_with(1)

def test_git_commit_success():
    """Тестирует успешное создание коммита."""
    with patch('subprocess.run') as mock_run:
        mock_process = mock_run.return_value
        mock_process.returncode = 0
        
        result = auto_commit.git_commit("test commit message")
        
        # Проверяем, что была вызвана правильная команда
        mock_run.assert_called_with(['git', 'commit', '-m', 'test commit message'], 
                                   capture_output=True, encoding='utf-8')
        
        # Проверяем результат функции
        assert result is True

def test_git_commit_failure():
    """Тестирует обработку ошибки при создании коммита."""
    with patch('subprocess.run') as mock_run:
        mock_process = mock_run.return_value
        mock_process.returncode = 1
        mock_process.stderr = "Test error"
        
        result = auto_commit.git_commit("test commit message")
        
        # Проверяем результат функции
        assert result is False

def test_generate_message_only_no_changes():
    """Тестирует генерацию сообщения когда нет изменений."""
    with patch('auto_commit.get_git_status', return_value=""):
        result = auto_commit.generate_message_only({})
        
        # Проверяем, что возвращается сообщение по умолчанию
        assert result == auto_commit.DEFAULT_COMMIT_MESSAGE