import json
import random

with open('/home/yannik/projects/activities/character/dependencies/translation/240_traits.json') as f:
    old_traits1 = json.loads(f.read())
    
with open('/home/yannik/projects/activities/character/dependencies/translation/240_traits_translated.json') as f:
    old_traits2 = json.loads(f.read())

numbers = random.shuffle(list(range(240)))
print(numbers)