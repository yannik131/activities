import random
import json

with open("/home/yannik/projects/activities/character/dependencies/all_traits.txt") as f:
    lines = f.readlines()
    random.shuffle(lines)

traits = dict()
for line in lines:
    print(line.split(' ('))
    question, category = line.split(' (')
    category = category[:-2]
    if category not in traits:
        traits[category] = list()
    traits[category].append(question)

categories = sorted(list(traits.keys()))
result = dict()

for category in categories:
    result[category] = traits[category][:2]
    print(category, traits[category])

dumped = json.dumps(result)
with open("/home/yannik/projects/activities/character/dependencies/120_traits.json", "w") as f:
    f.write(dumped)
