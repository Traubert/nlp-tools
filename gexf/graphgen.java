import org.gephi.graph.api.*;
import org.gephi.io.importer.api.*;
import org.gephi.io.exporter.api.*;
import org.gephi.layout.plugin.*;

import org.gephi.project.api.Workspace;
import org.gephi.project.api.ProjectController;
import org.gephi.io.processor.plugin.DefaultProcessor;
import org.gephi.layout.plugin.forceAtlas.ForceAtlasLayout;
import org.gephi.layout.plugin.forceAtlas.ForceAtlas;
import org.gephi.layout.plugin.forceAtlas2.ForceAtlas2;
import org.gephi.layout.plugin.forceAtlas2.ForceAtlas2Builder;
import org.gephi.layout.plugin.scale.Expand;
import org.gephi.layout.plugin.scale.ExpandLayout;

import org.gephi.io.exporter.spi.GraphExporter;
import org.gephi.filters.api.Query;
import org.gephi.filters.plugin.graph.EgoBuilder.EgoFilter;
import org.gephi.filters.api.FilterController;

import org.gephi.appearance.api.AppearanceController;
import org.gephi.appearance.api.AppearanceModel;
import org.gephi.appearance.api.Function;
import org.gephi.appearance.plugin.AbstractUniqueColorTransformer;
import org.gephi.appearance.plugin.UniqueElementColorTransformer;

import org.openide.util.Lookup;

import org.apache.commons.cli.*;

import java.awt.Color;
import java.lang.reflect.Field;
import java.io.File;
import java.io.IOException;

class Graphgen {

    public static void main(String[] args) {
        org.apache.commons.cli.Options options = new org.apache.commons.cli.Options();

        Option o = new Option("i", "input", true, "input file path");
        o.setRequired(true); options.addOption(o);

        o = new Option("o", "output", true, "output file/directory path");
        o.setRequired(true); options.addOption(o);
        
        options.addOption(new Option("c", "color", true, "color for nodes"));
        options.addOption(new Option("r", "rounds", true, "number of rounds to run layout algorithm"));
        options.addOption(new Option("e", "ego", false, "generate ego graphs"));
        options.addOption(new Option("l", "layout", false, "recalculate layout"));

        CommandLineParser parser = new DefaultParser();
        HelpFormatter helpformatter = new HelpFormatter();
        CommandLine cmd = null;
        
        try {
            cmd = parser.parse(options, args);
        } catch (ParseException e) {
            System.out.println(e.getMessage());
            helpformatter.printHelp("utility-name", options);
            System.exit(1);
        }

        Options opts = new Options();
        opts.input_file = cmd.getOptionValue("input");
        opts.output_file = cmd.getOptionValue("output");
        if (cmd.hasOption("layout")) { opts.do_layout = true; }

        String optval;
        if ((optval = cmd.getOptionValue("color")) != null) {
            try {
                Field field = Class.forName("java.awt.Color").getField(optval);
                opts.node_color = (Color)field.get(null);
            } catch (Exception e) { /* Leave as default */ }
        }
        if ((optval = cmd.getOptionValue("rounds")) != null) {
            try {
                opts.layout_rounds = Integer.valueOf(optval);
            } catch (Exception e) { /* Leave as default */ }
        }
        if (cmd.hasOption("ego")) {
                Egograph graph = new Egograph(opts);
            } else {
                Semgraph graph = new Semgraph(opts);
            }
        // graph.cluster();
        // graph.write_gexf();
        
    }
}

class Egograph {
    Options options;
    
    public Egograph(Options opts) {
        options = opts;
        ProjectController pc = Lookup.getDefault().lookup(ProjectController.class);
        pc.newProject();
        Workspace workspace = pc.getCurrentWorkspace();
        GraphModel graphModel = Lookup.getDefault().lookup(GraphController.class).getGraphModel();
        ImportController importController = Lookup.getDefault().lookup(ImportController.class);
        FilterController filterController = Lookup.getDefault().lookup(FilterController.class);
        

        // Import file
        Container container;
        try {
            File file = new File(opts.input_file);
            //            File file = new File(getClass().getResource(opts.input_file).toURI());
            container = importController.importFile(file);
        } catch (Exception ex) {
            ex.printStackTrace();
            return;
        }

        // Append imported data to GraphAPI
        importController.process(container, new DefaultProcessor(), workspace);

        //See if graph is well imported
        Graph graph = graphModel.getGraph();
        System.out.println("Nodes: " + graph.getNodeCount());
        System.out.println("Edges: " + graph.getEdgeCount());
        
        Node[] nodes = graph.getNodes().toArray();
        for (Node node : nodes) {
                                 //        .forEach(node -> {
                System.out.println(node.getLabel());
                EgoFilter egoFilter = new EgoFilter();
                egoFilter.setPattern(node.getLabel());
                egoFilter.setDepth(1);
                Query queryEgo = filterController.createQuery(egoFilter);
                GraphView viewEgo = filterController.filter(queryEgo);
                graphModel.setVisibleView(viewEgo);
                //Count nodes and edges on filtered graph
                Graph egograph = graphModel.getGraphVisible();
                System.out.println("Nodes: " + egograph.getNodeCount() + " Edges: " + egograph.getEdgeCount());

                if (opts.do_layout) {
                    ForceAtlas2 layout = new ForceAtlas2(new ForceAtlas2Builder());
                    layout.setGraphModel(graphModel);
                    layout.setAdjustSizes(true);
                    //                layout.setGravity(?);
                    
                    layout.initAlgo();
                    for (int i = 0; i < options.layout_rounds && layout.canAlgo(); i++) {
                        layout.goAlgo();
                    }
                    layout.endAlgo();
                    
                // ForceAtlasLayout layout = new ForceAtlasLayout(new ForceAtlas());
                // layout.setGraphModel(graphModel);
                // layout.resetPropertiesValues();
                // //                layout.setGravity(gravity_value);
                // layout.setAdjustSizes(true);
                
                // layout.initAlgo();
                // for (int i = 0; i < options.layout_rounds && layout.canAlgo(); i++) {
                //     layout.goAlgo();
                // }
                // layout.endAlgo();

                    ExpandLayout expand = new ExpandLayout(new Expand(), 3.0);
                    expand.setGraphModel(graphModel);
                    expand.initAlgo();
                    expand.goAlgo();
                    expand.endAlgo();
                }
                
                
                ExportController ec = Lookup.getDefault().lookup(ExportController.class);
                GraphExporter exporter = (GraphExporter) ec.getExporter("gexf");
                exporter.setExportVisible(true);  //Only exports the visible (filtered) graph
                exporter.setWorkspace(workspace);
                //System.out.println("#" + node.getTextProperties().getText() + "#");
                String name = node.getLabel().replace("/", "|").replace(" ", "_").replace("\"", "").replace("'", "");
                try {
                    ec.exportFile(new File(options.output_file + "egograph_" + name + ".gexf"), exporter);
                } catch (IOException ex) {
                    ex.printStackTrace();
                    return;
                }
                
        }
            
    }
}

    class Semgraph {
    static final double gravity_value = 300.0;
    
    Options options;
    
    public Semgraph(Options opts) {
        options = opts;
        ProjectController pc = Lookup.getDefault().lookup(ProjectController.class);
        pc.newProject();
        Workspace workspace = pc.getCurrentWorkspace();
        // AttributeModel attributeModel = Lookup.getDefault().lookup(AttributeController.class).getModel();
        GraphModel graphModel = Lookup.getDefault().lookup(GraphController.class).getGraphModel();
        // PreviewModel model = Lookup.getDefault().lookup(PreviewController.class).getModel();
        ImportController importController = Lookup.getDefault().lookup(ImportController.class);
        // FilterController filterController = Lookup.getDefault().lookup(FilterController.class);
        // RankingController rankingController = Lookup.getDefault().lookup(RankingController.class);
        AppearanceController appearanceController = Lookup.getDefault().lookup(AppearanceController.class);

        // Import file
        Container container;
        try {
            File file = new File(opts.input_file);
            //            File file = new File(getClass().getResource(opts.input_file).toURI());
            container = importController.importFile(file);
        } catch (Exception ex) {
            ex.printStackTrace();
            return;
        }

        // Append imported data to GraphAPI
        importController.process(container, new DefaultProcessor(), workspace);

        //See if graph is well imported
        Graph graph = graphModel.getGraph();
        System.out.println("Nodes: " + graph.getNodeCount());
        System.out.println("Edges: " + graph.getEdgeCount());

        ForceAtlasLayout layout = new ForceAtlasLayout(new ForceAtlas());
        layout.setGraphModel(graphModel);
        layout.resetPropertiesValues();
        layout.setGravity(gravity_value);
        layout.setAdjustSizes(true);

        layout.initAlgo();
        for (int i = 0; i < options.layout_rounds && layout.canAlgo(); i++) {
            layout.goAlgo();
        }
        layout.endAlgo();

        // Function simpleNodeColor = AppearanceModel.getNodeFunction(graph, AppearanceModel.GraphFunction.NODE_DEGREE, UniqueElementColorTransformer.class);
        // UniqueElementColorTransformer nodeColorTransformer = (UniqueElementColorTransformer) simpleNodeColor.getTransformer();
        // nodeColorTransformer.setColor(Color.GRAY);
        // appearanceController.transform(simpleNodeColor);
        // Function[] all_nodes = AppearanceModel.getNodeFunctions(graph);
        // UniqueElementColorTransformer color_transformer;
        // color_transformer.setColor(options.node_color);
        // for (Function f : all_nodes) {
        //     appearanceController.transform(f);
        // }

        // for (Node n : graph.getNodes()) {
        //     n.setColor(options.node_color);
        // }
        
        
        //Export
        ExportController ec = Lookup.getDefault().lookup(ExportController.class);
        try {
            ec.exportFile(new File(options.output_file));
        } catch (IOException ex) {
            ex.printStackTrace();
            return;
        }

    }

    
}

    
class Options {
    String input_file;
    String output_file;
    Color node_color = Color.orange;
    Integer layout_rounds = 450;
    Boolean do_layout = false;
}

