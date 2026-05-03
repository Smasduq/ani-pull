import yt_dlp
import logging
import os
from typing import Optional, Callable
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, DownloadColumn, TransferSpeedColumn

logger = logging.getLogger(__name__)

class Downloader:
    """
    A wrapper around yt-dlp to handle anime downloads with quality selection.
    """
    
    def __init__(self, output_template: str = "%(title)s.%(ext)s"):
        self.output_template = output_template

    def download(self, url: str, filename: Optional[str] = None, progress_hook: Optional[Callable] = None, 
                 referer: Optional[str] = None, resolution: str = "1080", 
                 write_subs: bool = False, embed_subs: bool = False):
        """
        Download a video from a given URL with a specific resolution limit.
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
        }
        if referer:
            headers['Referer'] = referer
            
        fmt = f"bestvideo[height<={resolution}]+bestaudio/best[height<={resolution}]/best"
        
        ydl_opts = {
            'format': fmt,
            'outtmpl': filename or self.output_template,
            'quiet': True,
            'embedsubtitles': embed_subs,
            'subtitleslangs': ['en.*'],
            'no_check_certificate': True,
            'prefer_ffmpeg': True,
        }
        
        # Don't use quiet: True, let it log to app.log but we'll suppress stdout in main if needed.
        # Actually, yt-dlp's logger can be used.
        ydl_opts['logger'] = logger
        
        if embed_subs:
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegEmbedSubtitle',
                'already_have_subtitle': False,
            }]
        
        if progress_hook:
            ydl_opts['progress_hooks'] = [progress_hook]
            
        logger.info(f"Starting download (Max resolution: {resolution}p)")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return True
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return False

class RichProgressHook:
    """
    A progress hook using rich for a clean, emoji-free progress bar.
    """
    def __init__(self, console):
        self.console = console
        self.progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            DownloadColumn(),
            "•",
            TransferSpeedColumn(),
            "•",
            TimeRemainingColumn(),
            console=self.console,
            expand=True
        )
        self.task_id = None

    def __call__(self, d):
        if d['status'] == 'downloading':
            if self.task_id is None:
                self.progress.start()
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 100
                self.task_id = self.progress.add_task("Downloading", total=total)
            
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            
            if total:
                self.progress.update(self.task_id, completed=downloaded, total=total)
            else:
                self.progress.update(self.task_id, completed=downloaded)
        
        elif d['status'] == 'finished':
            # Don't stop progress here, wait for the whole process to finish
            # or just finish the task.
            if self.task_id is not None:
                self.progress.update(self.task_id, completed=self.progress.tasks[self.task_id].total)
                # We'll stop in a cleanup or let the next step take over.
        
    def stop(self):
        if self.task_id is not None:
            self.progress.stop()
            self.console.print("[bold green]Download complete. Finalizing file...[/bold green]")
