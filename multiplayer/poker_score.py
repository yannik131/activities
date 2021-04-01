#https://towardsdatascience.com/poker-with-python-how-to-score-all-hands-in-texas-holdem-6fd750ef73d
#https://github.com/dirusali/pokerodds/blob/release-1.0/scores.py

import numpy as np
import itertools
from django.utils.translation import gettext_lazy as _

def combinations(arr, n):
    arr = np.asarray(arr)
    t = np.dtype([('', arr.dtype)]*n)
    result = np.fromiter(itertools.combinations(arr, n), t)
    return result.view(arr.dtype).reshape(-1, n)

def check_four_of_a_kind(hand,letters,numbers,rnum,rlet):
    for i in numbers:
        if numbers.count(i) == 4:
            four = i
        elif numbers.count(i) == 1:
            card = i
    score = 105 + four + card/100
    return score

def check_full_house(hand,letters,numbers,rnum,rlet):
    for i in numbers:
        if numbers.count(i) == 3:
            full = i
        elif numbers.count(i) == 2:
            p = i
    score = 90 + full + p/100  
    return score

def check_three_of_a_kind(hand,letters,numbers,rnum,rlet):
    cards = []
    for i in numbers:
        if numbers.count(i) == 3:
            three = i
        else: 
            cards.append(i)
    score = 45 + three + max(cards) + min(cards)/1000
    return score

def check_two_pair(hand,letters,numbers,rnum,rlet):
    pairs = []
    cards = []
    for i in numbers:
        if numbers.count(i) == 2:
            pairs.append(i)
        elif numbers.count(i) == 1:
            cards.append(i)
            cards = sorted(cards,reverse=True)
    score = 30 + max(pairs) + min(pairs)/100 + cards[0]/1000
    return score

def check_pair(hand,letters,numbers,rnum,rlet):    
    pair = []
    cards  = []
    for i in numbers:
        if numbers.count(i) == 2:
            pair.append(i)
        elif numbers.count(i) == 1:    
            cards.append(i)
            cards = sorted(cards,reverse=True)
    score = 15 + pair[0] + cards[0]/100 + cards[1]/1000 + cards[2]/10000
    return score

def score_hand(hand):
    number_map = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '1': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
    letters = [hand[i][1] for i in range(5)] # We get the suit for each card in the hand
    numbers = [number_map[hand[i][0]] for i in range(5)]  # We get the number for each card in the hand
    rnum = [numbers.count(i) for i in numbers]  # We count repetitions for each number
    rlet = [letters.count(i) for i in letters]  # We count repetitions for each letter
    dif = max(numbers) - min(numbers) # The difference between the greater and smaller number in the hand
    handtype = ''
    score = 0
    if 5 in rlet:
        if numbers ==[14,13,12,11,10]:
            handtype = 'royal_flush'
            score = 135

        elif dif == 4 and max(rnum) == 1:
            handtype = 'straight_flush'
            score = 120 + max(numbers)

        elif 4 in rnum:
            handtype == 'four_of_a_kind'
            score = check_four_of_a_kind(hand,letters,numbers,rnum,rlet)

        elif sorted(rnum) == [2,2,3,3,3]:
            handtype == 'full_house'
            score = check_full_house(hand,letters,numbers,rnum,rlet)

        elif 3 in rnum:
            handtype = 'three_of_a_kind'
            score = check_three_of_a_kind(hand,letters,numbers,rnum,rlet)

        elif rnum.count(2) == 4:
            handtype = 'two_pair'
            score = check_two_pair(hand,letters,numbers,rnum,rlet)

        elif rnum.count(2) == 2:
            handtype = 'pair'
            score = check_pair(hand,letters,numbers,rnum,rlet)

        else:
            handtype = 'flush'
            score = 75 + max(numbers)/100

    elif 4 in rnum:
        handtype = 'four_of_a_kind'
        score = check_four_of_a_kind(hand,letters,numbers,rnum,rlet)

    elif sorted(rnum) == [2,2,3,3,3]:
       handtype = 'full_house'
       score = check_full_house(hand,letters,numbers,rnum,rlet)

    elif 3 in rnum:
        handtype = 'three_of_a_kind' 
        score = check_three_of_a_kind(hand,letters,numbers,rnum,rlet)

    elif rnum.count(2) == 4:
        handtype = 'two_pair'
        score = check_two_pair(hand,letters,numbers,rnum,rlet)

    elif rnum.count(2) == 2:
        handtype = 'pair'
        score = check_pair(hand,letters,numbers,rnum,rlet)

    elif dif == 4:
        handtype = 'straight'
        score = 65 + max(numbers)

    else:
        handtype= 'high_card'
        n = sorted(numbers,reverse=True)
        score = n[0] + n[1]/100 + n[2]/1000 + n[3]/10000 + n[4]/100000

    return [score, handtype]
    
def highest_combo(common_cards, player_cards):
    combi = combinations(common_cards+player_cards, 5)
    scores = [score_hand(hand) for hand in combi]
    return max(scores, key=lambda l: l[0])
