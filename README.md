# CommitPilot

Automate git commits with AI-generated messages in [Conventional Commits](https://www.conventionalcommits.org/) format.

## Requirements

- Python 3.7+
- Git
- Bash (Git Bash on Windows)
- API token: [AITUNNEL](https://aitunnel.ru/) (default), [OpenAI](https://platform.openai.com/api-keys), or [Hugging Face](https://huggingface.co/settings/tokens)

## Install

```bash
git clone https://github.com/Father1993/CommitPilot.git
cd CommitPilot
bash install.sh
source ~/.bashrc   # Git Bash on Windows; use ~/.bash_profile if needed
```

The installer:

- installs Python dependencies (`requests`, `python-dotenv`, `openai`)
- creates `config.ini` if missing
- adds shell aliases
- installs the git hook in the current repo (if `.git` exists)

## Configuration

All settings live in the **CommitPilot directory** (same folder as `auto_commit.py`).

### Secrets (recommended)

Copy `.env.example` to `.env` and set your token:

```env
AI_TUNNEL=sk-aitunnel-your-token-here
```

Optional overrides:

```env
AITUNNEL_BASE_URL=https://api.aitunnel.ru/v1/
AITUNNEL_MODEL=gpt-4.1
```

### Non-secret settings

Edit `config.ini` (see `config.ini.example`):

```ini
[DEFAULT]
api_provider = aitunnel
branch = master
max_diff_size = 7000
```

Tokens can also be set in `config.ini`, but `.env` takes priority for `AI_TUNNEL`.

## Usage

Run from **any git repository**:

```bash
cd /path/to/your/project

acommit              # git add, AI commit, push to default branch
acommit-here         # git add, AI commit, no push
acommit-dev          # commit and push to dev
acommit-main         # commit and push to main
acommit-master       # commit and push to master
```

Short aliases (same commands):

```bash
acum                 # same as acommit
acm                  # same as acommit-here
acmd                 # push to dev
acmm                 # push to main
acmmm                # push to master
```

### CLI options

```bash
python /path/to/CommitPilot/auto_commit.py [options]

-c, --commit-only    Commit without push
-b, --branch NAME    Push to branch (default from config.ini)
-m, --message TEXT   Use custom message (skip AI)
-p, --provider NAME  aitunnel | openai | huggingface
--test               Check token and generate a test message
--get-message        Print generated message only
--setup              Interactive setup
--setup-hooks        Install prepare-commit-msg hook in current repo
-v, --version        Show version
```

### Git hook

Auto-generate a message when you run `git commit` with an empty message:

```bash
python /path/to/CommitPilot/auto_commit.py --setup-hooks
```

Or copy manually:

```bash
cp /path/to/CommitPilot/prepare-commit-msg /path/to/project/.git/hooks/
chmod +x /path/to/project/.git/hooks/prepare-commit-msg
```

## How it works

1. Read `git status` and `git diff`
2. Send changes to the configured AI provider
3. Run `git add .` and `git commit -m "..."`
4. Optionally `git push origin <branch>`

Default provider: AITUNNEL (OpenAI-compatible API).

## Troubleshooting

```bash
acommit --test
```

| Problem | Fix |
|---------|-----|
| Token not configured | Add `AI_TUNNEL=...` to `CommitPilot/.env` |
| Aliases not found | Run `source ~/.bashrc` or open a new terminal |
| No changes to commit | Make sure you are in a repo with uncommitted changes |
| Hook not working | Set `COMMITPILOT_PATH` to the CommitPilot directory |

## Windows 11 (Git Bash)

1. Install [Git for Windows](https://git-scm.com/download/win) (includes Git Bash).
2. Install [Python 3](https://www.python.org/downloads/) and enable **Add to PATH**.
3. Clone CommitPilot and run `bash install.sh` from Git Bash.
4. Reload shell: `source ~/.bashrc`.

Aliases use absolute paths, so they work from any drive or directory.

## Tests

```bash
python -m pip install pytest
python -m pytest tests/ -q
```

## Project layout

```
CommitPilot/
├── auto_commit.py        # CLI entry point
├── ai_common.py          # AI providers and shared helpers
├── prepare-commit-msg    # Git hook script
├── install.sh            # Installer
├── config.ini.example
└── .env.example
```

## License

MIT
