# This code sample uses the 'requests' library:
# http://docs.python-requests.org
import requests
import json
import os

# get trello api key from environment
key = os.environ.get('trello_key')
token = os.environ.get("trello_token")

url = "https://api.trello.com/1/members/me"

headers = {
    "Accept": "application/json"
}

query_org_1 = {
    'key': key,
    'token': token
}

response = requests.request("GET", url, headers=headers, params=query_org_1)

doneLists = []

organization_ids = json.loads(response.text)['idOrganizations']
boards = json.loads(response.text)['idBoards']
#


#find all organizations with "team" in the name
#list all these teams and ask the user to select one
teams = []
for organization_id in organization_ids:
    organization_board = []
    URL = "https://api.trello.com/1/organizations/" + organization_id + "?fields=name,url&boards=open&board_fields=name"
    organization_response = requests.request("GET", URL, headers=headers, params=query_org_1)
    organization = json.loads(organization_response.text)
    if not "team" in organization['name'].lower():
        continue
    teams.append(organization)
i = 0
for team in teams:
    print (team['name'] + ' (' + str(i) + ')')
    i = i + 1
team = teams[int(input('Select team: '))]
organization_boards = []

# delete all boards from team['boards'] that have "bewerbungen", "backlog" or "pinnwand" in the name
for board in team['boards']:
    if "bewerbungen" in board['name'].lower() or "backlog" in board['name'].lower() or "pinnwand" in board['name'].lower():
        #delete this board from the list
        team['boards'].remove(board)
        continue
    else:
        organization_boards.append(board)

# find and list all boards in these organizations that have a list called "done"
# list all these boards and ask the user to select one
i = 0
doneLists = {}
for board in organization_boards:
    URL = "https://api.trello.com/1/boards/" + board['id'] + "?fields=name,url&lists=open&list_fields=name"
    boards_response = requests.request("GET", URL, headers=headers, params=query_org_1)
    boards = json.loads(boards_response.text)

    for liste in boards['lists']:
        if liste['name'] == "Done":
            doneLists[board['name']] = liste['id']
            print(board['name'] + ' (' + str(i) + ')')
            i = i + 1
        else:
            continue
board = organization_boards[int(input('Select board: '))]
liste = doneLists[board['name']]
print("")
# find all cards in this "done" list
# print the name of the card and the labels
URL = "https://api.trello.com/1/lists/" + liste + "/cards"
cards_response = requests.request("GET", URL, headers=headers, params=query_org_1)
cards = json.loads(cards_response.text)
for card in cards:
    if "sprint" in card['name'].lower():
        continue
    print(card['name'], end=', ')
    print(card['dateLastActivity'])

