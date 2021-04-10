from __future__ import annotations
from dataclasses import dataclass
from typing import Union, Any, Iterator, Optional
import math

# =============== GLOBAL VARIABLES ===============

# List of expected headers from the song dataset
DATASET_HEADERS = ['acousticness', 'artists', 'danceability', 'duration_ms',
           'energy', 'explicit', 'id', 'instrumentalness', 'key', 'liveness',
           'loudness', 'mode', 'name', 'popularity', 'release_date',
           'speechiness', 'tempo', 'valence', 'year']

# Headers which need to be converted to different data types
# It is assumed that headers which do not need to converted to either
# a float or int represent data that is not comparable, so are not
# considered as attributes or converted to attribute vertices.
FLOAT_HEADERS = {'acousticness', 'danceability', 'energy', 'instrumentalness',
                 'liveness', 'loudness', 'speechiness', 'tempo', 'valence'}
INT_HEADERS = {'popularity', 'year', 'explicit'}

# Headers that are associated to attributes that represent
# exact values. For example, "mode" is either 1 or 0.
# Map each exact value to a quantifier that describes them.
EXACT_HEADERS = {'explicit': {0: 'not', 1: ''}}

# Headers that are associated to attributes that can span
# a range of values.
CONTINUOUS_HEADERS = {'acousticness', 'danceability', 'energy',
                      'instrumentalness', 'liveness', 'loudness',
                      'popularity', 'speechiness', 'tempo',
                      'valence', 'year'}

# The list of quantifiers which describe the different attributes
# associate with a continuous attribute header.
QUANTIFIERS = ['very low', 'low', 'medium low', 'medium high', 'high', 'very high']


# =============== GLOBAL VARIABLES END ===============


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

    def is_same_song_as(self, other: Song):
        """Return whether or self and other represent the same song."""
        return self.spotify_id == other.spotify_id

    def __str__(self):
        return f'{self.name} by {", ".join(self.artists)}'


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
    attribute_header: str
    quantifier: str

    def __init__(self, attribute_header: str, quantifier: str):
        self.attribute_header = attribute_header
        self.quantifier = quantifier

        Vertex.__init__(self, quantifier + ' ' + attribute_header)

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
        - attribute_header: the header of the attribute (ex. danceability)
        - quantifier: a string quantifying the attribute. Ex: high, low, average
        - value_range: a tuple representing the inclusive range of values represented
    """
    item: str
    attribute_header: str
    quantifier: str
    value_interval: Interval

    def __init__(self, attribute_header: str, quantifier: str,
                 value_interval: Interval):

        AttributeVertex.__init__(self, attribute_header, quantifier)
        self.value_interval = value_interval

    def matches_with(self, song: Song) -> bool:
        """Return whether or not song has the attribute
        inside the range of self.value_range.

        (i.e. whether or not the attribute in the song
        and its value matches with this attribute vertex).
        """
        return self.value_interval.is_inside(song.attributes[self.attribute_header])
        

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

    def __init__(self, attribute_header: str, quantifier: str,
                 value: Any):
        AttributeVertex.__init__(self, attribute_header, quantifier)
        self.value = value

    def matches_with(self, song: Song) -> bool:
        """Return whether or not the attribute and self.value
        matches exactly with the corresponding attribute
        in the song.
        """
        return song.attributes[self.attribute_header] == self.value


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

    def is_song_in_graph(self, song: Song) -> bool:
        # return song.spotify_id in self._songs_by_id
        return any(s1.is_same_song_as(song) for s1 in self.get_songs())

    def _add_attribute_vertex(self, vertex: Union[AttributeVertexContinuous, AttributeVertexExact]):
        """(PRIVATE) Add an attribute vertex to the graph.

        Raise a ValueError if the attribute vertex was added already.
        """
        if vertex.item in self._vertices:
            raise ValueError
        else:
            self._vertices[vertex.item] = vertex
            self._attributes[vertex.attribute_header][vertex.quantifier] = vertex

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

    def get_attribute_vertices_by_header(self, attribute_header: str) -> Iterator[AttributeVertex]:
        """(Iterator) Return the associated attribute vertices to an attribute header.
        Raise a ValueError if the attribute header does not exist in the graph.
        """
        if attribute_header in self._attributes:
            for quantifier in self._attributes[attribute_header]:
                yield self._attributes[attribute_header][quantifier]
        else:
            raise ValueError

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

    def generate_attr_vertices_from_header_flat(self, attribute_header: str):
        """Generate attribute vertices in the song graph
        given a specific CONTINUOUS attribute header.

        The flat algorithm follows the following separation:
             Split the attribute values into six intervals, which will
             each be represented by an attribute vertex. Ensure that roughly
             ~1/6 songs fall into each interval.

             So plotting a distribution curve will result in a flat line.

                    Do not use the parent graph to generate the attribute vertices.

        Preconditions:
            - attribute_header in self.continuous_headers
        """

        sorted_songs = sorted(self.get_songs(), key=lambda x: x.attributes[attribute_header])

        song_num = 0
        quantifier_num = 0
        next_target = self.num_songs / 6
        last_upper_bound = 0

        for song in sorted_songs:
            # The percentage of songs iterated through
            attr_value = song.attributes[attribute_header]

            if song_num >= next_target:
                # Move onto the next target
                if quantifier_num == 0:
                    # If it's the first interval
                    interval = Interval('open', -math.inf, attr_value, 'open')
                else:
                    interval = Interval('closed', last_upper_bound, attr_value, 'open')

                new_v = AttributeVertexContinuous(attribute_header,
                                                  QUANTIFIERS[quantifier_num],
                                                  interval)

                self._add_attribute_vertex(new_v)

                quantifier_num += 1
                next_target += self.num_songs / 6
                last_upper_bound = attr_value

            song_num += 1
            last_song = song

        # Complete the last attribute quantifier
        interval = Interval('closed', last_upper_bound, math.inf, 'open')

        new_v = AttributeVertexContinuous(attribute_header,
                                          QUANTIFIERS[quantifier_num],
                                          interval)

        self._add_attribute_vertex(new_v)

    def generate_attr_vertices_from_header_even(self, attribute_header: str):
        """Generate attribute vertices in the song graph
        given a specific CONTINUOUS attribute header.

        The 'even' algorithm follows the following separation:
            Split the attribute values into six intervals, which will
            each be represented by an attribute vertex. The interior
            four intervals will each have the same length, which is
            calculated by the minimum and maximum of attribute values
            for the songs in self.

            The two exterior intervals have the same effective length,
            except the left interval extends to -infinity and the
            right interval extends to +infinity.

        Do not use the parent graph to generate the attribute vertices.

        Preconditions:
            - attribute_header in self.continuous_headers
        """

        min_, max_, _, _ = self.get_attribute_header_stats(attribute_header)
        length = (max_ - min_) / 6

        # Left exterior interval
        left_interval = Interval('open', -math.inf, length, 'open')
        left_v = AttributeVertexContinuous(attribute_header, QUANTIFIERS[0], left_interval)
        self._add_attribute_vertex(left_v)

        for i in range(1, 5):
            start = length * i
            end = length * (i + 1)

            interval = Interval('closed', start, end, 'open')
            v = AttributeVertexContinuous(attribute_header, QUANTIFIERS[i], interval)

            self._add_attribute_vertex(v)

        # Right exterior interval
        right_interval = Interval('closed', length * 5, math.inf, 'open')
        right_v = AttributeVertexContinuous(attribute_header, QUANTIFIERS[-1], right_interval)
        self._add_attribute_vertex(right_v)

    def generate_attribute_vertices(self, year_separation: int = 10, use_parent: bool = False):
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
                    - 'instrumentalness' is split via the even algorithm
                        (see SongGraph.generate_attr_vertices_from_header_even)
                    - 'year' is split depending on the year_separation parameter.
                        For example, a year_separation of 10 represents splitting
                        the years into decades.
                    - all other continuous attribute headers are split via the flat algorithm
                        (see SongGraph.generate_attr_vertices_from_header_flat)

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

        for attribute_header in EXACT_HEADERS:
            # Create an exact attribute vertex for each "state" of the attribute
            states = EXACT_HEADERS[attribute_header]

            for state in states:
                vertex = AttributeVertexExact(attribute_header, states[state], state)
                self._add_attribute_vertex(vertex)

        if use_parent:
            for attr_v in self.parent_graph.get_attribute_vertices():
                attribute_header = attr_v.attribute_header
                quantifier = attr_v.quantifier

                if attribute_header in CONTINUOUS_HEADERS:
                    new_v = AttributeVertexContinuous(attribute_header, quantifier, attr_v.value_interval)
                    self._add_attribute_vertex(new_v)

            self._attributes_created = True
            self._generate_edges()
            return

        for attribute_header in CONTINUOUS_HEADERS:
            if attribute_header == 'instrumentalness':
                self.generate_attr_vertices_from_header_even(attribute_header)
            elif attribute_header == 'year':
                # Separate years into decades
                min_year, max_year, _, _ = self.get_attribute_header_stats(attribute_header)

                min_decade = int(min_year // year_separation) * year_separation
                max_decade = int(max_year // year_separation) * year_separation

                for period_start in range(min_decade, max_decade + year_separation, year_separation):
                    period_end = period_start + year_separation
                    interval = Interval('closed', period_start, period_end, 'open')
                    attr_v = AttributeVertexContinuous(attribute_header, f'({period_start}-{period_end})', interval)
                    self._add_attribute_vertex(attr_v)

            else:
                self.generate_attr_vertices_from_header_flat(attribute_header)

        self._attributes_created = True
        self._generate_edges()


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
