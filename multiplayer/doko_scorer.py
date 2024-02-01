import json
import multiplayer.utils as utils


# from django.utils.translation import gettext_lazy as _

# stupid hack until I get translations to work during tests
def _(arg):
    return arg


DOKO_GAME_VALUES = {
    "": 121, "w": 121, "9": 151, "6": 181, "3": 211, "s": 240
}


def calc_trick_points(trick):
    trick_points = 0
    for card in trick:
        trick_points += utils.CARD_VALUES[card[:-1]]
    return trick_points


def index(array, element):
    try:
        return array.index(element)
    except ValueError:
        return None


class DokoScorer:
    def __init__(self, data):
        self.tricks = json.loads(data["tricks"])
        self.data = data
        self.re_extra = []
        self.contra_extra = []
        self.players = json.loads(data["players"])
        self.re_team, self.contra_team = self.__get_teams()
        self.max_tricks = 10 if data['without_nines'] == '1' else 12
        self.re_points, self.re_trick_count, self.contra_points, self.contra_trick_count = self.__sum_tricks()

    def __get_teams(self):
        data = self.data
        if data["re_1"] and not data["re_2"]:
            data["solist"] = data["re_1"]
            data["re_1"] = ""
        if data["solist"]:
            re_players = [data["solist"]]
        else:
            re_players = [data["re_1"], data["re_2"]]
        contra_players = [p for p in json.loads(data["players"]) if p not in re_players]

        return re_players, contra_players

    def __give_fox_points(self, trick, winner, started):
        data = self.data
        if "Ad" in trick:
            winner_is_re = winner == data["re_1"] or winner == data["re_2"]
            players = utils.cycle_slice(started, self.players)
            for i, card in enumerate(trick):
                if card != "Ad":
                    continue
                fox_owner = players[i]
                owner_is_re = fox_owner == data["re_1"] or fox_owner == data["re_2"]
                if winner_is_re and not owner_is_re:
                    self.re_extra.append(_("Fuchs gefangen"))
                elif not winner_is_re and owner_is_re:
                    self.contra_extra.append(_("Fuchs gefangen"))

    def __give_doppelkopf_points(self, trick, winner):
        if calc_trick_points(trick) < 40:
            return
        if winner in self.re_team:
            self.re_extra.append(_("Doppelkopf"))
        else:
            self.contra_extra.append(_("Doppelkopf"))

    def __give_charlie_points(self, trick, winner, started):
        if "Jc" not in trick:
            return
        players = utils.cycle_slice(started, self.players)
        winner_index = players.index(winner)
        if not trick[winner_index] == "Jc":
            return
        if winner in self.re_team:
            self.re_extra.append(_("Karlchen"))
        else:
            self.contra_extra.append(_("Karlchen"))

    def __give_extra_points(self, result):
        data = self.data
        if data["solist"]:
            return

        if result == "Kontra":
            self.contra_extra.append(_("Gegen die Alten"))

        for trick, winner, started in self.tricks:
            self.__give_fox_points(trick, winner, started)
            self.__give_doppelkopf_points(trick, winner)

        self.__give_charlie_points(*self.tricks[-1])

    def __sum_tricks(self):
        re_points, re_trick_count, contra_points, contra_trick_count = 0, 0, 0, 0
        for trick, winner, started in self.tricks:
            points = calc_trick_points(trick)
            if winner in self.re_team:
                re_points += points
                re_trick_count += 1
            else:
                contra_points += points
                contra_trick_count += 1
        return re_points, re_trick_count, contra_points, contra_trick_count

    def __determine_winner_doko(self):
        re_bid, contra_bid = self.data["re_value"], self.data["contra_value"]

        re_goal_reached = (re_bid == "" and self.re_points >= 121 or
                           re_bid == "s" and self.re_trick_count == self.max_tricks or
                           self.re_points >= DOKO_GAME_VALUES[re_bid])
        contra_goal_reached = (contra_bid == "" and self.contra_points >= 120 or
                               contra_bid == "s" and self.contra_trick_count == self.max_tricks or
                               self.contra_points >= DOKO_GAME_VALUES[contra_bid])

        # Somebody won by reaching their goal
        if re_goal_reached:
            return "Re"
        if contra_goal_reached:
            return "Kontra"

        # Somebody won because they didn't say anything and the other party didn't reach their goal
        if not re_goal_reached and contra_bid == "":
            return "Kontra"
        if not contra_goal_reached and re_bid == "":
            return "Re"

        # Nobody won because neither party reached their goal
        return None

    def __give_doko_points(self, result):
        if result == "Re":
            self.re_extra.append(_("Gewonnen"))
        elif result == "Kontra":
            self.contra_extra.append(_("Gewonnen"))

        for mark in [151, 181, 211]:
            if self.re_points >= mark:
                self.re_extra.append(f"Unter {240 - mark + 1} gespielt")
            elif self.contra_points >= mark:
                self.contra_extra.append(f"Unter {240 - mark + 1} gespielt")
            else:
                break

        if self.re_trick_count == self.max_tricks:
            self.re_extra.append(_("Schwarz gespielt"))
        if self.contra_trick_count == self.max_tricks:
            self.contra_extra.append(_("Schwarz gespielt"))

        bids = ["9", "6", "3", "s"]
        contra_bid, re_bid = self.data["contra_value"], self.data["re_value"]

        messages_opposition = [
            _("120 gegen keine 90 erreicht"),
            _("90 gegen keine 60 erreicht"),
            _("60 gegen keine 30 erreicht"),
            _("30 gegen schwarz erreicht")
        ]
        messages_winner = [
            _("Keine 90 abgesagt"),
            _("Keine 60 abgesagt"),
            _("Keine 30 abgesagt")
        ]
        contra_bid_index, re_bid_index = index(bids, contra_bid), index(bids, re_bid)
        if contra_bid_index is not None:
            for i, mark in enumerate([120, 90, 60, 30][:contra_bid_index + 1]):
                if self.re_points >= mark:
                    self.re_extra.append(messages_opposition[i])
        if re_bid_index is not None:
            for i, mark in enumerate([120, 90, 60, 30][:re_bid_index + 1]):
                if self.contra_points >= mark:
                    self.contra_extra.append(messages_opposition[i])

        # "Absagen"
        if result and re_bid_index is not None:
            for i, mark in enumerate([151, 181, 211][:re_bid_index + 1]):
                if self.re_points >= mark:
                    self.re_extra.append(messages_winner[i])
        if result and contra_bid_index is not None:
            for i, mark in enumerate([151, 181, 211][:contra_bid_index + 1]):
                if self.contra_points >= mark:
                    self.contra_extra.append(messages_winner[i])

        if result and self.re_trick_count == self.max_tricks and re_bid == "s":
            self.re_extra.append(_("Schwarz abgesagt"))
        if result and self.contra_trick_count == self.max_tricks and contra_bid == "s":
            self.contra_extra.append(_("Schwarz abgesagt"))

        self.__give_extra_points(result)

        re_points = len(self.re_extra)
        contra_points = len(self.contra_extra)
        no_result = result is None
        if result == "Re":
            points = re_points - contra_points
        elif result == "Kontra":
            points = contra_points - re_points
        else:
            if re_points >= contra_points:
                result = "Re"
            else:
                result = "Kontra"
            points = abs(re_points - contra_points)
        summary_str = ""
        if not no_result:
            if re_bid == "w" or re_bid in bids:
                points += 2
                summary_str += _("+2: Re gesagt\n")
            if contra_bid == "w" or contra_bid in bids:
                points += 2
                summary_str += _("+2: Kontra gesagt\n")
        summary = []
        if self.data["solist"]:
            for player in self.players:
                if player == self.data["solist"]:
                    if result == "Re":
                        utils.sum_change(self.data, player + "_points", 3 * points, summary)
                    else:
                        utils.sum_change(self.data, player + "_points", -3 * points, summary)
                else:
                    if result == "Re":
                        utils.sum_change(self.data, player + "_points", -points, summary)
                    else:
                        utils.sum_change(self.data, player + "_points", points, summary)
        else:
            for player in self.players:
                if result == "Re":
                    if player in self.re_team:
                        utils.sum_change(self.data, player + "_points", points, summary)
                    else:
                        utils.sum_change(self.data, player + "_points", -points, summary)
                else:
                    if player in self.re_team:
                        utils.sum_change(self.data, player + "_points", -points, summary)
                    else:
                        utils.sum_change(self.data, player + "_points", points, summary)
        summary = sorted(summary, key=lambda t: t[1], reverse=True)
        summary_str = f"{result if not no_result else 'Niemand, ' + result}: {self.re_points if result == 'Re' else self.contra_points} Augen\n" + "".join(
            [t[0] for t in summary])[:-1] + "\n" + summary_str

        if result == "Re":
            for entry in self.re_extra:
                summary_str += f"+1: {entry}\n"
            for entry in self.contra_extra:
                summary_str += f"-1: {entry}\n"
        elif result == "Kontra":
            for entry in self.contra_extra:
                summary_str += f"+1: {entry}\n"
            for entry in self.re_extra:
                summary_str += f"-1: {entry}\n"

        return summary_str

    def calculate_score(self):
        result = self.__determine_winner_doko()
        summary_str = self.__give_doko_points(result)

        return summary_str
