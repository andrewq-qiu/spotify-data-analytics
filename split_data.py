"""Module for splitting the Spotify dataset into
songs by decade. This file is not imported by the program,
but has been used beforehand to pre-process the data.

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

import pandas


def split_songs_by_decade(start: int, end: int, dataset_filename: str, target_dir: str) -> None:
    """Open the Spotify song dataset at dataset_filename.

    Create a new csv file (or overwrite existing files) which contains songs
    from each decade in the range specified by start and end inclusive.
        - start and end represent the first year of the decade (1980, 2000, 2010)
        - Ex. if start=1980 and end=2000, then there will be a file created for
          the 1980s, 1990s, and 2000s.

    Preconditions:
        - start <= end
        - start % 10 == 0 and end % 10 == 0
    """

    songs = pandas.read_csv(dataset_filename)

    current_decade = start
    while current_decade <= end:
        # Dataframe containing songs of this decade
        df = songs.loc[(current_decade - 1 < songs['year']) & (songs['year'] < current_decade + 10)]
        df.to_csv(target_dir + f'/song_data_{current_decade}.csv', index=False)

        current_decade += 10


if __name__ == '__main__':
    import doctest
    import python_ta
    import python_ta.contracts

    doctest.testmod()

    python_ta.contracts.check_all_contracts()

    python_ta.check_all(config={
        'extra-imports': ['pandas'],
        'allowed-io': [],
        'max-line-length': 100,
        'disable': ['E1136']
    })

    # Running this will process create separate csv files splitting
    # the original dataset into the decades
    # split_songs_by_decade(1920, 2020, 'data/song_data_original.csv', 'data')
