import yt_dlp
import logging
import os
import subprocess
import re
from typing import Optional, Callable, Any
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, DownloadColumn, TransferSpeedColumn

logger = logging.getLogger(__name__)

class Downloader:
    """
    A wrapper around yt-dlp to handle anime downloads with quality selection.
    """
    
    def __init__(self, output_template: str = "%(title)s.%(ext)s"):
        self.output_template = output_template

    def _get_duration(self, filepath: str) -> float:
        """Get the duration of a video file using ffprobe."""
        try:
            cmd = [
                'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1', filepath
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except Exception as e:
            logger.warning(f"Could not get duration with ffprobe: {e}")
            return 0.0

    def _process_with_ffmpeg(self, input_path: str, output_path: str, progress_hook: Optional[Any]) -> bool:
        """Process the downloaded file with ffmpeg and report progress."""
        duration = self._get_duration(input_path)
        if duration <= 0:
            # Fallback to simple rename if we can't get duration
            try:
                if os.path.exists(output_path):
                    os.remove(output_path)
                os.rename(input_path, output_path)
                return True
            except Exception as e:
                logger.error(f"Failed to rename file: {e}")
                return False

        if progress_hook and hasattr(progress_hook, 'start_processing'):
            progress_hook.start_processing(duration)

        # FFmpeg command for remuxing (fast and safe)
        cmd = [
            'ffmpeg', '-i', input_path, '-c', 'copy', '-map', '0', '-y',
            '-progress', 'pipe:1', output_path
        ]
        
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Regex to find out_time_us in the progress output
            time_regex = re.compile(r'out_time_us=(\d+)')
            
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                
                match = time_regex.search(line)
                if match and progress_hook and hasattr(progress_hook, 'update_processing'):
                    out_time_us = int(match.group(1))
                    # Convert microseconds to seconds
                    out_time_s = out_time_us / 1000000.0
                    progress_hook.update_processing(out_time_s)
            
            process.wait()
            if process.returncode == 0:
                if os.path.exists(input_path):
                    os.remove(input_path)
                return True
            else:
                logger.error(f"FFmpeg failed with return code {process.returncode}")
                return False
        except Exception as e:
            logger.error(f"FFmpeg processing failed: {e}")
            return False

    def download(self, url: str, filename: Optional[str] = None, progress_hook: Optional[Any] = None, 
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
        
        # Download to a temporary file first
        target_file = filename or self.output_template
        temp_file = target_file + ".part"
        
        ydl_opts = {
            'format': fmt,
            'outtmpl': temp_file,
            'quiet': True,
            'embedsubtitles': embed_subs,
            'subtitleslangs': ['en.*'],
            'no_check_certificate': True,
            'prefer_ffmpeg': True,
        }
        
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
            
            # After download, process with ffmpeg
            logger.info("Starting FFmpeg processing...")
            # We need to find the actual file downloaded by yt-dlp. 
            # Sometimes it appends extensions or doesn't use the exact temp_file if it's a merge.
            # But with outtmpl, it should be temp_file.
            
            # yt-dlp might have changed the extension if it merged formats.
            actual_temp = temp_file
            if not os.path.exists(actual_temp):
                # Try common extensions
                for ext in ['.mp4', '.mkv', '.webm']:
                    if os.path.exists(temp_file + ext):
                        actual_temp = temp_file + ext
                        break
            
            success = self._process_with_ffmpeg(actual_temp, target_file, progress_hook)
            return success
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
        self.download_task = None
        self.process_task = None
        self._started = False

    def __call__(self, d):
        if d['status'] == 'downloading':
            if not self._started:
                self.progress.start()
                self._started = True
                
            if self.download_task is None:
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 100
                self.download_task = self.progress.add_task("Downloading", total=total)
            
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            
            if total:
                self.progress.update(self.download_task, completed=downloaded, total=total)
            else:
                self.progress.update(self.download_task, completed=downloaded)
        
        elif d['status'] == 'finished':
            if self.download_task is not None:
                self.progress.update(self.download_task, completed=self.progress.tasks[self.download_task].total)

    def start_processing(self, total_duration: float):
        if not self._started:
            self.progress.start()
            self._started = True
        self.process_task = self.progress.add_task("Processing ", total=total_duration)

    def update_processing(self, current_time: float):
        if self.process_task is not None:
            self.progress.update(self.process_task, completed=current_time)

    def stop(self):
        if self._started:
            # Mark processing as complete if it was started
            if self.process_task is not None:
                self.progress.update(self.process_task, completed=self.progress.tasks[self.process_task].total)
            
            self.progress.stop()
            self._started = False
            self.console.print("[bold green]All processing complete. Enjoy your anime![/bold green]")
