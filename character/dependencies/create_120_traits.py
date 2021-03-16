import random
import json

with open("/home/yannik/projects/activities/character/dependencies/all_traits.txt") as f:
    lines = f.readlines()
    random.shuffle(lines)

traits = dict()
non_redundant = dict()
goal = 4
for line in lines:
    question, category = line.split(' (')
    category = category[:-2]
    non_redundant[category[:-1]] = 0
    if category not in traits:
        traits[category] = list()
    traits[category].append(question)

categories = sorted(list(traits.keys()))
result = dict()

for category in non_redundant:
    p_items = traits[category+'+']
    n_items = traits[category+'-']
    if len(p_items) < goal:
        if len(n_items) < 2*goal-len(p_items):
            print(category, "not enough!")
            input()
            continue
        else:
            result[category+'+'] = traits[category+'+']
            result[category+'-'] = traits[category+'-'][:2*goal-len(p_items)]
    elif len(n_items) < goal:
        if len(p_items) < 2*goal-len(n_items):
            print(category, 'not enough!')
            input()
            continue
        else:
            result[category+'-'] = traits[category+'-']
            result[category+'+'] = traits[category+'+'][:2*goal-len(n_items)]
    else:
        result[category+'-'] = traits[category+'-'][:goal]
        result[category+'+'] = traits[category+'+'][:goal]

result_list = list()
for entry in result:
    for item in result[entry]:
        result_list.append([entry, "I "+item[0].lower()+item[1:]])
        
dumped = json.dumps(result_list)
with open("/home/yannik/projects/activities/character/dependencies/240_traits.json", "w") as f:
    f.write(dumped)
