import argparse
import embutils

parser = argparse.ArgumentParser(description = "Print the members of a Like() or Unlike() group.")
parser.add_argument('word1', action='store')
parser.add_argument('word2', action='store', nargs='?', default = None)
parser.add_argument('--embedding-file', '-f', metavar = 'FILENAME', action='store', help='File to read the word embeddings from')
parser.add_argument('-u', action='store_true', default=False, help='Unlike() instead of Like()')
parser.add_argument('--alternate-like', action='store_true', default=False, help='Alternate Unlike() implementation')
parser.add_argument('--alternate-unlike', action='store_true', default=False, help='Alternate Unlike() implementation')
parser.add_argument('--compare-implementations', action='store_true', default=False, help='Compare implementations')
parser.add_argument('--n-closest', type=int, default=20 , help='number of group members (default: 20)')
parser.add_argument('--projection-factor', type=float, default=1.0 , help='projection factor, 1.0 is full projection (default: 1.0)')
parser.add_argument('--cutoff', action='store', help='Only consider most common N or N%% of words')

args = parser.parse_args()
wordvecfilename = args.embedding_file
similarityfactor = args.projection_factor
nwords = args.n_closest
if args.cutoff is None:
    cutoff = 0
elif args.cutoff.endswith('%'):
    cutoff = float(args.cutoff[:-1]) * 0.01
else:
    cutoff = int(args.cutoff)

vecs = embutils.WordEmbeddings()
vecs.load_from_file(wordvecfilename, cutoff)

first = lambda x: x[0]
second = lambda x: x[1]

def alternate_like():
    '''
    Average two words and get closest neighbours of that point
    '''
    print(vecs.get_embedding(args.word1))

def alternate_unlike():
    candidatewords = vecs.like(args.word1, 10*nwords)
    result = []
    for word in candidatewords:
        if len(result) >= nwords:
            break
        if vecs.get_distance(args.word2, word[0]) > word[1]:
            result.append(word)
    return result
if args.word2 is None:
    args.word2 = args.word1
if args.word1 == args.word2:
    result = vecs.like(args.word1, nwords)
elif args.u:
    result = vecs.unlike(args.word1, args.word2, nwords, similarityfactor)
elif args.alternate_unlike:
    result = alternate_unlike()
elif args.alternate_like:
    result = alternate_like()
else:
    result = vecs.like(args.word1, args.word2, nwords, similarityfactor)
    
if args.compare_implementations:
    if args.u:
        regular = set(map(first, result))
        alternate = set(map(first, alternate_unlike()))
        for word in regular.difference(alternate):
            print("Regular unlike had " + word)
        for word in alternate.difference(regular):
            print("Alternate unlike had " + word)

for scoredword in result:
    print("{}\t{}".format(scoredword[0], 2-scoredword[1]))
