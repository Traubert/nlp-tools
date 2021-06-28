from gexf import GexfGraph, GexfNode
import sys
import copy
import multiprocessing

def make_egograph(maingraph, root_id, n = 1, id_edge_index = None):
    egograph = GexfGraph()
    egograph.attribs = maingraph.attribs
    if id_edge_index is None: id_edge_index = maingraph.get_edge_index()
    next_round = set([root_id])
    while n >= 0:
        this_round = list(next_round)
        # print(f"rounds left {n}, this round size {len(this_round)}, nodes in egograph {len(egograph.id2node)}")
        next_round = set()
        for new_id in this_round:
            egograph.id2node[new_id] = copy.deepcopy(maingraph.id2node[new_id])
            for (source, target, weight) in id_edge_index[new_id]:
                other = source if new_id == target else target
                if other in egograph.id2node:
                    egograph.edges.append((source, target, weight))
                else:
                    next_round.add(other)
        n -= 1
    return egograph

def make_egographs(maingraph, n = 1):
    egographs = {}
    edge_index = maingraph.get_edge_index()
    for node_id, node in maingraph.id2node.items():
        egographs[node.label] = make_egograph(maingraph, node_id, n, edge_index)
    return egographs

_maingraph = None
_id_edge_index = None
_n = None

def make_egograph_parallel(root_id):
    egograph = GexfGraph()
    egograph.attribs = _maingraph.attribs
    next_round = set([root_id])
    n = _n
    while n >= 0:
        this_round = list(next_round)
        next_round = set()
        for new_id in this_round:
            egograph.id2node[new_id] = copy.deepcopy(_maingraph.id2node[new_id])
            for (source, target, weight) in _id_edge_index[new_id]:
                other = source if new_id == target else target
                if other in egograph.id2node:
                    egograph.edges.append((source, target, weight))
                else:
                    next_round.add(other)
        n -= 1
    return root_id, egograph

def make_egographs_parallel(maingraph, n = 1):
    global _maingraph
    _maingraph = maingraph
    global _n
    _n = n
    egographs = {}
    global _id_edge_index
    _id_edge_index = _maingraph.get_edge_index()
    with multiprocessing.Pool(12) as pool:
        for _id, graph in pool.map(make_egograph_parallel, _maingraph.id2node.keys()):
            egographs[_maingraph.id2node[_id].label] = graph
    return egographs

if __name__ == '__main__':
    n = 1
    if len(sys.argv) > 2:
        n = int(sys.argv[2])
    for egograph in make_egographs_parallel(GexfGraph.from_gexf(sys.argv[1]), n).values():
        print(egograph.node_count(), egograph.edge_count())
