"""
Tests for CommitPilot auto_commit module.
"""
import os
import sys
import pytest
import configparser
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

# Mock load_dotenv before importing auto_commit to prevent loading real .env
with patch('dotenv.load_dotenv'):
    # Add parent directory to sys.path for importing tested modules
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import auto_commit


@pytest.fixture
def mock_config_file(tmp_path):
    """Create temporary configuration file for testing."""
    config_path = tmp_path / "config.ini"
    config_content = """[DEFAULT]
api_provider = aitunnel
aitunnel_token = test_token
aitunnel_base_url = https://api.aitunnel.ru/v1/
aitunnel_model = gpt-4.1
huggingface_token = test_token
openai_token = 
branch = master
max_diff_size = 7000
"""
    config_path.write_text(config_content)
    return config_path


def test_setup_config_existing_file(mock_config_file):
    """Test setup_config function when config file exists."""
    with patch('auto_commit.CONFIG_FILE', mock_config_file), \
         patch('auto_commit.load_dotenv'), \
         patch.dict(os.environ, {}, clear=True):
        # Reset cache and dotenv flag before test
        auto_commit._config_cache = None
        auto_commit._config_file_mtime = None
        if hasattr(auto_commit.setup_config, '_env_loaded'):
            delattr(auto_commit.setup_config, '_env_loaded')
        
        config = auto_commit.setup_config()
        assert config['DEFAULT']['api_provider'] == 'aitunnel'
        assert config['DEFAULT']['aitunnel_token'] == 'test_token'
        assert config['DEFAULT']['branch'] == 'master'
        assert config['DEFAULT']['max_diff_size'] == '7000'
        
        # Check caching - second call should use cache
        config2 = auto_commit.setup_config()
        assert config is config2  # Should be same object from cache


def test_setup_config_new_file(tmp_path):
    """Test setup_config function when config file doesn't exist."""
    mock_config = tmp_path / "new_config.ini"
    
    with patch('auto_commit.CONFIG_FILE', mock_config), \
         patch('auto_commit.load_dotenv'), \
         patch.dict(os.environ, {}, clear=True):
        # Reset cache and dotenv flag before test
        auto_commit._config_cache = None
        auto_commit._config_file_mtime = None
        if hasattr(auto_commit.setup_config, '_env_loaded'):
            delattr(auto_commit.setup_config, '_env_loaded')
        
        config = auto_commit.setup_config()
        
        # Check that file was created
        assert mock_config.exists()
        
        # Check default values
        assert config['DEFAULT']['api_provider'] == 'aitunnel'
        assert config['DEFAULT']['branch'] == 'master'
        assert config['DEFAULT']['max_diff_size'] == '7000'


def test_setup_config_env_variables(tmp_path):
    """Test that environment variables override config values."""
    mock_config = tmp_path / "test_config.ini"
    
    with patch('auto_commit.CONFIG_FILE', mock_config), \
         patch('auto_commit.load_dotenv'), \
         patch.dict(os.environ, {
             'AI_TUNNEL': 'env_token',
             'AITUNNEL_BASE_URL': 'https://custom.api.ru/v1/',
             'AITUNNEL_MODEL': 'custom-model'
         }, clear=True):
        auto_commit._config_cache = None
        auto_commit._config_file_mtime = None
        if hasattr(auto_commit.setup_config, '_env_loaded'):
            delattr(auto_commit.setup_config, '_env_loaded')
        
        # Create a real config file for this test
        mock_config.write_text("""[DEFAULT]
api_provider = aitunnel
aitunnel_token = 
aitunnel_base_url = https://api.aitunnel.ru/v1/
aitunnel_model = gpt-4.1
""")
        
        config = auto_commit.setup_config()
        assert config['DEFAULT']['aitunnel_token'] == 'env_token'
        assert config['DEFAULT']['aitunnel_base_url'] == 'https://custom.api.ru/v1/'
        assert config['DEFAULT']['aitunnel_model'] == 'custom-model'


def test_get_git_diff():
    """Test git diff retrieval using mocks."""
    expected_diff = "diff --git a/file.txt b/file.txt\nindex 123..456 789\n--- a/file.txt\n+++ b/file.txt\n@@ -1,1 +1,2 @@\n-old line\n+new line"

    # Mock subprocess.run to return expected diff
    with patch('subprocess.run') as mock_run:
        mock_process = mock_run.return_value
        mock_process.stdout = expected_diff
        mock_process.returncode = 0

        result = auto_commit.get_git_diff()

        # Check that function was called with correct parameters
        mock_run.assert_called_with(['git', 'diff', '--cached'], capture_output=True, encoding='utf-8')
        
        assert result == expected_diff


def test_get_git_diff_fallback():
    """Test git diff fallback to unstaged changes."""
    expected_diff = "diff --git a/file.txt b/file.txt\n+new line"

    with patch('subprocess.run') as mock_run:
        # First call returns empty (no staged changes)
        mock_process1 = MagicMock()
        mock_process1.stdout = ""
        mock_process1.returncode = 0
        
        # Second call returns diff (unstaged changes)
        mock_process2 = MagicMock()
        mock_process2.stdout = expected_diff
        mock_process2.returncode = 0
        
        mock_run.side_effect = [mock_process1, mock_process2]

        result = auto_commit.get_git_diff()
        
        assert result == expected_diff
        assert mock_run.call_count == 2


def test_get_git_status():
    """Test git status retrieval using mocks."""
    expected_status = "M file.txt\n?? new_file.txt"

    # Mock run to return expected status
    with patch('subprocess.run') as mock_run:
        mock_process = mock_run.return_value
        mock_process.stdout = expected_status
        mock_process.returncode = 0

        result = auto_commit.get_git_status()

        # Check that function was called with correct parameters
        mock_run.assert_called_with(['git', 'status', '--porcelain'], capture_output=True, encoding='utf-8')
        
        assert result == expected_status


def test_generate_commit_message_with_huggingface():
    """Test commit message generation using Hugging Face API."""
    mock_diff = "diff --git a/file.txt b/file.txt\n+new feature"
    mock_status = "M file.txt"
    mock_config = configparser.ConfigParser()
    mock_config['DEFAULT'] = {
        'huggingface_token': 'test_token',
        'max_diff_size': '7000'
    }
    
    # Mock requests.post to return expected API response
    expected_response = [{'generated_text': 'feat(core): add new feature'}]
    with patch('requests.post') as mock_post:
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status = MagicMock()
        
        result = auto_commit.generate_commit_message_with_huggingface(mock_diff, mock_status, mock_config)
        
        # Check that request was sent with correct parameters
        mock_post.assert_called_once()
        
        assert result == 'feat(core): add new feature'


def test_git_add_all_success():
    """Test successful file staging."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        
        auto_commit.git_add_all()
        
        # Check that correct command was called
        mock_run.assert_called_with(['git', 'add', '.'], check=True, capture_output=True)


def test_git_add_all_failure():
    """Test error handling when staging files fails."""
    with patch('subprocess.run') as mock_run, \
         patch('sys.exit') as mock_exit:
        mock_run.side_effect = Exception("Test error")
        
        auto_commit.git_add_all()
        
        # Check that program exited with error
        mock_exit.assert_called_once_with(1)


def test_git_commit_success():
    """Test successful commit creation."""
    with patch('subprocess.run') as mock_run:
        mock_process = mock_run.return_value
        mock_process.returncode = 0
        
        result = auto_commit.git_commit("test commit message")
        
        # Check that correct command was called
        mock_run.assert_called_with(['git', 'commit', '-m', 'test commit message'], 
                                   capture_output=True, encoding='utf-8')
        
        # Check function result
        assert result is True


def test_git_commit_failure():
    """Test error handling when commit creation fails."""
    with patch('subprocess.run') as mock_run:
        mock_process = mock_run.return_value
        mock_process.returncode = 1
        mock_process.stderr = "Test error"
        
        result = auto_commit.git_commit("test commit message")
        
        # Check function result
        assert result is False


def test_git_push_success():
    """Test successful push."""
    with patch('subprocess.run') as mock_run:
        mock_process = mock_run.return_value
        mock_process.returncode = 0
        
        result = auto_commit.git_push("master")
        
        # Check that correct command was called
        mock_run.assert_called_with(['git', 'push', 'origin', 'master'], 
                                   capture_output=True, encoding='utf-8')
        
        assert result is True


def test_git_push_failure():
    """Test error handling when push fails."""
    with patch('subprocess.run') as mock_run:
        mock_process = mock_run.return_value
        mock_process.returncode = 1
        mock_process.stderr = "Push failed"
        
        result = auto_commit.git_push("master")
        
        assert result is False


def test_generate_message_only_no_changes():
    """Test message generation when there are no changes."""
    mock_config = configparser.ConfigParser()
    mock_config['DEFAULT'] = {
        'api_provider': 'aitunnel',
        'aitunnel_token': '',
    }
    
    with patch('auto_commit.get_git_status', return_value=""):
        result = auto_commit.generate_message_only(mock_config)
        
        # Check that default message is returned
        assert result == auto_commit.DEFAULT_COMMIT_MESSAGE


def test_generate_message_only_empty_diff():
    """Test message generation when diff is empty."""
    mock_config = configparser.ConfigParser()
    mock_config['DEFAULT'] = {
        'api_provider': 'aitunnel',
        'aitunnel_token': '',
    }
    
    with patch('auto_commit.get_git_status', return_value="M file.txt"), \
         patch('auto_commit.get_git_diff', return_value=""):
        result = auto_commit.generate_message_only(mock_config)
        
        assert result == auto_commit.DEFAULT_COMMIT_MESSAGE


def test_config_file_path():
    """Test that CONFIG_FILE points to program directory."""
    config_file = auto_commit.CONFIG_FILE
    assert config_file.name == 'config.ini'
    # Should be in the same directory as auto_commit.py
    assert config_file.parent == Path(__file__).parent.parent


def test_default_commit_message():
    """Test default commit message constant."""
    assert auto_commit.DEFAULT_COMMIT_MESSAGE == "chore: automatic changes commit"


def test_version():
    """Test version constant."""
    assert auto_commit.VERSION == "1.0.0"
