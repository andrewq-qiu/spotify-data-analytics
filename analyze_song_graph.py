"""A module containing functions for analyzing a
song graph and for retrieving interesting information
about them.

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

from typing import Union, Any, Optional
import random
import networkx as nx
import song_graph
from song_graph import SongGraph, AttributeVertex,\
    SongVertex, Vertex, Song, AttributeVertexContinuous


def song_similarity_continuous(graph: SongGraph, s1: Song, s2: Song,
                               use_exact_headers: bool = True) -> float:
    """Return a similarity score between two songs s1 and s2.

    This similarity score follows a continuous algorithm, which
    means that two songs will have a higher similarity score if
    their attributes are close together, rather them being exactly
    in the same range (which is what is used in get_vertex_similarity).

    Preconditions:
        - graph.num_songs >= 1
    """

    net_similarity = 0
    num_attributes = 0

    for attr_header in s1.attributes:
        if use_exact_headers and attr_header in song_graph.EXACT_HEADERS:
            # Then the similarity is:
            # 1 - If the attribute matches
            # 0 - If the attribute does not match
            net_similarity += int(s1.attributes[attr_header] == s2.attributes[attr_header])

            num_attributes += 1
        elif attr_header not in song_graph.EXACT_HEADERS:
            # Then the similarity is based
            # on the relative distance between the
            # attribute values
            min_, max_, _, _ = graph.get_attribute_header_stats(attr_header, use_parent=True)

            # The closer they are, the more similar they should be
            closeness = abs(s1.attributes[attr_header] - s2.attributes[attr_header]) / (max_ - min_)

            net_similarity += 1 - closeness

            num_attributes += 1

    return net_similarity / num_attributes


def vertex_sim_by_neighbours(v1: Vertex, v2: Vertex) -> float:
    """Return a similarity score between v1 and v2.

    The similarity score is calculated with the following formula:
        0.0 - if the number of distinct neighbours between v1 and v2 is 0

        Otherwise, it is equal to the number of length two paths
        between v1 and v2 (number of shared neighbours) divided
        by the number of distinct neighbours of v1 and v2.

    This metric essentially measures how many neighbours
    these two vertices share.
    """

    shared = len(v1.neighbours.intersection(v2.neighbours))
    distinct = len(v1.neighbours.union(v2.neighbours))

    if distinct == 0:
        return 0.0
    else:
        return shared / distinct


def cluster_similarity(graph: SongGraph, cluster1: set[Vertex], cluster2: set[Vertex],
                       similarity_algorithm: str = 'continuous') -> float:
    """Find the similarity between two clusters.
    The similarity of the two clusters is the average similarity
    between any two pairs of vertices in the two clusters.

    similarity_algorithm identifies which similarity algorithm is to be used.
    Note that this only applies to a vertex of type 'song' as the continuous
    similarity algorithm requires attributes that only song vertices have.

    Preconditions:
        - len(cluster1) > 0 and len(cluster2) > 0
        - graph.are_attributes_created()
        - cluster1.isdisjoint(cluster2)
        - similarity_algorithm in {'continuous', 'neighbours'}
        - similarity_algorithm == 'neighbours' or \
            all(isinstance(v, SongVertex) for v in cluster1.union(cluster2))
    """

    total_similarity = 0

    for v in cluster1:
        for u in cluster2:
            if similarity_algorithm == 'continuous':
                total_similarity += song_similarity_continuous(graph, v.item, u.item)
            else:
                total_similarity += vertex_sim_by_neighbours(v, u)

    return total_similarity / (len(cluster1) * len(cluster2))


def get_pairs(lst: list) -> tuple[Any, Any]:
    """(Iterator) Return all the pairs of items in lst.

    Preconditions:
        - len(lst) >= 2
    """

    for i in range(len(lst)):
        for j in range(i + 1, len(lst)):
            yield lst[i], lst[j]


def find_clusters(graph: SongGraph, vertex_type: str = 'song',
                  similarity_algorithm: str = 'continuous',
                  similarity_threshold: float = 0.9) ->\
        list[set[Union[AttributeVertex, SongVertex]]]:
    """Find clusters in a song graph. This function uses an altered
    greedy clustering algorithm and instead maintains that the only clusters
    that should be merged together are those which are "similar enough".

    Rather than stopping when enough clusters are reached, the algorithm
    halts when there is either one cluster, or when any merging would
    merge two clusters which are too dissimilar to be merged.

    similarity_threshold identifies the minimum similarity that is
    needed for two clusters to be merged.

    similarity_algorithm identifies which similarity algorithm is to be used.
    Note that this only applies to vertex_type 'song' as the continuous
    similarity algorithm requires attributes that only song vertices have.

    Preconditions:
        - vertex_type in {'song', 'attribute'}
        - similarity_algorithm in {'continuous', 'neighbours'}
        - 0 <= similarity_threshold <= 1
        - graph.are_attributes_created()
        - similarity_algorithm != 'continuous' or vertex_type == 'song'
    """
    if vertex_type == 'song':
        clusters = [{graph.get_vertex_by_item(song)} for song in graph.get_songs()]
    else:
        clusters = [{attr_v} for attr_v in graph.get_attribute_vertices()]

    max_similarity = 1

    while max_similarity >= similarity_threshold and len(clusters) >= 2:
        max_similarity_pair = None
        max_similarity = 0

        for c1, c2 in get_pairs(clusters):
            similarity = cluster_similarity(graph, c1, c2, similarity_algorithm)

            if similarity > max_similarity:
                max_similarity_pair = c1, c2
                max_similarity = similarity

        if max_similarity >= similarity_threshold:
            # Then merge the two most similar clusters
            max_similarity_pair[0].update(max_similarity_pair[1])
            clusters.remove(max_similarity_pair[1])

    return clusters


def attr_significance_of_cluster(
        graph: SongGraph, cluster: set[SongVertex], attr_v: AttributeVertex) -> float:
    """Return a significance score of an attribute vertex in a song cluster.

    The significance score is a measure of the changes in the
    relative weight of an attribute (the amount of neighbours it has
    compared to other attributes of the same header) between
    that of the graph and that of the cluster.

    I.e. the significance score will be higher if a higher proportion
    of songs in the cluster match with attr_v than the proportion of
    songs in graph which match with attr_v.

    Preconditions:
        - graph.are_attributes_created()
    """

    graph_weight = len(attr_v.neighbours) / graph.num_songs

    num_songs_with_attribute = 0

    for song_v in cluster:
        if attr_v in song_v.neighbours:
            num_songs_with_attribute += 1

    cluster_weight = num_songs_with_attribute / len(cluster)

    if graph_weight == 0:
        return 0
    else:
        return cluster_weight / graph_weight


def top_attr_from_song_cluster(graph: SongGraph,
                               cluster: set[SongVertex],
                               n: int = 3,
                               ignore: set[str] = None) -> list[AttributeVertex]:
    """Return the top n attributes of the song cluster ignoring
    all attribute headers contained in ignore. The top n attributes
    are determined by their significance score defined in
    get_attribute_significance_score_of_cluster.

    Preconditions:
        - ignore is None or ignore.issubset(song_graph.INT_HEADERS.union(song_graph.FLOAT_HEADERS))
        - graph.are_attributes_created()
        - n > 0
    """

    if ignore is None:
        attribute_vertices = list(graph.get_attribute_vertices())
    else:
        attribute_vertices = [attr_v for attr_v in graph.get_attribute_vertices()
                              if attr_v.attribute_header not in ignore]

    attribute_vertices.sort(
        key=lambda x: attr_significance_of_cluster(graph, cluster, x),
        reverse=True)

    return attribute_vertices[:n]


def add_top_attr_v_to_cluster(graph: SongGraph, graph_nx: nx.Graph,
                              cluster: set[SongVertex], added_count: dict[str, int],
                              ignore: set[str] = None) -> None:
    """Add the top three attribute vertices of the song cluster to a
    graph_nx graph such that the attribute headers of the vertices
    are not in ignore. Retrieve these attribute vertices
    from graph.

    Create an edge between each of the new attribute vertices to
    each of the song between the song clusters.

    added_count is a dictionary mapping an attribute label to
    the number of times it has already been added to the graph
    (from other clusters).

    Update added_count with any attribute vertices which have
    been added to graph_nx.

    Preconditions:
        - all(song_v in graph_nx.nodes for song_v in cluster)
        - graph.are_attributes_created()
        - ignore is None or ignore.issubset(song_graph.INT_HEADERS.union(song_graph.FLOAT_HEADERS))
    """

    top_attributes = top_attr_from_song_cluster(graph, cluster, 3, ignore)
    for attr in top_attributes:
        # Add a number to the end of the attributes to differentiate
        # the top attributes of one cluster to another if they are
        # the same. (I.e. prevent edges between clusters which
        # share the same top attribute).

        attr_label = attr.item

        if attr_label in added_count:
            added_vertex_label = attr_label + str(added_count[attr_label])
            graph_nx.add_node(added_vertex_label, kind='attribute', ends_with_int=True)

            added_count[attr_label] += 1

        else:
            added_vertex_label = attr_label + ' 0'
            graph_nx.add_node(added_vertex_label, kind='attribute', ends_with_int=True)

            added_count[attr_label] = 1

        for song_v in cluster:
            song_name = song_v.item.name

            graph_nx.add_edge(song_name, added_vertex_label)


def create_clustered_nx_song_graph(graph: SongGraph, similarity_threshold: float = 0.9,
                                   ignore: set[str] = None) -> nx.Graph:
    """Return a focused networkx song graph based on the
    songs in the song graph.

    Create clusters and join song vertices in the same cluster
    with an edge given the similarity between songs.
    (see find_clusters)

    For each song cluster with 5 or more songs, create 3
    attribute vertices for the top 3 attributes of the song cluster
    (whose attribute headers are not in ignore) and create an edge
    between each of the attribute vertices and each of the song vertices.

    Preconditions:
        - 0 <= similarity_threshold <= 1
        - graph.are_attributes_created()
        - ignore is None or ignore.issubset(song_graph.INT_HEADERS.union(song_graph.FLOAT_HEADERS))
    """

    clusters = find_clusters(graph, vertex_type='song',
                             similarity_threshold=similarity_threshold)
    graph_nx = nx.Graph()

    for song in graph.get_songs():
        graph_nx.add_node(song.name, kind='song', song=song)

    # The number of times an attribute has been added to graph_nx
    added_count = {}

    for cluster in clusters:
        cluster_lst = list(cluster)

        for i in range(1, len(cluster_lst)):
            graph_nx.add_edge(cluster_lst[0].item.name, cluster_lst[i].item.name)

        # Get top three attributes for large enough clusters
        if len(cluster) >= 5:
            add_top_attr_v_to_cluster(graph, graph_nx, cluster, added_count, ignore)

    return graph_nx


def attribute_header_deviation(graph: SongGraph, attribute_header: str) -> float:
    """Return the deviation score with an attribute header between
    a child graph and its parent graph.

    The deviation score is equal to the absolute value difference
    between the averages of the child and parent graph, divided
    by the standard deviation of the parent graph. (Comparable to the
    z-score or standard score).

    Preconditions:
        - attribute_header in song_graph.INT_HEADERS.union(song_graph.FLOAT_HEADERS))
        - graph.are_attributes_created()
        - graph.parent_graph is not None
        - graph.parent_graph.are_attributes_created()
    """
    _, _, p_average, st_dev = graph.get_attribute_header_stats(attribute_header, use_parent=True)
    _, _, c_average, _ = graph.get_attribute_header_stats(attribute_header)

    return abs(c_average - p_average) / st_dev


def most_deviated_attr_headers(graph: SongGraph, n: int, ignore: set[str] = None) -> list[str]:
    """Return the top n attribute headers of a child SongGraph
    which deviate the most from the average of the parent SongGraph.
    Ignore all attribute headers in ignore and do not return them.

    Preconditions:
        - graph.are_attributes_created()
        - graph.parent_graph is not None
        - graph.parent_graph.are_attributes_created()
        - ignore is None or ignore.issubset(song_graph.INT_HEADERS.union(song_graph.FLOAT_HEADERS))
    """

    if ignore is None:
        attr_headers = list(song_graph.INT_HEADERS.union(song_graph.FLOAT_HEADERS))
    else:
        attr_headers = [header for header in song_graph.INT_HEADERS.union(song_graph.FLOAT_HEADERS)
                        if header not in ignore]

    attr_headers.sort(key=lambda x: attribute_header_deviation(graph, x), reverse=True)

    return attr_headers[:n]


def least_deviated_attr_headers(graph: SongGraph, n: int, ignore: set[str] = None) -> list[str]:
    """Return the top n attribute headers of a child SongGraph
    which deviate the least from the average of the parent SongGraph.
    Ignore all attribute headers in ignore and do not return them.

    Preconditions:
        - graph.are_attributes_created()
        - graph.parent_graph is not None
        - graph.parent_graph.are_attributes_created()
        - ignore is None or ignore.issubset(song_graph.INT_HEADERS.union(song_graph.FLOAT_HEADERS))
    """

    if ignore is None:
        attr_headers = list(song_graph.INT_HEADERS.union(song_graph.FLOAT_HEADERS))
    else:
        attr_headers = [header for header in song_graph.INT_HEADERS.union(song_graph.FLOAT_HEADERS)
                        if header not in ignore]

    attr_headers.sort(key=lambda x: attribute_header_deviation(graph, x))

    return attr_headers[:n]


def get_cluster_average_song(cluster: set[SongVertex]) -> Song:
    """Return a dummy song, which contains attributes containing the
    average attribute values over all the songs in cluster.

    The attributes in the returned song contain only continuous
    attributes and no exact attributes.

    Preconditions:
        - len(cluster) > 0
    """

    new_attributes = {}

    for header in song_graph.CONTINUOUS_HEADERS:
        total_value = 0

        for song_v in cluster:
            song = song_v.item
            total_value += song.attributes[header]

        new_attributes[header] = total_value / len(cluster)

    new_song = Song(name='dummy', spotify_id='dummy',
                    artists=[], attributes=new_attributes)

    return new_song


def cluster_attr_distr_by_header(graph: SongGraph, cluster: set[SongVertex],
                                 attribute_header: str) -> dict[str, float]:
    """Return a dictionary mapping quantifiers of the attribute
    header to a float between 0 and 1 representing the percentage
    of songs in cluster which have the attribute vertex associated
    to the quantifier and header.

    The returned dictionary is essentially a distribution of songs
    across the different quantifiers of an attribute header.

    Preconditions:
        - graph.are_attributes_created()
        - len(cluster) > 0
        - attribute_header in song_graph.INT_HEADERS.union(song_graph.FLOAT_HEADERS))
    """

    distr = {}

    for attr_v in graph.get_attr_vertices_by_header(attribute_header):
        quantifier = attr_v.quantifier
        distr[quantifier] = 0

    for song_v in cluster:
        for v in song_v.neighbours:
            h_match = v.attribute_header == attribute_header
            if isinstance(v, AttributeVertexContinuous) and h_match and v.matches_with(song_v.item):
                quantifier = v.quantifier
                distr[quantifier] += 1

    return {quantifier_: distr[quantifier_] / len(cluster)
            for quantifier_ in distr}


def cluster_attribute_distribution(graph: SongGraph, cluster: set[SongVertex]) \
        -> dict[str, dict[str, float]]:
    """Return a dictionary mapping CONTINUOUS attribute headers to a
    distribution of songs across the different quantifiers
    of that attribute header.

    (see cluster_attr_distr_by_header)

    Preconditions:
        - graph.are_attributes_created()
        - len(cluster) > 0
    """

    to_return = {}

    for attr_h in song_graph.CONTINUOUS_HEADERS:
        to_return[attr_h] = cluster_attr_distr_by_header(
            graph, cluster, attr_h)

    return to_return


def focused_song_to_cluster_sim(graph: SongGraph, song: Song,
                                attribute_distribution: dict, ignore: set[str] = None) -> float:
    """Return a similarity score between a song and song cluster.

    This similarity score is based on the idea that song clusters
    have a distinct few attributes and a measure of whether or not
    a song belongs in a cluster should be by these key attributes.

    This similarity score focuses only on the extremes in attribute
    distribution (so only counts attributes which few songs in the cluster
    have, or a large proportion of the songs in the cluster have).

    Preconditions:
        - graph.are_attributes_created()
        - attribute_distribution is generated by the function
          get_cluster_attribute_distribution
        - ignore is None or ignore.issubset(song_graph.INT_HEADERS.union(song_graph.FLOAT_HEADERS))
    """

    # Based on the idea that clusters have a few "defining attributes"
    # And that song similarity should be evaluated on those defining attributes

    n = 0
    net_similarity = 0

    significant_cutoff = 0.25
    too_low_cutoff = 0.1

    for attr_h in song_graph.CONTINUOUS_HEADERS:
        if ignore is None or attr_h not in ignore:
            belongs_to = graph.song_belongs_to(song, attr_h)
            significance = attribute_distribution[attr_h][belongs_to.quantifier]

            if significance >= significant_cutoff:
                # Essentially count this as a similarity of 1
                # I.e. the song has an attribute that lots
                # of songs in the cluster has.

                net_similarity += 1
                n += 1
            elif significance <= too_low_cutoff:
                # Essentially count this as a similarity of 0
                # I.e. the song has an attribute that
                # few songs in the cluster have.
                n += 1

    if n == 0:
        return 0
    else:
        return net_similarity / n


def get_similar_song_to_cluster(graph: SongGraph, cluster: set[SongVertex],
                                similarity_threshold: float = 0.9, ignore: set[Song] = None,
                                algorithm: str = 'focused') -> \
        Optional[Song]:
    """Return a song in graph.parent_graph whose similarity
    score is above the similarity_threshold. The similarity score
    algorithm is defined by the algorithm parameter.

    The focused algorithm can be found in focused_song_to_cluster_sim.

    The continuous algorithm is based on finding an average song, which
    is more or less representative of the cluster. (see get_cluster_average_song).
    The average song is then compared to a song in graph, with the similarity
    score being the continuous similarity between the two songs.
    (see get_song_similarity_continuous).

    If no such song exists, return None

    Preconditions:
        - graph.are_attributes_created()
        - len(cluster) > 0
        - 0 <= similarity_threshold <= 1
        - algorithm in {'focused', 'continuous'}
    """

    avg_song = get_cluster_average_song(cluster)
    songs = list(graph.get_songs())
    # Scramble songs to get unique recommended songs
    random.shuffle(songs)

    if algorithm == 'focused':
        attribute_distribution = cluster_attribute_distribution(graph, cluster)
    else:
        attribute_distribution = None

    for s1 in songs:
        if algorithm == 'focused':
            similarity = focused_song_to_cluster_sim(graph, s1, attribute_distribution)
        else:
            similarity = song_similarity_continuous(graph, avg_song, s1, use_exact_headers=False)

        # Logically Equivalent to: ignore is not None IMPLIES that s1 not in ignore
        passes_ignore = ignore is None or s1 not in ignore

        if similarity > similarity_threshold and passes_ignore:
            return s1

    return None


def recommended_song_for_cluster(graph: SongGraph, cluster: set[SongVertex],
                                 ignore: set[Song] = None) -> Song:
    """Return a recommended song for a song cluster in graph.
    The recommended song must not include any song in graph.
    The recommended song comes from the graph's parent_graph.

    If no recommended song exists, raise a ValueError.

    Preconditions:
        - graph.are_attributes_created()
        - len(cluster) > 0
        - graph.parent_graph is not None
        - graph.parent_graph.are_attributes_created()
    """

    similarity_threshold = 0.95
    song = None

    while (song is None and similarity_threshold >= 0) or graph.is_song_in_graph(song):
        song = get_similar_song_to_cluster(
            graph.parent_graph, cluster, similarity_threshold, ignore)
        similarity_threshold -= 0.05

    if song is not None:
        return song
    else:
        raise ValueError


def recommended_song_for_playlist(pl_graph: SongGraph,
                                  clusters: list[set[SongVertex]],
                                  ignore: set[Song] = None) -> tuple[Song, set[SongVertex]]:
    """Return a recommended song for a playlist graph.
    Do not return any songs in ignore.

    If no recommended song exists, raise a ValueError.

    Preconditions:
        - pl_graph.are_attributes_created()
        - pl_graph.parent_graph is not None
        - pl_graph.parent_graph.are_attributes_created()
    """
    num_songs = len([pl_graph.get_songs()])

    cluster_weights = [((len(cluster) / num_songs) + 1) ** 2 for cluster in clusters]

    chosen_cluster = random.choices(
        population=clusters,
        weights=cluster_weights,
        k=1
    )[0]

    recommended_song = recommended_song_for_cluster(
        pl_graph, chosen_cluster, ignore)

    return recommended_song, chosen_cluster


if __name__ == '__main__':
    import doctest
    import python_ta
    import python_ta.contracts

    doctest.testmod()

    python_ta.contracts.check_all_contracts()

    python_ta.check_all(config={
        'extra-imports': ['typing', 'random', 'song_graph', 'networkx'],
        'allowed-io': [],
        'max-line-length': 100,
        'disable': ['E1136']
    })
