import random
import json
from shared.shared import log
from django.utils.translation import gettext as _

from .poker_score import highest_combo
import multiplayer.doko_scorer as doko_scorer


def change(dictionary, key, change):
    dictionary[key] = int(dictionary[key]) + change


def append(game_data, key, element):
    arr = json.loads(game_data[key])
    arr.append(element)
    game_data[key] = json.dumps(arr)


def create_deck(*ranks):
    colors = ["c", "h", "s", "d"]
    deck = []
    for color in colors:
        for rank in ranks:
            deck.append(rank + color)
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
        data["deck"] = json.dumps(deck)


def possible_attack_count(data):
    stacks = json.loads(data['stacks'])
    n_played = len(stacks)
    return min(
        6 - n_played,
        len(json.loads(data[data['defending']])) - (n_played - sum(len(stack) == 2 for stack in stacks))
    )


def refresh_stacks(data, text_data, beating):
    if text_data['defending'] != data['defending'] or (
            not beating and text_data['action'] != 'transfer' and possible_attack_count(data) == 0):
        return True
    server_stacks = json.loads(data['stacks'])
    if not beating:
        played_cards = json.loads(text_data['played_cards'])
        for card in played_cards:
            server_stacks.append([card])
    else:
        client_stacks = json.loads(text_data['stacks'])
        for i in range(len(client_stacks)):
            if len(server_stacks[i]) < len(client_stacks[i]):
                server_stacks[i] = client_stacks[i]
                break
    data['stacks'] = json.dumps(server_stacks)
    return False


def check_durak_done(data):
    if possible_attack_count(data) > 0:
        n = len(get_players_with_cards(json.loads(data['players']), data))
        if n > 1:
            return len(json.loads(data['done_list'])) == min(2, n - 1)
    if data['taking']:
        return True
    return all(len(stack) == 2 for stack in json.loads(data['stacks']))


def handle_durak_next_phase(data, match, message, username):
    if not check_durak_done(data):
        return
    players = json.loads(data['players'])
    if data["taking"]:
        hand = json.loads(data[data["taking"]])
        stacks = json.loads(data["stacks"])
        for stack in stacks:
            for card in stack:
                hand.append(card)
        data[data["taking"]] = json.dumps(hand)
        data["attacking"] = left_player(data["taking"], players, data)
        data["taking"] = ""
        deal_cards(data, players)
    else:
        deal_cards(data, players)
        if data["defending"]:
            if json.loads(data[data["defending"]]):
                data["attacking"] = data["defending"]
            else:
                data["attacking"] = left_player(data["defending"], players, data)
        else:
            data["attacking"] = None
    players_with_cards = get_players_with_cards(players, data)
    if len(players_with_cards) <= 1:
        durak = None
        if players_with_cards:
            durak = players_with_cards[0]
        summary = give_durak_points(data, players, durak)
        if durak:
            data["defending"] = durak
            data["attacking"] = before(durak, players)
        else:
            data["attacking"] = data["first"]
            data["defending"] = after(data["attacking"], players)
        match.start_durak()
        match.game_data['summary'] = summary
        message['data']["game_data"] = match.game_data
    else:
        data["defending"] = left_player(data["attacking"], players, data)
        data["started"] = data["attacking"]
        data['done_list'] = json.dumps([])
        message['data']['new_round'] = data


def give_durak_points(data, players, durak):
    summary = []
    for player in players:
        if player == durak:
            points = -1
        elif data["first"] == player:
            points = 2
        else:
            points = 1
        change(data, player + "_points", points)
        summary.append([f"{player}: {'+' if points >= 0 else ''}{points} -> {data[player + '_points']}\n",
                        data[player + '_points']])
    summary = sorted(summary, key=lambda t: t[1], reverse=True)
    return "".join([t[0] for t in summary])[:-1]


def cycle_slice(start_index, arr):
    return arr[start_index:] + arr[:start_index]


def after(el, arr):
    n = len(arr)
    return arr[((arr.index(el) + 1) % n + n) % n]


def before(el, arr):
    n = len(arr)
    return arr[((arr.index(el) - 1) % n + n) % n]


def left_player(player, players, data):
    n = len(players)
    for i, player in enumerate(cycle_slice(players.index(player), players)):
        left = after(player, players)
        if json.loads(data[left]):
            return left
        if i == n - 2:
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
    if data[data["active"] + "_bid"] == "pass":
        if index == 0:  # forehand
            return participants[2], "1"
        elif index == 1:  # middlehand
            return participants[2], "1"
        elif index == 2:  # hindquarters
            if data[participants[1] + "_bid"] != "pass":
                return participants[1], ""
            elif data[participants[0] + "_bid"] != "pass":
                return participants[0], ""
    else:
        if index == 0:
            if data[participants[1] + "_bid"] != "pass":
                return participants[1], "1"
            elif data[participants[2] + "_bid"] != "pass":
                return participants[2], "1"
        elif index == 1:
            if data[participants[0] + "_bid"] != "pass":
                return participants[0], ""
            elif data[participants[2] + "_bid"] != "pass":
                return participants[2], "1"
        elif index == 2:
            if data[participants[0] + "_bid"] != "pass":
                return participants[0], ""
            elif data[participants[1] + "_bid"] != "pass":
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
        data["last_trick"] = json.dumps(trick)
        if game == "skat":
            append(data, winner + "_tricks", trick)
            data["forehand"] = winner
            message["data"]["forehand"] = winner
            ouvert_null_lost = (data["game_type"] == "n" and data["solist"] == winner) or (
                        ("o" in data["declarations"] or "b" in data["declarations"]) and (
                            data["solist"] != winner and data["game_type"] != "n"))
        else:
            ouvert_null_lost = False
            if data["game_type"] == "marriage":
                n_solist_tricks = len(json.loads(data[data["solist"] + "_tricks"]))
                if winner != data["solist"] and n_solist_tricks < 3:
                    data["re_1"] = data["solist"]
                    data["re_2"] = winner
                    data["m_show"] = n_solist_tricks + 1
                    data["game_type"] = "diamonds"
                    data["solist"] = ""
                    message["data"]["m_show"] = data["m_show"]
                    message["data"]["re_1"] = data["re_1"]
                    message["data"]["re_2"] = data["re_2"]
            append(data, "tricks", (trick, winner, json.loads(data["players"]).index(players[0])))

        data["active"] = winner
        data["trick"] = json.dumps([])
        message["data"]["clear"] = "1"
        message["data"]["active"] = winner
        if not json.loads(data[data["active"]]) or ouvert_null_lost:
            players = json.loads(data["players"])
            if game == "skat":
                result, points, game_value = determine_winner_skat(data)
                points_summary = give_skat_points(data, players, result, game_value)
                message["data"]["result"] = result
                if points:
                    message["data"]["points"] = points
            else:
                scorer = doko_scorer.DokoScorer(data)
                points_summary = scorer.calculate_score()
            message["data"]["summary"] = points_summary
            data["summary"] = points_summary
            if game == "skat":
                data["started"] = after(data["started"], players)
                match.start_skat()
                data["forehand"] = data["started"]
                data["active"] = after(data["forehand"], players)
            else:
                if not data["solist"]:
                    data["started"] = after(data["started"], players)
                match.start_doppelkopf()
                data["active"] = data["started"]
            message["data"]["game_number"] = data["game_number"]
            message["data"]["round"] = match.game_data


def sum_change(dictionary, key, _change, summary):
    change(dictionary, key, _change)
    pre = ""
    if _change >= 0:
        pre = "+"
    summary.append([f"{key[:-7]}: {pre}{_change} -> {dictionary[key]}\n", dictionary[key]])


CARD_VALUES = {
    "7": 0, "8": 0, "9": 0, "J": 2, "Q": 3,
    "K": 4, "10": 10, "A": 11
}
SKAT_GAME_VALUES = {
    "d": 9, "h": 10, "s": 11, "c": 12, "n": 23, "g": 24
}


def determine_winner_skat(data):
    points = 0
    skat = json.loads(data["deck"])
    tricks = json.loads(data[data["solist"] + "_tricks"])
    for trick in tricks + [skat]:
        for card in trick:
            points += CARD_VALUES[card[:-1]]
    data['points'] = points
    game_value = calc_game_value(data, points, tricks)
    result = "lost"
    if data["game_type"] == "n":
        if not tricks:
            result = "won"
    elif points > 60:
        declarations = data["declarations"]
        if "s" in declarations and points < 91 or \
                ("b" in declarations or "o" in declarations) and len(tricks) < 10:
            result = "overbid"
            game_value += 1
        elif game_value >= int(data[data["solist"] + "_bid"]):
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
        elif points >= 91 or points < 31:
            factor += 1
        return factor * SKAT_GAME_VALUES[data["game_type"]]


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
            if with_j and trump + data["game_type"] in cards:
                factor += 1
            elif not with_j and (trump + data["game_type"] not in cards):
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
    return factor + 1


def give_skat_points(data, players, result, game_value):
    solist_change = 0
    other_change = 0
    if result == "won":
        solist_change += 50 + game_value
        summary = data["solist"] + ": +" + str(solist_change)
    else:
        if len(players) == 3:
            other_change = 40
        else:
            other_change = 30
        solist_change -= 50 + 2 * game_value
        summary = data["solist"] + ": -" + str(-solist_change)
    change(data, data["solist"] + "_points", solist_change)
    summary += " -> " + str(data[data["solist"] + "_points"]) + "\n"
    summary = [[summary, data[data["solist"] + "_points"]]]
    players = cycle_slice(players.index(data["forehand"]), players)
    for player in players:
        if player == data["solist"]:
            continue
        change(data, player + "_points", other_change)
        summary.append([player + ": +" + str(other_change) + " -> " + str(data[player + "_points"]) + "\n",
                        data[player + "_points"]])
    summary = sorted(summary, key=lambda t: t[1], reverse=True)
    return "".join([t[0] for t in summary])[:-1]


"""
Poker stuff
"""


def determine_dealer(data):
    alive = json.loads(data['alive'])
    if not data['dealer']:
        data['dealer'] = random.choice(alive)
    else:
        if data['dealer'] not in alive:
            data['dealer'] = player_or(after, 'dealer', data)
        else:
            data['dealer'] = after(data['dealer'], alive)
    if len(alive) == 2:
        data['small_blind'] = data['dealer']
        data['big_blind'] = after(data['dealer'], alive)
    else:
        data['small_blind'] = after(data['dealer'], alive)
        data['big_blind'] = after(data['small_blind'], alive)


def _set_blind(blind, name, data):
    bet = min(blind, int(data[data[name] + '_stack']))
    change(data, data[name] + '_stack', -bet)
    data[data[name] + '_bet'] = bet
    return bet


def set_blinds(data, blinds):
    small_blind, big_blind = blinds[int(data['blind_level'])]
    a = _set_blind(small_blind, 'small_blind', data)
    b = _set_blind(big_blind, 'big_blind', data)
    data['pot'] = a + b
    data['highest_bet_user'] = ""
    data['highest_bet_value'] = big_blind
    data['previous_raise'] = big_blind


def no_fold(data, active=None):
    players = json.loads(data['alive'])
    if active is None:
        active = players[0]
    result = []
    for user in cycle_slice(players.index(active), players):
        if data[user + '_bet'] != 'fold':
            result.append(user)
    return result


def player_or(func, name, data):
    players = json.loads(data['players'])
    alive = json.loads(data['alive'])
    player = data[name]
    while data[player + '_bet'] == 'fold' or player not in alive:
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
        if len(total_players) == 2:  # head to head
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
    active = player_or(after, 'small_blind', data)
    data['active'] = no_fold(data, active)[0]


def replace_10_with_1(cards):
    return [card if len(card) == 2 else card[0] + card[-1] for card in cards]


def determine_forced_player(data):
    if data['highest_bet_user']:
        return data['highest_bet_user']
    else:
        return after(player_or(after, 'dealer', data), no_fold(data))


def determine_winners_poker(data):
    players = []  # [bet, user, score, name]
    common_cards = replace_10_with_1(json.loads(data['cards']))
    show_list = json.loads(data['show_list'])
    total = 0
    for player in no_fold(data):
        if player in show_list:
            hand = replace_10_with_1(json.loads(data[player]))
            score, name = highest_combo(common_cards, hand)
        else:
            score, name = highest_combo(common_cards, [])
        total += int(data[player + '_bet'])
        players.append([int(data[player + '_bet']),
                        player,
                        score,
                        name])
    pots = create_pots(players)
    pots[0][0] += int(data['pot']) - total  # folded
    summary = ""
    for i in range(len(pots)):
        pot = pots[i]
        if i == 0:
            summary += 'Main Pot:\n'
        else:
            summary += f'Side Pot {i}:\n'
        total_reward = pot[0]
        each = int(pot[0] / len(pot[1]))

        if len(pot[1]) > 1 or show_list:
            summary += f'HAND{pot[1][0][1]}HAND\n'

        for player in pot[1]:
            change(data, player[0] + '_stack', each)
            summary += f'{player[0]} +{each}\n'
        leftover = total_reward - each * len(pot[1])
        if leftover:
            player = random.choice(pot[1])
            change(data, player[0] + '_stack', leftover)
            summary += f'{player[0]} +{leftover}\n'
    data['summary'] = summary
    return summary


def create_pots(players):
    players = sorted(players, key=lambda l: l[0], reverse=True)
    pots = []  # [chips, [[user, name]]]
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
    pot = [min_bet * len(players), []]
    max_score = max(players, key=lambda l: l[2])[2]
    for player in players:
        player[0] -= min_bet
        if ignore_score or player[2] == max_score:
            pot[1].append([player[1], player[3]])
    return pot
