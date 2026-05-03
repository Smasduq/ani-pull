# Anime Downloader CLI (ani-pull)

A robust, user-friendly CLI for searching and downloading anime episodes.

## Features
- Search anime from **Anitaku (Gogoanime)**
- Select specific episodes or ranges
- High-quality downloads using **yt-dlp**
- Progress tracking with speed and ETA
- Native support for **Debian, Ubuntu, Fedora, and Arch Linux**

## Installation

### 🐧 Debian / Ubuntu
Download the latest `.deb` file from the [Releases](https://github.com/Smasduq/ani-pull/releases) page and run:
```bash
sudo apt install ./ani-pull_*.deb
```

### 🎩 Fedora
Download the latest `.rpm` or build from source:
```bash
sudo dnf install ./ani-pull-*.rpm
```

### 🏹 Arch Linux
Build using the PKGBUILD:
```bash
cd packaging/arch
makepkg -si
```

### 🐍 Python (Standard)
```bash
pip install .
```

## Usage
After installation, simply run:
```bash
ani-pull
```

Follow the interactive prompts:
1. Enter the anime name.
2. Select the anime from the search results.
3. Choose the episode range (e.g., `1`, `1-5`, or `all`).
4. Select resolution and confirm download.

## Development

### Requirements
- **Python 3.8+**
- **FFmpeg** (Required for merging video streams)

### Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Testing
```bash
pytest tests/
```

### Building Debian Package Locally
```bash
./release.sh
```

## Disclaimer
This tool is for educational purposes only. Please support the official creators and distributors of the anime you watch.
