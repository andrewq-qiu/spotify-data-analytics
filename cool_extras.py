"""A module that includes functions for generating the data used
in the cool extras section of the program. This file is not imported by the program,
but has been used beforehand to write the cool extras document.

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

import analyze_song_graph
from song_graph import SongGraph, SongVertex, AttributeVertex,\
    CONTINUOUS_HEADERS, AttributeVertexContinuous, Song
import visualize_data
import get_dataset_data


DECADES = {1970, 1980, 1990, 2000, 2010, 2020}


def get_continuous_attr_v_pairs(graph: SongGraph, ignore: set = None,
                                keep: set = None,
                                ignore_same_headers: bool = True) ->\
        list[tuple[AttributeVertexContinuous, AttributeVertexContinuous]]:
    """Return a list of tuples containing all pairs of CONTINUOUS attribute
    vertices in graph. Do not return any pairs which contain attribute
    vertices with attribute headers in ignore.

    If keep is not None, then only return pairs of tuples of attribute vertices
    whose attribute headers are in keep.

    If ignore_same_headers is True, then return only pairs of attribute vertices with
    distinct attribute headers.

    Preconditions:
        - graph.are_attributes_created()
        - ignore is not None or ignore.issubset()
    """

    vertices = [v for v in graph.get_attribute_vertices()
                if v.attribute_header in CONTINUOUS_HEADERS]
    pairs = []

    for i in range(len(vertices)):
        for j in range(i + 1, len(vertices)):
            v1 = vertices[i]
            v2 = vertices[j]

            h1 = v1.attribute_header
            h2 = v2.attribute_header

            pass_ignore = ignore is None or (h1 not in ignore and h2 not in ignore)
            pass_keep = keep is None or (h1 in keep and h2 in keep)
            pass_same_header = not ignore_same_headers or h1 != h2

            if pass_ignore and pass_keep and pass_same_header:
                pairs.append((v1, v2))

    return pairs


def most_similar_continuous_attr(graph: SongGraph, n: int = 3, ignore: set = None,
                                 keep: set = None, ignore_same_headers: bool = True) \
        -> list[tuple[str, str]]:
    """Return the n most similar continuous attributes in graph.
    Do not return any pairs which contain attribute
    vertices with attribute headers in ignore.

    If keep is not None, then only return pairs of tuples of attribute vertices
    whose attribute headers are in keep.

    Preconditions:
        - n > 0
        - ignore is None or ignore.issubset(CONTINUOUS_HEADERS)
        - keep is None or keep.issubset(CONTINUOUS_HEADERS)
        - graph.are_attributes_created()
    """

    pairs = get_continuous_attr_v_pairs(
        graph, ignore, keep, ignore_same_headers)

    pairs.sort(
        key=lambda x: analyze_song_graph.vertex_sim_by_neighbours(x[0], x[1]),
        reverse=True)

    return [(v1.item, v2.item) for v1, v2 in pairs[:n]]


def rep_song_of_cluster(graph: SongGraph, cluster: set[SongVertex]) -> Song:
    """Return the most representative song in the cluster.

    The representativity score is the product of the popularity of
    a song (in a scale from 0-1) and the similarity of a song to
    the average song in the cluster (see analyze_song_graph.get_cluster_average_song).

    So, a representative song in the cluster has both high popularity
    and traits that are similar to the cluster.

    Preconditions:
        - graph.are_attributes_created()
        - len(cluster) > 0
    """

    avg_song = analyze_song_graph.get_cluster_average_song(cluster)

    best_song_so_far = None
    best_score_so_far = 0

    for song_v in cluster:
        song = song_v.item

        similarity = analyze_song_graph.song_similarity_continuous(
            graph, song, avg_song, use_exact_headers=False)
        popularity = song.attributes['popularity'] / 100

        score = similarity * popularity

        if best_score_so_far < score:
            best_score_so_far = score
            best_song_so_far = song

    return best_song_so_far


def popular_song_cluster_by_decade(
        graph: SongGraph, decade: int, min_popularity: float = 50.0) -> set[SongVertex]:
    """Return a song cluster of songs from a decade with a popularity
    greater than or equal to min_popularity.

    Preconditions
        - 0 <= min_popularity <= 100
        - graph.are_attributes_created()
    """

    to_return = set()
    target_label = f'({decade}-{decade + 10}) year'

    for song_v in graph.get_vertex_by_item(target_label).neighbours:
        song = song_v.item
        assert isinstance(song_v, SongVertex)

        if song.attributes['popularity'] >= min_popularity:
            to_return.add(song_v)

    return to_return


def _generate_acousticness_energy_chart(graph: SongGraph) -> None:
    """Generate the chart for acousticness and energy used
    in the cool extras section of the program. Save the relevant
    chart in the cool extras folder.

    Preconditions:
        - graph.are_attributes_created()
    """

    very_low_energy_graph = SongGraph(parent_graph=graph)
    very_low_energy = graph.get_vertex_by_item('very low energy')

    assert isinstance(very_low_energy, AttributeVertex)

    for song_v in very_low_energy.neighbours:
        very_low_energy_graph.add_song(song_v.item)

    very_low_energy_graph.generate_attribute_vertices(use_parent=True)

    visualize_data.visualize_attr_header_distr_bar(
        very_low_energy_graph,
        'acousticness',
        output_to_html_path='cool extras/acousticness_energy.html',
        layout={'title': 'Acousticness under very low energy songs'},
        parent_trace_name=f'Songs from {min(DECADES)}-{max(DECADES) + 10}',
        child_trace_name='Songs with very low energy'
    )


def _generate_data_and_charts_by_decade(graph: SongGraph, decade: int) -> None:
    """Generate and print the data used in the cool extras given a decade. Save the relevant
    charts in the cool extras folder.

    Preconditions:
        - graph.are_attributes_created()
    """

    cluster = popular_song_cluster_by_decade(graph, decade)

    top_attr = analyze_song_graph.top_attr_from_song_cluster(
        graph, cluster, ignore={'year', 'explicit', 'popularity'})

    attr_labels = [attr_.item for attr_ in top_attr]

    print(f'Most significant attributes of {decade}-{decade + 10}: {", ".join(attr_labels)}')

    new_graph = SongGraph(parent_graph=graph)
    for song_v in cluster:
        new_graph.add_song(song_v.item)

    new_graph.generate_attribute_vertices(use_parent=True)

    for attr in top_attr:
        header = attr.attribute_header
        visualize_data.visualize_attr_header_distr_bar(
            new_graph, header, f'cool extras/{decade}_{header}.html',
            layout={'title': f'{header} from {decade}-{decade + 10}'.capitalize(),
                    'showlegend': False, 'margin': {'l': 0, 'r': 0}},
            parent_trace_name=f'Songs from {min(DECADES)}-{max(DECADES) + 10}',
            child_trace_name=f'Songs from {decade}-{decade + 10}'
        )

    print(f'The representative song of {decade}-{decade + 10}: ',
          rep_song_of_cluster(graph, cluster))


def generate_charts_and_data() -> None:
    """Generate and print the data used in the cool extras section.
    Save the relevant charts in the cool extras folder.
    """

    graph = get_dataset_data.get_song_graph_from_decades(DECADES)

    print('Most similar attributes:',
          most_similar_continuous_attr(graph, ignore={'year', 'explicit'}))

    _generate_acousticness_energy_chart(graph)

    for decade in DECADES:
        _generate_data_and_charts_by_decade(graph, decade)


if __name__ == '__main__':
    import doctest
    import python_ta
    import python_ta.contracts

    doctest.testmod()

    python_ta.contracts.check_all_contracts()

    python_ta.check_all(config={
        'extra-imports': ['analyze_song_graph', 'song_graph',
                          'visualize_data', 'get_dataset_data'],
        'allowed-io': ['generate_charts_and_data', '_generate_data_and_charts_by_decade'],
        'max-line-length': 100,
        'disable': ['E1136']
    })

    # generate_charts_and_data()
