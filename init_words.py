import json
import csv

# with open('gaming/words.json', 'r') as f:
#     data = json.load(f)

#     for word in data:
#         word['type'] = 'gre'

#     print("==============================================")
    
#     with open('gaming/words.json', 'w') as f:
#         json.dump(data, f, indent=2, ensure_ascii=False)

append_data = []

with open('7000.csv', 'r') as f:
    reader = csv.reader(f)
    
    for row in reader:
        for word_data in row:
            if not word_data:
                continue

            print(word_data)

            word, data = word_data.split('@')
            part_of_speech = data.split('.')[0][1:]
            
            sliced_data = data.split(')')
            chinese = "".join(sliced_data[1:])

            append_data.append({
                "word": word,
                "level": 0,
                "type": "hs7000",
                "definitions": [
                    {
                        "part_of_speech": part_of_speech,
                        "translation": chinese
                    }
                ]
            })


with open('gaming/words.json', 'r') as f:
    data = json.load(f)

    word_list = [d['word'] for d in data]

    for d in append_data:
        if d['word'] in word_list:
            continue
        
        data.append(d)

    with open('gaming/words.json', 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    