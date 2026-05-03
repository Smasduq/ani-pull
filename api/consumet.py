import requests
import logging
import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class ConsumetAPI:
    """
    A robust scraper for Anitaku.to (Gogoanime) - using direct HTML extraction.
    """
    
    def __init__(self):
        self.base_url = "https://anitaku.to"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': self.base_url
        })
        logger.info(f"Anitaku scraper initialized at {self.base_url}")

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for anime."""
        url = f"{self.base_url}/search.html?keyword={query}"
        try:
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            for item in soup.select('ul.items li'):
                title_tag = item.select_one('p.name a')
                if title_tag:
                    results.append({
                        'id': title_tag['href'].split('/')[-1],
                        'title': title_tag['title'],
                        'releaseDate': item.select_one('p.released').text.strip() if item.select_one('p.released') else 'N/A'
                    })
            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def get_info(self, anime_id: str) -> Dict[str, Any]:
        """Get info and episodes directly from the category page."""
        url = f"{self.base_url}/category/{anime_id}"
        try:
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            episodes = []
            ep_items = soup.select('ul#episode_related li a')
            for ep in ep_items:
                href = ep['href'].strip()
                ep_num_tag = ep.select_one('div.name')
                if ep_num_tag:
                    ep_num_str = ep_num_tag.text.replace('EP', '').strip()
                    try:
                        ep_num = float(ep_num_str) if '.' in ep_num_str else int(ep_num_str)
                    except ValueError:
                        ep_num = ep_num_str
                    
                    episodes.append({
                        'id': href.split('/')[-1],
                        'number': ep_num,
                        'url': f"{self.base_url}{href}"
                    })
            
            # Fallback to AJAX
            if not episodes:
                movie_id_tag = soup.select_one('input#movie_id')
                if movie_id_tag:
                    movie_id = movie_id_tag['value']
                    ajax_url = f"https://ajax.gogocdn.net/ajax/load-list-episode?ep_start=0&ep_end=10000&id={movie_id}"
                    ep_res = self.session.get(ajax_url, timeout=15)
                    ep_soup = BeautifulSoup(ep_res.text, 'html.parser')
                    for ep in ep_soup.select('li a'):
                        href = ep['href'].strip()
                        ep_num_str = ep.select_one('div.name').text.replace('EP', '').strip()
                        ep_num = float(ep_num_str) if '.' in ep_num_str else int(ep_num_str)
                        episodes.append({
                            'id': href.split('/')[-1],
                            'number': ep_num,
                            'url': f"{self.base_url}{href}"
                        })
            
            try:
                episodes.sort(key=lambda x: float(x['number']))
            except:
                pass
            
            title_tag = soup.select_one('div.anime_info_body_bg h1')
            title = title_tag.text.strip() if title_tag else anime_id
            
            img_tag = soup.select_one('div.anime_info_body_bg img')
            image = img_tag['src'] if img_tag else None
            
            return {
                'id': anime_id,
                'title': title,
                'episodes': episodes,
                'image': image
            }
        except Exception as e:
            logger.error(f"Failed to fetch info: {e}")
            return {}

    def get_links(self, anime_id: str, episode_id: str) -> Dict[str, Any]:
        """Get video streams with extracted m3u8 and correct referers."""
        url = f"{self.base_url}/{episode_id}"
        try:
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            sources = []
            server_items = soup.select('div.anime_muti_link ul li a')
            for server in server_items:
                video_url = server.get('data-video')
                if video_url:
                    if video_url.startswith('//'):
                        video_url = 'https:' + video_url
                    
                    server_name = server.text.replace('Choose this server', '').strip()
                    
                    try:
                        player_res = self.session.get(video_url, timeout=10)
                        # Extract m3u8 from JS
                        m3u8_match = re.search(r'(const|var|let)\s+(src|file)\s*=\s*"(.*?\.m3u8.*?)"', player_res.text)
                        if m3u8_match:
                            real_url = m3u8_match.group(3)
                            real_url = urljoin(video_url, real_url)
                            
                            sources.append({
                                'url': real_url,
                                'quality': f"{server_name} (m3u8)",
                                'referer': video_url
                            })
                            continue
                    except Exception as ex:
                        logger.warning(f"Failed to extract m3u8 from {server_name}: {ex}")
                    
                    sources.append({
                        'url': video_url,
                        'quality': server_name,
                        'referer': video_url
                    })
            
            return {'sources': sources}
        except Exception as e:
            logger.error(f"Failed to fetch links: {e}")
            return {}
