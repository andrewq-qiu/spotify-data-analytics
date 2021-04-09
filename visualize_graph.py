import networkx as nx
from plotly.graph_objs import Scatter, Figure, Bar, Layout, Pie
from song_graph import SongGraph, QUANTIFIERS


def remove_integer_suffix(s: str) -> str:
    """Return s without its integer suffix.

    Preconditions:
        - s has an integer suffix

    >>> remove_integer_suffix('high danceability5')
    'high danceability'
    >>> remove_integer_suffix('low valence12')
    'low valence'
    """

    lst = list(s)
    digits = '0123456789'

    # Iterate backwards
    for i in range(len(lst) - 1, -1, -1):
        if lst[i] in digits:
            lst.pop()
        else:
            return ''.join(lst)


def visualize_graph(graph_nx: nx.Graph):
    pos = getattr(nx, 'spring_layout')(graph_nx)

    x_values = [pos[k][0] for k in graph_nx.nodes]
    y_values = [pos[k][1] for k in graph_nx.nodes]
    labels = []

    for node_label in graph_nx.nodes:
        node = graph_nx.nodes[node_label]
        if node['kind'] == 'attribute' and node['ends_with_int']:
            labels.append(remove_integer_suffix(node_label))
        else:
            labels.append(node_label)

    x_edges = []
    y_edges = []
    for edge in graph_nx.edges:
        x_edges += [pos[edge[0]][0], pos[edge[1]][0], None]
        y_edges += [pos[edge[0]][1], pos[edge[1]][1], None]

    trace3 = Scatter(x=x_edges,
                     y=y_edges,
                     mode='lines',
                     name='edges',
                     line=dict(width=1),
                     hoverinfo='none',
                     )
    trace4 = Scatter(x=x_values,
                     y=y_values,
                     mode='markers',
                     name='nodes',
                     marker=dict(symbol='circle-dot',
                                 size=5,
                                 line=dict(width=0.5)
                                 ),
                     text=labels,
                     hovertemplate='%{text}',
                     hoverlabel={'namelength': 0}
                     )

    data1 = [trace3, trace4]
    fig = Figure(data=data1)
    fig.update_layout({'showlegend': False})
    fig.update_xaxes(showgrid=False, zeroline=False, visible=False)
    fig.update_yaxes(showgrid=False, zeroline=False, visible=False)

    fig.show()


def visualize_attribute_header_distribution_bar(graph: SongGraph, attribute_header: str):
    """"""

    num_neighbours_child = []
    num_neighbours_parent = []

    total_neighbours_child = 0
    total_neighbours_parent = 0

    quantifiers = []

    for attr_v_child in graph.get_attribute_vertices_by_header(attribute_header):
        attribute_label = attr_v_child.item

        attr_v_parent = graph.parent_graph.get_vertex_by_item(attribute_label)

        num_neighbours_child.append(len(attr_v_child.neighbours))
        num_neighbours_parent.append(len(attr_v_parent.neighbours))

        total_neighbours_child += len(attr_v_child.neighbours)
        total_neighbours_parent += len(attr_v_parent.neighbours)

        quantifiers.append(attr_v_child.quantifier)

    relative_neighbours_child = [num / total_neighbours_child
                                 for num in num_neighbours_child]

    relative_neighbours_parent = [num / total_neighbours_parent
                                  for num in num_neighbours_parent]

    fig = Figure(data=[
        Bar(x=quantifiers, y=relative_neighbours_parent, name='Songs from the same time period', opacity=0.5),
        Bar(x=quantifiers, y=relative_neighbours_child, name='Playlist', opacity=0.7)
    ], layout=Layout(barmode='overlay', title=attribute_header))

    fig.show()


def visualize_attribute_header_distribution_pie(graph: SongGraph, attribute_header: str):
    """"""

    num_neighbours = []
    quantifiers = []

    for attr_v in graph.get_attribute_vertices_by_header(attribute_header):
        num_neighbours.append(len(attr_v.neighbours))
        quantifiers.append(attr_v.quantifier)

    fig = Figure(data=[Pie(labels=quantifiers, values=num_neighbours)])
    fig.show()

