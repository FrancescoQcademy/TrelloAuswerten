# This is a sample Python script.

# Press Umschalt+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Strg+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # This code sample uses the 'requests' library:
    # http://docs.python-requests.org
    import requests
    import json

    url = "https://api.trello.com/1/boards/hxlYmwUJ/cards"

    query = {
        'key': '6ca3c0ee0cad50a92362992b206bf056',
        'token': 'cd38c02d7d9509896c3ce33336b7f753f323f8b6a60f85aa402a4737ac8eeccc'
    }

    response = requests.request(
        "GET",
        url,
        params=query
    )

    data = json.loads(response.text)
    for card in data:
        print(card['name'], end=', ')
        for label in card['labels']:
            print(label['name'], end=', ')
        print()
    #print(data)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
