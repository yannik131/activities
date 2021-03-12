big_five = {'N': 'Neuroticism', 'E': 'Extraversion',
            'O': 'Openness to experience', 'A': 'Agreeableness',
            'C': 'Conscientiousness'}

import json

with open("/home/yannik/projects/activities/character/dependencies/translation/questions.json") as f:
    print(json.loads(f.read()))
