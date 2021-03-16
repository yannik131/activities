import json
import random

with open('/home/yannik/projects/activities/character/dependencies/translation/240_traits.json') as f:
    old_traits1 = json.loads(f.read())
    
with open('/home/yannik/projects/activities/character/dependencies/translation/240_traits_translated.json') as f:
    old_traits2 = json.loads(f.read())

numbers = list(range(240))
random.shuffle(numbers)
new1, new2 = list(), list()

for i in numbers:
    new1.append(old_traits1[i])
    new2.append(old_traits2[i])
    
with open('/home/yannik/projects/activities/character/dependencies/translation/240_traits_shuffled.json', 'w') as f:
    f.write(json.dumps(new1))
    
with open('/home/yannik/projects/activities/character/dependencies/translation/240_traits_translated_shuffled.json', 'w') as f:
    f.write(json.dumps(new2))