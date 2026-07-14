#!/bin/bash
#
# CommitPilot installer
# Supports Linux, macOS, WSL, and Git Bash on Windows 11
#

set -e

GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}$1${NC}"; }
warn()  { echo -e "${YELLOW}$1${NC}"; }
error() { echo -e "${RED}$1${NC}"; exit 1; }

check_command() {
    if command -v "$1" &>/dev/null; then
        info "[ok] $1"
        return 0
    fi
    warn "[missing] $1"
    return 1
}

# Prefer "python" on Windows Git Bash; "python3" on Linux/macOS
if command -v python &>/dev/null; then
    PYTHON_CMD="python"
elif command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
else
    error "Python 3.7+ is required: https://www.python.org/downloads/"
fi

check_command git || error "Git is required: https://git-scm.com/downloads"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AUTO_COMMIT="$SCRIPT_DIR/auto_commit.py"

info "=================================================="
info "CommitPilot Installation"
info "=================================================="

warn "Installing Python dependencies..."
"$PYTHON_CMD" -m pip install --upgrade pip --quiet 2>/dev/null || true
"$PYTHON_CMD" -m pip install requests python-dotenv openai

warn "Setting permissions..."
chmod +x "$AUTO_COMMIT" "$SCRIPT_DIR/prepare-commit-msg" 2>/dev/null || true

detect_shell_rc() {
    # Prefer the login shell's rc (zsh users often have both .bashrc and .zshrc)
    case "${SHELL##*/}" in
        zsh)
            [ -f "$HOME/.zshrc" ] && { echo "$HOME/.zshrc"; return; }
            ;;
        bash)
            [ -f "$HOME/.bashrc" ] && { echo "$HOME/.bashrc"; return; }
            [ -f "$HOME/.bash_profile" ] && { echo "$HOME/.bash_profile"; return; }
            ;;
    esac
    if [ -f "$HOME/.bashrc" ]; then
        echo "$HOME/.bashrc"
    elif [ -f "$HOME/.bash_profile" ]; then
        echo "$HOME/.bash_profile"
    elif [ -f "$HOME/.zshrc" ]; then
        echo "$HOME/.zshrc"
    fi
}

install_aliases() {
    local rc="$1"
    local tmp
    tmp="$(mktemp)"

    # Remove previous CommitPilot block
    if [ -f "$rc" ]; then
        awk '
            /^# CommitPilot$/ { in_block=1; next }
            in_block && /^alias (acommit|acommit-|acm|acmd|acmm|acmmm|acum)=/ { next }
            in_block { in_block=0 }
            { print }
        ' "$rc" > "$tmp"
        mv "$tmp" "$rc"
    fi

    {
        echo ""
        echo "# CommitPilot"
        echo "alias acommit=\"$PYTHON_CMD \\\"$AUTO_COMMIT\\\"\""
        echo "alias acommit-here=\"$PYTHON_CMD \\\"$AUTO_COMMIT\\\" -c\""
        echo "alias acommit-dev=\"$PYTHON_CMD \\\"$AUTO_COMMIT\\\" -b dev\""
        echo "alias acommit-main=\"$PYTHON_CMD \\\"$AUTO_COMMIT\\\" -b main\""
        echo "alias acommit-master=\"$PYTHON_CMD \\\"$AUTO_COMMIT\\\" -b master\""
        echo "alias acum=\"$PYTHON_CMD \\\"$AUTO_COMMIT\\\"\""
        echo "alias acm=\"$PYTHON_CMD \\\"$AUTO_COMMIT\\\" -c\""
        echo "alias acmd=\"$PYTHON_CMD \\\"$AUTO_COMMIT\\\" --deploy-link\""
        echo "alias acmm=\"$PYTHON_CMD \\\"$AUTO_COMMIT\\\" -b main\""
        echo "alias acmmm=\"$PYTHON_CMD \\\"$AUTO_COMMIT\\\" -b master\""
    } >> "$rc"
}

warn "Setting up aliases..."
SHELL_RC="$(detect_shell_rc)"
if [ -n "$SHELL_RC" ]; then
    install_aliases "$SHELL_RC"
    info "[ok] Aliases added to $SHELL_RC"
    warn "Reload shell: source $SHELL_RC"
else
    warn "No shell config found. Add these aliases manually:"
    echo "alias acommit=\"$PYTHON_CMD \\\"$AUTO_COMMIT\\\"\""
    echo "alias acommit-here=\"$PYTHON_CMD \\\"$AUTO_COMMIT\\\" -c\""
    echo "alias acum=\"$PYTHON_CMD \\\"$AUTO_COMMIT\\\"\""
    echo "alias acm=\"$PYTHON_CMD \\\"$AUTO_COMMIT\\\" -c\""
fi

warn "Creating configuration..."
CONFIG_PATH="$SCRIPT_DIR/config.ini"
if [ ! -f "$CONFIG_PATH" ]; then
    if [ -f "$SCRIPT_DIR/config.ini.example" ]; then
        cp "$SCRIPT_DIR/config.ini.example" "$CONFIG_PATH"
        info "[ok] Created $CONFIG_PATH"
    else
        error "config.ini.example not found"
    fi
else
    info "[ok] Configuration exists: $CONFIG_PATH"
fi

ENV_FILE="$SCRIPT_DIR/.env"
if [ ! -f "$ENV_FILE" ] && [ -f "$SCRIPT_DIR/.env.example" ]; then
    warn "Copy .env.example to .env and add your API token:"
    warn "  cp $SCRIPT_DIR/.env.example $ENV_FILE"
fi

warn "Installing git hook..."
if [ -d "$SCRIPT_DIR/.git" ]; then
    mkdir -p "$SCRIPT_DIR/.git/hooks"
    cp "$SCRIPT_DIR/prepare-commit-msg" "$SCRIPT_DIR/.git/hooks/"
    chmod +x "$SCRIPT_DIR/.git/hooks/prepare-commit-msg"
    info "[ok] Hook installed in CommitPilot repo"
elif [ -d ".git" ]; then
    mkdir -p ".git/hooks"
    cp "$SCRIPT_DIR/prepare-commit-msg" ".git/hooks/"
    chmod +x ".git/hooks/prepare-commit-msg"
    info "[ok] Hook installed in current repo"
else
    warn "Not a git repo. Install hook later: $PYTHON_CMD $AUTO_COMMIT --setup-hooks"
fi

if [ -f "$ENV_FILE" ] || grep -q 'aitunnel_token\s*=\s*\S' "$CONFIG_PATH" 2>/dev/null; then
    warn "Testing message generation..."
    if "$PYTHON_CMD" "$AUTO_COMMIT" --test 2>/dev/null | grep -q 'Test message'; then
        info "[ok] API connection works"
    else
        warn "Token found but test message failed. Run: acommit --test"
    fi
else
    warn "Add AI_TUNNEL to $ENV_FILE then run: acommit --test"
fi

info "=================================================="
info "Installation complete"
info "=================================================="
warn "Commands: acommit | acommit-here | acum | acm | acommit-dev | acmd"
warn "Docs: $SCRIPT_DIR/README.md"
