import re
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
                  f"?fields=name,url,displayName&boards=open&board_fields=name,"
            query = {
                'key': self.key,
                'token': self.token
            }
            response = requests.get(URL, headers=self.headers, params=query)
            organization_details = json.loads(response.text)
            # only collect teams with "team" in the name
            if "team" in organization_details['name'].lower():
                # evaluate all boards of the organization and check their names to fit the criteria, if not delete from
                # the list of boards of the organization

                #create a deep copy of the board list to use it for iteration, because you can't iterate over a list and delete
                #elements at the same time.
                organization_boards = organization_details['boards'].copy()

                for board in organization_boards:
                    if "bewerbungen" in board['name'].lower() or \
                            "backlog" in board['name'].lower() or \
                            "pinnwand" in board['name'].lower() or \
                            "sprint planning" in board['name'].lower():
                        # delete this board from the list
                        organization_details['boards'].remove(board)
                        continue
                    # collect the filtered organization boards
                self.teams.append(organization_details)
                pass

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

    def get_custom_field_from_card(self, card_id: str, custom_field_id: str) -> {}:
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


    # define a function to get cards from all boards, that have a custom field and calculate the average for all cards with names that are alike
    def get_all_cards_from_all_boards_with_effort(self):

        effort_data = []

        # iterate over all boards in all teams
        for current_team in self.teams:
            for current_board in current_team['boards']:
                # get all cards from the board
                cards = self.get_cards_including_custom_field_from_board(current_board['id'])
                # iterate over all cards and print team name, board name, card name and effort-custom field
                for card in cards:
                    # get the custom fields for the card
                    if 'sprint' in card['name'].lower():
                        continue
                    if card['customFieldItems'][0]['value']['number'] != "0":
                        card['name'] = re.sub(r'\s*\([A-Za-z0-9\s]*\)|\s*\[[A-Za-z0-9\s]*\]', '', card['name'])
                        card_name = card['name']
                        #print(f"{current_team['displayName']}; {current_board['name']}, {card_name}; {card['customFieldItems'][0]['value']['number']}")

                        #put the data into a evaluatable data structure
                        effort_data.append({
                            'team': current_team['displayName'],
                            'board': current_board['name'],
                            'card': card_name,
                            'effort': card['customFieldItems'][0]['value']['number']
                        })
            #for all cards with the same name, calculate the average effort
            #get all cards with the same name
            cards_with_same_name = {}
            for card in effort_data:
                if card['card'] in cards_with_same_name:
                    cards_with_same_name[card['card']].append(card)
                else:
                    cards_with_same_name[card['card']] = [card]
            #calculate the average effort for all cards with the same name and print it sorted by card name
            for card_name in sorted(cards_with_same_name):
                effort_sum = 0
                for card in cards_with_same_name[card_name]:
                    effort_sum += float(card['effort'])
                average_effort = effort_sum / len(cards_with_same_name[card_name])
                print(f"{card_name}: {average_effort}")







    def get_cards_including_custom_field_from_board(self, current_board_id :str) -> []:
        URL = f"https://api.trello.com/1/boards/{current_board_id}?fields=name&cards=visible&card_fields=name&customFields=true&card_customFieldItems=true"
        query = {
            'key': self.key,
            'token': self.token
        }
        response = requests.request("GET", URL, headers=self.headers, params=query)
        if response.status_code != 200:
            return {}
        board = json.loads(response.text)
        # iterate over all custom fields to find the one with name  "Aufwand (h)"
        for custom_field in board['customFields']:
            if custom_field['name'] == "Aufwand (h)":
                effort_custom_field_id = custom_field['id']
        # iterate over all cards to find the ones with the custom field Aufwand (h)
        cards = []
        for card in board['cards']:
            for custom_field in card['customFieldItems'].copy():
                if custom_field['idCustomField'] == effort_custom_field_id:
                    cards.append(card)
                else:
                    card['customFieldItems'].remove(custom_field)
        return cards;

    # define a function to get cards from all boards, that have a custom field and calculate the average for all cards with names that are alike
    def get_all_cards_from_all_boards_with_effort_backup(self):
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
            if card['customFieldItems'] == [] or \
                    'sprint' in card['name'].lower():
                continue
            # print the card name and the date of the last activity in one line
            print(card['name'], end=";")
            print(card['dateLastActivity'], end=";")
            # get the custom fields for the card
            custom_fields = self.get_custom_fields_for_card(card['id'])
            if custom_fields == {}:
                print("0")
            for custom_field in custom_fields:
                if custom_field['value']['number'] != None:
                    print(custom_field['value']['number'])
                else:
                    print("0")

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
        # 4) get all cards from all boards with a custom field - use the function get_all_cards_from_all_boards_with_custom_field
        # 5) exit
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
            print("4) Get all cards from all boards with a custom field")
            print("5) Exit")
            function = int(input("Select function: "))
            if function == 1:
                self.get_all_done_cards_from_a_board()
            elif function == 2:
                self.print_cards_with_label("veröffentlichen")
            elif function == 3:
                self.print_cards_with_label("refine")
            elif function == 4:
                self.get_all_cards_from_all_boards_with_effort()
            elif function == 5:
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
