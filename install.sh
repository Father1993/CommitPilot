#!/bin/bash

#
# CommitPilot Installer
# 
# Checks dependencies, installs necessary components and 
# sets up convenient aliases for use
#

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if command exists
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}❌ $1 is not installed${NC}"
        return 1
    else
        echo -e "${GREEN}✓ $1 is installed${NC}"
        return 0
    fi
}

# Header
echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}          CommitPilot Installation              ${NC}"
echo -e "${GREEN}==================================================${NC}"

# Check dependencies
echo -e "\n${YELLOW}Checking required dependencies...${NC}"

# Check Git
check_command "git" || { 
    echo -e "${RED}Git is required. Please install Git: https://git-scm.com/downloads${NC}"
    exit 1
}

# Check Python
check_command "python3" || check_command "python" || { 
    echo -e "${RED}Python 3.6+ is required. Please install Python: https://www.python.org/downloads/${NC}"
    exit 1
}

# Determine Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

# Check pip
check_command "pip" || check_command "pip3" || {
    echo -e "${RED}pip is required for installing dependencies. It is usually installed with Python.${NC}"
    exit 1
}

# Determine pip command
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
else
    PIP_CMD="pip"
fi

# Install dependencies
echo -e "\n${YELLOW}Installing Python dependencies...${NC}"
$PIP_CMD install requests python-dotenv

# Install OpenAI SDK (needed for AITUNNEL and OpenAI)
echo -e "\n${YELLOW}Installing OpenAI SDK library (required for AITUNNEL and OpenAI)...${NC}"
$PIP_CMD install openai
echo -e "${GREEN}✓ OpenAI SDK library installed${NC}"

# Get current path
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Make scripts executable
echo -e "\n${YELLOW}Setting permissions...${NC}"
chmod +x "$SCRIPT_DIR/auto_commit.py"
chmod +x "$SCRIPT_DIR/prepare-commit-msg"

# Create aliases
SHELL_RC=""
if [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
elif [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
fi

echo -e "\n${YELLOW}Setting up aliases...${NC}"

if [ -n "$SHELL_RC" ]; then
    # Base alias
    if grep -q "alias acommit=" "$SHELL_RC"; then
        echo -e "${YELLOW}Updating existing acommit alias...${NC}"
        sed -i "s|alias acommit=.*|alias acommit=\"$PYTHON_CMD $SCRIPT_DIR/auto_commit.py\"|g" "$SHELL_RC"
    else
        echo -e "# CommitPilot" >> "$SHELL_RC"
        echo -e "alias acommit=\"$PYTHON_CMD $SCRIPT_DIR/auto_commit.py\"" >> "$SHELL_RC"
    fi
    
    # Additional aliases for convenience
    if ! grep -q "alias acommit-dev=" "$SHELL_RC"; then
        echo -e "alias acommit-dev=\"$PYTHON_CMD $SCRIPT_DIR/auto_commit.py -b dev\"" >> "$SHELL_RC"
        echo -e "alias acommit-main=\"$PYTHON_CMD $SCRIPT_DIR/auto_commit.py -b main\"" >> "$SHELL_RC"
        echo -e "alias acommit-master=\"$PYTHON_CMD $SCRIPT_DIR/auto_commit.py -b master\"" >> "$SHELL_RC"
        echo -e "alias acommit-here=\"$PYTHON_CMD $SCRIPT_DIR/auto_commit.py -c\"" >> "$SHELL_RC"
    fi
    
    echo -e "${GREEN}✓ Aliases added to $SHELL_RC${NC}"
    echo -e "${YELLOW}To activate aliases run: source $SHELL_RC${NC}"
else
    echo -e "${YELLOW}⚠️ Shell configuration file not found.${NC}"
    echo -e "${YELLOW}Add the following aliases manually to your configuration file:${NC}"
    echo -e "alias acommit=\"$PYTHON_CMD $SCRIPT_DIR/auto_commit.py\""
    echo -e "alias acommit-dev=\"$PYTHON_CMD $SCRIPT_DIR/auto_commit.py -b dev\""
    echo -e "alias acommit-main=\"$PYTHON_CMD $SCRIPT_DIR/auto_commit.py -b main\""
    echo -e "alias acommit-master=\"$PYTHON_CMD $SCRIPT_DIR/auto_commit.py -b master\""
    echo -e "alias acommit-here=\"$PYTHON_CMD $SCRIPT_DIR/auto_commit.py -c\""
fi

# Create configuration file
echo -e "\n${YELLOW}Creating configuration file...${NC}"
CONFIG_PATH="$SCRIPT_DIR/config.ini"
if [ ! -f "$CONFIG_PATH" ]; then
    echo -e "# CommitPilot - Configuration\n# Edit this file manually to configure\n\n[DEFAULT]\n# Choose AI provider: aitunnel (default), huggingface or openai\napi_provider = aitunnel\n\n# AITUNNEL API settings (recommended)\n# Token can also be specified in .env file as AI_TUNNEL=sk-aitunnel-xxx\naitunnel_token = \naitunnel_base_url = https://api.aitunnel.ru/v1/\naitunnel_model = gpt-4.1\n\n# Hugging Face API settings\nhuggingface_token = \n\n# OpenAI API settings\nopenai_token = \n\n# Default branch for git push\nbranch = master\n\n# Maximum diff size for sending to AI API\nmax_diff_size = 7000" > "$CONFIG_PATH"
    echo -e "${GREEN}✓ Created configuration file $CONFIG_PATH${NC}"
    echo -e "${YELLOW}⚠️ Please edit the configuration file and add your API token${NC}"
    echo -e "${YELLOW}   Or create .env file in project root with: AI_TUNNEL=sk-aitunnel-your_token${NC}"
else
    echo -e "${GREEN}✓ Configuration file already exists${NC}"
fi

# Create .env example file
ENV_PATH="$SCRIPT_DIR/.env.example"
if [ ! -f "$ENV_PATH" ]; then
    echo -e "# CommitPilot - Environment Variables Example\n# Copy this file to .env and add your token\n\n# AITUNNEL API token (recommended)\nAI_TUNNEL=sk-aitunnel-your_token_here\n\n# Custom URL for AITUNNEL (optional)\n# AITUNNEL_BASE_URL=https://api.aitunnel.ru/v1/\n\n# Model for AITUNNEL (optional)\n# AITUNNEL_MODEL=gpt-4.1" > "$ENV_PATH"
    echo -e "${GREEN}✓ Created .env.example file${NC}"
fi

# Create config.ini example file
CONFIG_EXAMPLE_PATH="$SCRIPT_DIR/config.ini.example"
if [ ! -f "$CONFIG_EXAMPLE_PATH" ]; then
    cp "$CONFIG_PATH" "$CONFIG_EXAMPLE_PATH"
    echo -e "${GREEN}✓ Created config.ini.example file${NC}"
fi

# Install Git hooks
echo -e "\n${YELLOW}Installing Git hooks in current repository...${NC}"
# Check for .git directory
if [ -d ".git" ]; then
    # Create hooks directory if it doesn't exist
    mkdir -p .git/hooks
    # Copy hook
    cp "$SCRIPT_DIR/prepare-commit-msg" .git/hooks/
    chmod +x .git/hooks/prepare-commit-msg
    echo -e "${GREEN}✓ Git hook installed at .git/hooks/prepare-commit-msg${NC}"
else
    echo -e "${YELLOW}⚠️ Current directory is not a git repository. Git hook not installed.${NC}"
    echo -e "${YELLOW}⚠️ To install hook in another project, run:${NC}"
    echo -e "${YELLOW}   cp $SCRIPT_DIR/prepare-commit-msg /path/to/your/project/.git/hooks/${NC}"
fi

# Check message generation capability
if [ -f "$CONFIG_PATH" ]; then
    echo -e "\n${YELLOW}Checking message generation capability...${NC}"
    TEST_MESSAGE=$($PYTHON_CMD "$SCRIPT_DIR/auto_commit.py" --get-message 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$TEST_MESSAGE" ]; then
        echo -e "${GREEN}✓ Example generated message:${NC} \"$TEST_MESSAGE\""
    else
        echo -e "${YELLOW}⚠️ API token must be configured in config.ini or .env to generate messages${NC}"
    fi
fi

echo -e "\n${GREEN}==================================================${NC}"
echo -e "${GREEN}      CommitPilot Installation Complete!          ${NC}"
echo -e "${GREEN}==================================================${NC}"
echo -e "\n${YELLOW}Available commands:${NC}"
echo -e "  ${GREEN}acommit${NC} - Create commit and push to default branch"
echo -e "  ${GREEN}acommit-dev${NC} - Create commit and push to dev branch"
echo -e "  ${GREEN}acommit-main${NC} - Create commit and push to main branch"
echo -e "  ${GREEN}acommit-master${NC} - Create commit and push to master branch"
echo -e "  ${GREEN}acommit-here${NC} - Create commit without push"
echo -e "\n${YELLOW}For use in other projects:${NC}"
echo -e "  ${GREEN}1.${NC} Create alias to call CommitPilot from any directory"
echo -e "  ${GREEN}2.${NC} Or copy hook: cp $SCRIPT_DIR/prepare-commit-msg /path/to/project/.git/hooks/"
echo -e "\n${YELLOW}For more information see README.md file${NC}" 