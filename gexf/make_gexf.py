from lxml import etree

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

def make_node(index, label, size = 1.0, xpos = 0.0, ypos = 0.0, color = (255, 255, 255)):
    element = etree.Element("node", id=str(index), label=label)
    element.append(etree.Element(viz_sizetag, value = str(size)))
    element.append(etree.Element(viz_positiontag, x = str(xpos), y = str(ypos)))
    element.append(etree.Element(viz_colortag, r = str(color[0]), g = str(color[1]), b = str(color[2])))
    return element

def from_tuples(pairs):
    xml = etree.Element("gexf",
                        version="1.3",
                        nsmap=nsmap,
                        schemaLocation_qname = schemaLocation_val)
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
        nodes.append(make_node(str(index), label))
        
    graph.append(nodes)
    graph.append(edges)
    xml.append(graph)
    
    return str(etree.tostring(xml, xml_declaration=True, pretty_print = True, encoding = "utf-8"), "utf-8")

if __name__ == '__main__':
    print("Testing make_gexf.py:")
    my_edges = [(("dog", "cat"), 1.5), (("elephant", "monkey"), 2.1)]
    print(from_tuples(my_edges))

