from lxml import etree
import sknetwork
import numpy as np
from scipy import sparse
import sys

class GexfNode:
    def __init__(self, label):
        self.label = label
        self.attvalues = {}
class GexfGraph:
    ''' An internal gexf graph representation with typical visual elements.
    '''
    def __init__(self):
        self.id2node = {}
        self.edges = []
        self.node_attributes = {}
        self.attributes = {}
    def node_count(self): return len(self.id2node)
    def edge_count(self): return len(self.edges)
    def renumber(self):
        n_nodes = len(self.id2node)
        new_id2node = {}
        oldid2newid = {}
        for i, k in enumerate(sorted(self.id2node.keys())):
            new_id2node[i] = self.id2node[k]
            oldid2newid[k] = i
        self.id2node = new_id2node
        for i in range(len(self.edges)):
            self.edges[i] = (oldid2newid[self.edges[i][0]], oldid2newid[self.edges[i][1]], self.edges[i][2])

    def get_edge_index(self):
        edge_index = {}
        for edge in self.edges:
            f, t, w = edge
            edge_index[f] = edge_index.setdefault(f, []) + [edge]
            edge_index[t] = edge_index.setdefault(t, []) + [edge]
        return edge_index
    
    def from_gexf(gexf_filename):
        gexf = etree.parse(gexf_filename)
        base_nsmap = gexf.getroot().nsmap
        nsmap = {
            'g': base_nsmap[None],
            'viz': base_nsmap['viz'],
        }
        def viz(s):
            return "{" + nsmap['viz'] + "}" + s
        graph = GexfGraph()

        graph_element = gexf.xpath('//g:graph', namespaces=nsmap)[0]
        for attribute, value in graph_element.items():
            graph.attributes[attribute] = value
        for attribute in gexf.xpath('//g:attribute', namespaces=nsmap):
            attrid = attribute.get('id') if attribute.get('id') else attribute.get('for')
            graph.node_attributes[attrid] = {'title': attribute.get('title'), 'type': attribute.get('type')}

        for node in gexf.xpath('//g:node', namespaces=nsmap):
            _id = str2int(node.get('id'))
            thisnode = GexfNode(node.get('label'))
            # for attvalue in node.xpath('//g:attvalue', namespaces=nsmap):
            #     attrid = attvalue.get('id') if attvalue.get('id') else attvalue.get('for')
            #     thisnode.attvalues[attrid] = attvalue.get('value')
            for child in node:
                if child.tag == '{' + nsmap['g'] + '}' + 'attvalues':
                    for attvalue in child:
                        attrname = attvalue.get('id') if attvalue.get('id') else attvalue.get('for')
                        thisnode.attvalues[attrname] = attvalue.get('value')
                elif child.tag == viz('size'):
                    thisnode.size = float(child.get('value'))
                elif child.tag == viz('position'):
                    thisnode.position = (float(child.get('x')), float(child.get('y')))
                elif child.tag == viz('color'):
                    thisnode.color = (int(child.get('r')), int(child.get('g')), int(child.get('b')))
            graph.id2node[_id] = thisnode

        for edge in gexf.xpath('//g:edge', namespaces=nsmap):
            weight = edge.get('weight')
            src = str2int(edge.get('source'))
            tgt = str2int(edge.get('target'))
            if weight is None:
                print(f"Unweighted edge: {src} ({graph.id2node[src].label}) - {tgt} ({graph.id2node[tgt].label}), set to 1.0", file=sys.stderr)
                weight = 1.0
            else:
                weight = float(weight)
            graph.edges.append((src, tgt, weight))
        return graph

    def get_crowded_nodes(self, threshold, gridlines = 10):
        pos2id = {}
        min_x, max_x, min_y, max_y = 0, 0, 0, 0
        for _id, node in self.id2node.items():
            x, y = node.position
            min_x = min(x, min_x)
            max_x = max(x, min_x)
            min_y = min(y, min_y)
            max_y = max(y, min_y)
            assert((x, y) not in pos2id)
            pos2id[(x, y)] = _id
        x_delta, y_delta = (max_x-min_x)/gridlines, (max_y-min_y)/gridlines
        x_intervals = [min_x + x_delta*i for i in range(gridlines)]
        y_intervals = [min_x + y_delta*i for i in range(gridlines)]
        sectors = [ [[] for j in range(gridlines)] for i in range(gridlines)]
        for pos in pos2id.keys():
            x_i = int((pos[0] - min_x) // x_delta)
            y_i = int((pos[1] - min_y) // y_delta)

def str2int(s): return int(float(s))
        

xmlns_url = "http://www.gexf.net/1.3"
xmlns_viz_url = "http://www.gexf.net/1.3/viz"
xmlns_viz_prefix = "{%s}" % xmlns_viz_url
viz_sizetag = xmlns_viz_prefix + "size"
viz_positiontag = xmlns_viz_prefix + "position"
viz_colortag = xmlns_viz_prefix + "color"
xmlns_xsi_url = "http://www.w3.org/2001/XMLSchema-instance"
schemaLocation_qname = etree.QName(xmlns_xsi_url, "schemaLocation")
schemaLocation_val = "http://www.gexf.net/1.3 http://www.gexf.net/1.3/gexf.xsd"
nsmap = {None: xmlns_url, "viz": xmlns_viz_url, "xsi": xmlns_xsi_url}

def make_gexf_node(index, label, size = 1.0, xpos = 0.0, ypos = 0.0, color = (255, 255, 255)):
    element = etree.Element("node", id=str(index), label=label)
    element.append(etree.Element(viz_sizetag, value = str(size)))
    element.append(etree.Element(viz_positiontag, x = str(xpos), y = str(ypos)))
    element.append(etree.Element(viz_colortag, r = str(color[0]), g = str(color[1]), b = str(color[2])))
    return element

def adjacency2edgelist(adjacency, undirected = True):
    '''
    Convert a matrix, typically in scipy.sparse.csr_matrix form, into an edge list
    '''
    coord_matrix = sparse.coo_matrix(adjacency)
    return list(zip(coord_matrix.row, coord_matrix.col, coord_matrix.data))

def gexf_from_edgelist(edgelist, labels, embedding = None):
    xml = etree.Element("gexf",
                        version="1.3",
                        nsmap=nsmap)
    xml.set(schemaLocation_qname, schemaLocation_val)
    graph = etree.Element("graph", mode="static", defaultedgetype="undirected")
    nodes = etree.Element("nodes")
    edges = etree.Element("edges")

    for edge in edgelist:
        source, destination, weight = edge[0] + 1, edge[1] + 1, 1.0
        if len(edge) > 2:
            weight = edge[2]
        edges.append(etree.Element("edge", id=str(len(edges)), source=str(source), target=str(destination), weight=str(weight)))

    for i, label in enumerate(labels):
        xpos = ypos = 0.0
        if embedding:
            xpos, ypos = embedding[i][0], embedding[i][1]
        nodes.append(make_gexf_node(str(i + 1), label, xpos = xpos, ypos = ypos))
    
    graph.append(nodes)
    graph.append(edges)
    xml.append(graph)
    
    return str(etree.tostring(xml, xml_declaration=True, pretty_print = True, encoding = "utf-8"), "utf-8")

def gexf_from_adjacency(adjacency, labels, embedding = None):
    return gexf_from_edgelist(adjacency2edgelist(adjacency, undirected = True), labels, embedding)

def gexf_from_tuples(pairs):
    xml = etree.Element("gexf",
                        version="1.3",
                        nsmap=nsmap)
    xml.set(schemaLocation_qname, schemaLocation_val)
    graph = etree.Element("graph", mode="static", defaultedgetype="undirected")
    # If you want additional node attributes (other than labels, like translations), list them:
    # node_attributes = etree.Element("attributes")
    # node_attributes.set("class", "node")
    # attributes.append(etree.Element("attribute", id="search_url", title="Search in Korp", type="string"))
    # graph.append(attributes)
    #
    # Alternatively, insert them with insert_attribs.py

    nodes = etree.Element("nodes")
    edges = etree.Element("edges")
    vocabulary = {}

    for source_destination, weight in pairs:
        source, destination = source_destination
        source_idx = vocabulary.setdefault(source, len(vocabulary) + 1)
        destination_idx = vocabulary.setdefault(destination, len(vocabulary) + 1)
        edges.append(etree.Element("edge", id=str(len(edges)), source=str(source_idx), target=str(destination_idx), weight=str(weight)))

    for label, index in vocabulary.items():
        # if you have node attributes, or want to set visual ones, you need more here
        nodes.append(make_gexf_node(str(index), label))
    graph.append(nodes)
    graph.append(edges)
    xml.append(graph)
    
    return str(etree.tostring(xml, xml_declaration=True, pretty_print = True, encoding = "utf-8"), "utf-8")

def gexf_from_GexfGraph(gexf_graph):
    xml = etree.Element("gexf",
                        version="1.3",
                        nsmap=nsmap,
                        schemaLocation_qname = schemaLocation_val)
    graph = etree.Element("graph")
    for k, v in gexf_graph.attributes.items():
        graph.set(k, v)
    nodes = etree.Element("nodes")
    edges = etree.Element("edges")
    vocabulary = {}

    if len(gexf_graph.node_attributes) > 0:
        node_attributes = etree.Element("attributes")
        node_attributes.set("class", "node")
        for name, vals in gexf_graph.node_attributes.items():
            attrib = etree.Element("attribute", id=name)
            for k, v in vals.items():
                attrib.set(k, v)
            # tr_def = etree.SubElement(translation_attrib, "default")
            # tr_def.text = "0"
            node_attributes.append(attrib)
        graph.append(node_attributes)


    for _id, node in gexf_graph.id2node.items():
        thisnode = make_gexf_node(_id, node.label, size = node.size, xpos = node.position[0], ypos = node.position[1], color = node.color)
        if len(node.attvalues) > 0:
            attvalues = etree.SubElement(thisnode, "attvalues")
            for k, v in node.attvalues.items():
                attvalue = etree.SubElement(attvalues, "attvalue")
                attvalue.set("for", k)
                attvalue.set("value", v)
        nodes.append(thisnode)
    for _source, _target, _weight in gexf_graph.edges:
        edges.append(etree.Element("edge", id=str(len(edges)), source=str(_source), target=str(_target), weight=str(_weight)))

    graph.append(nodes)
    graph.append(edges)
    xml.append(graph)
    
    return str(etree.tostring(xml, xml_declaration=True, pretty_print = True, encoding = "utf-8"), "utf-8")

if __name__ == '__main__':
    print("Testing gexf.py:")
    print("make gexf from...")
    my_edges = [(("dog", "cat"), 1.5), (("elephant", "monkey"), 2.1)]
    print(gexf_from_tuples(my_edges))
    print()
    print("Testing from_edgelist:")
    adjacency = np.array([[0, 1, 1, 0], [1, 0, 1, 1], [1, 1, 0, 0], [0, 1, 0, 0]])
    adjacency = sparse.csr_matrix(adjacency)
    labels = ["foo", "bar", "baz", "boz"]
    print(gexf_from_adjacency(adjacency, labels))


