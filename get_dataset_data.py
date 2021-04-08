import ast
import csv
from song_graph import SongGraph, Song, HEADERS, FLOAT_HEADERS, INT_HEADERS


def load_song_from_row(row: list[str]) -> Song:
    """Create a Song class instance based on a row
    in the precompiled Spotify dataset

    Preconditions:
        - row is a non-header row in the Spotify dataset
    """

    # Name column occurs in index 12
    # Spotify ID column occurs in index 6
    # Artists column occurs in index 1
    name, spotify_id, artists = row[12], row[6], ast.literal_eval(row[1])
    # row[1] (artists) is a string representation of a list
    # so we call ast.literal_eval to convert into a list

    attributes = {}

    # Create a dictionary for all other attributes
    for i in range(len(row)):
        if i != 12 and i != 6 and i != 1:
            # Then this row entry should be an attribute

            # The attribute name
            attr = HEADERS[i]

            if attr in FLOAT_HEADERS:
                attributes[attr] = float(row[i])
            elif attr in INT_HEADERS:
                attributes[attr] = int(row[i])
            # Ignore all other headers

    return Song(name, spotify_id, artists, attributes)


def get_song_graph_from_decades(decades: set) -> SongGraph:
    """Return a song graph containing songs from the
    decades in decades.

    Each element in decades is the first year of the decade.
    For example, if decades={1980, 2000, 1930},
    then get_songs_from_decades(decades) returns songs from the 80s,
    2000s, and 30s.
    """

    for decade in decades:
        with open(f'data/song_data_{decade}.csv', 'r', encoding='Latin1') as f:
            reader = csv.reader(f)
            headers = next(reader)

            assert headers == HEADERS

            graph = SongGraph()

            for row in reader:
                # The name column occurs in index 12
                song = load_song_from_row(row)
                graph.add_song(song)

    graph.generate_attribute_vertices()

    return graph


def get_song_graph_from_file(file_name: str) -> SongGraph:
    """Load the precompiled Spotify data from the file at file_name

    Preconditions:
        - file_name points to a csv file
        - the csv file follows the structure of the Spotify Song Dataset (TODO: SEE SOMETHING)
    """

    with open(file_name, 'r', encoding='Latin1') as f:
        reader = csv.reader(f)
        headers = next(reader)

        assert headers == HEADERS

        graph = SongGraph()

        for row in reader:
            # The name column occurs in index 12
            song = load_song_from_row(row)
            graph.add_song(song)

        graph.generate_attribute_vertices()

    return graph
