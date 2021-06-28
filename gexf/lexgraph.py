import os
import sys
import sknetwork
import gexf
from gexf import GexfGraph
import egographs

def calculate_layout(graph):
    algo = sknetwork.embedding.force_atlas.ForceAtlas2(n_iter = 40,
                                                       repulsive_factor = 0.2)
    return algo.fit_transform(graph)

def make_lexgraphs(graph):
    lexgraphs = []
    for label, egograph in egographs.make_egographs_parallel(graph):
        egograph.renumber()
        embedding = calculate_layout(
            sknetwork.utils.edgelist2adjacency(egograph.edges))
        for i, row in enumerate(embedding):
            egograph.id2node[i].position = tuple(row)
        lexgraphs.append((label, egograph))
    return lexgraphs


if __name__ == '__main__':
    try:
        os.mkdir(sys.argv[2])
    except FileExistsError:
        pass
    for label, lexgraph in make_lexgraphs(GexfGraph.from_gexf(sys.argv[1])):
        writeobj = open(os.path.join(sys.argv[2], "egograph_" + label + '.gexf'), 'w')
        writeobj.write(gexf.gexf_from_GexfGraph(lexgraph))

