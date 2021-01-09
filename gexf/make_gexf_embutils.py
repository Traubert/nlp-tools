import os
import sys
import argparse
import string
from lxml import etree
import urllib.parse
from math import log

import time
t = time.time()

import embutils

parser = argparse.ArgumentParser(description = "Compile a word embedding file into a gexf graph representation")
parser.add_argument('embedding_file', action='store')
parser.add_argument('--output', '-o', action='store', default=None, help='Output file, default is STDOUT')
parser.add_argument('--ego', type=str, action='store', default=None, help='Make an ego network around this word')
parser.add_argument('--ego-vocab', type=str, action='store', default=None, help='Make ego networks around words from vocabulary file')
parser.add_argument('--ego-all', type=str, action='store', default=None, help='Make ego networks around all words')
parser.add_argument('--n-words', type=int, default=1000 , help='How many words to initially include in the graph (default: 1000)')
parser.add_argument('--distance-limit', type=float, default=0.4 , help='Add arcs to words with distance less than this (default: 0.4)')
parser.add_argument('--min-neighbours', type=int, default=2 , help='A word should have at least this many neighbours (default: 2)')
parser.add_argument('--max-neighbours', type=int, default=60 , help='Consider at most this many neighbours within distance limit (default: 60)')
parser.add_argument('--weight-scaling', type=float, default=2.5 , help='Scaling factor of distances to arc strength (default: 2.5)')


def make_url_oracc(word):
    encoded_word = urllib.parse.quote(word)
    return "http://oracc.museum.upenn.edu/find?phrase=" + encoded_word

def make_url_korp(word):
    encoded_word = urllib.parse.quote(word)
    return f'https://korp.csc.fi/?mode=other_languages#?lang=en&cqp=%5Blemma%20%3D%20%22{encoded_word}%22%5D&corpus=oracc_adsd,oracc_ario,oracc_blms,oracc_cams,oracc_caspo,oracc_ctij,oracc_dcclt,oracc_dccmt,oracc_ecut,oracc_etcsri,oracc_hbtin,oracc_obmc,oracc_riao,oracc_ribo,oracc_rimanum,oracc_rinap,oracc_saao,oracc_others&stats_reduce=word&search_tab=1&search=cqp'

def make_url_ego(word):
    encoded_word = urllib.parse.quote(word)
    return f'http://0.0.0.0:8000/#egographs/egograph_{encoded_word}.gexf.json'
#    return f'_MAKE_ANCHOR_LEFT_{word}_MAKE_ANCHOR_MIDDLE_{word}_MAKE_ANCHOR_RIGHT_'# f'<a href="#{word}.json">{word}</a>'
def rewrite_anchors(s):
    return s.replace('_MAKE_ANCHOR_LEFT_', '<a href="#').replace('_MAKE_ANCHOR_MIDDLE_', '.json">').replace('_MAKE_ANCHOR_RIGHT_', '</a>')

make_url = lambda x: ''
make_url1 = make_url_oracc
make_url2 = make_url_korp

r_value = "100"
g_value = "0"
b_value = "100"

def acceptable_word_en(word):
    return word.isalpha() and word.islower() #[0] in string.ascii_letters and not word.startswith('<')
def acceptable_word_ak(word):
    return True

acceptable_word = acceptable_word_ak
#make_url1 = make_url
#make_url2 = make_url
#<gexf xmlns="http://www.gexf.net/1.3" version="1.3" xmlns:viz="http://www.gexf.net/1.3/viz" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.gexf.net/1.3 http://www.gexf.net/1.3/gexf.xsd">

def rewrite_tags(s):
    old_gexf_tag = '<gexf version="1.3" xmlns="http://www.gexf.net/1.3">'
    new_gexf_tag = '<gexf xmlns="http://www.gexf.net/1.3" version="1.3" xmlns:viz="http://www.gexf.net/1.3/viz" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.gexf.net/1.3 http://www.gexf.net/1.3/gexf.xsd">'
    old_size_open = '<size '
    new_size_open = '<viz:size '
    old_color_open = '<color '
    new_color_open = '<viz:color '
    old_size_close = '</size>'
    new_size_close = '</viz:size>'
    old_color_close = '</color>'
    new_color_close = '</viz:color>'
    old_position_open = '<position '
    new_position_open = '<viz:position '
    old_position_close = '</position>'
    new_position_close = '</viz:position>'
    return s.replace(old_gexf_tag, new_gexf_tag).replace(old_size_open, new_size_open).replace(old_color_open, new_color_open).replace(old_size_close, new_size_close).replace(old_color_close, new_color_close).replace(old_position_open, new_position_open).replace(old_position_close, new_position_close)

def build_graph(args):
    xml = etree.Element("gexf",
                        xmlns = "http://www.gexf.net/1.3",
                        version="1.3")
    #xml.set("xmlns:viz", "http://www.gexf.net/1.3/viz")
    graph = etree.Element("graph", mode="static", defaultedgetype="undirected")
    attributes = etree.Element("attributes")
    attributes.set("class", "node")
    # attributes.append(etree.Element("attribute", id="url1", title="url1", type="string"))
    attributes.append(etree.Element("attribute", id="search_url", title="Search in Korp", type="string"))
    if args.ego != None:
        attributes.append(etree.Element("attribute", id="egourl", title="Go to this ego graph", type="string"))
        
    attributes.append(etree.Element("attribute", id="freqrank", title="Frequency rank", type="string"))
    nodes = etree.Element("nodes")
    edges = etree.Element("edges")

    vecs = embutils.WordEmbeddings()
    vecs.load_from_file(args.embedding_file)
    vocabulary = vecs.get_vocabulary()
    words = list(filter(acceptable_word, vocabulary))
    if args.ego == None:
        seed_words = words[:args.n_words]
    else:
        seed_words = [args.ego] #list(map(lambda x: x[0], vecs.like(args.ego, 20)))

    edges_added = set()
    words_added = set()
    
    def make_node(word, index):
        node = etree.Element("node", id=str(index), label=word)
        attvalues = etree.SubElement(node, "attvalues")
        # attvalues.append(etree.Element("attvalue", id="url1", value=make_url1(word)))
        attvalues.append(etree.Element("attvalue", id="search_url", value=make_url2(word)))
        if args.ego != None:
            if word == args.ego:
                attvalues.append(etree.Element("attvalue", id="egourl", value=""))
                # etree.SubElement(node, "position", x = "0.0", y = "0.0")
            else:
                attvalues.append(etree.Element("attvalue", id="egourl", value=make_url_ego(word)))
            
        freqrank = vocabulary.index(word) + 1
        attvalues.append(etree.Element("attvalue", id="freqrank", value=f"{freqrank}/{len(vocabulary)}"))
        size = etree.SubElement(node, "size", value = str(-1*log(float(freqrank)/(10*args.n_words))))
        color = etree.SubElement(node, "color", r = r_value, g = g_value, b = b_value)
        return node

    for i, word in enumerate(seed_words):
        if len(words_added) >= args.n_words:
            break

        nodes.append(make_node(word, i))
        words_added.add(word)
        neighbours = vecs.get_words_at_distance_under(word, args.distance_limit)
        if len(neighbours) < args.min_neighbours + 1:
            neighbours = vecs.like(word, args.min_neighbours + 1)
        neighbours_added = 0
        for neighbour in neighbours:
            if len(words_added) >= args.n_words or neighbours_added >= args.max_neighbours:
                break
            neighbour_weight = max(0.0, (1 - neighbour[1] - args.distance_limit))*args.weight_scaling
            neighbour_word = neighbour[0]
            if (neighbour_word, word) in edges_added:
                neighbours_added += 1
                continue
            if not acceptable_word(neighbour_word) or word == neighbour_word:
                continue
            neighbour_id = str(words.index(neighbour_word))
            if neighbour_word not in words_added:
                nodes.append(make_node(neighbour_word, str(neighbour_id)))
                words_added.add(neighbour_word)
            edges_added.add((word, neighbour_word))
            edges.append(etree.Element("edge", id=str(len(edges)), source=str(i), target=neighbour_id, weight=str(neighbour_weight)))
            neighbours_added += 1
        if args.ego != None:
            for word1 in words_added:
                for word2 in words_added:
                    if word1 == word2 or args.ego in ((word1, word2)):
                        continue
                    distance = vecs.get_distance(word1, word2)
                    if distance < args.distance_limit:
                        edges_added.add((word1, word2))
                        word1_id = str(words.index(word1))
                        word2_id = str(words.index(word2))
                        weight = max(0.0, (1 - distance - args.distance_limit))*args.weight_scaling
                        edges.append(etree.Element("edge", id=str(len(edges)), source=word1_id, target=word2_id, weight=str(weight)))
    #print(time.time() - t)
    graph.append(attributes)
    graph.append(nodes)
    graph.append(edges)
    xml.append(graph)
    #print(time.time() - t)
    if args.output != None:
        outfile = open(args.output, 'w')
    else:
        outfile = sys.stdout
    xml_string = str(etree.tostring(xml, xml_declaration=True, pretty_print = True, encoding = "utf-8"), "utf-8")
    outfile.write(rewrite_tags(xml_string))
    #print(time.time() - t)

if __name__ == '__main__':
    args = parser.parse_args()
    if args.ego_vocab == None:
        build_graph(args)
    else:
        outputdir = args.output
        if not os.path.isdir(outputdir):
            if os.path.exists(outputdir):
                exit(f"Couldn't open output directory {outputdir}")
            else:
                os.mkdir(outputdir)
        for word in open(args.ego_vocab):
            args.ego = word.strip()
            args.output = os.path.join(outputdir, 'egograph_' + args.ego + '.gexf')
            build_graph(args)
    
