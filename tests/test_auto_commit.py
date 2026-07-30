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
api_provider = openai_compatible
api_token = test_token
api_base_url = https://api.openai.com/v1
api_model = gpt-4.1
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
        auto_commit._config_env_mtime = None
        auto_commit._env_loaded = False
        
        config = auto_commit.setup_config()
        assert config['DEFAULT']['api_provider'] == 'openai_compatible'
        assert config['DEFAULT']['api_token'] == 'test_token'
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
        auto_commit._config_env_mtime = None
        auto_commit._env_loaded = False
        
        config = auto_commit.setup_config()
        
        # Check that file was created
        assert mock_config.exists()
        
        # Check default values
        assert config['DEFAULT']['api_provider'] == 'openai_compatible'
        assert config['DEFAULT']['branch'] == 'master'
        assert config['DEFAULT']['max_diff_size'] == '7000'


def test_setup_config_env_variables(tmp_path):
    """Test that environment variables override config values."""
    mock_config = tmp_path / "test_config.ini"
    
    with patch('auto_commit.CONFIG_FILE', mock_config), \
         patch('auto_commit.load_dotenv'), \
         patch.dict(os.environ, {
             'API_TOKEN': 'env_token',
             'API_BASE_URL': 'https://custom.api.ru/v1/',
             'API_MODEL': 'custom-model'
         }, clear=True):
        auto_commit._config_cache = None
        auto_commit._config_file_mtime = None
        auto_commit._config_env_mtime = None
        auto_commit._env_loaded = False
        
        # Create a real config file for this test
        mock_config.write_text("""[DEFAULT]
api_provider = openai_compatible
api_token = 
api_base_url = https://api.openai.com/v1
api_model = gpt-4.1
""")
        
        config = auto_commit.setup_config()
        assert config['DEFAULT']['api_token'] == 'env_token'
        assert config['DEFAULT']['api_base_url'] == 'https://custom.api.ru/v1/'
        assert config['DEFAULT']['api_model'] == 'custom-model'


def test_setup_config_legacy_aitunnel_keys(tmp_path):
    """Legacy aitunnel_* keys and provider alias still work."""
    mock_config = tmp_path / "legacy.ini"
    mock_config.write_text("""[DEFAULT]
api_provider = aitunnel
aitunnel_token = legacy_token
aitunnel_base_url = https://legacy.example/v1/
aitunnel_model = legacy-model
""")
    with patch('auto_commit.CONFIG_FILE', mock_config), \
         patch('auto_commit.load_dotenv'), \
         patch.dict(os.environ, {}, clear=True):
        auto_commit._config_cache = None
        auto_commit._config_file_mtime = None
        auto_commit._config_env_mtime = None
        auto_commit._env_loaded = False

        config = auto_commit.setup_config()
        assert config['DEFAULT']['api_provider'] == 'openai_compatible'
        assert config['DEFAULT']['api_token'] == 'legacy_token'
        assert config['DEFAULT']['api_base_url'] == 'https://legacy.example/v1/'
        assert config['DEFAULT']['api_model'] == 'legacy-model'


def test_normalize_provider_alias():
    assert auto_commit.normalize_provider('aitunnel') == 'openai_compatible'
    assert auto_commit.normalize_provider('openai_compatible') == 'openai_compatible'


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

        mock_run.assert_called_with(['git', 'add', '.'], capture_output=True, encoding='utf-8', check=True)


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


def test_git_commit_with_body():
    """Subject + body becomes two -m arguments."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        msg = "feat(api): add rate limit\n\nProtect burst traffic on login."
        assert auto_commit.git_commit(msg) is True
        mock_run.assert_called_with(
            [
                'git', 'commit',
                '-m', 'feat(api): add rate limit',
                '-m', 'Protect burst traffic on login.',
            ],
            capture_output=True,
            encoding='utf-8',
        )


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
        mock_run.assert_called_with(['git', 'push', '-u', 'origin', 'master'], 
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
        'api_provider': 'openai_compatible',
        'api_token': '',
    }
    
    with patch('auto_commit.get_git_status', return_value=""):
        result = auto_commit.generate_message_only(mock_config)
        
        # Check that default message is returned
        assert result == auto_commit.DEFAULT_COMMIT_MESSAGE


def test_generate_message_only_empty_diff():
    """Test message generation when diff is empty."""
    mock_config = configparser.ConfigParser()
    mock_config['DEFAULT'] = {
        'api_provider': 'openai_compatible',
        'api_token': '',
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
    assert auto_commit.VERSION == "1.1.0"


def test_get_current_branch():
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.stdout = "dev\n"
        mock_run.return_value.returncode = 0
        assert auto_commit.get_current_branch() == "dev"


def test_get_current_branch_detached():
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.stdout = "\n"
        mock_run.return_value.returncode = 0
        assert auto_commit.get_current_branch() is None


def test_resolve_push_branch_override():
    assert auto_commit.resolve_push_branch("feature") == "feature"


def test_resolve_push_branch_current():
    with patch('auto_commit.get_current_branch', return_value="fix-auth"):
        assert auto_commit.resolve_push_branch(None) == "fix-auth"


def test_resolve_push_branch_detached():
    with patch('auto_commit.get_current_branch', return_value=None), \
         patch('builtins.print') as mock_print:
        assert auto_commit.resolve_push_branch(None) is None
        mock_print.assert_called()


def test_github_repo_url_https():
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "https://github.com/Father1993/mk-27.ru.git\n"
        assert auto_commit.github_repo_url() == "https://github.com/Father1993/mk-27.ru"


def test_github_repo_url_ssh():
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "git@github.com:Father1993/mk-27.ru.git\n"
        assert auto_commit.github_repo_url() == "https://github.com/Father1993/mk-27.ru"


def test_github_repo_url_ssh_scheme():
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "ssh://git@github.com/Father1993/mk-27.ru.git\n"
        assert auto_commit.github_repo_url() == "https://github.com/Father1993/mk-27.ru"


def test_github_repo_url_non_github():
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "git@gitlab.com:org/repo.git\n"
        assert auto_commit.github_repo_url() is None


def test_resolve_pr_base_feature_to_dev():
    with patch('auto_commit.get_default_branch', return_value="master"), \
         patch('auto_commit.remote_branch_exists', return_value=True):
        assert auto_commit.resolve_pr_base("fix-auth") == "dev"


def test_resolve_pr_base_dev_to_default():
    with patch('auto_commit.get_default_branch', return_value="master"), \
         patch('auto_commit.remote_branch_exists', return_value=False):
        assert auto_commit.resolve_pr_base("dev") == "master"


def test_resolve_pr_base_head_is_default():
    with patch('auto_commit.get_default_branch', return_value="main"):
        assert auto_commit.resolve_pr_base("main") is None


def test_resolve_pr_base_head_is_other_production():
    """main/master never get a deploy link, even if default differs."""
    with patch('auto_commit.get_default_branch', return_value="main"), \
         patch('auto_commit.remote_branch_exists', return_value=True):
        assert auto_commit.resolve_pr_base("master") is None


def test_resolve_pr_base_no_dev_uses_default():
    with patch('auto_commit.get_default_branch', return_value="main"), \
         patch('auto_commit.remote_branch_exists', return_value=False):
        assert auto_commit.resolve_pr_base("feature-x") == "main"


def test_print_deploy_link_compare_url():
    with patch('auto_commit.resolve_pr_base', return_value="dev"), \
         patch('auto_commit.github_repo_url', return_value="https://github.com/Father1993/mk-27.ru"), \
         patch('auto_commit._find_open_pr_url', return_value=None), \
         patch('builtins.print') as mock_print:
        auto_commit.print_deploy_link("fix-auth")
        mock_print.assert_called_with(
            "🔗 https://github.com/Father1993/mk-27.ru/compare/dev...fix-auth?expand=1"
        )


def test_print_deploy_link_existing_pr():
    with patch('auto_commit.resolve_pr_base', return_value="dev"), \
         patch('auto_commit.github_repo_url', return_value="https://github.com/Father1993/mk-27.ru"), \
         patch('auto_commit._find_open_pr_url', return_value="https://github.com/Father1993/mk-27.ru/pull/308"), \
         patch('builtins.print') as mock_print:
        auto_commit.print_deploy_link("fix-auth")
        mock_print.assert_called_with("🔗 https://github.com/Father1993/mk-27.ru/pull/308")


def test_print_deploy_link_skips_default_branch():
    with patch('auto_commit.resolve_pr_base', return_value=None), \
         patch('builtins.print') as mock_print:
        auto_commit.print_deploy_link("main")
        mock_print.assert_not_called()
