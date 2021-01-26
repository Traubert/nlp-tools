from lxml import etree

def from_tuples(pairs):
    xml = etree.Element("gexf",
                        xmlns = "http://www.gexf.net/1.3",
                        version="1.3")
    #xml.set("xmlns:viz", "http://www.gexf.net/1.3/viz")
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
        nodes.append(etree.Element("node", id=str(index), label=label))
        
    graph.append(nodes)
    graph.append(edges)
    xml.append(graph)
    
    return str(etree.tostring(xml, xml_declaration=True, pretty_print = True, encoding = "utf-8"), "utf-8")
