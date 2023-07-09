from unittest import TestCase
#import local class TrelloApi
from TrelloApi.api import TrelloAPI
import requests_mock


class TestTrelloAPI(TestCase):
    def test_find_item_in_named_list(self):
        # arrange
        # setup mock Trello API for https://api.trello.com/1/boards/63b31278b4d89900bc5f3cd3/lists?fields=name,dateLastActivity&customFieldItems=true&key=my_key&token=my_token&fields=name,url,displayName&lists=open&list_fields=name

        # define return values for the mock Trello API
        with requests_mock.Mocker() as mock_trello_api:
            mock_trello_api.get(
                "https://api.trello.com/1/boards/63b31278b4d89900bc5f3cd3?fields=name,url,displayName&lists=open&list_fields=name&key=my_key&token=my_token",
                json=[
                    {
                        "id": "1",
                        "name": "Backlog"
                    },
                    {
                        "id": "2",
                        "name": "Sprint Backlog"
                    },
                    {
                        "id": "3",
                        "name": "In Progress"
                    },
                    {
                        "id": "4",
                        "name": "Review"
                    },
                    {
                        "id": "5",
                        "name": "Done"
                    }
                ])
            # act
            # call the method under test
            sut = TrelloAPI("my_key", "my_token")
            listid = sut.find_item_in_named_list_for_board(list_name="Backlog", board_id="63b31278b4d89900bc5f3cd3")
            # assert
            # check the return value
            self.assertEqual(listid, "1")


if __name__ == '__main__':
    unittest.main()
