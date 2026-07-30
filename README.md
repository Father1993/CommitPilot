# CommitPilot

Automate git commits with AI-generated messages in [Conventional Commits](https://www.conventionalcommits.org/) format.

## Requirements

- Python 3.7+
- Git
- Bash (Git Bash on Windows)
- API token for an [OpenAI-compatible](https://platform.openai.com/docs/api-reference) host (default), [OpenAI](https://platform.openai.com/api-keys), or [Hugging Face](https://huggingface.co/settings/tokens)

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
API_TOKEN=your-token-here
```

Optional overrides for the OpenAI-compatible provider:

```env
API_BASE_URL=https://api.openai.com/v1
API_MODEL=gpt-4.1
```

Use any OpenAI-protocol host (`API_BASE_URL`): OpenRouter, RouterAI, a local gateway, etc.

### Non-secret settings

Edit `config.ini` (see `config.ini.example`):

```ini
[DEFAULT]
api_provider = openai_compatible
api_base_url = https://api.openai.com/v1
api_model = gpt-4.1
branch = master
max_diff_size = 7000
```

Providers: `openai_compatible` (default), `openai`, `huggingface`.

`branch` is **legacy** (kept for existing configs). Push always uses the **current git branch**, or `-b` to override.

Tokens can also be set in `config.ini`, but `.env` takes priority for `API_TOKEN`.

## Usage

Run from **any git repository**:

```bash
cd /path/to/your/project

acommit              # git add, AI commit, push current branch
acommit-here         # git add, AI commit, no push
acommit-dev          # commit and push to origin/dev (-b override)
acommit-main         # commit and push to origin/main
acommit-master       # commit and push to origin/master
```

Short aliases (same commands):

```bash
acum                 # same as acommit (push current branch)
acm                  # same as acommit-here (commit only)
acmd                 # push current branch + print PR/deploy link
acmm                 # push to main (-b override)
acmmm                # push to master (-b override)
```

### Deploy link (`acmd` / `--deploy-link`)

After a successful push, `acmd` prints a one-click URL:

1. Open PR if `gh` finds one for this head/base → `https://github.com/.../pull/N`
2. Otherwise → `https://github.com/.../compare/BASE...HEAD?expand=1` (Create PR form)

BASE resolution:

- feature branch → `dev` if it exists on remote, else default (`main`/`master`)
- `dev` → default production branch
- already on default branch → no link

### CLI options

```bash
python /path/to/CommitPilot/auto_commit.py [options]

-c, --commit-only    Commit without push
-b, --branch NAME    Override push branch (default: current branch)
-d, --deploy-link    Print PR/compare link after push
-m, --message TEXT   Use custom message (skip AI)
-p, --provider NAME  openai_compatible | openai | huggingface
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
4. Optionally `git push -u origin <current-or--b-branch>`
5. With `--deploy-link`, print PR or compare URL

Default provider: `openai_compatible` (OpenAI SDK / HTTP with custom `api_base_url` + `api_model`).

## Troubleshooting

```bash
acommit --test
```

| Problem | Fix |
|---------|-----|
| Token not configured | Add `API_TOKEN=...` to `CommitPilot/.env` |
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
