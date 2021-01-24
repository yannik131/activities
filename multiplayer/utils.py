import random
import json
from shared.shared import log
from django.utils.translation import gettext_lazy as _


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
    
    
def player_with_cards(players, data):
    count = 0
    for player in players:
        if data[player] != "[]":
            count += 1
    return count
    
    
def next_bidder(data):
    players = json.loads(data["players"])
    participants = cycle_slice(players.index(data["forehand"]), players)[:3]
    index = participants.index(data["active"])
    if data[data["active"]+"_bid"] == "pass":
        if index == 0: #forehand
            return participants[2], "1"
        elif index == 1: #middlehand
            return participants[2], "1"
        elif index == 2: #hindquarters
            if data[participants[1]+"_bid"] != "pass":
                return participants[1], ""
            elif data[participants[0]+"_bid"] != "pass":
               return participants[0], ""
    else:
        if index == 0:
            if data[participants[1]+"_bid"] != "pass":
                return participants[1], "1"
            elif data[participants[2]+"_bid"] != "pass":
                return participants[2], "1"
        elif index == 1:
            if data[participants[0]+"_bid"] != "pass":
                return participants[0], ""
            elif data[participants[2]+"_bid"] != "pass":
                return participants[2], "1"
        elif index == 2:
            if data[participants[0]+"_bid"] != "pass":
                return participants[0], ""
            elif data[participants[1]+"_bid"] != "pass":
                return participants[1], ""
    return None, ""
    
    
CARD_VALUES = {
    "7": 0, "8": 0, "9": 0, "J": 2, "Q": 3,
    "K": 4, "10": 10, "A": 11
}
GAME_VALUES = {
    "d": 9, "h": 10, "s": 11, "c": 12, "n": 23, "g": 24
}

def determine_winner(data):
    tricks = json.loads(data[data["solist"]+"_tricks"])
    if data["game_type"] == "n":
        if tricks:
            return _("Verloren"), None
        return _("Gewonnen"), None
    skat = json.loads(data["deck"])
    log("skat", skat, "tricks", tricks)
    points = 0
    for trick in tricks+[skat]:
        for card in trick:
            points += CARD_VALUES[card[:-1]]
    won = points > 60
    if won:
        game_value = calc_game_value(data, points)
        if game_value >= int(data[data["solist"]+"_bid"]):
            return _("Gewonnen"), points
        else:
            return _("Überreizt"), points
    return _("Verloren"), points
    

def calc_game_value(data, points):
    if data["game_type"] == "n":
        declarations = data["declarations"]
        if declarations == "h":
            return 35
        elif declarations == "o":
            return 46
        elif declarations == "ho":
            return 59
        else:
            return 23
    else:
        factor = int(data["factor"])
        if points == 0:
            factor += 2
        elif points <= 30:
            factor += 1
        return int(data["factor"])*GAME_VALUES[data["game_type"]]


def determine_factor(data):
    factor = 1
    if data["game_type"] == "n":
        return factor
    highest = ["Js", "Jh", "Jd"]
    cards = json.loads(data[data["solist"]])
    with_j = "Jc" in cards
    for trump in highest:
        if with_j and trump in cards:
            factor += 1
        elif not with_j and trump not in cards:
            factor += 1
        elif (with_j and trump not in cards) or (not with_j and trump in cards):
            break
    declarations = data["declarations"]
    if "h" in declarations:
        factor += 1
    if data["game_type"] != "g":
        highest = ["A", "10", "K", "Q", "J", "9", "8", "7"]
        for trump in highest:
            if trump+data["game_type"] in cards:
                factor += 1
            else:
                break
    return factor

def random_name():
    with open("multiplayer/random_names.txt", "r") as f:
        names = f.readlines()
        if not names:
            raise RuntimeError("Out of names.")
    with open("multiplayer/random_names.txt", "w") as f:
        f.writelines(names[1:])
    return names[0][:-1]
    