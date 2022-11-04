'''From a token-per-line & empty-line-between-paragraphs format, generate
training data useful for training a repunctuator: normalized tokens, TAB, and
either 'O' for no change, or, other character for self-insert.
'''

word_cache = None
while True:
    try:
        word = input().strip()
    except EOFError:
        break
    if word == '':
        if word_cache:
            print(word.lower() + '\t' + 'O')
        word_cache = None
        print()
        continue
    if not word_cache:
        word_cache = word
        continue
    if word in '?.!,':
        pass
        
