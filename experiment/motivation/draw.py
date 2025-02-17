import networkx as nx
import matplotlib.pyplot as plt

# Create directed graph
G = nx.DiGraph()

# Add nodes
nodes = ['alloca.c', 'imalloc.c', 'mstats.h', 'malloc.c', 'stats.c', 'table.c', 'table.h', 'trace.c', 'watch.c', 'watch.h', 'xmalloc.c']
G.add_nodes_from(nodes)

# Add solid edges
solid_edges = [
    ('alloca.c', 'imalloc.c'), ('imalloc.c', 'malloc.c'), ('malloc.c', 'stats.c'), ('stats.c', 'trace.c'),
    ('trace.c', 'stats.c'), ('trace.c', 'malloc.c'), ('malloc.c', 'mstats.h'), ('mstats.h', 'stats.c'),
    ('malloc.c', 'table.c'), ('table.c', 'table.h'), ('table.h', 'malloc.c'), ('watch.c', 'malloc.c'),
    ('malloc.c', 'watch.h'), ('watch.h', 'watch.c')
]
G.add_edges_from(solid_edges)

# Add dashed edges
dashed_edges = [
    ('xmalloc.c', 'watch.c'), ('xmalloc.c', 'alloca.c'), ('xmalloc.c', 'imalloc.c'), ('xmalloc.c', 'mstats.h'), 
    ('xmalloc.c', 'malloc.c'), ('xmalloc.c', 'stats.c'), ('xmalloc.c', 'table.c'), ('xmalloc.c', 'table.h'), 
    ('xmalloc.c', 'trace.c'), ('xmalloc.c', 'watch.h'), 
    ('alloca.c', 'imalloc.c'), ('alloca.c', 'mstats.h'), ('alloca.c', 'malloc.c'), ('alloca.c', 'stats.c'),
    ('alloca.c', 'table.c'), ('alloca.c', 'table.h'), ('alloca.c', 'trace.c'), ('alloca.c', 'watch.c'),
    ('alloca.c', 'watch.h'), ('alloca.c', 'xmalloc.c')
]

# Draw graph with circular layout
pos = nx.circular_layout(G)

plt.figure(figsize=(12, 8))
nx.draw(G, pos, with_labels=True, node_color='skyblue', node_size=3000, font_size=10, font_weight='bold', arrowsize=20)

# Draw solid edges
nx.draw_networkx_edges(G, pos, edgelist=solid_edges, edge_color='blue', arrows=True)

# Draw dashed edges
nx.draw_networkx_edges(G, pos, edgelist=dashed_edges, edge_color='grey', style='dashed', arrows=True)

plt.title("Dependency Graph with Circular Layout")

# Save the plot to a file
plt.savefig("./dependency_graph_circular_with_dashed_edges.png")
plt.show()
