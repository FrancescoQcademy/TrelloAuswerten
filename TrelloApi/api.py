import math
import re
import requests
import json
import os
import colorama
from colorama import Fore, Back, Style
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
        return self.boards

    #return all boards of the user with information on board name and id
    def get_boards_i_have_access_to(self):
        url = "https://api.trello.com/1/members/me"
        query = {
            'key': self.key,
            'token': self.token
        }
        response = requests.get(url, headers=self.headers, params=query)
        response_dict = json.loads(response.text)
        self.boards = response_dict['idBoards']
        return self.boards

    # retrun a dictionary with board names and ideas based on self.boards
    def get_board_names_and_ids(self):

        url = "https://getflowshare.com/de/preisgestaltung/?utm_medium=referral&utm_source=flowshare&utm_campaign=settings-de"
        boards = {}
        for board in self.boards:
            url = f"https://api.trello.com/1/boards/{board}"
            query = {
                'key': self.key,
                'token': self.token
            }
            response = requests.get(url, headers=self.headers, params=query)
            response_dict = json.loads(response.text)
            boards[response_dict['name']] = response_dict['id']
        return boards

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

    def find_item_in_named_list_for_board(self, list_name: str, board_id: str):
        item_list = []
        list_id = ""
        URL = f"https://api.trello.com/1/boards/{board_id}" \
              f"?fields=name,url,displayName&lists=open&list_fields=name"
        query = {
            'key': self.key,
            'token': self.token
        }
        response = requests.get(URL, headers=self.headers, params=query)
        board_dict = json.loads(response.text)
        for liste in board_dict['lists']:
            if liste['name'] == "list_name":
                list_id = liste['id']
        if list_id == "":
            return []
        URL = f"https://api.trello.com/1/lists/{list_id}/cards"
        query = {
            'key': self.key,
            'token': self.token
        }
        try:
            response = requests.get(URL, headers=self.headers, params=query)
            cards = json.loads(response.text)
            for card in cards:
                item_list.append(card['name'])
        except  Exception as e:
            print(e)
            return []
        return item_list


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
        cards_with_same_name = {}

        # iterate over all boards in all teams and gather effort data
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
                        card['name'] = self.clean_card_name(card['name'])
                        card_name = card['name']
                        #put the data into a evaluatable data structure
                        effort_data.append({
                            'team': current_team['displayName'],
                            'board': current_board['name'],
                            'card': card_name,
                            'effort': card['customFieldItems'][0]['value']['number'],
                        })
                if (len(effort_data) == 0):
                    continue
        #for all cards with the same name, calculate the average effort and the sample size
        #get all cards with the same name

        for card in effort_data:
            if card['card'] in cards_with_same_name:
                cards_with_same_name[card['card']].append(card)
            else:
                cards_with_same_name[card['card']] = [card]

        #sort cards_with_same_name by card name
        cards_with_same_name = dict(sorted(cards_with_same_name.items()))

        #calculate average, standard deviation, median, min and max for all cards, group by card name
        for card_name in cards_with_same_name:
            effort_data = cards_with_same_name[card_name]

            effort_sum = 0
            sample_size = len(cards_with_same_name[card_name])
            effort_list = []
            if sample_size == 0:
                continue
            for card in effort_data:
                effort_sum += float(card['effort'])
                effort_list.append(float(card['effort']))
                #sample_size += 1
            average_effort = effort_sum / sample_size   #average
            effort_list.sort()
            median_effort = effort_list[int(sample_size/2)] #median
            min_effort = effort_list[0] #min
            max_effort = effort_list[-1] #max
            effort_sum = 0
            for effort in effort_list:
                effort_sum += (effort - average_effort)**2
            standard_deviation = math.sqrt(effort_sum / sample_size) #standard deviation
            print(f"{card_name} Average: {average_effort}; Standard Deviation: {standard_deviation}; Median: {median_effort}; Min: {min_effort}; Max: {max_effort}")

    def clean_card_name(self, card_name):
        cleaned_card_name = re.sub(r'\s*\([A-Za-z0-9\s]*\)|\s*\[[A-Za-z0-9\s]*\]', '', card_name)
        return cleaned_card_name

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


    def get_cards_from_board(self, current_board_id :str) -> []:
        URL = f"https://api.trello.com/1/boards/{current_board_id}?fields=name&cards=visible&card_fields=name&customFields=true&card_customFieldItems=true"
        query = {
            'key': self.key,
            'token': self.token
        }
        response = requests.request("GET", URL, headers=self.headers, params=query)
        if response.status_code != 200:
            return {}
        board = json.loads(response.text)
        return board['cards']

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


    # rename a card, return success status and new name of card, as well as the link to the card
    def rename_card(self, card_id, new_name):
        URL = f"https://api.trello.com/1/cards/{card_id}?name={new_name}"
        query = {
            'key': self.key,
            'token': self.token
        }
        response = requests.request("PUT", URL, headers=self.headers, params=query)
        card = json.loads(response.text)
        return card['name'] == new_name, card['name'], card['shortUrl']

    def get_all_cards_from_one_board_and_calculate_efforts(self):
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
        sum_efforts = 0.0
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
                    sum_efforts += float(custom_field['value']['number'])
                else:
                    print("0")
        print(f"Sum of efforts: {sum_efforts}")


    #get all lists of a board
    def get_all_lists(self, board_id):
        URL = f"https://api.trello.com/1/boards/{board_id}/lists"
        query = {
            'key': self.key,
            'token': self.token
        }
        response = requests.request("GET", URL, headers=self.headers, params=query)
        lists = json.loads(response.text)
        return lists

    #for a board, return all cards - return only fields: card name, card id, card url
    def get_all_cards(self, board_id):
        URL = f"https://api.trello.com/1/boards/{board_id}/cards?fields=name,id,shortUrl"
        query = {
            'key': self.key,
            'token': self.token
        }
        response = requests.request("GET", URL, headers=self.headers, params=query)
        cards = json.loads(response.text)
        return cards

    def select_board(self):
        i = 0
        localBoards = []
        for team in self.teams:
            print(f"----------{team['displayName']} ----------")
            for board in team['boards']:
                print(f"{board['name']} ({i})")
                localBoards.append(board['id'])
                i += 1
        board_id = localBoards[int(input("Select board: "))]
        return board_id

    def add_checkpoint_to_all_cards_in_board(self, board_id, checklist_name, checkpoint_name):
        cards = self.get_all_cards(board_id)
        i = 0
        for card in cards:
            print (f"{i} Adding checkpoint to card {card['name']} .. ", end="")
            self.add_checkpoint_to_card_if_not_present(card['id'], checklist_name, checkpoint_name)
            i = i + 1

    def add_checkpoint_to_card(self, checklist_id, check_item_name):
        URL = f"https://api.trello.com/1/checklists/{checklist_id}/checkItems"
        query = {
            'key': self.key,
            'token': self.token,
            'name': check_item_name
        }
        response = requests.request("POST", URL, headers=self.headers, params=query)
        if response.status_code != 200:
            print(Fore.RED+f"Error adding checklist to card {card_id}"+Fore.RESET)
            return False
        print(Fore.GREEN+f"Checkpoint added"+Fore.RESET)
        return True

    def add_checkpoint_to_card_if_not_present(self, card_id, checklist_name, check_item_name):
        done = False
        checklists = self.get_checklists_for_card_id(card_id, check_item_name)
        for checklist in checklists:
            if checklist_name != checklist['name']:
                continue
            # check if checklist item already exists
            # extract all checklist items names as new list
            name_list = [item['name'] for item in checklist['checkItems']]
            if check_item_name in name_list:
                print(Fore.BLUE+f"Checkpoint already exists"+Fore.RESET)
                return
            else:
                self.add_checkpoint_to_card(checklist['id'], check_item_name)
                done = True
        if not done:
            print (Fore.LIGHTRED_EX+"Checklist not found"+Fore.RESET)

    def get_checklists_for_card_id(self, card_id, check_item_name):
        URL = f"https://api.trello.com/1/cards/{card_id}/checklists"
        query = {
            'key': self.key,
            'token': self.token,
            'name': check_item_name
        }
        response = requests.request("GET", URL, headers=self.headers, params=query)
        if response.status_code != 200:
            print(f"Error getting checklists for card {card_id}")
            return []
        checklists = json.loads(response.text)
        return checklists

    def run(self):

        #select function to execute
        #either
        # 1) get all done cards from a board or
        # 2) get all cards from all boards with label "veröffentlichen"
        # 3) get all cards from all boards with label "refine"
        # 4) get all cards from all boards with a custom field - use the function get_all_cards_from_all_boards_with_custom_field
        # 5) get all cards from one named board and calculate efforts
        # 6) add a specific checkpoint to all cards in a board, if not yet present
        # 7) get all cards from all boards in list "review" and list with assignees and short url
        # 0) exit
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
            print("4) Get cards Effort Data")
            print("5) Get all cards from a board to sum efforts")
            print("6) Add a checkpoint to all cards in a board")
            print("7) Get all cards from all boards in list \"review\" and list with assignees and short url")
            print("0) Exit")
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
                self.get_all_cards_from_one_board_and_calculate_efforts()
            elif function == 6:
                self.add_checkpoint_to_all_cards_in_board(self.select_board(), "Acceptance Criteria", "Fill out Feedback Form https://forms.gle/g4BR8kehcamNowHw9")
            elif function == 7:
                self.print_cards_in_list("review", True)
            elif function == 0:
                exit(0)
            else:
                print("Invalid input")


if __name__ == "__main__":
    #check for available environment variables trello_token and trello_key
    if os.environ.get('trello_key') is None or os.environ.get('trello_token') is None:
        print("Please set environment variables trello_key and trello_token")
        exit(1)
    key = os.environ.get('trello_key')
    token = os.environ.get("trello_token")
    api = TrelloAPI(key, token)
    api.run()
