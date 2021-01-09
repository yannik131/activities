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
    data["stacks"] = json.dumps([])
    if deck:
        player_cycle = cycle_slice(players.index(data["first_attacker"]), players)
        for player in player_cycle:
            hand = json.loads(data[player])
            if deck and len(hand) < 6:
                while deck and len(hand) < 6:
                    hand.append(deck[0])
                    del deck[0]
                data[player] = json.dumps(hand)
        data["deck"] = json.dumps(deck)
    

def cycle_slice(start_index, arr):
    return arr[start_index:]+arr[:start_index]
    

def after(el, arr):
    return arr[((arr.index(el)+1)%len(arr)+len(arr))%len(arr)]


def before(el, arr):
    return arr[((arr.index(el)-1)%len(arr)+len(arr))%len(arr)]


def left_player(player, players, data):
    n = len(players)
    for i, player in enumerate(cycle_slice(players.index(player), players)):
        left = after(player, players)
        if json.loads(data[left]):
            return left
        if i == n-2:
            return None
    return None