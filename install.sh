#!/bin/bash

# Ani-Pull One-Command Installer for Debian/Ubuntu
# https://github.com/Smasduq/ani-pull

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}--- Ani-Pull Installer ---${NC}"

# 1. Check for sudo
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root (use sudo)"
  exit 1
fi

# 2. Identify Distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
    CODENAME=$VERSION_CODENAME
else
    echo "Unsupported distribution."
    exit 1
fi

echo -e "Detected ${GREEN}$DISTRO ($CODENAME)${NC}..."

# 3. Install prerequisites
echo "Installing prerequisites..."
apt-get update -y > /dev/null
apt-get install -y wget gpg > /dev/null

# 4. Add GPG Key
echo "Adding GPG key..."
wget -qO - https://smasduq.github.io/ani-pull/repo/key.gpg | gpg --dearmor --yes -o /etc/apt/trusted.gpg.d/ani-pull.gpg

# 5. Add Sources List
echo "Adding repository source..."
echo "deb https://smasduq.github.io/ani-pull/repo/ $CODENAME main" | tee /etc/apt/sources.list.d/ani-pull.list > /dev/null

# 6. Install
echo -e "${GREEN}Installing ani-pull...${NC}"
apt-get update -y > /dev/null
apt-get install -y ani-pull

echo -e "${GREEN}Done!${NC} You can now run 'ani-pull' from your terminal."
