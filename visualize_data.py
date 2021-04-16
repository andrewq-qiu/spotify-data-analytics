"""Module for visualizing the data in the Spotify dataset.

MIT License

Copyright (c) 2021 Andrew Qiu

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import networkx as nx
from plotly.graph_objs import Scatter, Figure, Bar, Layout, Pie
from song_graph import SongGraph, CONTINUOUS_HEADERS, Song


ATTRIBUTE_COLOUR = 'rgb(24, 195, 49)'
SONG_COLOUR = 'rgb(246, 123, 58)'
EDGE_COLOR = 'rgb(0, 0, 0)'


def remove_integer_suffix(s: str) -> str:
    """If s has an integer suffix, return s
    without its integer suffix.

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

    return ''


def visualize_graph_with_attributes(graph: SongGraph, graph_nx: nx.Graph,
                                    output_to_html_path: str = None,
                                    layout: dict = None, config: dict = None) -> None:
    """Visualize a song graph given its corresponding clustered graph_nx
    counterpart. The graph_nx graph must be generated according the the
    specifications of analyze_song_graph.create_clustered_nx_song_graph.

    Preconditions:
        - graph.are_attributes_created()
        - graph.parent_graph is not None
        - graph.parent_graph.are_attributes_created()
    """

    pos = getattr(nx, 'spring_layout')(graph_nx)

    song_pos = ([], [])
    attr_pos = ([], [])

    song_labels = []
    attr_labels = []

    songs = []

    for node_label in graph_nx.nodes:
        node = graph_nx.nodes[node_label]

        if node['kind'] == 'attribute':
            attr_pos[0].append(pos[node_label][0])
            attr_pos[1].append(pos[node_label][1])

            attr_labels.append(remove_integer_suffix(node_label))
        elif node['kind'] == 'song':
            song_pos[0].append(pos[node_label][0])
            song_pos[1].append(pos[node_label][1])
            songs.append(node['song'])

            song_labels.append(node_label)

    attr_trace = Scatter(
        x=attr_pos[0],
        y=attr_pos[1],
        mode='markers',
        name='attribute vertices',
        marker=dict(size=9,
                    line=dict(width=0.5),
                    color=ATTRIBUTE_COLOUR),
        text=attr_labels,
        hovertemplate='%{text}',
        showlegend=False
    )

    fig = Figure(data=[_make_edge_trace(graph_nx, pos)] + _make_song_traces(
        graph, songs, song_pos[0], song_pos[1], song_labels) + [attr_trace])

    fig.update_layout(layout)
    fig.update_xaxes(showgrid=False, zeroline=False, visible=False)
    fig.update_yaxes(showgrid=False, zeroline=False, visible=False)

    if output_to_html_path is not None:
        fig.write_html(output_to_html_path, config=config)
    else:
        fig.show(config=config)


def _make_edge_trace(graph_nx: nx.Graph, pos: dict) -> Scatter:
    """(HELPER) This function is a helper function to visualize_graph_with_attributes.

    Return a trace containing lines which represent edges between nodes
    given the position of nodes in pos.
    """

    x_edges = []
    y_edges = []

    for edge in graph_nx.edges:
        x_edges += [pos[edge[0]][0], pos[edge[1]][0], None]
        y_edges += [pos[edge[0]][1], pos[edge[1]][1], None]

    edge_trace = Scatter(
        x=x_edges,
        y=y_edges,
        mode='lines',
        name='edges',
        line=dict(width=1, color=EDGE_COLOR),
        hoverinfo='none',
        showlegend=False
    )

    return edge_trace


def _make_song_traces(graph: SongGraph, songs: list[Song],
                      song_x: list[float], song_y: list[float],
                      song_labels: list[str]) -> list[Scatter]:
    """(HELPER) This function is a helper function to visualize_graph_with_attributes.

    Return a list of traces for each attribute header (with the exception of year)
    containing the color-scaled songs in graph.
    """
    to_return = []
    is_first_header = True

    headers = sorted(CONTINUOUS_HEADERS)

    for header in headers:
        attr_values = [song.attributes[header] for song in songs]
        min_, max_, _, _ = graph.get_attribute_header_stats(header, use_parent=True)

        trace = Scatter(x=song_x,
                        y=song_y,
                        mode='markers',
                        name=header,
                        marker=dict(
                            size=7,
                            line=dict(width=0.5),
                            color=attr_values,
                            colorscale='thermal',
                            cmin=min_,  # Base the color scale off the min and max
                            cmax=max_  # of the parent dataset
                        ),
                        text=song_labels,
                        hovertemplate='%{text}',
                        visible='legendonly'
                        )

        if is_first_header:
            trace.visible = True
            is_first_header = False

        to_return.append(trace)

    return to_return


def visualize_attr_header_distr_bar(graph: SongGraph, attribute_header: str,
                                    output_to_html_path: str = None,
                                    layout: dict = None, config: dict = None,
                                    parent_trace_name: str = 'Songs from the same time period',
                                    child_trace_name: str = 'Playlist') -> None:
    """Visualize the distributions of the quantifiers of an attribute header
    in a bar chart with plotly.

    Preconditions:
        - graph.are_attributes_created()
        - attribute_header in CONTINUOUS_HEADERS
    """

    quantifiers, distr_child, distr_parent = _get_distribution_values(graph, attribute_header)

    fig = Figure(data=[
        Bar(x=quantifiers, y=distr_parent, name=parent_trace_name, opacity=0.5),
        Bar(x=quantifiers, y=distr_child, name=child_trace_name, opacity=0.7)
    ], layout=Layout(barmode='overlay', title=attribute_header))

    fig.update_layout(layout)

    if output_to_html_path is not None:
        fig.write_html(output_to_html_path, config=config, include_plotlyjs='cdn')
    else:
        fig.show(config=config)


def _get_distribution_values(graph: SongGraph, attribute_header: str) -> tuple[list, list, list]:
    """(HELPER FUNCTION) This is a helper function for visualize_attr_header_distr_bar.

    Return the distribution values for both the child and parent graph.
    The return type is a tuple:
        - the first element is list of quantifiers for the attribute header
        - the second element is the distribution values for the child
        - the third element is the distribution values for the parent

    Preconditions:
        - graph.are_attributes_created()
        - attribute_header in CONTINUOUS_HEADERS
    """

    num_neighbours_child = []
    num_neighbours_parent = []

    total_neighbours_child = 0
    total_neighbours_parent = 0

    quantifiers = []

    for attr_v_child in graph.get_attr_vertices_by_header(attribute_header):
        attribute_label = attr_v_child.item

        attr_v_parent = graph.parent_graph.get_vertex_by_item(attribute_label)

        num_neighbours_child.append(len(attr_v_child.neighbours))
        num_neighbours_parent.append(len(attr_v_parent.neighbours))

        total_neighbours_child += len(attr_v_child.neighbours)
        total_neighbours_parent += len(attr_v_parent.neighbours)

        quantifiers.append(attr_v_child.quantifier)

    distr_child = [num / total_neighbours_child
                   for num in num_neighbours_child]

    distr_parent = [num / total_neighbours_parent
                    for num in num_neighbours_parent]

    return quantifiers, distr_child, distr_parent


def visualize_attr_header_distr_pie(graph: SongGraph, attribute_header: str,
                                    output_to_html_path: str = None,
                                    layout: dict = None, config: dict = None) -> None:
    """Visualize the distributions of the quantifiers of an attribute header
    in a pie chart with plotly.

    Preconditions:
        - graph.are_attributes_created()
        - attribute_header in CONTINUOUS_HEADERS
    """

    num_neighbours = []
    quantifiers = []

    for attr_v in graph.get_attr_vertices_by_header(attribute_header):
        num_neighbours.append(len(attr_v.neighbours))
        quantifiers.append(attr_v.quantifier)

    fig = Figure(data=[Pie(labels=quantifiers, values=num_neighbours)])
    fig.update_layout(layout)

    if output_to_html_path is not None:
        fig.write_html(output_to_html_path, config=config, include_plotlyjs='cdn')
    else:
        fig.show(config=config)


if __name__ == '__main__':
    import doctest
    import python_ta
    import python_ta.contracts

    doctest.testmod()

    python_ta.contracts.check_all_contracts()

    python_ta.check_all(config={
        'extra-imports': ['networkx', 'plotly.graph_objs', 'song_graph'],
        'allowed-io': [],
        'max-line-length': 100,
        'disable': ['E1136', 'R0913']
    })
