#!/usr/bin/env python3
"""
Anime Downloader CLI - Interactive anime search and download tool
"""
from AnimepaheAPI.animepahe import AnimepaheAPI
import json
import sys


def print_banner():
    print("=" * 50)
    print("       Anime Downloader - Animepahe CLI")
    print("=" * 50)
    print()


def print_anime_list(results):
    """Display search results in a formatted way"""
    print("\n📺 Search Results:")
    print("-" * 50)
    for i, anime in enumerate(results, 1):
        title = anime.get('title', 'Unknown')
        anime_type = anime.get('type', 'N/A')
        episodes = anime.get('episodes', 'N/A')
        status = anime.get('status', 'N/A')
        score = anime.get('score', 'N/A')
        season = anime.get('season', '')
        year = anime.get('year', '')
        
        print(f"{i}. {title}")
        print(f"   Type: {anime_type} | Episodes: {episodes} | Status: {status}")
        print(f"   Season: {season} {year} | Score: {score}")
        print()


def print_episode_info(release_data):
    """Display episode information"""
    result = release_data.get('result', {})
    print(f"\n🎬 Episode {result.get('episode', 'N/A')}")
    print("-" * 30)
    print(f"   Duration: {result.get('duration', 'N/A')} minutes")
    print(f"   Session ID: {result.get('session', 'N/A')}")
    print()


def print_download_options(download_data):
    """Display available download qualities"""
    results = download_data.get('results', [])
    print("\n📥 Available Downloads:")
    print("-" * 50)
    for i, option in enumerate(results, 1):
        quality = option.get('quality', 'N/A')
        size = option.get('size', 'N/A')
        audio = option.get('audio', 'N/A')
        url = option.get('url', 'N/A')
        
        print(f"{i}. Quality: {quality} | Size: {size} | Audio: {audio}")
        if url:
            print(f"   URL: {url[:80]}..." if len(url) > 80 else f"   URL: {url}")
        else:
            print(f"   URL: Not available")
        print()


def get_user_choice(max_options, prompt="Enter your choice"):
    """Get a valid user choice from menu"""
    while True:
        try:
            choice = input(f"{prompt} (1-{max_options}) or 'q' to quit: ").strip()
            if choice.lower() == 'q':
                return None
            choice_num = int(choice)
            if 1 <= choice_num <= max_options:
                return choice_num
            else:
                print(f"❌ Please enter a number between 1 and {max_options}")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")


def print_episode_list(anime_title, release_data, total_episodes):
    """Display list of available episodes"""
    print(f"\n📋 Episodes for: {anime_title}")
    print("-" * 50)
    print(f"Total Episodes: {total_episodes}")
    print("-" * 50)
    
    result = release_data.get('result', {})
    episode = result.get('episode', 'N/A')
    duration = result.get('duration', 'N/A')
    print(f"1. Episode {episode} (Duration: {duration} min) - Most recent")
    print(f"\n💡 Use option 1 to get the latest episode, or modify the code to fetch specific episodes.")


def main():
    print_banner()
    
    # Initialize API
    animepahe = AnimepaheAPI()
    
    # Step 1: Search for anime
    search_query = input("🔍 What anime would you like to search for? ").strip()
    
    if not search_query:
        print("❌ Search query cannot be empty.")
        return
    
    print(f"\n⏳ Searching for '{search_query}'...")
    
    try:
        results = animepahe.search(search_query)
        
        if not results:
            print("❌ No results found. Try a different search term.")
            return
        
        print_anime_list(results)
        
        # Step 2: Select anime
        choice = get_user_choice(len(results), "Select an anime")
        
        if choice is None:
            print("👋 Goodbye!")
            return
        
        selected_anime = results[choice - 1]
        anime_id = selected_anime['id']
        anime_title = selected_anime['title']
        total_episodes = selected_anime.get('episodes', 'Unknown')
        
        print(f"\n✅ You selected: {anime_title}")
        
        # Step 3: Get episodes (using session from search result)
        session = selected_anime.get('session')
        
        if not session:
            print("❌ No session available for this anime.")
            return
        
        # Get first episode to see total count
        print(f"\n⏳ Fetching episode information for {anime_title}...")
        release_data = animepahe.get_release(str(anime_id), episode=1)
        
        if release_data.get('success'):
            print_episode_list(anime_title, release_data, total_episodes)
            
            # Step 4: Get download links for episode 1
            episode_session = release_data['result'].get('session')
            
            if episode_session:
                print("\n⏳ Fetching download links for latest episode...")
                download_data = animepahe.get_download_links(episode_session)
                
                if download_data.get('success'):
                    print_download_options(download_data)
                    
                    # Step 5: Offer to download
                    results_list = download_data.get('results', [])
                    if results_list:
                        dl_choice = get_user_choice(len(results_list), "Select download quality")
                        
                        if dl_choice:
                            selected_option = results_list[dl_choice - 1]
                            print(f"\n✅ Selected: {selected_option.get('quality')} - {selected_option.get('size')}")
                            print(f"📎 Download URL: {selected_option.get('url')}")
                            print("\n💡 You can use yt-dlp or ffmpeg to download the .m3u8 stream.")
                else:
                    print("❌ Failed to get download links.")
        else:
            print("❌ Failed to get episode information.")
            
    except KeyboardInterrupt:
        print("\n\n👋 Operation cancelled. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return


if __name__ == "__main__":
    main()

