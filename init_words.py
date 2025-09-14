import json
import csv

with open('gaming/words.json', 'r') as f:
    data = json.load(f)

    for word in data:
        word['test_type'] = word['type']
        word.pop('type')

        print("==============================================")
    
    with open('gaming/words.json', 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
