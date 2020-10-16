import random
import math

ids = [i for i in range(17)]
scores = dict([(id, 0) for id in ids])
tie_break_scores = dict([(id, 0) for id in ids])

round_duration_in_days = 2
total_rounds = round(math.log2(len(ids)))

def print_table(players, tie_break_scores=None):
    if tie_break_scores:
        print("id\tpoints\ttie break\n"+"-"*30)
        for (id, points) in players:
            print(f"{id}\t{points}\t{tie_break_scores[id]}")
        print("-"*30)
    else:
        print("id\tpoints\n"+"-"*30)
        for (id, points) in players:
            print(f"{id}\t{points}")
        print("-"*30)

def create_pairings(players, tie_break_scores=None, scores=None, team_size=2):
    if len(players) % team_size != 0:
        raise RuntimeError('create_pairings: impossible team size')
    pairings = []
    i = 0
    tie_breaks_enabled = team_size == 2 and tie_break_scores and scores
    while i < len(players):
        pairing = [player[0] for player in players[i:i+team_size]]
        if tie_breaks_enabled:
            tie_break_scores[pairing[0]] += scores[pairing[1]]
            tie_break_scores[pairing[1]] += scores[pairing[0]]
        pairings.append(pairing)
        i += team_size
    return pairings

"""
For two player/team games with 1/0.5/0 points for winning/drawing/losing
"""
def swiss_pairings_danish_standard(scores, tie_break_scores):
    players = sorted([(k, v) for (k, v) in scores.items()],
                     key=lambda pair: (pair[1], tie_break_scores[pair[0]]),
                     reverse=True)
    
    if len(players) % 2 != 0:
        scores[players[-1][0]] += 1 # player receives a bye
        del players[-1] # kick last player from this round

    pairings = create_pairings(players, tie_break_scores=tie_break_scores,
                               scores=scores)
    
    print_table(players, tie_break_scores)
    return pairings

def swiss_pairings_danish_skat(scores):
    players = sorted([(k, v) for (k, v) in scores.items()],
                     key=lambda pair: pair[1],
                     reverse=True)
    num_players = len(players)
    if num_players % 3 == 0:
        pairings = create_pairings(players, team_size=3)
    elif num_players % 4 == 0:
        pairings = create_pairings(players, team_size=4)
    else:
        full_teams = int(num_players/3)
        if full_teams*4 < num_players:
            raise RuntimeError('skat: impossible number of players')
        leftover_players = []
        while len(players) % 3 != 0:
            leftover_players.append(players[-1])
            del players[-1]
        pairings = create_pairings(players, team_size=3)
        for i in range(len(leftover_players)):
            pairings[i].append(leftover_players[i][0])
    print_table(players)
    return pairings
    
def play_standard(scores, pairings):
    for pair in pairings:
        winner = random.randint(0, 2)
        if winner < 2:
            scores[pair[winner]] += 1
        else:
            scores[pair[0]] += 0.5
            scores[pair[1]] += 0.5

def play_skat(scores, pairings):
    for pair in pairings:
        if len(pair) == 3:
            games = 36
        else:
            games = 48
        for i in range(games):
            chosen = pair[random.randint(0, len(pair)-1)]
            if random.randint(0, 1):
                #one player won
                scores[chosen] += random.randint(68, 200)
            else:
                #one player lost
                scores[chosen] += random.randint(-240, -86)
                for player in pair:
                    if player == chosen:
                        continue
                    scores[player] += 40
        
def standard_play():
    i = 0
    while i < total_rounds:
        pairings = swiss_pairings_danish_standard(scores, tie_break_scores)
        play_standard(scores, pairings)
        i += 1
    pairings = swiss_pairings_danish_standard(scores, tie_break_scores)

def skat_play():
    i = 0
    while i < total_rounds:
        pairings = swiss_pairings_danish_skat(scores)
        play_skat(scores, pairings)
        i += 1
    pairings = swiss_pairings_danish_skat(scores)

skat_play()
print(f"Number of rounds: {total_rounds}")
