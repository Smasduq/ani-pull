# Anime Downloader CLI

A robust, user-friendly CLI for searching and downloading anime episodes.

## Features
- Search anime from **Anitaku (Gogoanime)**
- Select specific episodes or ranges
- High-quality downloads using **yt-dlp**
- Progress tracking with speed and ETA
- Automatically bypasses site protections

## Requirements
- **Python 3.8+**
- **FFmpeg** (Required for merging video streams)
- Dependencies: `requests`, `beautifulsoup4`, `yt-dlp`, `tqdm`

## Installation
1. Clone the repository.
2. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

## Usage
Run the main script:
```bash
python3 main.py
```

Follow the interactive prompts:
1. Enter the anime name.
2. Select the anime from the search results.
3. Choose the episode range (e.g., `1`, `1-5`, or `all`).
4. Watch the progress as it downloads!

## Technical Notes
- Built using a robust scraper for **Anitaku.to**.
- Leverages **yt-dlp**'s internal extractors for streaming players like Vidstreaming and Doodstream.
- Uses **requests** with custom headers for reliable scraping.

## Disclaimer
This tool is for educational purposes only. Please support the official creators and distributors of the anime you watch.
