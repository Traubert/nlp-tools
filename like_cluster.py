import argparse
from subprocess import Popen, PIPE

import word2vec

parser = argparse.ArgumentParser(description = "Perform Like() clustering for one target word and a word embedding file. The word embedding file can be in binary or text format.")
parser.add_argument('target_word', action='store')
parser.add_argument('word_embedding_file', action='store')
parser.add_argument('--n-closest', type=int, default=20 , help='number of neighbour words to consider (default: 20)')
parser.add_argument('--shared-proportion-cutoff', type=float, default=0.5 , help='what proportion of cluster members must be shared (default: 0.5)')
parser.add_argument('--projection-factor', type=float, default=1.0 , help='projection factor for Like() operation, 1.0 is full projection (default: 1.0)')
parser.add_argument('--print-like-lists', action='store_true', default=False, help='whether to print the members of each Like(target_word, neighbour_of_target_word')
parser.add_argument('--print-shared-member-counts', action='store_true', default=False, help='print how many members were shared with each cluster')
parser.add_argument('--fill-graph', action='store_true', default=False, help='print list of words that participate in any cluster')
parser.add_argument('--suppress-false-results', action='store_true', default=True, help="don't print that a pair doesn't cluster with each other")
parser.add_argument('--suppress-true-results', action='store_true', default=False, help="don't print that a pair does cluster with each other")
parser.add_argument('--verbose', action='store_true', default=False, help='print everything')

args = parser.parse_args()
clusterword = args.target_word
wordvecfilename = args.word_embedding_file
similarityfactor = args.projection_factor
nwords = args.n_closest

vecs = word2vec.VecReader(wordvecfilename)
words = vecs.closest_n(clusterword, nwords)
likes = []

script = ''
script += "set need-separators off\n"
script += "set vector-similarity-projection-factor " + str(similarityfactor) + '\n'
script += '@vec"' + wordvecfilename + '"\n'
for word2 in words:
    word2 = word2.replace('-', '#').replace('_', '#')
    script += "define " + word2 + ' Like("' + clusterword + '", "' + word2 + '")^' + str(nwords) + ';\n'
    likes.append(word2)
script += "define TOP " + ' | '.join(map(lambda x: '[ {' + x + ' } ' + x + ' ]\n', likes)) + ";\n"
pmatch2fst_process = Popen(["hfst-pmatch2fst"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
pmatch_out, err = pmatch2fst_process.communicate(input=script.encode('utf-8'))

fst2strings_process = Popen(["hfst-fst2strings"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
fst2strings_out, err = fst2strings_process.communicate(input=pmatch_out)
strings = str(fst2strings_out, "utf-8")

threshold = args.shared_proportion_cutoff

groups = {}
associations = {}

for line in strings.split('\n'):
    if ' ' not in line:
        continue
    groupword, word = line.split(' ')
    groups[groupword] = groups.setdefault(groupword, []) + [word]

groups[clusterword] = list(groups.keys())

for key in groups:
    associations[key] = {}
    for key2 in groups:
        if key == key2:
            continue
        associations[key][key2] = len(list(filter(lambda x: x in groups[key2], groups[key])))

if args.print_like_lists or args.verbose:
    for key in groups:
        print("Like(" + clusterword + ", " + key + ") contains the words:")
        for item in groups[key]:
            print("  " + item)

if args.print_shared_member_counts or args.verbose:
    for key in associations:
        print("Like(" + clusterword + ", " + key + ")")
        for item in associations[key]:
            print("  shares " + str(associations[key][item]) + " members with Like(" + clusterword + ", " + item + ")")

def clusters_with(a, b):
    return float(associations[a][b])/nwords > threshold

all_cluster_members = set()

for a in groups.keys():
    clusteringgroup = []
    nonclusteringgroup = []
    for b in groups.keys():
        if a == b:
            continue
        if clusters_with(a, b):
            all_cluster_members.add(a)
            clusteringgroup.append(b)
        else:
            nonclusteringgroup.append(b)
    if len(clusteringgroup) > 0 and (not args.suppress_true_results) or args.verbose:
        print(a + " clusters with " + ', '.join(clusteringgroup))
    if len(nonclusteringgroup) > 0 and (not args.suppress_false_results) or args.verbose:
        print(a + " doesn't cluster with " + ', '.join(nonlusteringgroup))

if args.fill_graph:
    for word in all_cluster_members:
        print(word)
