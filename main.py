import os
import sys
import logging
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt

from api.consumet import ConsumetAPI
from api.downloader import Downloader, RichProgressHook

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler(sys.stdout)]
)
# Disable most logs for the CLI
logging.getLogger("yt_dlp").setLevel(logging.ERROR)
logging.getLogger("requests").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)

console = Console()

def get_videos_dir():
    """Get the user's Videos/Anime directory."""
    home = os.path.expanduser("~")
    videos_dir = os.path.join(home, "Videos", "Anime")
    if not os.path.exists(videos_dir):
        os.makedirs(videos_dir, exist_ok=True)
    return videos_dir

def get_unique_path(filepath):
    """If file exists, append (1), (2), etc. until a unique name is found."""
    if not os.path.exists(filepath):
        return filepath
    
    base, ext = os.path.splitext(filepath)
    counter = 1
    while os.path.exists(f"{base} ({counter}){ext}"):
        counter += 1
    return f"{base} ({counter}){ext}"

def main():
    console.print(Panel.fit("ANIME DOWNLOADER", style="bold cyan", border_style="blue"))
    
    api = ConsumetAPI()
    downloader = Downloader()
    
    # Step 1: Search
    query = Prompt.ask("[bold yellow]Enter anime name[/bold yellow]")
    if not query:
        return

    console.print(f"Searching for '[bold cyan]{query}[/bold cyan]'...")
    results = api.search(query)
    
    if not results:
        console.print("[bold red]No results found.[/bold red]")
        return

    # Display Results
    table = Table(title="Search Results", show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=4)
    table.add_column("Title", style="cyan")
    table.add_column("Release", style="green")
    
    for i, r in enumerate(results, 1):
        table.add_row(str(i), r.get('title'), r.get('releaseDate'))
    
    console.print(table)
    
    choice = IntPrompt.ask("Select an anime number", choices=[str(i) for i in range(1, len(results) + 1)])
    selected = results[choice - 1]
    anime_id = selected.get('id')
    anime_title = selected.get('title')

    # Step 2: Get Info & Episodes
    console.print(f"Fetching details for '[bold cyan]{anime_title}[/bold cyan]'...")
    info = api.get_info(anime_id)
    episodes = info.get('episodes', [])
    
    if not episodes:
        console.print("[bold red]No episodes found.[/bold red]")
        return

    console.print(f"Found [bold green]{len(episodes)}[/bold green] episodes.")
    
    # Episode Selection
    console.print("\nEnter episode range (e.g., '1', '1-5', or 'all'):")
    ep_range = Prompt.ask("Range")
    
    to_download = []
    if ep_range.lower() == 'all':
        to_download = episodes
    elif '-' in ep_range:
        try:
            start, end = map(int, ep_range.split('-'))
            to_download = [e for e in episodes if start <= float(e.get('number')) <= end]
        except ValueError:
            console.print("[bold red]Invalid range format.[/bold red]")
            return
    else:
        try:
            num = float(ep_range)
            to_download = [e for e in episodes if float(e.get('number')) == num]
        except ValueError:
            console.print("[bold red]Invalid episode number.[/bold red]")
            return

    if not to_download:
        console.print("[bold red]Invalid selection.[/bold red]")
        return

    # Step 3: Get Links for First Episode to choose Server
    first_ep = to_download[0]
    console.print(f"\nFetching available servers for [bold cyan]Episode {first_ep.get('number')}[/bold cyan]...")
    links_data = api.get_links(anime_id, first_ep.get('id'))
    sources = links_data.get('sources', [])
    
    if not sources:
        console.print("[bold red]No streaming links found.[/bold red]")
        return

    # Display Sources
    source_table = Table(title="Available Servers", show_header=True, header_style="bold magenta")
    source_table.add_column("#", style="dim", width=4)
    source_table.add_column("Server / Quality", style="cyan")
    
    for i, s in enumerate(sources, 1):
        source_table.add_row(str(i), s.get('quality'))
    
    console.print(source_table)
    
    source_choice = IntPrompt.ask("Select a server number", choices=[str(i) for i in range(1, len(sources) + 1)])
    preferred_server = sources[source_choice - 1].get('quality')

    # Step 4: Subtitles
    sub_choice = Prompt.ask("\nDownload & Embed Subtitles?", choices=["y", "n"], default="y")
    enable_subs = sub_choice == 'y'

    # Step 5: Download Path
    videos_dir = get_videos_dir()
    console.print(f"Videos will be saved to: [bold cyan]{videos_dir}[/bold cyan]")

    # Step 6: Download Episodes
    for ep in to_download:
        ep_num = ep.get('number')
        ep_id = ep.get('id')
        console.print(f"\n--- Processing Episode {ep_num} ---", style="bold yellow")
        
        links_data = api.get_links(anime_id, ep_id)
        sources = links_data.get('sources', [])
        
        if not sources:
            console.print(f"[bold red]No streaming links found for Episode {ep_num}.[/bold red]")
            continue
        
        # Match preferred server
        selected_source = next((s for s in sources if s.get('quality') == preferred_server), sources[0])
        
        url = selected_source.get('url')
        quality = selected_source.get('quality', 'default')
        referer = selected_source.get('referer')
        
        console.print(f"Using server: [bold cyan]{quality}[/bold cyan]")
        
        safe_title = "".join([c for c in anime_title if c.isalnum() or c in (' ', '.', '-', '_')]).strip()
        filename = f"{safe_title} - Episode {ep_num}.mp4"
        filepath = os.path.join(videos_dir, filename)
        filepath = get_unique_path(filepath)
        final_filename = os.path.basename(filepath)
        
        confirm = Prompt.ask(f"Download to '{final_filename}'?", choices=["y", "n"], default="y")
        if confirm == 'y':
            hook = RichProgressHook(console)
            success = downloader.download(url, filename=filepath, progress_hook=hook, referer=referer, write_subs=enable_subs, embed_subs=enable_subs)
            hook.stop()
            if success:
                console.print(f"[bold green]Successfully downloaded: {final_filename}[/bold green]")
            else:
                console.print(f"[bold red]Failed to download: {final_filename}[/bold red]")
        else:
            console.print("Skipping...")

    console.print("\nProcess finished. Enjoy your anime!", style="bold green")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]Cancelled by user.[/bold red]")
        sys.exit(0)
