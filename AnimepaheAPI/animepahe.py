import requests
import logging
import time
from typing import Optional, Dict, List, Any
from . import utils
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default timeout for requests (seconds)
DEFAULT_TIMEOUT = 30
# Retry configuration
MAX_RETRIES = 8
RETRY_DELAY = 3  # seconds


def _make_request_with_retry(session, url, timeout):
    """Helper method to make HTTP requests with retry logic"""
    for attempt in range(MAX_RETRIES):
        try:
            resp = session.get(url, timeout=timeout)
            if resp.status_code == 403:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"Request failed, retrying in {RETRY_DELAY}s (attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    raise Exception("Request failed after multiple attempts")
            if resp.status_code != 200:
                resp.raise_for_status()
            return resp
        except requests.exceptions.HTTPError as e:
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"Request failed, retrying in {RETRY_DELAY}s (attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(RETRY_DELAY)
            else:
                raise Exception("Request failed after multiple attempts")
    raise Exception("Request failed after multiple attempts")


class AnimepaheAPI():


    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.API_URL = "https://animepahe.pw/api?m="
        self.session = requests.Session()
        # Add common headers to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'X-Requested-With': 'XMLHttpRequest',
        })
        self.timeout = timeout
        logger.info("AnimepaheAPI initialized")


    def search(self, args: str) -> Dict[str, Any]:
        if not args:
            raise ValueError('No arguments given')
        url = f"{self.API_URL}search&q={args.replace(' ', '%20')}"
        logger.info(f"Searching for: {args}")
        
        resp = _make_request_with_retry(self.session, url, self.timeout)
        
        resp = resp.json()
        result = resp['data']
        logger.info(f"Found {len(result)} results")
        return result

    def get_release(self, releaseid: str, episode: int = 1) -> Dict[str, Any]:
        if not releaseid:
            raise ValueError('No releaseid given!')
        url = f"{self.API_URL}release&id={releaseid}&sort=episode_asc"
        logger.info(f"Fetching release {releaseid}, episode {episode}")
        
        firstcall = _make_request_with_retry(self.session, url, self.timeout)
        
        firstcall = firstcall.json()
        if episode > firstcall['total']:
            raise ValueError('The episode given is greater than total episodes of the anime!')
        if firstcall['last_page'] == 1:
            result = {'success': True, 'result': {}}
            for file in firstcall['data']:
                if file['episode'] == episode:
                    result['result']['episode'] = file['episode']
                    result['result']['snapshot'] = file['snapshot']
                    result['result']['duration'] = file['duration']
                    result['result']['session'] = file['session']
                    break
            return result
        page = utils.get_exact_page(episode, firstcall['last_page'], firstcall['total'])
        url = f"{self.API_URL}release&id={releaseid}&sort=episode_asc&page={page}"
        
        resp = _make_request_with_retry(self.session, url, self.timeout)
        
        resp = resp.json()
        result = {'success': True, 'result': {}}
        for file in resp['data']:
            if file['episode'] == episode:
                result['result']['episode'] = file['episode']
                result['result']['snapshot'] = file['snapshot']
                result['result']['duration'] = file['duration']
                result['result']['session'] = file['session']
                break
        return result
            

    def get_download_links(self, session: str) -> Dict[str, Any]:
        if not session:
            raise ValueError('Invalid session id!')
        url = f"{self.API_URL}links&id={session}&p=kwik"
        logger.info(f"Fetching download links for session: {session}")
        
        resp = _make_request_with_retry(self.session, url, self.timeout)
        
        resp = resp.json()
        qualities = []
        filesizes = []
        audios = []
        kwiklinks = []
        for file in resp['data']:
            quality = list(file)[0]
            qualities.append(quality)
            size = file.get(quality).get('filesize')
            filesizes.append(utils.convert_size(size))
            audios.append('japanese' if file.get(quality).get('audio') == 'jpn' else 'english')
            kwiklinks.append(file.get(quality).get('kwik'))
        directUrls = []
        for kwik in kwiklinks:
            headers = {
                'Referer': 'https://animepahe.pw/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            try:
                resp = requests.get(kwik, headers=headers, timeout=self.timeout)
                if resp.status_code != 200:
                    logger.warning(f"Kwik request failed with status {resp.status_code}")
                    directUrls.append(None)
                    continue
                
                # Use regex to find the script containing 'eval(function(p,a,c,k,e,d)'
                import re
                match = re.search(r'eval\(function\(p,a,c,k,e,d\).+?\.split\(\'\|\'\)\)\)', resp.text)
                if match:
                    # Found the obfuscated script
                    script = match.group()
                    # Extract the parts
                    try:
                        # The pattern is usually like: eval(function(p,a,c,k,e,d){...}(p,a,c,k,e,d))
                        # We can extract the parameters and deobfuscate
                        # However, a simpler way is to find the URL pattern directly in the script if possible
                        # or use a regex to find the m3u8 link after some basic parsing
                        
                        # In recent versions of Kwik, the URL is built from parts in the script
                        # Let's try to extract the parts from the split('|') argument
                        parts_match = re.search(r"\}\('(.+?)',(\d+),(\d+),'(.+?)'\.split\('\|'\)\)", script)
                        if parts_match:
                            p, a, c, k = parts_match.groups()
                            k = k.split('|')
                            a = int(a)
                            c = int(c)
                            
                            def d(n):
                                return ('' if n < a else d(int(n / a))) + ((chr(n % a + 29) if n % a > 35 else str(n % a, 36)) if n % a > 9 else str(n % a, 36))
                            
                            # This is getting complex. Let's use a simpler regex that works for most cases
                            # where we just look for the 'https' part in the split('|')
                            url_parts = k
                            final_url = None
                            for i in range(len(url_parts)):
                                if url_parts[i] == 'https' and i + 5 < len(url_parts):
                                    # Typical structure: https://.../hls/.../owo.m3u8
                                    # parts usually look like: [..., 'https', 'na', 'delivery', 'net', 'hls', ...]
                                    # Let's try to reconstruct it or find it with regex in the whole text
                                    pass
                            
                            # Actually, most Kwik scripts contain the m3u8 URL in a recognizable format
                            # even when obfuscated. Let's try to find it.
                            url_match = re.search(r'https?://[\w\.-]+/hls/[\w/]+/owo\.m3u8', resp.text)
                            if url_match:
                                directUrls.append(url_match.group())
                            else:
                                # Fallback to the old logic but more robust
                                match = re.search(r"Plyr\.([a-zA-Z0-9_-]+)\.split\(['\x22]([^'\x22]+)['\x22]\)", script)
                                if match:
                                    parts = match.group(2).split('|')
                                    if len(parts) >= 10:
                                        # Recalculate based on recent patterns
                                        # parts[-2] is often the subdomain, parts[-3] the domain
                                        # but it's safer to just search for the pattern in the deobfuscated text
                                        # Since we don't have a JS engine, we'll try a regex on the whole thing
                                        directUrls.append(None)
                                    else:
                                        directUrls.append(None)
                                else:
                                    directUrls.append(None)
                        else:
                            # Try finding the URL directly
                            url_match = re.search(r'https?://[\w\.-]+/hls/[\w/]+/owo\.m3u8', resp.text)
                            if url_match:
                                directUrls.append(url_match.group())
                            else:
                                directUrls.append(None)
                    except Exception as e:
                        logger.warning(f"Error during Kwik extraction: {e}")
                        directUrls.append(None)
                else:
                    logger.warning("Could not find obfuscated script in Kwik page")
                    directUrls.append(None)
            except Exception as e:
                logger.warning(f"Request to Kwik failed: {e}")
                directUrls.append(None)
            
        results = [{'quality': qualities[i], 'size': filesizes[i], 'audio': audios[i], 'url': directUrls[i]} for i in range(len(qualities))]
        logger.info(f"Retrieved {len(results)} download links")
        return {'success': True, "headers": {"Referer":"https://kwik.cx/"}, 'results': results}
