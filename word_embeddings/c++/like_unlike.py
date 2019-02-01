import argparse
import embutils

parser = argparse.ArgumentParser(description = "Print the members of a Like() or Unlike() group.")
parser.add_argument('word1', action='store')
parser.add_argument('word2', action='store')
parser.add_argument('word_embedding_file', action='store')
parser.add_argument('-u', action='store_true', default=False, help='Unlike() instead of Like()')
parser.add_argument('--n-closest', type=int, default=20 , help='number of group members (default: 20)')
parser.add_argument('--projection-factor', type=float, default=1.0 , help='projection factor, 1.0 is full projection (default: 1.0)')

args = parser.parse_args()
wordvecfilename = args.word_embedding_file
similarityfactor = args.projection_factor
nwords = args.n_closest
vecs = embutils.WordEmbeddings()
vecs.load_from_file(wordvecfilename)

if args.word1 == args.word2:
    result = vecs.like(args.word1, nwords)
elif args.u:
    result = vecs.unlike(args.word1, args.word2, nwords, similarityfactor)
else:
    result = vecs.like(args.word1, args.word2, nwords, similarityfactor)
for scoredword in result:
    print(scoredword[0])
