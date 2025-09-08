import json
import requests

word_level_map = {}

with open('word_level.json', 'r') as f:
    data = json.load(f)

    for i, word_list in enumerate(data):
        for word in word_list:
            word_level_map[word] = i + 1

with open('gaming/words.json', 'r') as f:
    data = json.load(f)

    for word in data:
        word_level = word_level_map.get(word['word'], None)

        if word_level is None:
            print(word['word'], "is not in word_level_map")
            continue

        word['level'] = word_level

    print("==============================================")
    
    with open('gaming/words.json', 'w') as f:
        json.dump(data, f)