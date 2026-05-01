from AnimepaheAPI.animepahe import AnimepaheAPI
import logging

logging.basicConfig(level=logging.INFO)

def test_search():
    api = AnimepaheAPI()
    try:
        results = api.search("One Piece")
        print(f"Search results: {results}")
    except Exception as e:
        print(f"Search failed: {e}")

if __name__ == "__main__":
    test_search()
