gitfrom __future__ import annotations
from dataclasses import dataclass
from typing import Union, Any, Iterator, Optional
import math
import networkx as nx


# =============== GLOBAL VARIABLES ===============

# List of expected headers from the song dataset
HEADERS = ['acousticness', 'artists', 'danceability', 'duration_ms',
           'energy', 'explicit', 'id', 'instrumentalness', 'key', 'liveness',
           'loudness', 'mode', 'name', 'popularity', 'release_date',
           'speechiness', 'tempo', 'valence', 'year']

# Headers which need to be converted to different data types
# It is assumed that headers which do not need to converted to either
# a float or int represent data that is not comparable, so are not
# considered as attributes or converted to attribute vertices.
FLOAT_HEADERS = {'acousticness', 'danceability', 'energy', 'instrumentalness',
                 'liveness', 'loudness', 'speechiness', 'tempo', 'valence'}
INT_HEADERS = {'key', 'mode', 'popularity', 'year', 'explicit'}

# Headers that are associated to attributes that represent
# exact rather than continuous values. For example, "mode" is either 1 or 0.
# Map each exact value to a label that describes them.

# It is assumed that all other headers associated to attributes
# that are not in this dict represent continuous values.
EXACT_HEADERS = {'mode': {0: 'minor', 1: 'major'},
                 'explicit': {0: 'not explicit', 1: 'explicit'},
                 'key': {}}

# =============== END ==========================


class Song:
    """A class representing a Spotify Song"""

    name: str
    spotify_id: str
    artists: list[str]
    attributes: dict[str, Union[str, float, int, bool]]

    def __init__(self, name: str, spotify_id: str, artists: list[str],
                 attributes: dict[str, Union[str, float, int, bool]]):
        self.name = name
        self.artists = artists
        self.spotify_id = spotify_id
        self.attributes = attributes


class Vertex:
    """A class representing a vertex in a Graph"""
    neighbours: set[Vertex]
    item: Any

    def __init__(self, item: Any):
        self.item = item
        self.neighbours = set()


class AttributeVertex(Vertex):
    """An abstract class representing an attribute vertex in a SongGraph.

    An attribute vertex contains an attribute name (the thing
    being described) and a quantifier (how much of the thing
    being described).

    For example, an attribute vertex could describe high loudness.
    """
    item: str
    attribute_name: str
    quantifier: str

    def __init__(self, attribute_name: str, quantifier: str):
        self.attribute_name = attribute_name
        self.quantifier = quantifier

        Vertex.__init__(self, quantifier + ' ' + attribute_name)

    def matches_with(self, song: Song):
        """Return whether or the song matches with the attribute vertex.

        (I.e. whether or not the song has the attribute).
        """
        raise NotImplementedError


@dataclass
class Interval:
    """A class representing an interval that is closed/open/both.

    Representation Invariants:
        - left_bound_type in {'open', 'closed'}
        - right_bound_type in {'open', 'closed'}
    """
    left_bound_type: str
    left_bound: float
    right_bound: float
    right_bound_type: str

    def is_inside(self, value: Union[int, float]) -> bool:
        """Return whether or not a value is inside the interval."""
        if self.left_bound_type == 'open':
            left_true = self.left_bound < value
        else:
            left_true = self.left_bound < value or \
                        math.isclose(self.left_bound, value)
        if self.right_bound_type == 'open':
            right_true = value < self.right_bound
        else:
            right_true = value < self.right_bound or \
                         math.isclose(self.right_bound, value)

        return left_true and right_true


class AttributeVertexContinuous(AttributeVertex):
    """A class representing an attribute vertex in a Graph.

    This class differs from AttributeVertexExact in that it
    represents a range of values of an attribute.

    For example, an instance of AttributeVertexContinuous
    could represent 0.8 <= danceability <= 1.0

    Instance Attributes:
        - attribute_name: the name of the attribute (ex. danceability)
        - quantifier: a string quantifying the attribute. Ex: high, low, average
        - value_range: a tuple representing the inclusive range of values represented
    """
    item: str
    attribute_name: str
    quantifier: str
    value_interval: Interval

    def __init__(self, attribute_name: str, quantifier: str,
                 value_interval: Interval):

        AttributeVertex.__init__(self, attribute_name, quantifier)
        self.value_interval = value_interval

    def matches_with(self, song: Song) -> bool:
        """Return whether or not song has the attribute
        inside the range of self.value_range.

        (i.e. whether or not the attribute in the song
        and its value matches with this attribute vertex).
        """
        return self.value_interval.is_inside(song.attributes[self.attribute_name])
        

class AttributeVertexExact(AttributeVertex):
    """A class representing an attribute in a Graph.

    This class differs from AttributeVertexContinuous in that
    it represents a single value of an attribute.

    For example, an instance of AttributeVertexExact
    could represent the "mode" attribute being exactly 1.

    Instance Attributes:
        - attribute_name: the name of the attribute (ex. danceability)
        - quantifier: a string describing the attribute.
            Ex. For an instance representing mode=1 quantifies "major"
        - value: the exact value represented by the attribute
    """

    def __init__(self, attribute_name: str, quantifier: str,
                 value: Any):
        AttributeVertex.__init__(self, attribute_name, quantifier)
        self.value = value

    def matches_with(self, song: Song) -> bool:
        """Return whether or not the attribute and self.value
        matches exactly with the corresponding attribute
        in the song.
        """
        return song.attributes[self.attribute_name] == self.value


class SongVertex(Vertex):
    """A class representing a single song as a
    vertex in a graph.
    """
    item: Song

    def __init__(self, song: Song):
        Vertex.__init__(self, song)


class Graph:
    """A class representing a graph"""
    _vertices: dict[Any, Vertex]

    def __init__(self):
        """Initialize an empty graph"""
        self._vertices = {}

    def add_vertex_by_item(self, item: Any):
        """Create a new vertex in the graph given an item"""
        if item not in self._vertices:
            self._vertices[item] = Vertex(item)

    def add_vertex(self, vertex: Vertex):
        """Add a vertex in the graph with an existing
        Vertex object"""
        if vertex.item not in self._vertices:
            self._vertices[vertex.item] = vertex

    def add_edge(self, item1: Any, item2: Any):
        """Add an edge between two vertices given
        their items
        """
        v1 = self._vertices[item1]
        v2 = self._vertices[item2]

        v1.neighbours.add(v2)
        v2.neighbours.add(v1)

    def get_vertex_by_item(self, item: Any):
        """Return a vertex given an item.

        Raise a ValueError if no such vertex exists.
        """
        if item in self._vertices:
            return self._vertices[item]
        else:
            raise ValueError


class SongGraph(Graph):
    """A class representing a graph
    of song and attribute vertices based
    on the Spotify dataset
    """

    parent_graph: SongGraph
    num_songs: int
    _attributes_created: bool
    _saved_attribute_stats: dict[str, tuple[float, float, float, float]]
    _attributes: dict[str, dict[str, Union[AttributeVertexContinuous, AttributeVertexExact]]]

    def __init__(self, parent_graph: SongGraph = None):
        """Initialize an empty song graph.

        The optional parent_graph parameter allows this
        new graph to inherit the statistics on attributes
        (ex. the average valence) from the parent graph.
        """
        Graph.__init__(self)
        self.parent_graph = parent_graph
        self.num_songs = 0
        self._attributes_created = False
        self._saved_attribute_stats = {}
        self._attributes = {attribute: {}
                            for attribute in INT_HEADERS.union(FLOAT_HEADERS)}

    def update_parent_graph(self, parent_graph: SongGraph):
        """Change the graph's parent graph."""
        self.parent_graph = parent_graph

    def are_attributes_created(self) -> bool:
        """Return whether or not the attribute vertices of the
        song graph have been created yet."""
        return self._attributes_created

    def add_song(self, song: Song):
        """Add a song to the Graph.
        Do not create or update any edges.
        Do not change the attributes vertices.
        """
        Graph.add_vertex(self, SongVertex(song))
        self.num_songs += 1

    def _add_attribute_vertex(self, vertex: Union[AttributeVertexContinuous, AttributeVertexExact]):
        """(PRIVATE) Add an attribute vertex to the graph.

        Raise a ValueError if the attribute vertex was added already.
        """
        if vertex.item in self._vertices:
            raise ValueError
        else:
            self._vertices[vertex.item] = vertex
            self._attributes[vertex.attribute_name][vertex.quantifier] = vertex

    def get_attribute_header_stats(self, attribute_header: str, use_parent: bool = False)\
            -> tuple[float, float, float, float]:
        """Return the min, max, average, and standard deviation
        of attribute values of songs in the graph given an attribute_header.

        use_parent can be used to get the attribute header stats
        of this graph's parent graph, if applicable.

        If use_parent=True but the graph has no parent graph,
        calculate the stats directly from this graph instead.

        Preconditions:
            - attribute_header in INT_HEADERS or attribute in FLOAT_HEADERS
            - attribute_header not in EXACT_HEADERS
        """
        if use_parent and self.parent_graph is not None:
            return self.parent_graph.get_attribute_header_stats(attribute_header)
        elif attribute_header in self._saved_attribute_stats:
            return self._saved_attribute_stats[attribute_header]
        else:
            sum_so_far = 0
            sum_mean_deviation = 0
            min_so_far = math.inf
            max_so_far = -math.inf

            for song in self.get_songs():
                attribute_value = song.attributes[attribute_header]
                sum_so_far += attribute_value

                if attribute_value < min_so_far:
                    min_so_far = attribute_value
                if attribute_value > max_so_far:
                    max_so_far = attribute_value

            average = sum_so_far / self.num_songs

            for song in self.get_songs():
                attribute_value = song.attributes[attribute_header]
                sum_mean_deviation += (average - attribute_value) ** 2

            st_dev = (sum_mean_deviation / self.num_songs) ** 0.5

            # Save the calculations
            self._saved_attribute_stats[attribute_header] = \
                min_so_far, max_so_far, average, st_dev

            return min_so_far, max_so_far, average, st_dev

    def get_attribute_vertices(self) -> \
            Iterator[Union[AttributeVertexContinuous, AttributeVertexExact]]:
        """(Iterator) Return all the attribute vertices in the graph."""
        for attribute in self._attributes:
            for quantifier in self._attributes[attribute]:
                yield self._attributes[attribute][quantifier]

    def get_songs(self) -> Iterator[Song]:
        """(Iterator) Return all the songs in the graph."""
        for item in self._vertices:
            if isinstance(item, Song):
                yield item

    def _generate_edges(self):
        """Generate edges between the attribute and song vertices.

        Raise a ValueError if the attribute vertices have not
        been generated yet.
        """
        if not self.are_attributes_created():
            raise ValueError

        for song in self.get_songs():
            for attr_v in self.get_attribute_vertices():
                if attr_v.matches_with(song):
                    self.add_edge(song, attr_v.item)

    def generate_attribute_vertices(self, use_parent: bool = False):
        """Call this function only once most -> all of the
        data wanted is loaded into the graph.

        Create the attribute vertices and create edges
        between the attribute vertices and existing song vertices.

        Exact Attributes are split according to the EXACT_HEADERS global
        variable for each value that an attribute can take on.

        use_parent determines whether or not to use the stats from
        a parent graph and affects the behaviour of continuous attributes.
            If use_parent is False,
            Continuous Attributes are split into six attribute vertices based on distribution
            of attribute values:
                very low, low, medium low, medium high, high, very high
                such that ~1/6 of songs fall into each attribute vertex

            If use_parent is True,
            Use the continuous attribute ranges of the parent.

        Make an edge between songs and the attribute vertices
        which match with them.

        Preconditions:
            - self.num_songs >= 6
            - not use_parent or self.parent_graph is not None
                # use_parent implies self.parent_graph is not None
            - not use_parent or self.parent_graph.are_attributes_created()
                # use_parent implies the attributes of the parent have been created
        """

        attributes_headers = FLOAT_HEADERS.union(INT_HEADERS)

        for attribute_header in attributes_headers:
            if attribute_header in EXACT_HEADERS:
                # Create an exact attribute vertex for each "state" of the attribute
                states = EXACT_HEADERS[attribute_header]

                for state in states:
                    vertex = AttributeVertexExact(attribute_header, states[state], state)
                    self._add_attribute_vertex(vertex)
            # Implied that the attribute header is for a continuous
            # attribute for the next two cases
            elif use_parent:
                attribute_quantifiers = ['very low', 'low', 'medium low', 'medium high', 'high', 'very high']

                for quantifier in attribute_quantifiers:
                    attribute_label = quantifier + ' ' + attribute_header
                    parent_attr_v = self.parent_graph.get_vertex_by_item(attribute_label)
                    assert isinstance(parent_attr_v, AttributeVertexContinuous)

                    new_v = AttributeVertexContinuous(attribute_header,
                                                      quantifier,
                                                      parent_attr_v.value_interval)

                    self._add_attribute_vertex(new_v)

            else:
                attribute_quantifiers = ['very low', 'low', 'medium low', 'medium high', 'high', 'very high']

                sorted_songs = sorted(self.get_songs(), key=lambda x: x.attributes[attribute_header])

                song_num = 0
                quantifier_num = 0
                next_target = self.num_songs / 6
                last_upper_bound = sorted_songs[0].attributes[attribute_header]

                last_song = None

                for song in sorted_songs:
                    # The percentage of songs iterated through
                    attr_value = song.attributes[attribute_header]

                    if song_num >= next_target:
                        # Move onto the next target
                        interval = Interval('closed', last_upper_bound, attr_value, 'open')

                        new_v = AttributeVertexContinuous(attribute_header,
                                                          attribute_quantifiers[quantifier_num],
                                                          interval)

                        self._add_attribute_vertex(new_v)

                        quantifier_num += 1
                        next_target += self.num_songs / 6
                        last_upper_bound = attr_value

                    song_num += 1
                    last_song = song

                # Complete the last attribute quantifier
                interval = Interval('closed', last_upper_bound,
                                    last_song.attributes[attribute_header], 'closed')

                new_v = AttributeVertexContinuous(attribute_header,
                                                  attribute_quantifiers[quantifier_num],
                                                  interval)

                self._add_attribute_vertex(new_v)

        self._attributes_created = True
        self._generate_edges()

    def to_networkx(self, max_vertices: int = 5000) -> nx.Graph:
        """Convert this graph into a networkx Graph.

        max_vertices specifies the maximum number of vertices that can appear in the graph.
        (This is necessary to limit the visualization output for large graphs.)

        Note that this method is provided for you, and you shouldn't change it.
        """
        graph_nx = nx.Graph()
        for song in self.get_songs():
            graph_nx.add_node(song.name, kind='song')
            v = self._vertices[song]

            for u in v.neighbours:
                graph_nx.add_node(u.item, kind='attribute')

                graph_nx.add_edge(song.name, u.item)

            if graph_nx.number_of_nodes() >= max_vertices:
                break

        return graph_nx


if __name__ == '__main__':
    # import timeit
    # print(timeit.timeit("load_graph_data('data/song_data_2020.csv')", globals=globals(), number=1))
    #
    # graph = load_graph_data('data/song_data_2020.csv')
    #
    # print(timeit.timeit("graph.to_networkx()", globals=locals(), number=1))
    #
    # # import a3_visualization
    # #
    # # a3_visualization.visualize_graph(graph)
    ...
