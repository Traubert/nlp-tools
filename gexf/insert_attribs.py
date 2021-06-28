import sys
import argparse
import urllib.parse
from lxml import etree
import csv

parser = argparse.ArgumentParser(description = "Insert and modify attributes in gexf graphs")
parser.add_argument('--input', '-i', action='store')
parser.add_argument('--output', '-o', action='store')
parser.add_argument("--swap-translation", help="swap labels and translations",
                    action="store_true")
parser.add_argument("--write-ego", help="write egograph links",
                    action="store_true")
parser.add_argument("--write-korp", help="write links to Korp",
                    action="store_true")
parser.add_argument("--write-translations-from",
                    help="write translation fields from tsv or gexf file", action="store")
parser.add_argument("--site", help="url prefix",
                    action="store", default = 'https://kielipankki.fi/tools/demo/')
parser.add_argument("--name", help="name for graph", action="store", default = None)


#site = 'http://kielipankki.fi/tools/demo/'

args = parser.parse_args()
if args.write_translations_from:
    if args.write_translations_from.endswith(".tsv"):
        with open(args.write_translations_from) as tsvfile:
            translations = dict(csv.reader(tsvfile, delimiter="\t"))
    elif args.write_translations_from.endswith(".gexf"):
        translations = {}
        tree = etree.parse(args.write_translations_from)
        root = tree.getroot()
        for node in root.findall(".//node", namespaces=root.nsmap):
            label = node.get('label')
            translation = node.find(".//attvalue[@for='translation']", namespaces=root.nsmap).get("value")
            translations[label] = translation

def url_normalize(word):
    return urllib.parse.quote(word.replace('/', '|').replace("'","").replace('"','').replace(' ', '_'))

def make_url_ego(word):
    encoded_word = url_normalize(word)
    return '{}#egographs/egograph_{}.json'.format(args.site, encoded_word)

def make_url_korp(word):
    if '_' in word:
        word = word[:word.rindex('_')]
    encoded_word = urllib.parse.quote(word)
    return 'https://korp.csc.fi/?mode=other_languages#?lang=en&cqp=%5Blemma%20%3D%20%22{word}%22%5D&corpus=oracc_adsd,oracc_ario,oracc_blms,oracc_cams,oracc_caspo,oracc_ctij,oracc_dcclt,oracc_dccmt,oracc_ecut,oracc_etcsri,oracc_hbtin,oracc_obmc,oracc_riao,oracc_ribo,oracc_rimanum,oracc_rinap,oracc_saao,oracc_others&stats_reduce=word&search_tab=1&search=cqp'.format(word=encoded_word)

this_ego = ""
if "egograph_" in args.input:
    start_idx = args.input.find("egograph_")
    stop_idx = args.input.find(".gexf")
    this_ego = args.input[start_idx+9:stop_idx]
    
tree = etree.parse(args.input)
base_nsmap = tree.getroot().nsmap
nsmap = {
    'g': base_nsmap[None],
    'viz': base_nsmap['viz'],
}

if args.name is not None:
    tree.xpath('g:graph', namespaces=nsmap)[0].set("name", args.name)
attributes = tree.xpath('//g:attributes', namespaces=nsmap)[0]
children = set(map(lambda x: x.get('id'), attributes.getchildren()))
if 'korp_url' not in children and args.write_korp:
    attributes.append(etree.Element("attribute", id="korp_url", title="Search in Korp", type="string"))
if 'egourl' not in children and args.write_ego:
    attributes.append(etree.Element("attribute", id="egourl", title="Go to this ego graph", type="string"))


for node in tree.xpath('//g:node', namespaces=nsmap):
    write_ego = args.write_ego
    write_korp = args.write_korp
    write_translation = (args.write_translations_from != None)
    attributes = node.xpath('g:attvalues', namespaces=nsmap)[0]
    attpairs = list(map(lambda x: x.values(), attributes.iterchildren()))
    # for pair in attpairs:
    #     if 'korp_url' == pair[0]:
    #         write_korp = False
    label = node.get('label')
    if not label:
        continue
    if write_korp:
        korp_url = make_url_korp(label)
        korp_url_element = node.find(".//attvalue[@for='korp_url']", namespaces=base_nsmap)
        if korp_url_element is None:
            korp_url_element = node.find(".//attvalue[@id='korp_url']", namespaces=base_nsmap)
        if korp_url_element is None:
            korp_url_element = etree.Element("attvalue", nsmap=nsmap)
            attributes.append(korp_url_element)
        korp_url_element.set("for", "korp_url")
        korp_url_element.set("value", korp_url)
        korp_url_element.set("title", "See in Korp")
        korp_url_element.set("type", "string")
    if args.swap_translation or write_translation:
        translation_attvalue = node.find(".//attvalue[@for='translation']", namespaces=base_nsmap)
        if write_translation and label in translations:
            translation_attvalue.set("value", translations[label])
        if args.swap_translation:
            translation = translation_attvalue.get("value").strip(';')
            node.set("label", translation)
            translation_attvalue.set("value", label)
            label = translation
    if write_ego:
        if url_normalize(this_ego) == url_normalize(label):
            ego_url = ''
        else:
            ego_url = make_url_ego(label)
        ego_url_element = node.find(".//attvalue[@for='egourl']", namespaces=base_nsmap)
        if ego_url_element is None:
            ego_url_element = node.find(".//attvalue[@id='egourl']", namespaces=base_nsmap)
        if ego_url_element is None:
            ego_url_element = etree.Element("attvalue", nsmap=nsmap)
            attributes.append(ego_url_element)
        ego_url_element.set("for", "egourl")
        ego_url_element.set("value", ego_url)
        ego_url_element.set("title", "Go to this ego graph")
        ego_url_element.set("type", "string")

#    node.set('attvalues', attributes)

tree.write(args.output, xml_declaration=True, pretty_print = True, encoding = "utf-8")
# xml_string = str(etree.tostring(tree, xml_declaration=True, pretty_print = True, encoding = "utf-8"), "utf-8")
# writeobj = open(args.output, 'w')
# writeobj.write(xml_string)

