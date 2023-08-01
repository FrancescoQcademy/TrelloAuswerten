from unittest import TestCase
#import local class TrelloApi
from TrelloApi.api import TrelloAPI
import requests_mock


class TestTrelloAPI(TestCase):
    json_expected_lists = [
                    { "id": "1", "name": "Backlog"},
                    { "id": "2", "name": "Sprint Backlog"},
                    { "id": "3", "name": "In Progress"},
                    { "id": "4", "name": "Review" },
                    { "id": "5", "name": "Done"}
    ]

    json_expected_cards = [
                    { "id": "6486cf58ad8a489bbd41f2bc", "name": "Basic Locators Practice 1", "shortUrl": "https://trello.com/c/efDRSS3d" },
                    { "id": "6486cf463bd2b2fe3e3d1dde", "name": "Basic Introduction to Selenium", "shortUrl": "https://trello.com/c/hVs8vz9o"}
    ]

    def test_find_item_in_named_list(self):
        # arrange
        # setup mock Trello API for https://api.trello.com/1/boards/63b31278b4d89900bc5f3cd3/lists?fields=name,dateLastActivity&customFieldItems=true&key=my_key&token=my_token&fields=name,url,displayName&lists=open&list_fields=name

        # define return values for the mock Trello API
        with requests_mock.Mocker() as mock_trello_api:
            mock_trello_api.get(
                url="https://api.trello.com/1/boards/63b31278b4d89900bc5f3cd3/lists?fields=name&filter=open&key=my_key&token=my_token",
                json=self.json_expected_lists)
            mock_trello_api.get(
                url="https://api.trello.com/1/lists/1/cards?fields=name,shortUrl&key=my_key&token=my_token",
                json=self.json_expected_cards)

            # act
            # call the method under test
            sut = TrelloAPI("my_key", "my_token")
            actual_cards = sut.find_item_in_named_list_for_board(list_name="Backlog", board_id="63b31278b4d89900bc5f3cd3")
            # assert
            # check the return value
            self.assertEqual(actual_cards, self.json_expected_cards)


if __name__ == '__main__':
    unittest.main()
