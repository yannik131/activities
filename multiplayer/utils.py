import random
import json
from shared.shared import log
from django.utils.translation import gettext as _


def change(dictionary, key, change):
    dictionary[key] = int(dictionary[key])+change
    

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
        player_cycle = cycle_slice(players.index(data["started"]), players)
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
    
    
def get_players_with_cards(players, data):
    l = []
    for player in players:
        if data[player] != "[]":
            l.append(player)
    return l
    
    
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
    

def handle_play(game, data, text_data, username, message, match):
    players = json.loads(data["players"])
    if game == "skat":
        players = cycle_slice(players.index(data["forehand"]), players)
    else:
        players = cycle_slice(players.index(after(data["active"], players)), players)
    data["trick"] = text_data["trick"]
    trick = json.loads(data["trick"])
    data[data["active"]] = text_data["hand"]
    data["active"] = after(username, players)
    message["data"] = {
        "action": "play",
        "trick": data["trick"],
        "username": username,
        "active": data["active"]
    }
    if game == "skat" and len(trick) == 3 or game == "doko" and len(trick) == 4:
        winner = players[int(text_data["index"])]
        tricks = json.loads(data[winner+"_tricks"])
        tricks.append(trick)
        data[winner+"_tricks"] = json.dumps(tricks)
        if game == "skat":
            data["forehand"] = winner
            message["data"]["forehand"] = winner
            ouvert_null_lost = (data["game_type"] == "n" and data["solist"] == winner) or (("o" in data["declarations"] or "b" in data["declarations"]) and data["solist"] != winner)
        else:
            ouvert_null_lost = False
            if data["game_type"] == "marriage":
                if winner != data["solist"] and len(tricks) < 4:
                    data["re_1"] = data["solist"]
                    data["re_2"] = winner
                    data["m_show"] = len(tricks)
                    data["game_type"] = "diamonds"
                    data["solist"] = ""
                    message["m_show"] = data["m_show"]
        data["active"] = winner
        data["trick"] = json.dumps([])
        message["data"]["clear"] = "1"
        message["data"]["active"] = winner
        if not json.loads(data[data["active"]]) or ouvert_null_lost:
            players = json.loads(data["players"])
            if game == "skat":
                result, winner_points, game_value = determine_winner_skat(data)
                points_summary = give_skat_points(data, players, result, game_value)
            else:
                result, winner_points = determine_winner_doko(data)
                points_summary = give_doko_points(data, players, result)
            message["data"]["result"] = result
            if winner_points:
                message["data"]["points"] = winner_points
            message["data"]["summary"] = points_summary
            data["summary"] = points_summary
            starting = after(data["started"], players)
            if game == "skat":
                match.start_skat()
                match.game_data["forehand"] = starting
            else:
                match.start_doppelkopf()
            message["data"]["game_number"] = data["game_number"]
            match.game_data["active"] = after(starting, players)
            message["data"]["round"] = match.game_data
            match.game_data["started"] = starting

DOKO_GAME_VALUES = {
    "": 121, "w": 121, "9": 151, "6": 181, "3": 211, "s": 240
}

DOKO_VALUES = {
    "": 1, "w": 2, "9": 3, "6": 4, "3": 5, "s": 6
}

def determine_winner_doko(data):
    if data["solist"]:
        re = [data["solist"]]
    else:
        re = [data["re_1"], data["re_2"]]
    re_points = 0
    count = 0
    for player in re:
        for trick in json.loads(data[player+"_tricks"]):
            count += 1
            for card in trick:
                re_points += CARD_VALUES[card[:-1]]
    value = data["contra_value"]
    if value == "s" and count == 12:
        return "contra", 240
    elif value == "s":
        return "re", re_points
    if 240-re_points >= DOKO_GAME_VALUES[value]:
        return "contra", 240-re_points
    value = data["re_value"]
    if value == "s" and count == 12:
        return "re", 240
    elif value == "s":
        return "contra", 240-re_points
    if re_points >= DOKO_GAME_VALUES[value]:
        return "re", re_points
    else:
        return "contra", 240-re_points
        
def sum_change(dictionary, key, _change, summary):
    change(dictionary, key, _change)
    pre = ""
    if _change >= 0:
        pre = "+"
    summary.append([f"{key[:-7]}: {pre}{_change} -> {dictionary[key]}\n", {dictionary[key]}])
    
def give_doko_points(data, players, result):
    points = 0
    value = data[result+"_value"]
    if result == "contra":
        points += 1 # gegen die alten
    points += DOKO_VALUES[value]
    summary = []
    if data["solist"]:
        for player in players:
            if player == data["solist"]:
                sum_change(data, player+"_points", 3*points, summary)
            else:
                sum_change(data, player+"_points", points, summary)
    else:
        for player in players:
            if result == "re":
                if player == data["re_1"] or player == data["re_2"]:
                    sum_change(data, player+"_points", points, summary)
                else:
                    sum_change(data, player+"_points", -points, summary)
            else:
                if player == data["re_1"] or player == data["re_2"]:
                    sum_change(data, player+"_points", -points, summary)
                else:
                    sum_change(data, player+"_points", points, summary)
    summary = sorted(summary, key=lambda t: t[1])
    return "".join([t[0] for t in summary])
    

CARD_VALUES = {
    "7": 0, "8": 0, "9": 0, "J": 2, "Q": 3,
    "K": 4, "10": 10, "A": 11
}
GAME_VALUES = {
    "d": 9, "h": 10, "s": 11, "c": 12, "n": 23, "g": 24
}

def determine_winner_skat(data):
    points = 0
    skat = json.loads(data["deck"])
    tricks = json.loads(data[data["solist"]+"_tricks"])
    for trick in tricks+[skat]:
        for card in trick:
            points += CARD_VALUES[card[:-1]]
    game_value = calc_game_value(data, points, tricks)
    result = "lost"
    if data["game_type"] == "n":
        if not tricks:
            result = "won"
    elif points > 60:
        declarations = data["declarations"]
        if "s" in declarations and points < 91 or\
            ("b" in declarations or "o" in declarations) and len(tricks) < 10:
            result = "overbid"
        elif game_value >= int(data[data["solist"]+"_bid"]):
            result = "won"
        else:
            result = "overbid"
    
    return result, points, game_value
    

def calc_game_value(data, points, tricks):
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
        if len(tricks) == 10:
            factor += 2
        elif points > 30:
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
        else:
            break
    declarations = data["declarations"]
    if "h" in declarations:
        factor += 1
    if "s" in declarations:
        factor += 1
    elif "b" in declarations:
        factor += 2
    elif "o" in declarations:
        factor += 3
    if data["game_type"] != "g":
        highest = ["A", "10", "K", "Q", "J", "9", "8", "7"]
        for trump in highest:
            if with_j and trump+data["game_type"] in cards:
                factor += 1
            elif not with_j and (trump+data["game_type"] not in cards):
                factor += 1
            else:
                break
    return factor+1
    
    
def give_skat_points(data, players, result, game_value):
    solist_change = 0
    other_change = 0
    summary = []
    if result == "won":
        solist_change += 50 + game_value
        summary = data["solist"]+": +"+str(solist_change)
    else:
        if len(players) == 3:
            other_change = 40
        else:
            other_change = 30
        solist_change -= 50 + 2*game_value
        summary = data["solist"]+": -"+str(-solist_change)
    change(data, data["solist"]+"_points", solist_change)
    summary += " -> "+str(data[data["solist"]+"_points"])+"\n"
    summary = [[summary, data[data["solist"]+"_points"]]]
    players = cycle_slice(players.index(data["forehand"]), players)
    for player in players:
        if player == data["solist"]:
            continue
        change(data, player+"_points", other_change)
        summary.append([player+": +"+str(other_change)+" -> "+str(data[player+"_points"])+"\n", data[player+"_points"]])
    summary = sorted(summary, key=lambda t: t[1], reverse=True)
    return "".join([t[0] for t in summary])
    
    
def give_durak_points(data, players, durak):
    summary = []
    for player in players:
        if player == durak:
            points = 0
        elif data["first"] == player:
            points = 2
        else:
            points = 1
        change(data, player+"_points", points)
        summary.append([f"{player}: +{points} -> {data[player+'_points']}\n", data[player+'_points']])
    summary = sorted(summary, key=lambda t: t[1], reverse=True)
    return "".join([t[0] for t in summary])
    

def random_name():
    with open("multiplayer/random_names.txt", "r") as f:
        names = f.readlines()
        if not names:
            raise RuntimeError("Out of names.")
    with open("multiplayer/random_names.txt", "w") as f:
        f.writelines(names[1:])
    return names[0][:-1]
    
    