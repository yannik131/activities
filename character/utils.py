BIG_FIVE = {
    'n': ['anx', 'ang', 'dep', 'con', 'imm', 'vul'],
    'e': ['fri', 'gre', 'ass', 'act', 'exc', 'che'],
    'o': ['ima', 'art', 'emo', 'adv', 'int', 'lib'],
    'a': ['tru', 'mor', 'alt', 'coo', 'mod', 'sym'],
    'c': ['eff', 'ord', 'dut', 'ach', 'dis', 'cau']
}

MAX_TRAIT_VALUE = 20 # 4 questions, 1-5 points each
MIN_TRAIT_VALUE = 4


def to_numbers(d):
    return dict([(k, int(v)) for k, v in d.items()])
    

def create_trait_dict(default=0):
    traits = dict()
    for big in BIG_FIVE:
        for trait in BIG_FIVE[big]:
            traits[trait] = default
    return traits
    
