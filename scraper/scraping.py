import PyPDF2
import re
import pandas as pd


def read_prob():

    # creating a pdf reader object
    reader = PyPDF2.PdfReader('113_NI_quiz.pdf')

    # print the text of the first page
    pages = reader.pages
    content = pages[0].extract_text().split('\n')[9:]

    for i in range(1, len(pages)):
        content += pages[i].extract_text().split('\n')[9:]

    adddingProb = False

    records = {
        'problems': [],
        'options': [],
    }

    for line in content:
        # adding problem
        if adddingProb:

            # restart adding records['options']
            if 57740 <= ord(line[0]) <= 57743:
                adddingProb = False

                records['options'].append([])
                reStr = '|'.join(map(lambda x: chr(x), range(57740, 57744)))
                newChoices = re.split(reStr, line)
                newChoices = [x for x in newChoices if bool(x)]
                records['options'][-1] += newChoices

            # adding problem
            else:
                records['problems'][-1] += line

        # adding records['options']
        else:
            # restart adding problem
            if line[0].isnumeric():
                adddingProb = True

                i = 0
                while line[i].isnumeric():
                    i += 1

                records['problems'].append(line[i:])

            # adding choice
            elif 57740 <= ord(line[0]) <= 57743:
                reStr = '|'.join(map(lambda x: chr(x), range(57740, 57744)))
                newChoices = re.split(reStr, line)
                newChoices = [x for x in newChoices if bool(x)]
                records['options'][-1] += newChoices

            else:
                continue

    df = pd.DataFrame(records)
    return df


def read_ans():
    # creating a pdf reader object
    reader = PyPDF2.PdfReader(open('113_NI_ans.pdf', 'rb'))

    # print the text of the first page
    t = reader.get_form_text_fields()
    print(t)


if __name__ == '__main__':
    read_ans()
    # df = read_prob()
