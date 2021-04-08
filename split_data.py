"""Module for splitting the Spotify dataset into
songs by decade.

This helps with loading less data into memory.
"""

import pandas


def split_songs_by_decade(start: int, end: int, dataset_filename: str, target_dir: str):
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
    split_songs_by_decade(1920, 2020, 'data/song_data_original.csv', 'data')
