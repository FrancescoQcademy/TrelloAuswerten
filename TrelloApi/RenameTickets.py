# I want to read a google doc spreadsheet and rename tickets in Trello
# the ticket id will be used as a prefix to the ticket name
# the ticket name will be the name of the ticket in the spreadsheet
# the spreadsheet will be open to read from anyone with the link
# jira connection will be provided by api-token and api-key
# the spreadsheet link will be hard coded in the script
# the trello connection will be hard coded in the script
# the spreadsheet will be read from the first row to the last row
# story name will be in a column called "Story"
# story id will be in a column called "UE Code"
# the script will be run from the command line
# the script will run without any arguments
# the script will list all boards accessible to the user
# the script will ask the user to select a board
# the script will then rename the tickets in the selected board
# the script will print the name of the ticket and the new name of the ticket
# the script will print the number of tickets renamed
# the script will print the number of tickets that could not be renamed
# the script will print the name of the tickets that could not be renamed
# the script will print the reason why the tickets could not be renamed
# the script will print the number of tickets that were renamed
# the script will print the name of the tickets that were renamed
# the script will print the new name of the tickets that were renamed
# the script will print the number of tickets that were not renamed
# the script will print the name of the tickets that were not renamed
# the script will print the reason why the tickets were not renamed
# the script will print the number of tickets that were not renamed
# the script will print the name of the tickets that were not renamed

from TrelloApi import api
import os
import gspread



#class to access the google doc spreadsheet
class GoogleDoc:
    def __init__(self, url):
        self.url = url
        self.storys = []
        self.storys_not_found = []
        self.storys_not_renamed = []
        self.storys_renamed = []
        self.storys_not_renamed_reason = []
        self.storys_not_found_reason = []
        self.storys_renamed_reason = []

    def get_storys(self):
        #get the spreadsheet
        url = "gspread"
        expected_headers = ["Story", "UE Code"]
        #read the spreadsheet
        try:
            gc = gspread.service_account()
            #get the sheet "Aufwand pro Modul und LE"
            worksheet_document = gc.open_by_url(self.url)
            #get the storys names from column "Story
            sheet = worksheet_document.get_worksheet(0)
            records = sheet.get_all_records(expected_headers=expected_headers)
            #clear all fields, not in expected_headers
            self.storys = [{key: value for key, value in record.items() if key in expected_headers} for record in records]
        except Exception as e:
            print("Error: " + str(e))
            exit(1)
        return self.storys

    def get_new_name_for_story(self, old_name:str):
        new_name = ""
        for story in self.storys:
            if story["Story"] == old_name:
                new_name = story["UE Code"] + " - " + old_name
                break
        return new_name

if __name__ == "__main__":
    #check for available environment variables trello_token and trello_key
    if os.environ.get('trello_key') is None or os.environ.get('trello_token') is None:
        print("Please set environment variables trello_key and trello_token")
        exit(1)
    key = os.environ.get('trello_key')
    token = os.environ.get("trello_token")
    api = TrelloApi.TrelloAPI(key, token)

    # initialize GoogleDoc
    doc = GoogleDoc("https://docs.google.com/spreadsheets/d/1q_bMG5F4wvdc_vcQ3l4GL6R54rnOjCH6ujqNKIFdgRA")
    # get all storys from google doc
    doc.get_storys()
    print ("Story names loaded from GDrive")


    # get all boards
    api.get_boards_i_have_access_to()
    boards = api.get_board_names_and_ids()
    # #print all board - numbered - than ask which board to use
    i = 0
    board_list = []
    for board in boards.keys():
        if "Bewerbung" in board:
            continue
        board_list.append(board)
        print(f"{i}) {board}")
        i = i + 1
    # get board id from user
    board_id = input("Please enter the board id: ")
    # #get all storys in the board
    technical_board_id = boards[board_list[int(board_id)]]
    cards = api.get_cards_from_board(technical_board_id)
    # #simulate renaming all storys
    for card in cards:
         card_name_original = card["name"]
         if "sprint" in card_name_original.lower():
            continue
         card_name_cleaned = api.clean_card_name(card["name"])
         card_name_new = doc.get_new_name_for_story(card_name_cleaned)
         if len(card_name_new) == 0:
             print (f"Card name is empty: {card['name']}")
             continue
         card_name = card_name_original.replace(card_name_cleaned, card_name_new)
         print(f"Old name: {card['name']} - New name: {card_name}")


