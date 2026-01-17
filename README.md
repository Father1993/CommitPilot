# CommitPilot 🤖

Automate git commits with AI-generated messages in Conventional Commits format.

## Quick Usage

**After installation** (one time), use in **any project**:

```bash
cd /path/to/your/project
acommit              # Automatically: git add + commit + push
acommit-here         # Commit only, no push
```

No need to copy files to each project — commands work globally!

## Quick Start

### Installation (one time)

```bash
git clone https://github.com/Father1993/CommitPilot.git
cd CommitPilot
bash install.sh
source ~/.bashrc  # or ~/.zshrc
```

After installation, `acommit` commands will work from **any directory** with a git repository.

### Configuration

Create a `.env` file in your project root:

```env
AI_TUNNEL=sk-aitunnel-your-token-here
# Optional: custom API endpoint and model
AITUNNEL_BASE_URL=https://api.aitunnel.ru/v1/
AITUNNEL_MODEL=gpt-4.1
```

Or use `config.ini` (example in `config.ini.example`):

```ini
[DEFAULT]
api_provider = aitunnel
aitunnel_token = sk-aitunnel-your-token-here
aitunnel_base_url = https://api.aitunnel.ru/v1/
aitunnel_model = gpt-4.1
branch = master
max_diff_size = 7000
```

**Note**: `config.ini` is stored in the CommitPilot directory and used for all projects. Tokens are better stored in `.env` files in each project.

### Usage

**Main commands:**
```bash
acommit              # Commit with AI message and push to default branch
acommit-here         # Commit only, no push
acommit-dev          # Commit and push to dev branch
acommit-main         # Commit and push to main branch
acommit-master       # Commit and push to master branch
```

**Additional options:**
```bash
acommit -b branch    # Commit to specified branch
acommit -m "msg"     # Custom message (disables AI)
acommit -p openai    # Choose provider (aitunnel/openai/huggingface)
acommit --test       # Check settings
acommit --get-message # Generate message only
```

## Features

- 🚀 **Automation**: `git add`, `git commit`, `git push` in one command
- 🧠 **AI Providers**: AITUNNEL (default), OpenAI, Hugging Face
- 🔄 **Git Hooks**: Automatic generation on `git commit`
- 💡 **Conventional Commits**: Messages in standard format
- 🔒 **Security**: `.env` support for tokens

## Requirements

- Python 3.7+
- Git
- Dependencies: `requests`, `python-dotenv`, `openai`
- API Token: [AITUNNEL](https://aitunnel.ru/) (recommended), [OpenAI](https://platform.openai.com/api-keys) or [Hugging Face](https://huggingface.co/settings/tokens)

## How It Works

1. **Analyze changes**: Get `git diff` and `git status`
2. **Generate message**: Send to AITUNNEL API (OpenAI compatible)
3. **Create commit**: `git add .` and `git commit` with AI message
4. **Push**: `git push` to specified branch (optional)

**Message format**: Conventional Commits (`type(scope): description`)

## Usage Methods

### Method 1: Global Aliases (Recommended)

**Install once:**
```bash
cd CommitPilot
bash install.sh
source ~/.bashrc  # or ~/.zshrc
```

**Use in any project:**
```bash
cd /path/to/your/project
acommit              # Commit + push
acommit-here         # Commit only
acommit-dev          # Commit to dev
```

### Method 2: Local Usage

**In project directory:**
```bash
# Copy CommitPilot to project or use directly
python /path/to/CommitPilot/auto_commit.py
python /path/to/CommitPilot/auto_commit.py -c  # Commit only
python /path/to/CommitPilot/auto_commit.py -b dev  # To dev branch
```

**Or create a local alias in project:**
```bash
# In project root create .bashrc or add to ~/.bashrc
alias acommit-local='python "$(pwd)/../CommitPilot/auto_commit.py"'
```

## Examples

**Local commit:**
```bash
acommit-here  # Commit without push
```

**Working with branches:**
```bash
acommit-dev   # Commit to dev
acommit -b feature/new-feature  # To any branch
```

**Git hooks** (auto-generation on `git commit`):
```bash
cp prepare-commit-msg /path/to/project/.git/hooks/
chmod +x /path/to/project/.git/hooks/prepare-commit-msg
```

**Message examples:**
- `feat(auth): add OAuth authentication`
- `fix(api): resolve timeout issue`
- `docs: update installation guide`
- `refactor(core): optimize diff processing`

## Troubleshooting

**Check settings:**
```bash
acommit --test
```

**Error "API token not configured":**
- Check `.env` file with `AI_TUNNEL=sk-aitunnel-...`
- Or configure `aitunnel_token` in `config.ini`

**Aliases not working:**
```bash
source ~/.bashrc  # or ~/.zshrc
```

## Security

- Files `.env` and `config.ini` in `.gitignore`
- Don't publish tokens in public repositories
- Use `.env` for local development

## License

MIT © Andrej Spinej

## Architecture

```
CommitPilot/
├── auto_commit.py          # Main module
├── aitunnel_support.py     # AITUNNEL API
├── openai_support.py       # OpenAI API
├── prepare-commit-msg       # Git hook
└── install.sh              # Installer
```

## API Providers

| Provider | Model | Token |
|----------|-------|-------|
| **AITUNNEL** (default) | gpt-4.1 | `AI_TUNNEL` in `.env` |
| OpenAI | gpt-4o-mini | `openai_token` in config.ini |
| Hugging Face | Mixtral-8x7B | `huggingface_token` in config.ini |
