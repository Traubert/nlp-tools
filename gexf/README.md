# Gexf tools

These are currently just internal to some projects, used for generating and manipulating `.gexf` files (a graph serialization format).

## Barebones `.gexf` generation

If you have just sources, destinations and edge weights, you can use `make_gexf.py` to write a simple `.gexf` file, into which you can add other attributes later.

The function `from_tuples(pairs)` takes an iterable of tuples (or lists) with two members: the first one is a (source, destination) pair, the second is a weight. It returns a pretty-printed utf-8 string representing the XML. Eg.

```python
>>> import make_gexf

>>> my_edges = [(("dog", "cat"), 1.5), (("elephant", "monkey"), 2.1)]

>>> print(make_gexf.from_tuples(my_edges))

<?xml version='1.0' encoding='utf-8'?>
<gexf xmlns="http://www.gexf.net/1.3" version="1.3">
  <graph mode="static" defaultedgetype="undirected">
    <nodes>
      <node id="1" label="dog"/>
      <node id="2" label="cat"/>
      <node id="3" label="elephant"/>
      <node id="4" label="monkey"/>
    </nodes>
    <edges>
      <edge id="0" source="1" target="2" weight="1.5"/>
      <edge id="1" source="3" target="4" weight="2.1"/>
    </edges>
  </graph>
</gexf>
```

## Compiling and running semgraph.java:

* You need to get the Gephi toolkit, available [here](https://github.com/gephi/gephi-toolkit/releases/download/v0.9.2/gephi-toolkit-0.9.2-all.jar), put it in this directory
* You'll need the Apache commons cli library, eg. `apt install libcommons-cli-java`
* If your system is configured nicely, you don't need to worry about $CLASSPATH, but if compiling doesn't work, figure out where your Java libraries are and explicitly tell javac, as in:

```bash
javac -cp "/usr/share/java/*:./gephi-toolkit-0.9.2-all.jar" graphgen.java
```

Then you can run it like:

```bash
java -cp "/usr/share/java/*:./gephi-toolkit-0.9.2-all.jar:." Graphgen -e -l -i /path/to/input/gexf -o /output/directory/
```

to generate ego graphs (`-e`) with recalculated layouts (`-l`) in a given output directory, or

```bash
java -cp "/usr/share/java/*:./gephi-toolkit-0.9.2-all.jar:." Graphgen -i /path/to/input/gexf -o /output/file --rounds 100
```

to not generate ego graphs, but just run 100 rounds of ForceAtlas2 on a graph. To tweak beyond that, you currently have to edit the code.

The Gephi toolkit apidocs are [here](https://gephi.org/gephi-toolkit/0.9.2/apidocs/). Good luck!

