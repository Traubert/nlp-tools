'''From a token-per-line & empty-line-between-paragraphs format, generate
training data useful for training a recapitalizer: normalized tokens, TAB, and
either 'O' for no change, or 'C' for capitalize, 'A' for allcaps, 'M' for other.
'''

while True:
    try:
        word = input().strip()
    except EOFError:
        break
    if word == '':
        print()
        continue
    if word.lower != word:
        if word.istitle():
            print(word.lower() + '\t' + 'C')
        elif word.isupper():
            print(word.lower() + '\t' + 'A')
        else:
            print(word.lower() + '\t' + 'M')
    else:
        print(word + '\t' + 'O')
