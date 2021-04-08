import networkx as nx
from plotly.graph_objs import Scatter, Figure


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
