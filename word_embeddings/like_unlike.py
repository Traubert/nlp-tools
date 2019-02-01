import argparse
from subprocess import Popen, PIPE

import word2vec

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
vecs = word2vec.VecReader(wordvecfilename)

fun = 'Like('
if args.u:
    fun = 'Unlike('

likes = []

script = ''
script += "set need-separators off\n"
script += "set vector-similarity-projection-factor " + str(similarityfactor) + '\n'
script += '@vec"' + wordvecfilename + '"\n'
if args.word1 == args.word2 and not args.u:
    script += 'define TOP ' + fun + args.word1 + ')^' + str(args.n_closest) + ';\n'
else:
    script += 'define TOP ' + fun + args.word1 + ', ' + args.word2 + ')^' + str(args.n_closest) + ';\n'
pmatch2fst_process = Popen(["hfst-pmatch2fst", "--cosine-distances"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
pmatch_out, err = pmatch2fst_process.communicate(input=script.encode('utf-8'))

fst2strings_process = Popen(["hfst-fst2strings", "--print-weights"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
fst2strings_out, err = fst2strings_process.communicate(input=pmatch_out)
out_lines =  str(fst2strings_out, "utf-8").split("\n")
scored_strings = []
for line in out_lines:
    if line != "":
        parts = line.split("\t")
        scored_strings.append((parts[0], float(parts[1])))
for word, score in sorted(scored_strings, key = lambda x: x[1]):
    print(word)
