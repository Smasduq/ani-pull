import unittest
from unittest.mock import patch, MagicMock
from api.consumet import ConsumetAPI

class TestConsumetAPI(unittest.TestCase):
    def setUp(self):
        self.api = ConsumetAPI()

    @patch('requests.get')
    def test_search_success(self, mock_get):
        # Mocking a successful response from the API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'results': [{'id': 'one-piece', 'title': 'One Piece', 'releaseDate': '1999'}]
        }
        mock_get.return_value = mock_response

        results = self.api.search('one piece')
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], 'one-piece')
        self.assertEqual(results[0]['title'], 'One Piece')

    @patch('requests.get')
    def test_get_info_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'one-piece',
            'title': 'One Piece',
            'episodes': [{'id': 'ep-1', 'number': 1}]
        }
        mock_get.return_value = mock_response

        info = self.api.get_info('one-piece')
        
        self.assertEqual(info['id'], 'one-piece')
        self.assertEqual(len(info['episodes']), 1)

if __name__ == '__main__':
    unittest.main()
