# Gexf tools

These are currently just internal to some projects, used for generating and manipulating `.gexf` files (a graph serialization format).

Compiling and running semgraph.java:

* You need to get the Gephi toolkit, available [here](https://github.com/gephi/gephi-toolkit/releases/download/v0.9.2/gephi-toolkit-0.9.2-all.jar), put it in this directory
* You'll need the Apache commons cli library, eg. `apt install libcommons-cli-java`
* If your system is configured nicely, you don't need to worry about $CLASSPATH, but if compiling doesn't work, figure out where your Java libraries are and explicitly tell javac, as in:

```bash
javac -cp "/usr/share/java/*:./gephi-toolkit-0.9.2-all.jar" semgraph.java
```

Then you can run it like:

```bash
java -cp "/usr/share/java/*:./gephi-toolkit-0.9.2-all.jar:." Main -e -l -i /path/to/input/gexf -o /output/directory/
```

to generate ego graphs (`-e`) with recalculated layouts (`-l`) in a given output directory, or

```bash
java -cp "/usr/share/java/*:./gephi-toolkit-0.9.2-all.jar:." Main -i /path/to/input/gexf -o /output/file --rounds 100
```

to not generate ego graphs, but just run 100 rounds of ForceAtlas2 on a graph. To tweak beyond that, you currently have to edit the code.

Good luck!

