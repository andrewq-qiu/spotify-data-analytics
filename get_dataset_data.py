"""This module contains functions for retrieving song data
from the Spotify dataset files.

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

import ast
import csv
from song_graph import SongGraph, Song, DATASET_HEADERS, FLOAT_HEADERS, INT_HEADERS


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
        if i not in {12, 6, 1}:
            # Then this row entry should be an attribute

            # The attribute name
            attr = DATASET_HEADERS[i]

            if attr in FLOAT_HEADERS:
                attributes[attr] = float(row[i])
            elif attr in INT_HEADERS:
                attributes[attr] = int(row[i])
            # Ignore all other headers

    return Song(name, spotify_id, artists, attributes)


def get_song_graph_from_decades(decades: set, year_separation: int = 10) -> SongGraph:
    """Return a song graph containing songs from each
    decade in decades from the pre-processed Spotify
    dataset files (these files can be created in the
    split_data.py module)

    Each element in decades is the first year of the decade.
    For example, if decades={1980, 2000, 1930},
    then get_songs_from_decades(decades) returns songs from the 80s,
    2000s, and 30s all in one song graph.

    year_separation defines the way year attribute vertices are to be
    created. I.e. the intervals in year attribute vertices. For example,
    a year_separation of 10 will create year attribute vertices
    for each decade spanned by the playlist.

    Preconditions:
        - all(decade % 10 = 0 for decade in decades)
        - all(1920 <= decade <= 2020 for decade in decades)
        - year_separation > 0
    """

    graph = SongGraph()

    for decade in decades:
        with open(f'data/song_data_{decade}.csv', 'r', encoding='Latin1') as f:
            reader = csv.reader(f)
            headers = next(reader)

            assert headers == DATASET_HEADERS
            for row in reader:
                # The na
                # me column occurs in index 12
                song = load_song_from_row(row)
                graph.add_song(song)

    graph.generate_attribute_vertices(year_separation)

    return graph


def get_song_graph_from_file(file_path: str, year_separation: int) -> SongGraph:
    """Return a song graph containing all songs in a
    Spotify dataset CSV file given a path.

    year_separation defines the way year attribute vertices are to be
    created. I.e. the intervals in year attribute vertices. For example,
    a year_separation of 10 will create year attribute vertices
    for each decade spanned by the playlist.

    Preconditions:
        - file_path points to a csv file
        - year_separation > 0
    """

    with open(file_path, 'r', encoding='Latin1') as f:
        reader = csv.reader(f)
        headers = next(reader)

        assert headers == DATASET_HEADERS

        graph = SongGraph()

        for row in reader:
            # The name column occurs in index 12
            song = load_song_from_row(row)
            graph.add_song(song)

        graph.generate_attribute_vertices(year_separation)

    return graph


if __name__ == '__main__':
    import doctest
    import python_ta
    import python_ta.contracts

    doctest.testmod()

    python_ta.contracts.check_all_contracts()

    python_ta.check_all(config={
        'extra-imports': ['ast', 'csv', 'song_graph'],
        'allowed-io': ['get_song_graph_from_decades', 'get_song_graph_from_file'],
        'max-line-length': 100,
        'disable': ['E1136']
    })
