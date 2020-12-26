from shared.shared import add
from django.utils.translation import gettext_lazy as _


def create_pairings(players, points, tie_breaks=None, team_size=2):
    pairings = []
    i = 0
    tie_breaks_enabled = tie_breaks is not None
    while i < len(players):
        pairing = [player[0] for player in players[i:i + team_size]]
        if tie_breaks_enabled:
            add(tie_breaks, pairing[0], points[pairing[1]])
            add(tie_breaks, pairing[1], points[pairing[0]])
        pairings.append(pairing)
        i += team_size
    return pairings


def sorted_player_list(points, tie_breaks=None):
    if tie_breaks:
        return sorted([(k, v, tie_breaks[k]) for (k, v) in points.items()], key=lambda pair: (float(pair[1]), tie_breaks[pair[0]]), reverse=True)
    else:
        return sorted([(k, v) for (k, v) in points.items()], key=lambda pair: float(pair[1]), reverse=True)


def swiss_pairings_danish_standard(points, tie_breaks):
    players = sorted_player_list(points, tie_breaks)
    leftover = None

    if len(players) % 2 != 0:
        add(points, players[-1][0], 1)  # player receives a bye
        leftover = players[-1][0]
        del players[-1]  # kick last player from this round

    pairings = create_pairings(players, points, tie_breaks)
    return pairings, leftover


def swiss_pairings_danish_skat(points, team_sizes=None):
    players = sorted_player_list(points)
    num_players = len(players)
    if team_sizes:
        pairings = None
        for team_size in team_sizes:
            if num_players % team_size == 0:
                pairings = create_pairings(players, points, team_size=team_size)
                break
        if pairings is None:
            raise RuntimeError('Impossible team size')
    else:
        full_teams = int(num_players / 3)
        if full_teams * 4 < num_players:
            raise RuntimeError('Impossible number of players')
        leftover_players = []
        while len(players) % 3 != 0:
            leftover_players.append(players[-1])
            del players[-1]
        pairings = create_pairings(players, points, team_size=3)
        for i in range(len(leftover_players)):
            pairings[i].append(leftover_players[i][0])
    return pairings, None


def get_pairings_for(activity_name, tournament):
    if tournament.members.all().count() <= 1:
        raise RuntimeError(_('Nicht genug Spieler'))
    if activity_name == _('Schach spielen'):
        return swiss_pairings_danish_standard(tournament.points, tournament.tie_breaks)
    elif activity_name == _('Doppelkopf spielen'):
        return swiss_pairings_danish_skat(tournament.points, team_sizes=[4, 5])
    elif activity_name == _('Azul spielen'):
        return swiss_pairings_danish_skat(tournament.points, team_sizes=[2, 3, 4])
    elif activity_name == _('Skat spielen'):
        return swiss_pairings_danish_skat(tournament.points, team_sizes=[3, 4])
    else:
        raise NotImplementedError(_('Gibts doch nicht.'))