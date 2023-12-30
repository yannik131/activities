from .doko_scorer import DokoScorer
from itertools import product
from copy import deepcopy

"""
Solo player is always A.
Re team is always A and B.
"""


def assert_points(data, points):
    for i, player in enumerate(["A", "B", "C", "D"]):
        assert (int(data[player + "_points"]) == points[i])


"""
@brief Contra wins with 136 points. No extra points.
"""


def test_normal_contra_wins():
    data = {'re_1': 'A', 're_2': 'B', 'solist': '',
            'players': '["A", "B", "C", "D"]', 're_value': '', 'contra_value': '',
            'tricks': '[[["10d", "10d", "Qd", "9c"], "B", 2], [["Qc", "Qs", "Qc", "10s"], "D", 4], [["Jh", "Ah", '
                      '"Js", "Ac"], "A", 3], [["Kc", "10h", "9c", "Qh"], "B", 2], [["As", "Ac", "Kh", "9s"], "D", 1], '
                      '[["10s", "9d", "Kd", "Ks"], "D", 3], [["Jc", "Js", "Ks", "Jh"], "B", 4], [["Kd", "Qh", "10h", '
                      '"9s"], "C", 1], [["Ad", "Qd", "10c", "9h"], "D", 2], [["Ah", "As", "9h", "Jd"], "C", 0], '
                      '[["Jc", "9d", "Jd", "Kh"], "C", 1], [["Ad", "Qs", "Kc", "10c"], "B", 0]]',
            'A_points': '0', 'B_points': '0', 'C_points': '0', 'D_points': '0',
            'without_nines': '0'}

    combinations = list(product(["", "w", "9", "6", "3", "s"], repeat=2))
    expected_results = {('', ''): [-2, -2, 2, 2], ('', 'w'): [-4, -4, 4, 4], ('', '9'): [3, 3, -3, -3],
                        ('', '6'): [4, 4, -4, -4],
                        ('', '3'): [5, 5, -5, -5],
                        ('', 's'): [6, 6, -6, -6], ('w', ''): [-4, -4, 4, 4], ('w', 'w'): [-6, -6, 6, 6],
                        ('w', '9'): [0, 0, 0, 0],
                        ('w', '6'): [1, 1, -1, -1],
                        ('w', '3'): [2, 2, -2, -2], ('w', 's'): [3, 3, -3, -3], ('9', ''): [-5, -5, 5, 5],
                        ('9', 'w'): [-7, -7, 7, 7], ('9', '9'): [-1, -1, 1, 1],
                        ('9', '6'): [0, 0, 0, 0], ('9', '3'): [1, 1, -1, -1], ('9', 's'): [2, 2, -2, -2],
                        ('6', ''): [-6, -6, 6, 6], ('6', 'w'): [-8, -8, 8, 8],
                        ('6', '9'): [-2, -2, 2, 2], ('6', '6'): [-1, -1, 1, 1], ('6', '3'): [0, 0, 0, 0],
                        ('6', 's'): [1, 1, -1, -1],
                        ('3', ''): [-7, -7, 7, 7],
                        ('3', 'w'): [-9, -9, 9, 9], ('3', '9'): [-3, -3, 3, 3], ('3', '6'): [-2, -2, 2, 2],
                        ('3', '3'): [-1, -1, 1, 1], ('3', 's'): [0, 0, 0, 0],
                        ('s', ''): [-8, -8, 8, 8], ('s', 'w'): [-10, -10, 10, 10], ('s', '9'): [-4, -4, 4, 4],
                        ('s', '6'): [-3, -3, 3, 3],
                        ('s', '3'): [-2, -2, 2, 2],
                        ('s', 's'): [-1, -1, 1, 1]}
    for combination in reversed(combinations):
        data_ = deepcopy(data)
        data_["re_value"], data_["contra_value"] = combination
        scorer = DokoScorer(data_)
        result = scorer.calculate_score()
        if expected_results[combination]:
            try:
                assert_points(data_, expected_results[combination])
            except AssertionError:
                print(f"Re: {combination[0] or 'Nichts'}, Kontra: {combination[1] or 'Nichts'}\n" + "-" * 20)
                print("NOT OK")
                print(result)
                continue
        else:
            print(f"Re: {combination[0] or 'Nichts'}, Kontra: {combination[1] or 'Nichts'}\n" + "-" * 20)
            print(result)


def test_extra_points():
    data = {'re_1': 'A', 're_2': 'B', 'solist': '',
            'players': '["A", "B", "C", "D"]', 're_value': '', 'contra_value': '',
            'tricks': '[[["10d", "10d", "Qd", "9c"], "B", 2], [["Qc", "Qs", "Qc", "10s"], "D", 4], [["Jh", "Ah", '
                      '"Js", "Qd"], "A", 3], [["Kc", "9h", "9c", "Qh"], "B", 2], [["As", "Ac", "Kh", "9s"], "D", 1], '
                      '[["10s", "9d", "Kd", "Ks"], "D", 3], [["Qs", "Js", "Ks", "Jh"], "B", 4], [["Kd", "Qh", "10h", '
                      '"9s"], "C", 1], [["Ad", "Ac", "10c", "10h"], "D", 2], [["Ah", "As", "9h", "Jd"], "C", 0], '
                      '[["Jc", "9d", "Jd", "Kh"], "C", 1], [["Kc", "Jc", "Ad", "10c"], "B", 0]]',
            'A_points': '0', 'B_points': '0', 'C_points': '0', 'D_points': '0',
            'without_nines': '0'}
    scorer = DokoScorer(data)
    scorer.calculate_score()
    assert_points(data, [-2, -2, 2, 2])

def test_solo_contra_no_90_wins():
    data = {'re_1': '', 're_2': '', 'solist': 'A',
            'players': '["A", "B", "C", "D"]', 're_value': '', 'contra_value': '9',
            'tricks': '[[["10d", "10d", "Qd", "9c"], "A", 2], [["Qc", "Qs", "Qc", "10s"], "A", 4], [["Jh", "Ah", '
                      '"Js", "Qd"], "A", 3], [["Kc", "9h", "9c", "Qh"], "B", 2], [["As", "Ac", "Kh", "9s"], "D", 1], '
                      '[["10s", "9d", "Kd", "Ks"], "D", 3], [["Qs", "Js", "Ks", "Jh"], "B", 4], [["Kd", "Qh", "10h", '
                      '"9s"], "C", 1], [["Ad", "Ac", "10c", "10h"], "A", 2], [["Ah", "As", "9h", "Jd"], "A", 0], '
                      '[["Jc", "9d", "Jd", "Kh"], "A", 1], [["Kc", "Jc", "Ad", "10c"], "B", 0]]',
            'A_points': '0', 'B_points': '0', 'C_points': '0', 'D_points': '0',
            'without_nines': '0'}
    scorer = DokoScorer(data)
    scorer.calculate_score()
    assert_points(data, [12, -4, -4, -4])

if __name__ == "__main__":
    test_normal_contra_wins()
    test_extra_points()
    test_solo_contra_no_90_wins()
    print("OK")
