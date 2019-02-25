import argparse
import embutils

parser = argparse.ArgumentParser(description = "Perform Like() clustering for one target word and a word embedding file. The word embedding file can be in binary or text format.")
parser.add_argument('target_word', action='store')
parser.add_argument('word_embedding_file', action='store')
parser.add_argument('--n-closest', type=int, default=20 , help='number of neighbour words to consider (default: 20)')
parser.add_argument('--shared-proportion-cutoff', type=float, default=0.5 , help='what proportion of cluster members must be shared (default: 0.5)')
parser.add_argument('--projection-factor', type=float, default=1.0 , help='projection factor for Like() operation, 1.0 is full projection (default: 1.0)')
parser.add_argument('--print-like-lists', action='store_true', default=False, help='whether to print the members of each Like(target_word, neighbour_of_target_word')
parser.add_argument('--print-shared-member-counts', action='store_true', default=False, help='print how many members were shared with each cluster')
parser.add_argument('--fill-graph', action='store_true', default=False, help='print list of words that participate in any cluster')
parser.add_argument('--show-false-results', action='store_true', default=False, help="report that a pair doesn't cluster with each other")
parser.add_argument('--suppress-true-results', action='store_true', default=False, help="don't report that a pair does cluster with each other")
parser.add_argument('--verbose', action='store_true', default=False, help='print everything')
parser.add_argument('--draw-graph', action='store_true', default=False, help='Write a picture of the graph as out.png')

args = parser.parse_args()
clusterword = args.target_word
wordvecfilename = args.word_embedding_file
similarityfactor = args.projection_factor
nwords = args.n_closest
threshold = args.shared_proportion_cutoff

first = lambda x: x[0]
get_words = lambda x: list(map(first, x))

vecs = embutils.WordEmbeddings()
vecs.load_from_file(wordvecfilename)
words_with_weights = vecs.like(clusterword, nwords)
words = get_words(words_with_weights)

groups = {}
groups_with_weights = {}
associations = {}

groups[clusterword] = words
groups_with_weights[clusterword] = words_with_weights
for word2 in words:
    if word2 != clusterword:
        clusterwords_with_weights = vecs.like(clusterword, word2, nwords, similarityfactor)
        groups[word2] = get_words(clusterwords_with_weights)
        groups_with_weights[word2] = clusterwords_with_weights

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
    if len(nonclusteringgroup) > 0 and (args.show_false_results) or args.verbose:
        print(a + " doesn't cluster with " + ', '.join(nonclusteringgroup))

if args.fill_graph:
    for word in all_cluster_members:
        print(word)

if args.draw_graph:
        
    import matplotlib.pyplot as plt
    import networkx as nx

    G=nx.Graph()

    for a in groups.keys():
        for b in groups.keys():
            if a == b:
                continue
            if clusters_with(a, b):
                G.add_edge(a, b, weight=vecs.get_distance(a, b))

    edges = [(u,v) for (u,v,d) in G.edges(data=True)]
    pos=nx.spring_layout(G)
    nx.draw_networkx_nodes(G,pos,node_size=60)
    nx.draw_networkx_edges(G,pos,edgelist=edges,
                           width=1,alpha=0.1,edge_color='b')

    def add_to_verticals(posdict, delta = 0.05):
        retval = {}
        for item, key in posdict.items():
            retval[item] = (key[0], key[1] + delta)
        return retval

    nx.draw_networkx_labels(G, add_to_verticals(pos), font_size=10, font_family='sans-serif')

    plt.axis('off')
    plt.savefig("out.png", dpi = 500) # save as png
