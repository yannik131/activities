import random
import json


def create_deck(*ranks):
    colors = ["c", "h", "s", "d"]
    deck = []
    for color in colors:
        for rank in ranks:
            deck.append(rank+color)
    random.shuffle(deck)
    return deck
    

def deal_cards(data, players):
    deck = json.loads(data["deck"])
    player_cycle = cycle_slice(players.index(data["first_attacker"]), players)
    data["stacks"] = json.dumps([])
    if deck:
        for player in player_cycle:
            hand = json.loads(data[player])
            if deck and len(hand) < 6:
                while deck and len(hand) < 6:
                    hand.append(deck[0])
                    del deck[0]
                data[player] = json.dumps(hand)
    

def cycle_slice(start_index, arr):
    return arr[start_index:]+arr[:start_index]
    

def after(el, arr):
    return arr[((arr.index(el)+1)%len(arr)+len(arr))%len(arr)]


def before(el, arr):
    return arr[((arr.index(el)-1)%len(arr)+len(arr))%len(arr)]
