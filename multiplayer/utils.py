import random
import json
from shared.shared import log
from django.utils.translation import gettext as _
from .poker_score import highest_combo


def change(dictionary, key, change, guard_zero=False):
    dictionary[key] = int(dictionary[key])+change
    if guard_zero:
        if dictionary[key] < 0:
            dictionary[key] = 0

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
    first = data['first']
    if deck:
        player_cycle = cycle_slice(players.index(data["started"]), players)
        for player in player_cycle:
            hand = json.loads(data[player])
            if deck and len(hand) < 6:
                while deck and len(hand) < 6:
                    hand.append(deck[0])
                    del deck[0]
                data[player] = json.dumps(hand)
                if player == first:
                    data['first'] = ''
                    log('unsetting', player, 'as first after dealing cards')
        data["deck"] = json.dumps(deck)
    

def cycle_slice(start_index, arr):
    return arr[start_index:]+arr[:start_index]
    

def after(el, arr):
    n = len(arr)
    return arr[((arr.index(el)+1)%n+n)%n]


def before(el, arr):
    n = len(arr)
    return arr[((arr.index(el)-1)%n+n)%n]


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
        data["last_trick"] = json.dumps(trick)
        data[winner+"_tricks"] = json.dumps(tricks)
        if game == "skat":
            data["forehand"] = winner
            message["data"]["forehand"] = winner
            ouvert_null_lost = (data["game_type"] == "n" and data["solist"] == winner) or (("o" in data["declarations"] or "b" in data["declarations"]) and (data["solist"] != winner and data["game_type"] != "n"))
        else:
            ouvert_null_lost = False
            if data["game_type"] == "marriage":
                if winner != data["solist"] and len(json.loads(data[data["solist"]+"_tricks"])) < 3:
                    data["re_1"] = data["solist"]
                    data["re_2"] = winner
                    data["m_show"] = len(tricks)
                    data["game_type"] = "diamonds"
                    data["solist"] = ""
                    message["data"]["m_show"] = data["m_show"]
                    message["data"]["re_1"] = data["re_1"]
                    message["data"]["re_2"] = data["re_2"]
            if not data["solist"] and "Ad" in trick:
                winner_is_re = winner == data["re_1"] or winner == data["re_2"]
                for i, card in enumerate(trick):
                    if card != "Ad":
                        continue
                    fox_owner = players[i]
                    owner_is_re = fox_owner == data["re_1"] or fox_owner == data["re_2"]
                    if winner_is_re and not owner_is_re:
                        change(data, "re_extra", 1)
                    elif not winner_is_re and owner_is_re:
                        change(data, "contra_extra", 1)
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
                result, winner_points = determine_winner_doko(data, winner, "Jc" == tricks[-1][int(text_data["index"])])
                points_summary = give_doko_points(data, players, result, winner_points)
            message["data"]["result"] = result
            if winner_points:
                message["data"]["points"] = winner_points
            message["data"]["summary"] = points_summary
            data["summary"] = points_summary
            data["started"] = after(data["started"], players)
            if game == "skat":
                match.start_skat()
                data["forehand"] = data["started"]
                data["active"] = after(data["forehand"], players)
            else:
                match.start_doppelkopf()
                data["active"] = data["started"]
            message["data"]["game_number"] = data["game_number"]
            message["data"]["round"] = match.game_data

DOKO_GAME_VALUES = {
    "": 121, "w": 121, "9": 151, "6": 181, "3": 211, "s": 240
}

DOKO_VALUES = {
    "w": 2, "9": 3, "6": 4, "3": 5, "s": 6
}

def sum_tricks(data, team, name):
    count = 0
    points = 0
    log("Counting points for team", name, "with members", team)
    for player in team:
        for trick in json.loads(data[player+"_tricks"]):
            count += 1
            trick_points = 0
            for card in trick:
                points += CARD_VALUES[card[:-1]]
                log("Card", card, "adds", CARD_VALUES[card[:-1]], "total:", points)
                trick_points += CARD_VALUES[card[:-1]]
            if not data["solist"] and trick_points >= 40:
                change(data, name+"_extra", 1)
    return points, count

def determine_winner_doko(data, last_winner, charlie):
    if data["re_1"] and not data["re_2"]:
        data["solist"] = data["re_1"]
        data["re_1"] = ""
    if data["solist"]:
        re = [data["solist"]]
    else:
        re = [data["re_1"], data["re_2"]]
    contra = [p for p in json.loads(data["players"]) if p not in re]
    if charlie:
        if last_winner in re:
            change(data, "re_extra", 1)
        else:
            change(data, "contra_extra", 1)
    re_points, count = sum_tricks(data, re, "re")
    _, _ = sum_tricks(data, contra, "contra")
    
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
    summary.append([f"{key[:-7]}: {pre}{_change} -> {dictionary[key]}\n", dictionary[key]])
    
def give_doko_points(data, players, result, winner_points):
    points = 1 # somebody won, +1
    log("start:", points)
    re_extra = int(data["re_extra"])
    contra_extra = int(data["contra_extra"])
    log("re_extra", re_extra, "contra_extra", contra_extra)
    if result == "contra":
        if not data["solist"]:
            points += 1 # gegen die alten
    if data["contra_value"]:
        points += DOKO_VALUES[data["contra_value"]]
    if data["re_value"]:
        points += DOKO_VALUES[data["re_value"]]
    
    for mark in [151, 181, 211, 240]:
        if winner_points > mark:
            points += 1
            log(">", mark, "+1")
        else:
            break
    summary = []
    log("total:", points, "solist:", bool(data["solist"]))
    if data["solist"]:
        for player in players:
            if player == data["solist"]:
                if result == "re":
                    sum_change(data, player+"_points", 3*points, summary)
                else:
                    sum_change(data, player+"_points", -3*points, summary)
            else:
                if result == "re":
                    sum_change(data, player+"_points", -points, summary)
                else:
                    sum_change(data, player+"_points", points, summary)
    else:
        for player in players:
            if result == "re":
                if player == data["re_1"] or player == data["re_2"]:
                    sum_change(data, player+"_points", (points+re_extra-contra_extra), summary)
                else:
                    sum_change(data, player+"_points", -(points+re_extra-contra_extra), summary)
            else:
                if player == data["re_1"] or player == data["re_2"]:
                    sum_change(data, player+"_points", -(points-re_extra+contra_extra), summary)
                else:
                    sum_change(data, player+"_points", (points-re_extra+contra_extra), summary)
    log("sorting summary:", summary)
    summary = sorted(summary, key=lambda t: t[1], reverse=True)
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
        log("game_value:", game_value, "bid:", int(data[data["solist"]+"_bid"]), "->", result)
    
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
        elif points >= 91 or points < 31:
            factor += 1
        return factor*GAME_VALUES[data["game_type"]]


def determine_factor(data):
    factor = 1
    if data["game_type"] == "n":
        return 1
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
    if data["game_type"] != "g" and factor == 4:
        highest = ["A", "10", "K", "Q", "J", "9", "8", "7"]
        for trump in highest:
            if with_j and trump+data["game_type"] in cards:
                factor += 1
            elif not with_j and (trump+data["game_type"] not in cards):
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
            points = -1
        elif data["first"] == player:
            points = 2
        else:
            points = 1
        change(data, player+"_points", points)
        summary.append([f"{player}: {'+' if points >= 0 else ''}{points} -> {data[player+'_points']}\n", data[player+'_points']])
    summary = sorted(summary, key=lambda t: t[1], reverse=True)
    return "".join([t[0] for t in summary])
    

"""
Poker stuff
"""

def determine_dealer(data):
    players = json.loads(data['alive'])
    if not data['dealer']:
        data['dealer'] = random.choice(players)
    else:
        data['dealer'] = after(data['dealer'], players)
    if len(players) == 2:
        data['small_blind'] = data['dealer']
        data['big_blind'] = after(data['dealer'], players)
    else:
        data['small_blind'] = after(data['dealer'], players)
        data['big_blind'] = after(data['small_blind'], players)
        
def no_fold(data, active=None):
    players = json.loads(data['alive'])
    if active is None:
        active = players[0]
    result = []
    for user in cycle_slice(players.index(active), players):
        if data[user+'_bet'] != 'fold':
            result.append(user)
    return result
    
    
def player_or(func, name, data):
    players = json.loads(data['players'])
    alive = json.loads(data['alive'])
    player = data[name]
    while data[player+'_bet'] == 'fold' or player not in alive:
        player = func(player, players)
    return player
    
def get_next_round_number(data, action, active):
    cards = json.loads(data['cards'])
    n = len(cards)
    alive = no_fold(data, after(active, json.loads(data['alive'])))
    total_players = json.loads(data['alive'])
    if n == 0 and action == 'check':
        return 2
    elif (action == 'call' or action == 'fold') and alive[0] == data['highest_bet_user']:
        if n == 0:
            return 2
        else:
            return n
    elif action == 'check':
        if len(total_players) == 2: # head to head
            if active == data['big_blind']:
                return n
        else:
            if active == player_or(before, 'dealer', data):
                return n
    return None
    
def start_round(data):
    deck = json.loads(data['deck'])
    cards = json.loads(data['cards'])
    if len(cards) == 0:
        cards = deck[:3]
        deck = deck[3:]
    else:
        cards.append(deck[0])
        del deck[0]
    data['cards'] = json.dumps(cards)
    data['deck'] = json.dumps(deck)
    data['highest_bet_user'] = ''
    players = json.loads(data['alive'])
    active = player_or(after, 'small_blind', data)
    data['active'] = no_fold(data, active)[0]
    
def showdown(data):
    winners = []
    common_cards = json.loads(data.cards)
    scores = [[user, round(highest_combo(common_cards, json.loads(data[user])))] for user in no_fold(data)]
    scores = sorted(scores, key=lambda t: t[1][0], reverse=True)
    winners.append(scores[0])
    for score in scores[1:]:
        if score[1][0] == winners[0][1][0]:
            winners.append(score)
        else:
            break
    
def determine_forced_player(data):
    if data['highest_bet_user']:
        return data['highest_bet_user']
    else:
        return after(player_or(after, 'dealer', data), no_fold(data))
        
def determine_winners_poker(data):
    players = [] #[bet, user, score, name]
    common_cards = json.loads(data['cards'])
    show_list = json.loads(data['show_list'])
    for player in no_fold(data):
        if player in show_list:
            hand = json.loads(data[player])
            score, name = highest_combo(common_cards, hand)
        else:
            score, name = highest_combo(common_cards, [])
        players.append([int(data[player+'_bet']),
                        player,
                        score,
                        name])
    pots = create_pots(players)
    summary = ""
    for i in range(len(pots)):
        pot = pots[i]
        if i == 0:
            summary += 'Main Pot:\n'
        else:
            summary += f'Side Pot {i}:\n'
        total_reward = pot[0]
        each = int(pot[0]/len(pot[1]))
        summary += f'HAND{pot[1][0][1]}HAND\n'
        for player in pot[1]:
            change(data, player[0]+'_stack', each)
            summary += f'{player[0]} +{each}\n'
        leftover = total_reward-each*len(pot[1])
        if leftover:
            player = random.choice(pot[1])
            change(data, player[0]+'_stack', leftover)
            summary += f'{player[0]} +{leftover}\n'
    data['summary'] = summary
    return summary
    
def create_pots(players):
    players = sorted(players, key=lambda l: l[0], reverse=True)
    pots = [] #[chips, [[user, name]]]
    while True:
        pots.append(create_pot(players))
        players = [player for player in players if player[0]]
        if not players or players[-1][0] == players[0][0]:
            break
    if len(players) > 0:
        pots.append(create_pot(players, True))
    return pots
            
def create_pot(players, ignore_score=False):
    min_bet = players[-1][0]
    pot = [min_bet*len(players), []]
    max_score = max(players, key=lambda l: l[2])[2]
    for player in players:
        player[0] -= min_bet
        if ignore_score or player[2] == max_score:
            pot[1].append([player[1], player[3]])
    return pot
