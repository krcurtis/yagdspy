# Copyright 2016 Fred Hutchinson Cancer Research Center

import os

import pydot



class Digraph:
    def __init__(self):
        self.node_outs = { }
        self.node_ins = { }
    def has_node(self, node):
        return node in self.node_outs;
    def has_edge(self, edge):
        n1, n2 = edge
        return n1 in self.node_outs and n2 in self.node_outs[n1]
    def add_node(self, node):
        if (node not in self.node_outs):
              self.node_outs[node] = set();
              self.node_ins[node] = set();
    def add_nodes(self, nodes):
        for n in nodes:
              self.add_node(n);
    def add_edge(self, edge):
        n1,n2 = edge;
        self.node_outs[n1].add(n2);
        self.node_ins[n2].add(n1);
    def neighbors(self, node):
        # return list( self.nodes[node] );
        return self.node_outs[node];
    def __contains__(self, t):
        if (not self.has_node(t[0]) or not self.has_node(t[1])):
            return False;
        return t[1] in self.node_outs[t[0]];

    def nodes(self):
        return self.node_outs.keys();

    def find_sources(self):
        """return list of nodes that are source nodes, nothing points to them
        in the digraph, and they have nodes they point to"""
        nodes = [ n for n in self.nodes() if 0 == len(self.node_ins[n]) and 0 != len(self.node_outs[n]) ]
        return nodes;

    def find_sinks(self):
        """return list of nodes that are sink nodes, they don't point to any other node in the diagraph, and something points to them"""
        nodes = [ n for n in self.nodes() if 0 != len(self.node_ins[n]) and 0 == len(self.node_outs[n]) ]
        return nodes;






class TopologicalSort:
    def __init__(self, D):
        self.unmarked = set(D.nodes())
        self.D = D;
        self.temporary = set()
        self.marked = set();
        self.L = []

    def topological_sort(self):
        while len(self.unmarked) > 0:
            n = self.unmarked.pop();
            self.visit(n);

        self.L.reverse()
        return self.L

    def visit(self, node):
        if node in self.temporary:
            raise Exception("ERROR graph is not acyclic");
        if node in self.marked:
            return;
        self.temporary.add(node)
        for m in self.D.neighbors(node):
            self.visit(m)
        self.marked.add(node)
        self.temporary.remove(node);
        self.L.append(node);





def generate_processing_graph(processing_modules):
    D = Digraph()
    for m in processing_modules:
        D.add_node(m);
        for r in m.requires:
            D.add_node(r);
            D.add_edge( (r,m) );
        for p in m.provides:
            D.add_node(p);
            D.add_edge( (m,p) );
    return D;


def minimally_distinguishable_form(pathnames):
    def fullsplit(pathname):
        """Split path directories, and keep non-empty components"""
        if '' == pathname or '/' == pathname:
            return []
        head, tail = os.path.split(pathname)
        if '' == head:
            return [tail]
        elif '' != tail:
            return fullsplit(head) + [ tail]
        else:
            return fullsplit(head)

    def path_forms(path_list):
        """possible minimal forms of the path name using the list of components"""
        return [ os.path.join(*path_list[i:]) for i in range(len(path_list))]

    graph1 = {} # re-forumalating the full-path to path candidates as a dictionary
    for p in pathnames:
        for f in path_forms(fullsplit(p)):
            if f in graph1:
                graph1[f].append(p)
            else:
                graph1[f] = [p]
    groups = {}
    for candidate, names in graph1.items():
        if 1 != len(names):
            continue
        for name in names:
            if name in groups:
                groups[name].append(candidate)
            else:
                groups[name] = [candidate]
    mapping_table = {}
    for name, candidates in groups.items():
        mapping_table[name] = sorted(candidates, key=lambda x: len(x))[0]
    return mapping_table
            



def plot_graph(output_file, D):
    # graph = pydot.Dot(graph_type='digraph', nodesep=".75");
    graph = pydot.Dot(graph_type='digraph', ratio="compress");
    # graph.set_node_defaults(style="filled", fillcolor="grey")
    graph.set_edge_defaults(color="blue", arrowhead="vee", weight="1")

    # isinstance(x, str) ...

    path_names = [ n for n in D.nodes() if isinstance(n, str) ]
    minimal_table = minimally_distinguishable_form(path_names)


    node_to_pydot = {}
    for n in D.nodes():
        if isinstance(n, str):
            node_to_pydot[n] = pydot.Node( minimal_table[n], style='filled', fillcolor='lightblue', shape='box')
        else:
            # print n
            node_to_pydot[n] = pydot.Node( str(n), style='filled', fillcolor='grey')
        graph.add_node(node_to_pydot[n])


    for a in D.nodes():
        for b in D.neighbors(a):
            edge = pydot.Edge(node_to_pydot[a], node_to_pydot[b]);
            graph.add_edge(edge);
    graph.write_png(output_file);


