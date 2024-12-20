BIG_FIVE = {
    'n': ['anx', 'ang', 'dep', 'con', 'imm', 'vul'],
    'e': ['fri', 'gre', 'ass', 'act', 'exc', 'che'],
    'o': ['ima', 'art', 'emo', 'adv', 'int', 'lib'],
    'a': ['tru', 'mor', 'alt', 'coo', 'mod', 'sym'],
    'c': ['eff', 'ord', 'dut', 'ach', 'dis', 'cau']
}


def to_numbers(d):
    return dict([(k, int(v)) for k, v in d.items()])
    

def create_trait_dict(default=0):
    traits = dict()
    for big in BIG_FIVE:
        for trait in BIG_FIVE[big]:
            traits[trait] = default
    return traits
    
def calc_score(score, reference, inverted):
    if reference >= 50:
        result = 50/(100-reference)*score+100-5000/(100-reference)
    else:
        result = 50/reference*score
    if result < 0:
        result = 0
    elif result > 100:
        result = 100
    if inverted:
        return 100-result
    return result
    
