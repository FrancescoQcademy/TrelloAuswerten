import requests
import json
import os
# get necessary import for strptime
from datetime import datetime


class TrelloAPI:
    def __init__(self, key, token):
        self.key = key
        self.token = token
        self.headers = {
            "Accept": "application/json"
        }
        self.custom_field_definitions = {}
        self.team_boards = {}

    # gets all boards of the user
    def get_boards_and_organizations_i_have_access_to(self):
        url = "https://api.trello.com/1/members/me"
        query = {
            'key': self.key,
            'token': self.token
        }
        response = requests.get(url, headers=self.headers, params=query)
        response_dict = json.loads(response.text)
        self.organization_ids = response_dict['idOrganizations']
        self.boards = response_dict['idBoards']

    # gets all organizations of the user and filters them for "team" AND deletes all boards that have "bewerbungen",
    # "backlog" or "pinnwand" in the name
    def collect_user_boards_of_all_organizations_i_have_access_to(self):
        self.teams = []
        for organization_id in self.organization_ids:
            URL = f"https://api.trello.com/1/organizations/{organization_id}" \
                  f"?fields=name,url,displayName&boards=open&board_fields=name"
            query = {
                'key': self.key,
                'token': self.token
            }
            response = requests.get(URL, headers=self.headers, params=query)
            organization_details = json.loads(response.text)
            # only collect teams with "team" in the name
            if "team" in organization_details['name'].lower():
                # evaluate all boards of the organization and check their names to fit the criteria
                for board in organization_details['boards']:
                    if "bewerbungen" in board['name'].lower() or \
                            "backlog" in board['name'].lower() or \
                            "pinnwand" in board['name'].lower() or \
                            "sprint planning" in board['name'].lower():
                        # delete this board from the list
                        organization_details['boards'].remove(board)
                        continue
                    # collect the filtered organization boards
                self.teams.append(organization_details)

    # collect custom field definitions for a board
    # https://api.trello.com/1/boards/{id}/customFields?key={key}&token={token}
    def get_custom_field_definition_for_board(self, board_id):
        url = f"https://api.trello.com/1/boards/{board_id}/customFields"
        query = {
            'key': key,
            'token': token
        }
        response = requests.request("GET", url, headers=self.headers, params=query)
        if response.status_code != 200:
            return {}
        custom_fields = json.loads(response.text)
        self.custom_field_definitions = custom_fields
        return custom_fields

    def find_done_lists(self):
        self.done_lists = {}
        for board in self.boards:
            URL = f"https://api.trello.com/1/boards/{board['id']}" \
                  f"?fields=name,url,displayName&lists=open&list_fields=name"
            query = {
                'key': self.key,
                'token': self.token
            }
            response = requests.get(URL, headers=self.headers, params=query)
            board_dict = json.loads(response.text)
            for liste in board_dict['lists']:
                if liste['name'] == "Done":
                    self.done_lists[board_dict['name']] = liste['id']

    def get_custom_fields_for_card(self, card_id):
        url = f"https://api.trello.com/1/cards/{card_id}/customFieldItems"
        query = {
            'key': self.key,
            'token': self.token
        }
        response = requests.request("GET", url, headers=self.headers, params=query)
        # return empty result if responsecode is not 200
        if response.status_code != 200:
            return {}
        custom_fields = json.loads(response.text)
        return custom_fields

    def get_all_done_cards_from_a_board(self):

        # select team and board to work with
        print("Teams:")
        i = 0
        for team in self.teams:
            print(f"{team['displayName']} ({i})")
            i += 1
        team = self.teams[int(input("Select team: "))]
        self.boards = team['boards']

        self.find_done_lists()
        i = 0
        for board_name in self.done_lists:
            print(f"{board_name} ({i})")
            i += 1
        board_name = list(self.done_lists.keys())[int(input("Select board: "))]
        board_id = self.done_lists[board_name]
        liste = self.done_lists[board_name]
        print("")
        URL = f"https://api.trello.com/1/lists/{liste}/cards?fields=name,dateLastActivity&customFieldItems=true"
        query = {
            'key': self.key,
            'token': self.token
        }
        response = requests.request("GET", URL, headers=self.headers, params=query)
        cards = json.loads(response.text)
        for card in cards:
            print(card['name'])
            print(card['dateLastActivity'])
            print("")

    # get all cards in all boards of the team, that have the label "veröffentlichen"
    def get_cards_with_label(self, label):
        cards = []

        # collect cards on all boards, that have a defined label
        URL = f"https://api.trello.com/1/search?query=label:{label}&cards=all&card_fields=name,dateLastActivity,shortUrl,labels&customFieldItems=true"
        query = {
            'key': self.key,
            'token': self.token
        }
        response = requests.get(URL, headers=self.headers, params=query)
        cards_in_board = json.loads(response.text)['cards']

        return cards_in_board


    #print cards with label
    def print_cards_with_label(self, label):
        cards = self.get_cards_with_label(label)
        print(f"Found {len(cards)} cards with label {label}")
        print()
        print("name".ljust(60), "dateLastActivity".ljust(30), "shortUrl".ljust(60), sep="\t")
        print("----------------------------------------------------------------------------------------------------------------------------")
        for card in cards:
            print(card['name'].ljust(60), card['dateLastActivity'].ljust(30), card['shortUrl'].ljust(60), sep="\t")
        print("----------------------------------------------------------------------------------------------------------------------------")
        print("")

    def run(self):

        #select function to execute
        #either
        # 1) get all done cards from a board or
        # 2) get all cards from all boards with label "veröffentlichen"
        # 3) get all cards from all boards with label "refine"
        # 4) exit
        #also have a option to exit the program
        #repeat until user selects exit
        while True:

            self.get_boards_and_organizations_i_have_access_to()
            self.collect_user_boards_of_all_organizations_i_have_access_to()

            print("---- Qcademy Trello Cockpit - V0.1 ---")
            print("Select function to execute:")

            print("1) Get all done cards from a board")
            print("2) Get all cards from all boards with label \"veröffentlichen\"")
            print("3) Get all cards from all boards with label \"refine\"")
            print("4) Exit")
            function = int(input("Select function: "))
            if function == 1:
                self.get_all_done_cards_from_a_board()
            elif function == 2:
                self.print_cards_with_label("veröffentlichen")
            elif function == 3:
                self.print_cards_with_label("refine")
            elif function == 4:
                exit(0)
            else:
                print("Invalid input")
                return







if __name__ == "__main__":
    #check for available environment variables trello_token and trello_key
    if os.environ.get('trello_key') is None or os.environ.get('trello_token') is None:
        print("Please set environment variables trello_key and trello_token")
        exit(1)
    key = os.environ.get('trello_key')
    token = os.environ.get("trello_token")
    api = TrelloAPI(key, token)
    api.run()
