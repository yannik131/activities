from account.models import User


def create_pairings(players, tie_breaks=None, points=None, team_size=2):
    if len(players) % team_size != 0:
        raise RuntimeError('create_pairings: impossible team size')
    pairings = []
    i = 0
    tie_breaks_enabled = team_size == 2 and tie_breaks and points
    while i < len(players):
        pairing = [player[0] for player in players[i:i + team_size]]
        if tie_breaks_enabled:
            tie_breaks[pairing[0]] += points[pairing[1]]
            tie_breaks[pairing[1]] += points[pairing[0]]
        pairings.append(pairing)
        i += team_size
    return pairings


def sorted_player_list(points, tie_breaks):
    if tie_breaks:
        return sorted([(k, v, tie_breaks[k]) for (k, v) in points.items()], key=lambda pair: (pair[1], tie_breaks[pair[0]]), reverse=True)
    else:
        return sorted([(k, v) for (k, v) in points.items()], key=lambda pair: pair[1], reverse=True)


def swiss_pairings_danish_standard(points, tie_breaks):
    players = sorted_player_list(points, tie_breaks)

    if len(players) % 2 != 0:
        points[players[-1][0]] += 1  # player receives a bye
        del players[-1]  # kick last player from this round

    pairings = create_pairings(players, tie_breaks=tie_breaks,
                               points=points)

    return pairings


def swiss_pairings_danish_skat(points):
    players = sorted_player_list(points)
    num_players = len(players)
    if num_players % 3 == 0:
        pairings = create_pairings(players, team_size=3)
    elif num_players % 4 == 0:
        pairings = create_pairings(players, team_size=4)
    else:
        full_teams = int(num_players / 3)
        if full_teams * 4 < num_players:
            raise RuntimeError('skat: impossible number of players')
        leftover_players = []
        while len(players) % 3 != 0:
            leftover_players.append(players[-1])
            del players[-1]
        pairings = create_pairings(players, team_size=3)
        for i in range(len(leftover_players)):
            pairings[i].append(leftover_players[i][0])
    return pairings
